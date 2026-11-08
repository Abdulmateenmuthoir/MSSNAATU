from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import ROLE_SUPER


def role_required(*roles):
    """Allow the listed roles, plus Administrators and Super Users."""

    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if user.is_administrator or user.role in roles:
                return view(request, *args, **kwargs)
            raise PermissionDenied("You do not have access to this area.")

        return wrapper

    return decorator


def superuser_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.user.is_super_admin:
            return view(request, *args, **kwargs)
        raise PermissionDenied("Only a Super User can do this.")

    return wrapper
