from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from apps.accounts.emails import send_dues_reminder
from apps.finance.models import DuesCycle, Payment, ReminderLog
from apps.accounts.models import ROLE_MEMBER, Student


class Command(BaseCommand):
    help = "Email a fortnightly dues reminder to active members who have not paid."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Send even if the member received a reminder in the last 14 days.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Show who would be emailed.")

    def handle(self, *args, **options):
        cycle = DuesCycle.objects.filter(is_active=True).first()
        if not cycle:
            self.stdout.write(self.style.WARNING("No active dues cycle. Nothing sent."))
            return

        paid_ids = Payment.objects.filter(cycle=cycle, status=Payment.SUCCESS).values_list("student_id", flat=True)
        students = Student.objects.filter(is_active=True, role=ROLE_MEMBER).exclude(id__in=paid_ids).select_related("department")
        if not options["force"]:
            recently = ReminderLog.objects.filter(
                cycle=cycle, sent_at__gte=timezone.now() - timedelta(days=14)
            ).values_list("student_id", flat=True)
            students = students.exclude(id__in=recently)

        pay_url = f"{settings.SITE_URL}{reverse('finance:dues')}"
        sent = 0
        for student in students:
            if options["dry_run"]:
                self.stdout.write(f"Would remind {student.matric_no} <{student.email}>")
                continue
            if send_dues_reminder(student, cycle, pay_url):
                ReminderLog.objects.create(cycle=cycle, student=student)
                sent += 1
        if options["dry_run"]:
            self.stdout.write(self.style.SUCCESS(f"{students.count()} member(s) would be reminded."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{sent} reminder(s) sent for {cycle.session}."))
