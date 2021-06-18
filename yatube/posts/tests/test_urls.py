from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='AndreyG')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.test_user,
        )
        cls.post_id = cls.post.id

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.another_user = User.objects.create_user(username='DaBaby')
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.another_user)

    def test_index_url_exists_at_desired_location(self):
        """Страницы /, /<username>/, /<username>/<post_id>/
        доступны любому пользователю."""
        url_names = (
            '/',
            '/AndreyG/',
            '/AndreyG/1/'

        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response_code = self.guest_client.get(adress)
                self.assertEqual(response_code.status_code, HTTPStatus.OK)

    def test_new_post_url_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /new/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/new/')

    def test_edit_post_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /<username>/<post_id>/edit/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(reverse('post_edit', kwargs={
            'username': PostURLTests.test_user,
            'post_id': PostURLTests.post_id
        }), follow=True)
        self.assertRedirects(
            response,
            '/auth/login/?next=/AndreyG/'
            f'{PostURLTests.post_id}/edit/'
        )

    def test_post_edit_url_exists_at_desired_location_for_author(self):
        """Страница /<username>/<post_id>/edit/ доступна
        авторизованному пользователю автору поста."""
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': PostURLTests.test_user,
            'post_id': PostURLTests.post_id
        }))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location_for_not_author(self):
        """Страница /<username>/<post_id>/edit/ не доступна
        авторизованному пользователю не автору поста."""
        client = self.another_authorized_client
        response = client.get(reverse('post_edit', kwargs={
            'username': PostURLTests.test_user,
            'post_id': PostURLTests.post_id
        }))
        self.assertRedirects(
            response, f'/AndreyG/{PostURLTests.post_id}/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/post_new_or_edit.html': '/new/',
            'posts/profile.html': '/AndreyG/',
            'posts/post.html': '/AndreyG/1/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create_user(username='AndreyG')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.test_user
        )

        cls.group = Group.objects.create(
            title='Постовый текст',
            slug='some-slug',
            description='Какое-то описание'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = GroupURLTests.test_user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_group_url_exists_at_desired_location(self):
        """Страница /group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get('/group/some-slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/group.html': '/group/some-slug/',
            'posts/post_new_or_edit.html':
                f'/{GroupURLTests.test_user.username}/'
                f'{GroupURLTests.post.id}/edit/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)


class DefunctURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_response(self):
        """При вызове к несуществующей странице
        сервер возвращает код 404."""
        response = self.guest_client.get('/baby_admin/0/')
        self.assertEqual(response.status_code, 404)
