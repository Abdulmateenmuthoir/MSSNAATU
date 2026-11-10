from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.dues_home, name="dues"),
    path("pay/", views.initialize_payment, name="pay"),
    path("callback/", views.callback, name="callback"),
    path("receipt/<str:reference>/", views.receipt, name="receipt"),
]
