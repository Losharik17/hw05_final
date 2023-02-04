from django.contrib import admin

from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'

    # Хотел ограничить длину текста, но тесты не пускают
    # def short_text(self, obj):
    #     return obj.text[:settings.POST_TEXT_LENGTH]
    # short_text.short_description = 'Текст'


admin.site.register(Post, PostAdmin)
admin.site.register(Group)
admin.site.register(Comment)
