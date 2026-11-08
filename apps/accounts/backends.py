from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import Student


class MatricOrEmailBackend(ModelBackend):
    """Allow members to sign in with either their matric number or email."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identifier = username or kwargs.get("matric_no") or kwargs.get("email")
        if not identifier or password is None:
            return None
        identifier = identifier.strip()
        try:
            user = Student.objects.get(
                Q(matric_no__iexact=identifier) | Q(email__iexact=identifier)
            )
        except Student.DoesNotExist:
            Student().set_password(password)  # equalise timing
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
