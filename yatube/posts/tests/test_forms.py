import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


def get_url(url: str, **kwargs) -> str:
    """Принимает строку вида 'namespace:name'
    и возвращает url для данного пути"""
    return reverse(url, kwargs=kwargs)


def get_small_gif(filename: str = 'filename') -> SimpleUploadedFile:
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    )
    uploaded = SimpleUploadedFile(
        name=f'{filename}.gif',
        content=small_gif,
        content_type='image/gif'
    )
    return uploaded


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='Ivanov37')
        cls.group1 = Group.objects.create(
            title='Культура',
            description='Про культуру',
        )
        cls.group2 = Group.objects.create(
            title='Спорт',
            description='Про спорт',
        )
        cls.post = Post.objects.create(
            text='Не более 15 символов может уместиться в превью',
            author=cls.user,
            group=cls.group1
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_create_post_add_new_post(self):
        """Заполненная форма создает запись в Post."""
        old_posts_id = list(Post.objects.values_list('id', flat=True))
        posts_count = Post.objects.count()
        filename = 'new_post_image'
        form_data = {
            'text': 'Новый пост',
            'group': PostFormTests.group1.id,
            'image': get_small_gif(f'{filename}'),
        }
        response = self.authorized_client.post(
            get_url('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            get_url(
                'posts:profile',
                username=PostFormTests.user.username
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        new_post = Post.objects.filter(
            text='Новый пост',
            group=PostFormTests.group1,
            author=PostFormTests.user,
            image=f'posts/{filename}.gif'
        )
        self.assertTrue(new_post.exists())
        self.assertNotIn(new_post.first().id, old_posts_id)

    def test_edit_post_not_add_new_post(self):
        """Редактирование поста не создаёт запись в Post,
        а изменяет существующую."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': PostFormTests.group2.id,
            'image': get_small_gif('edit_post_image'),
        }
        response = self.authorized_client.post(
            get_url('posts:post_edit', post_id=PostFormTests.post.id),
            data=form_data,
            follow=True
        )
        PostFormTests.post.refresh_from_db()

        self.assertRedirects(
            response,
            get_url('posts:post_detail', post_id=PostFormTests.post.id),
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            PostFormTests.post.text, 'Отредактированный текст'
        )
        self.assertEqual(
            PostFormTests.post.group, PostFormTests.group2
        )
        self.assertIsNotNone(PostFormTests.post.image)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(username='Ivanov37')
        cls.group = Group.objects.create(
            title='Культура',
            description='Про культуру',
        )
        cls.post = Post.objects.create(
            text='Не более 15 символов может уместиться в превью',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentFormTests.user)

    def test_create_post_add_new_post(self):
        """Заполненная форма создает запись в Comments, а пользователь
        перенаправляется на страницу поста."""
        old_comments_id = list(Comment.objects.values_list('id', flat=True))
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.authorized_client.post(
            get_url('posts:add_comment', post_id=CommentFormTests.post.id),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            get_url(
                'posts:post_detail',
                post_id=CommentFormTests.post.id
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

        new_comment = Comment.objects.filter(
            text='Новый комментарий',
            author=CommentFormTests.user,
            post=CommentFormTests.post,
        )
        self.assertTrue(new_comment.exists())
        self.assertNotIn(new_comment.first().id, old_comments_id)
