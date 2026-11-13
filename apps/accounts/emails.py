import logging
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send(subject, text_template, html_template, context, to_email):
    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)
    if settings.BREVO_API_KEY and settings.BREVO_SENDER_EMAIL:
        payload = {
            "sender": {"name": settings.BREVO_SENDER_NAME, "email": settings.BREVO_SENDER_EMAIL},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_body,
            "textContent": text_body,
        }
        request = Request(
            "https://api.brevo.com/v3/smtp/email",
            data=json.dumps(payload).encode(),
            headers={
                "api-key": settings.BREVO_API_KEY,
                "accept": "application/json",
                "content-type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                return response.status in (200, 201, 202)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.error("Brevo rejected email to %s (HTTP %s): %s", to_email, exc.code, detail[:300])
            return False
        except (URLError, TimeoutError, OSError):
            logger.exception("Brevo could not send email to %s", to_email)
            return False

    if not settings.EMAIL_HOST:
        logger.error("Email not sent to %s: configure Brevo API credentials or EMAIL_HOST.", to_email)
        return False

    message = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [to_email])
    message.attach_alternative(html_body, "text/html")
    try:
        message.send(fail_silently=False)
        return True
    except Exception:  # pragma: no cover - delivery failures are logged, never fatal
        logger.exception("Could not send email to %s", to_email)
        return False


def send_credentials(student, temporary_password):
    context = {
        "student": student,
        "password": temporary_password,
        "login_url": f"{settings.SITE_URL}/accounts/login/",
        "site_url": settings.SITE_URL,
    }
    return _send(
        subject="Your MSSN AATU login details",
        text_template="emails/credentials.txt",
        html_template="emails/credentials.html",
        context=context,
        to_email=student.email,
    )


def send_password_reset(student, reset_url):
    context = {"student": student, "reset_url": reset_url, "site_url": settings.SITE_URL}
    return _send(
        subject="Reset your MSSN AATU password",
        text_template="emails/password_reset.txt",
        html_template="emails/password_reset.html",
        context=context,
        to_email=student.email,
    )


def send_event_confirmation(registration):
    event = registration.event
    student = registration.student
    context = {"student": student, "event": event, "site_url": settings.SITE_URL}
    return _send(
        subject=f"You're registered: {event.title}",
        text_template="emails/event_confirmation.txt",
        html_template="emails/event_confirmation.html",
        context=context,
        to_email=student.email,
    )


def send_event_reminder(event, student):
    context = {"student": student, "event": event, "site_url": settings.SITE_URL}
    return _send(
        subject=f"Reminder: {event.title}",
        text_template="emails/event_reminder.txt",
        html_template="emails/event_reminder.html",
        context=context,
        to_email=student.email,
    )


def send_payment_receipt(payment):
    context = {
        "student": payment.student,
        "payment": payment,
        "cycle": payment.cycle,
        "site_url": settings.SITE_URL,
    }
    return _send(
        subject=f"Dues receipt — {payment.cycle.session}",
        text_template="emails/payment_receipt.txt",
        html_template="emails/payment_receipt.html",
        context=context,
        to_email=payment.student.email,
    )


def send_donation_receipt(donation):
    context = {"donation": donation, "site_url": settings.SITE_URL}
    return _send(
        subject="MSSN AATU donation receipt",
        text_template="emails/donation_receipt.txt",
        html_template="emails/donation_receipt.html",
        context=context,
        to_email=donation.email,
    )


def send_dues_reminder(student, cycle, pay_url):
    context = {"student": student, "cycle": cycle, "pay_url": pay_url, "site_url": settings.SITE_URL}
    return _send(
        subject=f"Dues reminder — {cycle.session}",
        text_template="emails/dues_reminder.txt",
        html_template="emails/dues_reminder.html",
        context=context,
        to_email=student.email,
    )
