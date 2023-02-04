from django.test import TestCase

from posts.models import Group, Post, User


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user('Ivanov34')
        cls.group = Group.objects.create(
            title='Спорт',
            description='Всё о спорте',
        )
        cls.post = Post.objects.create(
            text='Не более 15 символов может уместиться в превью',
            author=cls.user,
            group=cls.group
        )

    def test_model_post__str__method_return_post_text_max_15_symbols(self):
        """Метод __str__ возвращает текст поста(не более 15 символов)."""
        post = ModelsTest.post
        self.assertEqual(str(post), 'Не более 15 сим')

    def test_model_group__str__method_return_group_title(self):
        """Метод __str__ возвращает название группы."""
        group = ModelsTest.group
        self.assertEqual(str(group), 'Спорт')
