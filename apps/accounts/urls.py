from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password/setup/", views.password_setup, name="password_setup"),
    path("password/setup/continue/", views.password_setup_skip, name="password_setup_skip"),
    path("password/change/", views.password_change, name="password_change"),
    path("password/forgot/", views.password_forgot, name="password_forgot"),
    path("password/forgot/sent/", views.password_forgot_done, name="password_forgot_done"),
    path("password/reset/<uidb64>/<token>/", views.password_reset, name="password_reset"),
    path("password/reset/complete/", views.password_reset_complete, name="password_reset_complete"),
    path("profile/", views.profile, name="profile"),
]
