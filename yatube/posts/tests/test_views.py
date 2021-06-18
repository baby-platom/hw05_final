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
        response_1 = self.guest_client.get(reverse('index'))
        response_2 = self.guest_client.get(reverse('index'))
        cache.clear()
        response_3 = self.guest_client.get(reverse('index'))
        self.assertEqual(response_1.content, response_2.content)
        self.assertNotEqual(response_1.content, response_3.content)

    def test_authorized_can_subscribe(self):
        """Авторизированный пользователь может подписываться и отписываться."""
        Follow.objects.create(
            user=self.test_user,
            author=self.another_user
        )
        subscribe_exist = Follow.objects.filter(
            user=self.test_user,
            author=self.another_user).exists()
        Follow.objects.filter(
            user=self.test_user,
            author=self.another_user).delete()
        subscribe_not_exist = Follow.objects.filter(
            user=self.test_user,
            author=self.another_user).exists()
        self.assertTrue(subscribe_exist)
        self.assertFalse(subscribe_not_exist)

    def test_follow_page_work_properly(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан на него."""
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
        another_post = Post.objects.create(
            text='Особый текст',
            author=self.additional_user,
        )
        response = self.authorized_client.get(reverse("follow_index"))
        test_user_context = response.context['page'][0]
        self.assertNotEqual(test_user_context.author, another_post.author)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AndreyG')
        for i in range(1, 14):
            Post.objects.create(
                text=f'Тестовый текст{i}',
                author=cls.user,
            )

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
