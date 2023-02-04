from http import HTTPStatus

from django.test import Client, TestCase

from posts.models import User


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Ivanov34')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersURLTests.user)

    # Общедоступные страницы
    def test_public_urls_exists(self):
        """Существование общедоступных страниц."""
        urls = (
            '/auth/signup/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/<uidb64>/<token>/',
            '/auth/reset/done/',
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(f'{url}')
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'Ошибка при получении страницы: "{url}", '
                    f'код ответа: {response.status_code}'
                )

    def test_urls_redirect_anonymous_on_login(self):
        """Переадресация неавторизованного пользователя."""
        login_url = '/auth/login/'
        password_change_url = '/auth/password_change/'
        password_change_done_url = '/auth/password_change/done/'
        urls = (
            password_change_url,
            password_change_done_url
        )
        redirect_urls = (
            f'{login_url}?next={password_change_url}',
            f'{login_url}?next={password_change_done_url}',
        )
        for url, redirect_url in zip(urls, redirect_urls):
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, redirect_url)

    # Страницы для авторизованных пользователей
    def test_authorized_user_url_accesses(self):
        """Доступ к страницам для авторизованного пользователя."""
        urls = (
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/logout/',
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'Ошибка при получении страницы: {url}, '
                    f'код ответа: {response.status_code}'
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = (
            '/auth/signup/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/<uidb64>/<token>/',
            '/auth/reset/done/',
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/logout/',
        )
        templates = (
            'users/signup.html',
            'users/login.html',
            'users/password_reset_form.html',
            'users/password_reset_done.html',
            'users/password_reset_confirm.html',
            'users/password_reset_complete.html',
            'users/password_change_form.html',
            'users/password_change_done.html',
            'users/logged_out.html',
        )
        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
