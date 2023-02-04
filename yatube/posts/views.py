from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (TemplateView, CreateView, UpdateView,
                                  FormView, View)

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Follow


def get_page_object(page_number: int, model_list):
    """Принимает номер страницы и список объектов из model.
    Возвращает объект класса Page."""
    paginator = Paginator(model_list, settings.PAGE_SIZE)
    return paginator.get_page(page_number)


class IndexView(TemplateView):
    template_name = 'posts/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)

        post_list = Post.objects.select_related('author', 'group').all()
        page_obj = get_page_object(self.request.GET.get('page'), post_list)
        context['page_obj'] = page_obj

        return context


class GroupPostsView(TemplateView):
    template_name = 'posts/group_list.html'

    def get_context_data(self, slug, **kwargs):
        context = super(GroupPostsView, self).get_context_data(**kwargs)

        group = get_object_or_404(
            Group.objects.prefetch_related('posts__author'),
            slug=slug
        )
        post_list = group.posts.all()
        page_obj = get_page_object(self.request.GET.get('page'), post_list)

        context.update({
            'group': group,
            'page_obj': page_obj,
        })
        return context


class ProfileView(TemplateView):
    template_name = 'posts/profile.html'

    def get_context_data(self, username, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)

        user = get_object_or_404(
            User.objects.prefetch_related('posts', 'following'),
            username=username
        )
        post_list = user.posts.all()
        page_obj = get_page_object(self.request.GET.get('page'), post_list)
        posts_count = page_obj.paginator.count

        following = None
        if self.request.user.is_authenticated and user != self.request.user:
            following = Follow.objects.filter(
                user=self.request.user, author=user,
            ).exists()

        context.update({
            'author': user,
            'page_obj': page_obj,
            'posts_count': posts_count,
            'followers_count': user.following.count(),
            'following': following,
        })
        return context


class PostDetailView(TemplateView):
    template_name = 'posts/post_detail.html'

    def get_context_data(self, post_id, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)

        post = get_object_or_404(
            Post.objects.select_related(
                'author', 'group'
            ).prefetch_related('comments__author'),
            pk=post_id
        )
        title = f'Пост "{post.text[:30]}"'

        context.update({
            'title': title,
            'post': post,
            'comment_form': CommentForm(),
            'comments': post.comments.all(),
        })
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    template_name = 'posts/create_post.html'
    form_class = PostForm

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.request.user
        post.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy(
            'posts:profile',
            kwargs={'username': self.request.user.username}
        )


class PostEditView(UpdateView):
    template_name = 'posts/create_post.html'
    form_class = PostForm
    model = Post

    def get_object(self, queryset=None):
        obj = Post.objects.select_related('group').get(
            id=self.kwargs['post_id']
        )
        return obj

    def get_context_data(self, **kwargs):
        context = super(PostEditView, self).get_context_data(**kwargs)
        context['post_id'] = self.kwargs['post_id']
        return context

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != self.request.user:
            return redirect(self.get_success_url())
        return super(PostEditView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'posts:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class AddCommentView(LoginRequiredMixin, FormView):
    form_class = CommentForm

    def form_valid(self, form):
        comment = form.save(commit=False)
        comment.author = self.request.user
        comment.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        comment.save()
        return super(AddCommentView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'posts:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class FollowIndexView(LoginRequiredMixin, TemplateView):
    template_name = 'posts/follow.html'

    def get_context_data(self, **kwargs):
        context = super(FollowIndexView, self).get_context_data(**kwargs)

        posts = Post.objects.filter(author__following__user=self.request.user)
        page_obj = get_page_object(self.request.GET.get('page'), posts)

        context.update({
            'page_obj': page_obj,
        })
        return context


class ProfileFollowView(LoginRequiredMixin, View):
    def get(self, request, username):
        author = get_object_or_404(User, username=username)
        if request.user != author:
            Follow.objects.get_or_create(author=author, user=request.user)

        return redirect('posts:profile', username=username)


class ProfileUnfollowView(LoginRequiredMixin, View):
    def get(self, request, username):
        author = get_object_or_404(User, username=username)
        Follow.objects.filter(author=author, user=request.user).delete()

        return redirect('posts:profile', username=username)
