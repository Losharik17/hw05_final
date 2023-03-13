from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import (CreateView, FormView, UpdateView, View,
                                  ListView, DetailView, RedirectView)

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


class IndexView(ListView):
    template_name = 'posts/index.html'
    model = Post
    paginate_by = settings.PAGE_SIZE
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.select_related('author', 'group')


class GroupPostsView(ListView):
    template_name = 'posts/group_list.html'
    model = Post
    paginate_by = settings.PAGE_SIZE
    context_object_name = 'posts'

    def get_queryset(self):
        self.group = get_object_or_404(
            Group.objects.prefetch_related('posts__author'),
            slug=self.kwargs['slug']
        )
        return self.group.posts.all()

    def get_context_data(self, **kwargs):
        context = super(GroupPostsView, self).get_context_data(**kwargs)
        context['group'] = self.group
        return context


class ProfileView(ListView):
    template_name = 'posts/profile.html'
    model = Post
    paginate_by = settings.PAGE_SIZE
    context_object_name = 'posts'

    def get_queryset(self):
        self.user = get_object_or_404(
            User.objects.prefetch_related('posts__author',
                                          'posts__group',
                                          'following'),
            username=self.kwargs['username']
        )
        return self.user.posts.all()

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)

        following = None
        if self.request.user.is_authenticated:
            following = Follow.objects.filter(
                user=self.request.user, author=self.user,
            ).exists()

        context.update({
            'author': self.user,
            'following': following,
        })
        return context


class PostDetailView(DetailView):
    template_name = 'posts/post_detail.html'
    model = Post
    context_object_name = 'post'

    def get_object(self, queryset=None):
        self.post = get_object_or_404(
            Post.objects.select_related(
                'author', 'group'
            ).prefetch_related('comments__author'),
            pk=self.kwargs['post_id']
        )
        return self.post

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)

        title = f'Пост "{self.post.text[:30]}"'
        context.update({
            'title': title,
            'comment_form': CommentForm(),
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


class FollowIndexView(LoginRequiredMixin, ListView):
    template_name = 'posts/follow.html'
    model = Post
    paginate_by = settings.PAGE_SIZE
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(author__following__user=self.request.user)


class ProfileFollowView(LoginRequiredMixin, RedirectView):
    pattern_name = 'posts:profile'

    def get_redirect_url(self, *args, **kwargs):
        author = get_object_or_404(User, username=kwargs['username'])
        if self.request.user != author:
            Follow.objects.get_or_create(author=author, user=self.request.user)
        return super().get_redirect_url(*args, **kwargs)


class ProfileUnfollowView(LoginRequiredMixin, RedirectView):
    pattern_name = 'posts:profile'

    def get_redirect_url(self, *args, **kwargs):
        author = get_object_or_404(User, username=kwargs['username'])
        Follow.objects.filter(author=author, user=self.request.user).delete()
        return super().get_redirect_url(*args, **kwargs)


