from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_and_tech_page_accessible_by_name(self):
        """URL, генерируемый при помощи имени author и tech, доступен."""
        url_names = (
            'about:author',
            'about:tech'
        )
        for name in url_names:
            with self.subTest(name=name):
                response = self.guest_client.get(reverse(name))
                response_code = response.status_code
                self.assertEqual(response_code, HTTPStatus.OK)

    def test_author_and_tech_page_uses_correct_template(self):
        """При запросе к author и tech
        применяется шаблон author.html и tech.html"""
        templates_url_names = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for name, template in templates_url_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse(name))
                self.assertTemplateUsed(response, template)
