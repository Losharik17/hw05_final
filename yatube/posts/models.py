from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from core.debugging_tools import slugify

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200, verbose_name='Название',
        help_text='Название группы'
    )
    slug = models.SlugField(unique=True, help_text='slug группы')
    description = models.TextField(
        verbose_name='Описание',
        help_text='Информация о группе'
    )

    def __str__(self):
        return f'{self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:100]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Группы"
        verbose_name = "Группа"


class Post(models.Model):
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Дата публикации поста',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Автор поста',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа к которой относится пост',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Картинка на странице поста',
    )

    def __str__(self):
        return self.text[:settings.POST_TEXT_LENGTH]

    class Meta:
        verbose_name_plural = "Посты"
        verbose_name = "Пост"
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
        help_text='Пост к которому относится комментарий',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
        help_text='Автор комментария',
    )
    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст комментария'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
        help_text='Дата публикации комментария',
    )

    def __str__(self):
        return (f'{self.author.username} '
                f'[{self.created.strftime("%H:%M %d.%m.%y")}]: '
                f'{self.text[:30]}')

    class Meta:
        verbose_name_plural = "Комментарии"
        verbose_name = "Комментарий"
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE,
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_author_user_following'
            )
        ]
