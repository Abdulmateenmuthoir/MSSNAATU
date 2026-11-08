from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from .models import Student


class PasswordSetupMiddleware:
    """Keep first-time users on the password screen until they decide.

    A student can either set a new password or choose to continue with the
    temporary one. Continuing only dismisses the prompt for the session; the
    dashboard keeps a gentle reminder until the password is changed.
    """

    ALLOWED_NAMES = {
        "accounts:password_setup",
        "accounts:password_setup_skip",
        "accounts:login",
        "accounts:logout",
        "accounts:password_change",
        "accounts:password_forgot",
        "accounts:password_forgot_done",
        "accounts:password_reset",
        "accounts:password_reset_complete",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and getattr(user, "must_change_password", False):
            if not request.session.get("password_prompt_dismissed"):
                try:
                    match = resolve(request.path_info)
                except Resolver404:
                    return self.get_response(request)
                if match.view_name not in self.ALLOWED_NAMES:
                    return redirect("accounts:password_setup")
        return self.get_response(request)
