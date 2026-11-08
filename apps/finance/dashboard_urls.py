from django.urls import path

from . import views

app_name = "money"

urlpatterns = [
    path("", views.finance_dashboard, name="overview"),
    path("cycle/", views.save_cycle, name="save_cycle"),
    path("payments/", views.payments_list, name="payments"),
    path("export/", views.export_payments, name="export"),
    path("remind/", views.send_reminders, name="remind"),
]
