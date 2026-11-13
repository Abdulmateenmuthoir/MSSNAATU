from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from apps.events import views as event_views
from apps.core.views import public_media
from apps.finance import views as finance_views

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("news/", include("apps.blog.urls")),
    path("events/", include("apps.events.urls")),
    path("programmes/", event_views.programme_list, name="programmes_list"),
    path("library/", include("apps.library.urls")),
    path("dues/", include("apps.finance.urls")),
    path("donate/", finance_views.donate, name="donate"),
    path("donate/initialize/", finance_views.initialize_donation_view, name="donate_initialize"),
    path("donate/callback/", finance_views.donation_callback, name="donate_callback"),
    path("donate/receipt/<str:reference>/", finance_views.donation_result, name="donation_result"),
    path("dashboard/", include("apps.core.dashboard_urls")),
    path("dashboard/students/", include("apps.accounts.dashboard_urls")),
    path("dashboard/news/", include("apps.blog.dashboard_urls")),
    path("dashboard/events/", include("apps.events.dashboard_urls")),
    path("dashboard/programmes/", include("apps.events.program_dashboard_urls")),
    path("dashboard/library/", include("apps.library.dashboard_urls")),
    path("dashboard/finance/", include("apps.finance.dashboard_urls")),
]

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # cPanel Passenger does not serve Django's MEDIA_ROOT automatically.
    # Expose only public image uploads; library files stay behind their views.
    urlpatterns += [re_path(r"^media/(?P<path>.+)$", public_media, name="public_media")]
