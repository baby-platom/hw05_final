from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


@require_GET
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')

    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/index.html',
        {'page': page}
    )


@require_GET
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, 10)

    page_number = request.GET.get('page')

    page = paginator.get_page(page_number)
    return render(request, "posts/group.html", {"group": group, "page": page})


@require_GET
def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    number_of_posts = posts.count()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "author": author,
        "number_of_posts": number_of_posts,
        "page": page,
    }
    if request.user.is_authenticated:
        following = Follow.objects.filter(user=request.user,
                                          author=author).exists()
        context["following"] = following

    return render(request, 'posts/profile.html', context)


@require_GET
def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    number_of_posts = Post.objects.filter(author=author).count()
    post = get_object_or_404(Post, author=author, id=post_id)
    comments = Comment.objects.filter(post=post)
    form = CommentForm()
    return render(
        request,
        'posts/post.html',
        {
            "author": author,
            "number_of_posts": number_of_posts,
            "post": post,
            "form": form,
            "comments": comments
        }
    )


@require_http_methods(["GET", "POST"])
@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        form.save()
        return redirect('index')
    return render(request, 'posts/post_new_or_edit.html', {'form': form})


@require_http_methods(["GET", "POST"])
@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request,
        'posts/post_new_or_edit.html',
        {
            'form': form,
            'post': post
        }
    )


@require_http_methods(["GET", "POST"])
@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request, 'posts/comments.html',
        {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@require_GET
@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')

    page = paginator.get_page(page_number)
    return render(request, "posts/follow.html", {'page': page})


@require_http_methods(["GET", "POST"])
@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if request.user != author:
        author, user = Follow.objects.get_or_create(
            author=author,
            user=user,
        )
    return redirect('profile', username)


@require_http_methods(["GET", "POST"])
@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        get_object_or_404(Follow, user=request.user,
                          author=author).delete()
    return redirect('profile', username)
