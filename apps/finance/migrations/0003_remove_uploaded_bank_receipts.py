from django.db import migrations


def discard_legacy_bank_receipts(apps, schema_editor):
    Payment = apps.get_model("finance", "Payment")
    receipt_storage = Payment._meta.get_field("receipt").storage

    for payment in Payment.objects.filter(gateway="bank_transfer").exclude(receipt="").iterator():
        receipt_storage.delete(payment.receipt.name)
        payment.receipt = ""
        if payment.status != "success":
            payment.status = "failed"
        payment.save(update_fields=["receipt", "status"])


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0002_payment_receipt_payment_review_note_and_more"),
    ]

    operations = [
        migrations.RunPython(discard_legacy_bank_receipts, migrations.RunPython.noop),
        migrations.RemoveField(model_name="payment", name="receipt"),
        migrations.RemoveField(model_name="payment", name="review_note"),
        migrations.RemoveField(model_name="payment", name="reviewed_at"),
        migrations.RemoveField(model_name="payment", name="reviewed_by"),
    ]
