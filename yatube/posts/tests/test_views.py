import shutil

from django.core.cache import cache
from django.test import Client, TestCase, override_settings

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User

from .test_forms import TEMP_MEDIA_ROOT, get_small_gif, get_url


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user('Ivanov34')
        cls.group = Group.objects.create(
            title='Спорт',
            description='Про спорт',
        )
        cls.post = Post.objects.create(
            text='Текст поста в группе спорт длинной более 30 символов',
            author=cls.user,
            group=cls.group,
            image=get_small_gif('sport_post_image')
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsPagesTests.user)
        cache.clear()

    def assertPostEqual(self, post1, post2):
        attributes = ('id', 'text', 'author', 'group', 'image')

        for attr in attributes:
            with self.subTest(attr=attr):
                self.assertEqual(getattr(post1, attr), getattr(post2, attr))

    # Проверяем используемые шаблоны
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls = (
            get_url('posts:index'),
            get_url('posts:group_list', slug=PostsPagesTests.group.slug),
            get_url('posts:post_detail', post_id=PostsPagesTests.post.id),
            get_url('posts:profile', username=PostsPagesTests.user.username),
            get_url('posts:post_edit', post_id=PostsPagesTests.post.id),
            get_url('posts:post_create'),
        )
        templates = (
            'posts/index.html',
            'posts/group_list.html',
            'posts/post_detail.html',
            'posts/profile.html',
            'posts/create_post.html',
            'posts/create_post.html',
        )
        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_url_contains_post(self):
        """Словарь context главной страницы содержит 10 последних постов."""
        response = self.authorized_client.get(get_url('posts:index'))
        posts = response.context['page_obj'].object_list

        self.assertEqual(list(posts), list(Post.objects.all()[:10]))
        self.assertPostEqual(posts[0], PostsPagesTests.post)

    def test_group_list_url_contains_post_and_group(self):
        """Словарь context страницы группы содержит 10 последних постов группы
        и саму группу"""
        response = self.authorized_client.get(
            get_url('posts:group_list', slug=PostsPagesTests.group.slug)
        )
        posts = response.context['page_obj'].object_list
        group = response.context['group']

        self.assertEqual(
            posts,
            list(Post.objects.all()[:10])
        )
        self.assertEqual(group, PostsPagesTests.group)
        self.assertPostEqual(posts[0], PostsPagesTests.post)

    def test_profile_url_contains_post_group_and_author(self):
        """Словарь context страницы пользователя содержит 10 последних
        постов пользователя, группу и автора поста, а в posts_count указано
        верное количество постов автора"""
        response = self.authorized_client.get(
            get_url('posts:profile', username=PostsPagesTests.user.username)
        )
        posts = response.context['page_obj'].object_list
        author = response.context['author']
        posts_count = response.context['posts_count']

        self.assertEqual(
            posts,
            list(PostsPagesTests.user.posts.all()[:10])
        )
        self.assertEqual(author, PostsPagesTests.user)
        self.assertEqual(posts_count, PostsPagesTests.user.posts.count())
        self.assertPostEqual(posts[0], PostsPagesTests.post)

    def test_post_detail_url_contains_post(self):
        """Словарь context страницы поста содержит сам пост, переменную
        title содержащую первые 30 символов текста поста, все комментарии к
        посту и форму создания комментария"""
        response = self.authorized_client.get(
            get_url('posts:post_detail', post_id=PostsPagesTests.post.id),
        )
        page_post = response.context['post']
        comments = response.context['comments']
        comment_form = response.context['comment_form']
        title = response.context['title']

        self.assertEqual(title, 'Пост "Текст поста в группе спорт дли"')
        self.assertPostEqual(page_post, PostsPagesTests.post)
        self.assertIsInstance(comment_form, CommentForm)
        self.assertEqual(
            list(comments),
            list(PostsPagesTests.post.comments.all())
        )

    def test_post_detail_url_contains_new_comment(self):
        """Словарь context страницы поста содержит новый комментарий"""
        self.authorized_client.post(
            get_url('posts:add_comment', post_id=PostsPagesTests.post.id),
            data={'text': 'Новый комментарий'},
            follow=True,
        )
        response = self.authorized_client.get(
            get_url('posts:post_detail', post_id=PostsPagesTests.post.id),
        )
        comments = response.context['comments']

        self.assertEqual(
            list(comments),
            list(PostsPagesTests.post.comments.all())
        )

    def test_post_create_url_contains_post_form(self):
        """Страница post_create содержит форму создания поста (PostForm)."""
        response = self.authorized_client.get(
            get_url('posts:post_create')
        )
        form = response.context['form']
        self.assertIsInstance(form, PostForm)

    def test_post_edit_url_contains_post_form_with_post_data(self):
        """Страница post_edit содержит форму создания поста
        с данными самого поста."""
        response = self.authorized_client.get(
            get_url('posts:post_edit', post_id=PostsPagesTests.post.id)
        )
        form = response.context['form']
        self.assertIsInstance(form, PostForm)
        self.assertEqual(form.initial['text'], PostsPagesTests.post.text)
        self.assertEqual(form.initial['group'], PostsPagesTests.post.group.id)

    def test_index_url_contains_cache_index_page(self):
        """Посты на главной странице кешируются"""
        new_post = Post.objects.create(
            text='Пост для проверки кеширования',
            author=PostsPagesTests.user,
        )
        response = self.authorized_client.get(get_url('posts:index'))
        posts = response.content
        new_post.delete()
        response = self.authorized_client.get(get_url('posts:index'))
        cached_posts = response.content

        self.assertEqual(posts, cached_posts)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user1 = User.objects.create_user('Ivanov34')
        cls.user2 = User.objects.create_user('Smirnov61')
        cls.group1 = Group.objects.create(
            title='Спорт',
            description='Группа о спорте',
        )
        cls.group2 = Group.objects.create(
            title='Новости',
            description='Группа о новостях',
        )
        for i in range(34):
            if i % 2 == 1:
                Post.objects.create(
                    text=f'{i}',
                    author=cls.user1,
                    group=cls.group1
                )
            else:
                Post.objects.create(
                    text=f'{i}',
                    author=cls.user2,
                    group=cls.group2
                )
        cls.post = Post.objects.create(
            text='Самый последний пост',
            author=cls.user1,
            group=cls.group2
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_page_records(self):
        """Страница содержит правильное кол-во постов."""
        urls = (
            get_url('posts:index'),
            get_url('posts:index') + '?page=4',
            get_url('posts:group_list', slug=PaginatorViewsTest.group1.slug),
            get_url('posts:group_list',
                    slug=PaginatorViewsTest.group2.slug
                    ) + '?page=2',
            get_url('posts:profile',
                    username=PaginatorViewsTest.user1.username),
            get_url('posts:profile',
                    username=PaginatorViewsTest.user2.username
                    ) + '?page=2',
        )
        posts_count = (10, 5, 10, 8, 10, 7,)

        for url, page_posts_count in zip(urls, posts_count):
            with self.subTest(page_posts_count=page_posts_count):
                response = self.guest_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 page_posts_count)


class NewPostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user('Ivanov34')
        cls.group1 = Group.objects.create(
            title='Спорт',
            description='Группа о спорте',
        )
        cls.group2 = Group.objects.create(
            title='Новости',
            description='Группа о новостях',
        )
        cls.post = Post.objects.create(
            text='Новый пост',
            author=cls.user,
            group=cls.group1
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_new_post_on_page(self):
        """Новый пост отображается на страницах группы, автора и главной."""
        urls = (
            get_url('posts:index'),
            get_url('posts:group_list', slug=NewPostTest.group1.slug),
            get_url('posts:profile', username=NewPostTest.user.username),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                post = response.context['page_obj'][0]
                self.assertEqual(post, NewPostTest.post)

    def test_new_post_not_in_different_group(self):
        """Новый пост не отображается в чужой группе."""
        response = self.guest_client.get(
            get_url('posts:group_list', slug=NewPostTest.group2.slug),
        )
        posts = response.context['page_obj']
        self.assertNotIn(NewPostTest.post, posts)


class FollowModuleTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user('Ivanov34')
        cls.follower = User.objects.create_user('Smirnov61')
        cls.unfollower = User.objects.create_user('Sidorov48')
        Follow.objects.create(
            author=cls.author, user=cls.follower
        )

    def setUp(self):
        self.follower_client = Client()
        self.follower_client.force_login(FollowModuleTest.follower)
        self.unfollower_client = Client()
        self.unfollower_client.force_login(FollowModuleTest.unfollower)
        cache.clear()

    def test_new_author_post_see_followers_and_unseen_unfollowers(self):
        """Новая запись пользователя появляется в ленте тех, кто подписан на
        автора и не появляется в ленте тех, кто не подписан."""
        Post.objects.create(
            text='Новый пост',
            author=FollowModuleTest.author,
        )
        response = self.follower_client.get(get_url('posts:follow_index'))
        follower_posts = response.context['page_obj']

        response = self.follower_client.get(get_url('posts:follow_index'))
        unfollower_posts = response.context['page_obj']

        self.assertNotEqual(follower_posts, unfollower_posts)

    def test_user_can_follow_and_unfollow_on_another_user(self):
        """Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок."""
        self.follower_client.get(
            get_url(
                'posts:profile_follow',
                username=FollowModuleTest.author.username
            ),
        )
        self.assertTrue(
            Follow.objects.filter(
                author=FollowModuleTest.author,
                user=FollowModuleTest.follower
            ).exists()
        )
        self.follower_client.get(
            get_url(
                'posts:profile_unfollow',
                username=FollowModuleTest.author.username
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                author=FollowModuleTest.author,
                user=FollowModuleTest.follower
            ).exists()
        )
