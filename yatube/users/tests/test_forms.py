from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User


class UserCreateFormTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_signup_create_new_user(self):
        """Валидная форма создает нового пользователя."""
        users_count = User.objects.count()
        form_data = {
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
            'username': 'Ivanov34',
            'email': 'ivanov34@mail.ru',
            'password1': '456721s89sd26',
            'password2': '456721s89sd26',
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(User.objects.filter(username='Ivanov34').exists())
