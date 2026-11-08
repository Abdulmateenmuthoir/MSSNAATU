from django.urls import path

from . import views

app_name = "money"

urlpatterns = [
    path("", views.finance_dashboard, name="overview"),
    path("cycle/", views.save_cycle, name="save_cycle"),
    path("payments/", views.payments_list, name="payments"),
    path("receipts/", views.receipt_reviews, name="receipts"),
    path("receipts/<int:payment_id>/review/", views.review_bank_receipt, name="review_receipt"),
    path("receipts/<int:payment_id>/file/", views.private_receipt_file, name="receipt_file"),
    path("export/", views.export_payments, name="export"),
    path("remind/", views.send_reminders, name="remind"),
]
