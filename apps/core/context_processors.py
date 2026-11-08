from django.conf import settings

from apps.finance.models import DuesCycle


def site_context(request):
    active_cycle = DuesCycle.objects.filter(is_active=True).first()
    return {
        "site_name": settings.SITE_NAME,
        "site_legal_name": settings.SITE_LEGAL_NAME,
        "site_domain": settings.SITE_DOMAIN,
        "site_email": settings.SITE_EMAIL,
        "current_session": settings.CURRENT_SESSION,
        "active_dues_cycle": active_cycle,
        "site_url": settings.SITE_URL,
    }
