from django.test import Client, TestCase

from posts.models import User
from posts.tests.test_forms import get_url
from users.forms import CreationForm


class UsersPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Ivanov34')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(UsersPagesTests.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = (
            get_url('users:password_change_form'),
            get_url('users:password_change_done'),
            get_url('users:logout'),
            get_url('users:signup'),
            get_url('users:login'),
            get_url('users:password_reset_form'),
            get_url('users:password_reset_done'),
            get_url('users:password_reset_confirm', uidb64='1', token='1'),
            get_url('users:password_reset_complete'),
        )
        templates = (
            'users/password_change_form.html',
            'users/password_change_done.html',
            'users/logged_out.html',
            'users/signup.html',
            'users/login.html',
            'users/password_reset_form.html',
            'users/password_reset_done.html',
            'users/password_reset_confirm.html',
            'users/password_reset_complete.html',
        )
        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_signup_url_contains_creation_form(self):
        """Словарь context страницы регистрации содержит форму CreationForm."""
        response = self.authorized_client.get(get_url('users:signup'))
        form = response.context['form']
        self.assertIsInstance(form, CreationForm)
