import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostGroupPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='AndreyG')
        cls.group = Group.objects.create(
            title='Постовый текст',
            slug='some-slug',
            description='Какое-то описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.test_user,
            group=cls.group,
            image=cls.uploaded
        )

        cls.username = cls.post.author.username
        cls.post_id = cls.post.id

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = PostGroupPagesTests.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.another_user = User.objects.create_user(username='DaBaby')
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)

        self.additional_user = User.objects.create_user(username='NaBaby')
        self.additional_client = Client()
        self.additional_client.force_login(self.additional_user)

        cache.clear()

    def _assert_post_fields(self, first_object):
        author = self.test_user
        text = self.post.text
        group = self.group
        image = self.post.image
        self.assertEqual(first_object.author, author)
        self.assertEqual(first_object.text, text)
        self.assertEqual(first_object.group, group)
        self.assertEqual(first_object.image, image)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/post_new_or_edit.html': reverse('new_post'),
            'posts/group.html': (
                reverse('group_posts', kwargs={'slug': 'some-slug'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        self._assert_post_fields(first_object)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('profile', kwargs={
            'username': PostGroupPagesTests.username,
        }))
        first_object = response.context['page'][0]
        self._assert_post_fields(first_object)

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('post', kwargs={
            'username': PostGroupPagesTests.username,
            'post_id': PostGroupPagesTests.post_id,
        }))
        first_object = response.context['post']
        self._assert_post_fields(first_object)

    def test_post_edit_post_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': PostGroupPagesTests.username,
            'post_id': PostGroupPagesTests.post_id,
        }))
        content = response.context['form'].instance
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

        self.assertEqual(content.text, 'Тестовый текст')
        self.assertEqual(content.author, PostGroupPagesTests.test_user)
        self.assertEqual(content.group, PostGroupPagesTests.group)

    def test_group_posts_page_shows_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'some-slug'}))
        first_object = response.context['page'][0]
        self._assert_post_fields(first_object)

    def test_index_use_cache_appropriately(self):
        """Страница index использует кэш правильно."""
        initial_response = self.guest_client.get(reverse('index'))
        Post.objects.create(
            text='Условный текст',
            author=self.another_user
        )
        cached_response = self.guest_client.get(reverse('index'))
        cache.clear()
        non_cached_response = self.guest_client.get(reverse('index'))
        self.assertEqual(initial_response.content, cached_response.content)
        self.assertNotEqual(initial_response.content,
                            non_cached_response.content)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

        cls.test_user = User.objects.create_user(username='AndreyB')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.test_user)

        cls.another_user = User.objects.create_user(username='DaBaby')
        cls.another_authorized_client = Client()
        cls.another_authorized_client.force_login(cls.another_user)

        cls.additional_user = User.objects.create_user(username='NaBaby')
        cls.additional_client = Client()
        cls.additional_client.force_login(cls.additional_user)

    def test_follow_page_work_properly_for_subscribers(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        Follow.objects.create(
            user=self.test_user,
            author=self.another_user
        )
        post = Post.objects.create(
            text='Специальный текст',
            author=self.another_user,
        )
        response = self.authorized_client.get(reverse("follow_index"))
        test_user_context = response.context['page'][0]
        self.assertEqual(test_user_context.author, post.author)

    def test_follow_page_work_properly_for_not_subscribers(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто не подписан на него."""
        Post.objects.create(
            text='Особый текст',
            author=self.additional_user,
        )
        response = self.authorized_client.get(reverse("follow_index"))
        test_user_context = response.context['page']
        self.assertEqual(len(test_user_context), 0)

    def test_authorized_can_follow(self):
        """Авторизированный пользователь может подписываться."""
        self.authorized_client.get(reverse(
            "profile_follow",
            kwargs={'username': 'DaBaby'}
        ))
        existence = Follow.objects.filter(
            user=self.test_user,
            author=self.another_user
        ).exists()
        self.assertTrue(existence)

    def test_authorized_can_unfollow(self):
        """Авторизированный пользователь может  отписываться."""
        Follow.objects.create(
            user=self.test_user,
            author=self.another_user
        )
        self.authorized_client.get(reverse(
            "profile_unfollow",
            kwargs={'username': 'DaBaby'}
        ))
        existence = Follow.objects.filter(
            user=self.test_user,
            author=self.another_user
        ).exists()
        self.assertFalse(existence)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AndreyG')
        Post.objects.bulk_create([
            Post(text=f'Тестовый текст{i}', author=cls.user)
            for i in range(1, 14)
        ])

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
