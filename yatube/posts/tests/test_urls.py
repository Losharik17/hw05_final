from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user('Ivanov34')
        cls.group = Group.objects.create(
            title='Спорт',
            description='Группа о спорте',
        )
        cls.post = Post.objects.create(
            text='Не более 15 символов может уместиться в превью',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        cache.clear()

    # Общедоступные страницы
    def test_public_urls_exists(self):
        """Существование общедоступных страниц."""
        urls = (
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            f'/posts/{PostsURLTests.post.id}/',
            f'/profile/{PostsURLTests.user.username}/',
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(
                    response.status_code, HTTPStatus.OK,
                    f'Ошибка при получении страницы: {url}, '
                    f'код ответа: {response.status_code}'
                )

    def test_unexisting_url_not_found(self):
        """Код 404 при запросе несуществующей страницы и использование
        кастомного шаблона"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_redirect_anonymous_on_login(self):
        """Переадресация неавторизованного пользователя."""
        login_url = '/auth/login/'
        urls = {
            '/create/',
            f'/posts/{PostsURLTests.post.id}/edit/',
            f'/posts/{PostsURLTests.post.id}/comment/',
            '/follow/',
            f'/profile/{PostsURLTests.user.username}/follow/',
            f'/profile/{PostsURLTests.user.username}/unfollow/',
        }
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(
                    response,
                    f'{login_url}?next={url}'
                )

    # Страницы для авторизованных пользователей
    def test_post_create_url_accesses(self):
        """Доступ к странице создания поста."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_nonauthor_redirect(self):
        """Перенаправление при попытке редактировать чужой пост."""
        user = User.objects.create_user('Smirnov61')
        authorized_client = Client()
        authorized_client.force_login(user)

        response = authorized_client.get(
            f'/posts/{PostsURLTests.post.id}/edit/'
        )
        redirect_url = f'/posts/{PostsURLTests.post.id}/'

        self.assertRedirects(response, redirect_url)

    # Персональные страницы пользователя
    def test_post_edit_author_accesses(self):
        """Доступ к странице редактирования поста."""
        response = self.authorized_client.get(
            f'/posts/{PostsURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = (
            '/',
            f'/group/{PostsURLTests.group.slug}/',
            f'/posts/{PostsURLTests.post.id}/',
            f'/profile/{PostsURLTests.user.username}/',
            f'/posts/{PostsURLTests.post.id}/edit/',
            '/create/',
            '/follow/',
        )
        templates = (
            'posts/index.html',
            'posts/group_list.html',
            'posts/post_detail.html',
            'posts/profile.html',
            'posts/create_post.html',
            'posts/create_post.html',
            'posts/follow.html',
        )
        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
