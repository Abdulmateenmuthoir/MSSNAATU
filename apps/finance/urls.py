from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.dues_home, name="dues"),
    path("pay/", views.initialize_payment, name="pay"),
    path("receipt-upload/", views.submit_bank_receipt, name="submit_bank_receipt"),
    path("callback/", views.callback, name="callback"),
    path("demo/<str:reference>/", views.demo_checkout, name="demo_checkout"),
    path("receipt/<str:reference>/", views.receipt, name="receipt"),
]
