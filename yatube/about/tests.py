from http import HTTPStatus

from django.test import Client, TestCase


class AboutURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_exists(self):
        """Существование общедоступных страниц."""
        urls = (
            '/about/author/',
            '/about/tech/',
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(f'{url}')
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'Ошибка при получении страницы: "{url}", '
                    f'код ответа: {response.status_code}'
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = (
            '/about/author/',
            '/about/tech/',
        )
        templates = (
            'about/author.html',
            'about/tech.html',
        )
        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
