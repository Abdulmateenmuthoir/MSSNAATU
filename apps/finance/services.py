import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def is_configured():
    return bool(settings.PAYSTACK_SECRET_KEY)


def initialize_transaction(payment):
    """Create a Paystack transaction. Returns (authorization_url, error)."""
    if not is_configured():
        return None, "Paystack keys are not configured."
    payload = {
        "email": payment.student.email,
        "amount": int(payment.amount * 100),
        "reference": str(payment.reference),
        "currency": "NGN",
        "callback_url": settings.PAYSTACK_CALLBACK_URL,
        "metadata": {
            "student_id": payment.student_id,
            "matric_no": payment.student.matric_no,
            "cycle": payment.cycle.session,
            "payment_id": payment.id,
        },
    }
    try:
        response = requests.post(
            f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
            json=payload,
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
            timeout=20,
        )
        data = response.json()
        if response.ok and data.get("status"):
            return data["data"]["authorization_url"], None
        logger.warning("Paystack init failed: %s", data)
        return None, data.get("message", "The payment gateway rejected the request.")
    except requests.RequestException as exc:
        logger.exception("Paystack network error")
        return None, str(exc)


def initialize_donation(donation):
    """Create a public Paystack transaction for a donation."""
    if not is_configured():
        return None, "Paystack keys are not configured."
    payload = {
        "email": donation.email,
        "amount": int(donation.amount * 100),
        "reference": str(donation.reference),
        "currency": "NGN",
        "callback_url": f"{settings.SITE_URL}/donate/callback/",
        "metadata": {
            "donation_id": donation.id,
            "donor_name": donation.donor_name,
            "cause": donation.cause,
        },
    }
    try:
        response = requests.post(
            f"{settings.PAYSTACK_BASE_URL}/transaction/initialize",
            json=payload,
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
            timeout=20,
        )
        data = response.json()
        if response.ok and data.get("status"):
            return data["data"]["authorization_url"], None
        logger.warning("Paystack donation init failed: %s", data)
        return None, data.get("message", "The payment gateway rejected the request.")
    except requests.RequestException as exc:
        logger.exception("Paystack donation network error")
        return None, str(exc)


def verify_transaction(reference):
    """Verify a transaction. Returns (success, payload_or_message)."""
    if not is_configured():
        return False, "Paystack keys are not configured."
    try:
        response = requests.get(
            f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"},
            timeout=20,
        )
        data = response.json()
        if response.ok and data.get("status") and data.get("data", {}).get("status") == "success":
            return True, data["data"]
        return False, data.get("message", "Payment was not successful.")
    except requests.RequestException as exc:
        logger.exception("Paystack verification error")
        return False, str(exc)
