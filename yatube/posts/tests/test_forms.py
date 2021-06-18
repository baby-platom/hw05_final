import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_user = User.objects.create_user(username='AndreyG')

        cls.group = Group.objects.create(
            title='Имя группы',
            slug='some-slug',
            description='Какое-то описание'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.test_user,
            group=cls.group
        )

        cls.another_group = Group.objects.create(
            title='Имя другой группы',
            slug='some-slug2',
            description='Какое-то описание2'
        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = PostCreateFormTests.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Типичный текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_obj = Post.objects.get(text='Типичный текст')
        fields = {
            'Типичный текст': post_obj.text,
            self.group.id: post_obj.group.id,
            self.test_user: post_obj.author,
            'media/small.gif': post_obj.image.name
        }
        for value, expected in fields.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_edit_post(self):
        """Валидная форма меняет запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый текст',
            'group': PostCreateFormTests.another_group.id,
        }

        response = self.authorized_client.post(
            reverse('post_edit',
                    kwargs={
                        'username': PostCreateFormTests.test_user,
                        'post_id': PostCreateFormTests.post.id
                    }),
            data=form_data,
            follow=True)
        self.assertRedirects(
            response,
            '/AndreyG/'
            f'{PostCreateFormTests.post.id}/')
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Новый текст',
                author=PostCreateFormTests.post.author,
                group=PostCreateFormTests.another_group
            ).exists())
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст',
                author=PostCreateFormTests.post.author,
                group=PostCreateFormTests.group
            ).exists())

    def test_comment_post(self):
        comments_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(
            reverse('add_comment', kwargs={
                'username': 'AndreyG',
                'post_id': 1
            }),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('post', kwargs={
            'username': 'AndreyG',
            'post_id': 1
        }))
        self.assertEqual(Comment.objects.count(), comments_count + 1)
