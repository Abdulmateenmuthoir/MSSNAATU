import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _send(subject, text_template, html_template, context, to_email):
    text_body = render_to_string(text_template, context)
    html_body = render_to_string(html_template, context)
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
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


def send_dues_reminder(student, cycle, pay_url):
    context = {"student": student, "cycle": cycle, "pay_url": pay_url, "site_url": settings.SITE_URL}
    return _send(
        subject=f"Dues reminder — {cycle.session}",
        text_template="emails/dues_reminder.txt",
        html_template="emails/dues_reminder.html",
        context=context,
        to_email=student.email,
    )
