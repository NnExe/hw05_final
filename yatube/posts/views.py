from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import my_paginator


@cache_page(settings.CACHE_TIME)
def index(request):
    posts = (
        Post.objects
        .select_related("author", "group").all()
    )
    page_number = request.GET.get('page')
    page_obj = my_paginator(posts, page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = (
        group.posts
        .select_related("author", "group").all()
    )
    page_number = request.GET.get('page')
    page_obj = my_paginator(posts, page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
        'is_group_page': True,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = (
        user.posts
        .select_related("author", "group").all()
    )
    page_number = request.GET.get('page')
    page_obj = my_paginator(posts, page_number)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(user=request.user)
        .filter(author=user).exists()
    )
    context = {
        'page_obj': page_obj,
        'no_author': True,
        'author': user,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    num_posts = (
        Post.objects
        .select_related("author", "group")
        .filter(author=post.author).count()
    )
    comments = (
        Comment.objects
        .select_related("author", "post").filter(post=post)
    )
    form = CommentForm()
    context = {
        'post': post,
        'num_posts': num_posts,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    context = {
        'form': form,
        'title': 'Добавить запись',
        'button_name': 'Добавить',
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    context = {
        'form': form,
        'title': 'Редактировать запись',
        'button_name': 'Сохранить',
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author.username != request.user.username:
        return redirect("posts:post_detail", post_id)
    post.delete()
    return redirect('posts:profile', post.author.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = (
        Post.objects
        .select_related('author', 'group')
        .filter(author__following__user=request.user)
    )
    page_number = request.GET.get('page')
    page_obj = my_paginator(posts, page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if ((not Follow.objects.filter(user=user).filter(
         author=author).exists()) and (author != user)):
        Follow.objects.create(
            author=author,
            user=user,
        )
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=user, author=author)
    follower.delete()
    return redirect('posts:profile', author.username)
