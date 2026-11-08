from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.accounts.decorators import role_required
from apps.accounts.models import ROLE_EDITOR

from .forms import CommentForm, PostForm
from .models import CATEGORY_CHOICES, Comment, Post


def post_list(request):
    posts = Post.objects.filter(is_published=True).select_related("author")
    category = request.GET.get("category", "")
    query = (request.GET.get("q") or "").strip()
    if category:
        posts = posts.filter(category=category)
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query))
    featured = posts.first()
    rest = posts.exclude(pk=featured.pk) if featured else posts
    paginator = Paginator(rest, 8)
    page = paginator.get_page(request.GET.get("page"))
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "blog/list.html",
        {
            "featured": featured,
            "page": page,
            "categories": CATEGORY_CHOICES,
            "selected_category": category,
            "query": query,
            "query_string": query_params.urlencode(),
        },
    )


def post_detail(request, slug):
    post = get_object_or_404(Post.objects.select_related("author"), slug=slug)
    if not post.is_published and not (request.user.is_authenticated and request.user.can_manage_content):
        raise Http404
    Post.objects.filter(pk=post.pk).update(views=post.views + 1)
    comments = post.comments.filter(is_visible=True).select_related("author")
    form = CommentForm()
    related = (
        Post.objects.filter(is_published=True, category=post.category).exclude(pk=post.pk).select_related("author")[:3]
    )
    return render(
        request,
        "blog/detail.html",
        {"post": post, "comments": comments, "form": form, "related": related},
    )


@login_required
@require_POST
def comment_create(request, slug):
    post = get_object_or_404(Post, slug=slug, is_published=True)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        messages.success(request, "Your comment is live.")
    else:
        messages.error(request, "Your comment could not be posted. Please try again.")
    return redirect(post.get_absolute_url() + "#comments")


# ---------------------------------------------------------------------------
# Newsroom dashboard
# ---------------------------------------------------------------------------


@role_required(ROLE_EDITOR)
def manage_list(request):
    posts = Post.objects.select_related("author").annotate(comment_count=models.Count("comments"))
    status = request.GET.get("status", "")
    if status == "published":
        posts = posts.filter(is_published=True)
    elif status == "drafts":
        posts = posts.filter(is_published=False)
    return render(request, "dashboard/news/list.html", {"posts": posts, "status": status})


@role_required(ROLE_EDITOR)
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "Article saved.")
        return redirect("newsroom:list")
    return render(request, "dashboard/news/form.html", {"form": form, "post": None})


@role_required(ROLE_EDITOR)
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Article updated.")
        return redirect("newsroom:list")
    return render(request, "dashboard/news/form.html", {"form": form, "post": post})


@role_required(ROLE_EDITOR)
@require_POST
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    title = post.title
    post.delete()
    messages.success(request, f"“{title}” was deleted.")
    return redirect("newsroom:list")


@role_required(ROLE_EDITOR)
def comment_list(request):
    comments = Comment.objects.select_related("post", "author")
    return render(request, "dashboard/news/comments.html", {"comments": comments})


@role_required(ROLE_EDITOR)
@require_POST
def comment_toggle(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.is_visible = not comment.is_visible
    comment.save(update_fields=["is_visible"])
    messages.success(request, "Comment visibility updated.")
    return redirect("newsroom:comments")


@role_required(ROLE_EDITOR)
@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    messages.success(request, "Comment deleted.")
    return redirect("newsroom:comments")
