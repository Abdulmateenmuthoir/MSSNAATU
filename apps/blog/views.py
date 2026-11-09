from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.html import escape

from apps.accounts.decorators import role_required
from apps.accounts.models import ROLE_EDITOR, ROLE_MEMBER
from apps.core.models import NewsletterSubscriber

from .forms import CommentForm, NewsletterCampaignForm, PostForm
from .models import CATEGORY_CHOICES, Comment, NewsEmailCampaign, NewsletterCampaign, Post


def send_news_campaign(campaign):
    """Send one personalized Brevo message per recipient, in bounded batches."""
    import json
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL:
        campaign.status = NewsEmailCampaign.QUEUED
        campaign.last_error = "Configure BREVO_API_KEY and BREVO_SENDER_EMAIL to send this campaign."
        campaign.save(update_fields=["status", "last_error"])
        return
    User = get_user_model()
    addresses = set(NewsletterSubscriber.objects.filter(is_active=True).values_list("email", flat=True))
    addresses.update(User.objects.filter(is_active=True, role=ROLE_MEMBER).exclude(email="").values_list("email", flat=True))
    addresses = sorted({address.strip().lower() for address in addresses if address.strip()})
    if not addresses:
        campaign.status = NewsEmailCampaign.SENT
        campaign.recipient_count = 0
        campaign.sent_at = timezone.now()
        campaign.last_error = ""
        campaign.save(update_fields=["status", "recipient_count", "sent_at", "last_error"])
        return
    post = campaign.post
    url = f"{settings.SITE_URL}{post.get_absolute_url()}"
    excerpt = post.excerpt
    html = (f"<div style='font-family:Arial,sans-serif;max-width:640px;margin:auto;color:#18201d'>"
            f"<p style='color:#16804d;font-weight:bold'>MSSN AATU · NEWS</p><h1>{escape(post.title)}</h1>"
            f"<p>{escape(excerpt)}</p><p><a href='{escape(url)}' style='display:inline-block;padding:12px 20px;"
            f"background:#0e4b3a;color:white;text-decoration:none;border-radius:8px'>Read the full story</a></p>"
            f"<p style='font-size:12px;color:#777'>You received this because you have an MSSN AATU account or subscribed to society updates.</p></div>")
    try:
        for start in range(0, len(addresses), 1000):
            batch = addresses[start:start + 1000]
            versions = [{"to": [{"email": email}]} for email in batch]
            payload = {"sender": {"name": settings.BREVO_SENDER_NAME, "email": settings.BREVO_SENDER_EMAIL},
                       "subject": f"MSSN AATU: {post.title}", "htmlContent": html,
                       "textContent": f"{post.title}\n\n{excerpt}\n\nRead: {url}", "messageVersions": versions}
            req = Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(payload).encode(),
                          headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json",
                                   "content-type": "application/json"}, method="POST")
            with urlopen(req, timeout=30) as response:
                if response.status not in (200, 201, 202):
                    raise RuntimeError(f"Brevo returned HTTP {response.status}")
        campaign.status = NewsEmailCampaign.SENT
        campaign.recipient_count = len(addresses)
        campaign.sent_at = timezone.now()
        campaign.last_error = ""
    except (HTTPError, URLError, RuntimeError, TimeoutError) as exc:
        campaign.status = NewsEmailCampaign.FAILED
        campaign.recipient_count = len(addresses)
        campaign.last_error = str(exc)[:300]
    campaign.save(update_fields=["status", "recipient_count", "sent_at", "last_error"])


def queue_news_campaign(post):
    campaign, created = NewsEmailCampaign.objects.get_or_create(post=post)
    if created or campaign.status != NewsEmailCampaign.SENT:
        send_news_campaign(campaign)


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
    campaigns = NewsEmailCampaign.objects.select_related("post")
    newsletters = NewsletterCampaign.objects.all()
    return render(request, "dashboard/news/list.html", {"posts": posts, "status": status, "campaigns": campaigns, "newsletters": newsletters})


@role_required(ROLE_EDITOR)
def post_create(request):
    form = PostForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        if post.is_published:
            transaction.on_commit(lambda: queue_news_campaign(post))
        messages.success(request, "Article saved.")
        return redirect("newsroom:list")
    return render(request, "dashboard/news/form.html", {"form": form, "post": None})


@role_required(ROLE_EDITOR)
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    was_published = post.is_published
    form = PostForm(request.POST or None, request.FILES or None, instance=post)
    if request.method == "POST" and form.is_valid():
        post = form.save()
        if post.is_published and not was_published:
            transaction.on_commit(lambda: queue_news_campaign(post))
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


@role_required(ROLE_EDITOR)
def subscriber_list(request):
    subscribers = NewsletterSubscriber.objects.all()
    query = (request.GET.get("q") or "").strip()
    if query:
        subscribers = subscribers.filter(email__icontains=query)
    return render(request, "dashboard/news/subscribers.html", {"subscribers": subscribers, "query": query})


@role_required(ROLE_EDITOR)
@require_POST
def subscriber_toggle(request, pk):
    subscriber = get_object_or_404(NewsletterSubscriber, pk=pk)
    subscriber.is_active = not subscriber.is_active
    subscriber.save(update_fields=["is_active"])
    messages.success(request, "Subscriber status updated.")
    return redirect("newsroom:subscribers")


@role_required(ROLE_EDITOR)
def newsletter_list(request):
    return render(request, "dashboard/newsletters/list.html", {"campaigns": NewsletterCampaign.objects.all()})


@role_required(ROLE_EDITOR)
def newsletter_create(request):
    form = NewsletterCampaignForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.created_by = request.user
        campaign.save()
        messages.success(request, "Newsletter draft saved.")
        return redirect("newsroom:newsletter_edit", pk=campaign.pk)
    return render(request, "dashboard/newsletters/form.html", {"form": form, "campaign": None})


@role_required(ROLE_EDITOR)
def newsletter_edit(request, pk):
    campaign = get_object_or_404(NewsletterCampaign, pk=pk)
    if campaign.status == NewsletterCampaign.SENT:
        messages.info(request, "A sent newsletter cannot be edited or sent again.")
        return redirect("newsroom:newsletters")
    form = NewsletterCampaignForm(request.POST or None, instance=campaign)
    if request.method == "POST" and form.is_valid():
        campaign = form.save()
        messages.success(request, "Newsletter draft updated.")
        return redirect("newsroom:newsletter_edit", pk=campaign.pk)
    return render(request, "dashboard/newsletters/form.html", {"form": form, "campaign": campaign})


def send_newsletter_campaign(campaign):
    import json
    from urllib.error import HTTPError, URLError
    from urllib.request import Request, urlopen

    if not settings.BREVO_API_KEY or not settings.BREVO_SENDER_EMAIL:
        campaign.status = NewsletterCampaign.FAILED
        campaign.last_error = "Configure BREVO_API_KEY and BREVO_SENDER_EMAIL to send this newsletter."
        campaign.save(update_fields=["status", "last_error", "updated_at"])
        return False
    User = get_user_model()
    addresses = set(NewsletterSubscriber.objects.filter(is_active=True).values_list("email", flat=True))
    addresses.update(User.objects.filter(is_active=True, role=ROLE_MEMBER).exclude(email="").values_list("email", flat=True))
    addresses = sorted({address.strip().lower() for address in addresses if address.strip()})
    body = "<br>".join(escape(line) for line in campaign.content.splitlines())
    html = ("<div style='font-family:Arial,sans-serif;max-width:640px;margin:auto;color:#18201d'>"
            f"<p style='color:#16804d;font-weight:bold'>MSSN AATU · NEWSLETTER</p><h1>{escape(campaign.title)}</h1>"
            f"<p style='color:#66736d'>{escape(campaign.preview)}</p><div style='line-height:1.7'>{body}</div>"
            "<p>MSSN AATU</p></div>")
    try:
        for start in range(0, len(addresses), 1000):
            batch = addresses[start:start + 1000]
            payload = {"sender": {"name": settings.BREVO_SENDER_NAME, "email": settings.BREVO_SENDER_EMAIL},
                       "subject": campaign.title, "htmlContent": html,
                       "textContent": f"{campaign.title}\n\n{campaign.preview}\n\n{campaign.content}",
                       "messageVersions": [{"to": [{"email": email}]} for email in batch]}
            req = Request("https://api.brevo.com/v3/smtp/email", data=json.dumps(payload).encode(),
                          headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json",
                                   "content-type": "application/json"}, method="POST")
            with urlopen(req, timeout=30) as response:
                if response.status not in (200, 201, 202):
                    raise RuntimeError(f"Brevo returned HTTP {response.status}")
        campaign.status = NewsletterCampaign.SENT
        campaign.recipient_count = len(addresses)
        campaign.sent_at = timezone.now()
        campaign.last_error = ""
    except (HTTPError, URLError, RuntimeError, TimeoutError) as exc:
        campaign.status = NewsletterCampaign.FAILED
        campaign.recipient_count = len(addresses)
        campaign.last_error = str(exc)[:300]
    campaign.save(update_fields=["status", "recipient_count", "sent_at", "last_error", "updated_at"])
    return campaign.status == NewsletterCampaign.SENT


@role_required(ROLE_EDITOR)
@require_POST
def newsletter_send(request, pk):
    campaign = get_object_or_404(NewsletterCampaign, pk=pk)
    if campaign.status == NewsletterCampaign.SENT:
        messages.info(request, "This newsletter has already been sent.")
    elif send_newsletter_campaign(campaign):
        messages.success(request, f"Newsletter sent to {campaign.recipient_count} member(s) and subscriber(s).")
    else:
        messages.error(request, campaign.last_error or "The newsletter could not be sent.")
    return redirect("newsroom:newsletters")


@role_required(ROLE_EDITOR)
@require_POST
def campaign_retry(request, pk):
    campaign = get_object_or_404(NewsEmailCampaign, pk=pk)
    if campaign.status != NewsEmailCampaign.SENT:
        send_news_campaign(campaign)
        messages.success(request, "News email campaign processed.")
    return redirect("newsroom:list")
