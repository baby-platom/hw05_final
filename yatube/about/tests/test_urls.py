from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_author_and_author(self):
        """Страницы author и tech доступны любому пользователю."""
        url_names = (
            '/about/author/',
            '/about/tech/'
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response_code = self.guest_client.get(adress).status_code
                self.assertEqual(response_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
