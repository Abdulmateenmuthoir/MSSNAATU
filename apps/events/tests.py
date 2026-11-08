from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, Registration

Student = get_user_model()


class EventRegistrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brother = Student.objects.create_user(
            matric_no="AATU/CSC/26/010",
            email="brother@example.com",
            password="StrongPass2026!",
            first_name="Musa",
            last_name="Danjuma",
            gender="M",
            must_change_password=False,
        )
        cls.sister = Student.objects.create_user(
            matric_no="AATU/CSC/26/011",
            email="sister@example.com",
            password="StrongPass2026!",
            first_name="Aminah",
            last_name="Oseni",
            gender="F",
            must_change_password=False,
        )
        start = timezone.now() + timedelta(days=7)
        cls.open_event = Event.objects.create(
            title="Open Halaqah",
            summary="A circle for everyone.",
            description="Come and benefit.",
            starts_at=start,
            venue="Main Auditorium",
            registration_deadline=start - timedelta(days=1),
            capacity=10,
        )
        cls.brothers_event = Event.objects.create(
            title="Brothers' Circle",
            summary="For brothers.",
            description="A brothers-only circle.",
            starts_at=start,
            venue="Lecture Theatre 2",
            registration_deadline=start - timedelta(days=1),
            eligibility="brothers",
        )

    def test_event_list_and_detail_are_public(self):
        self.assertEqual(self.client.get(reverse("events:list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("events:detail", args=[self.open_event.slug])).status_code,
            200,
        )

    def test_member_can_register_and_cancel(self):
        self.client.force_login(self.brother)
        response = self.client.post(reverse("events:register", args=[self.open_event.slug]))
        self.assertRedirects(response, self.open_event.get_absolute_url())
        self.assertTrue(
            Registration.objects.filter(event=self.open_event, student=self.brother).exists()
        )
        self.client.post(reverse("events:cancel", args=[self.open_event.slug]))
        self.assertFalse(
            Registration.objects.filter(event=self.open_event, student=self.brother).exists()
        )

    def test_gender_eligibility_is_enforced(self):
        self.client.force_login(self.sister)
        response = self.client.post(reverse("events:register", args=[self.brothers_event.slug]))
        self.assertRedirects(response, self.brothers_event.get_absolute_url())
        self.assertFalse(
            Registration.objects.filter(event=self.brothers_event, student=self.sister).exists()
        )

    def test_past_event_cannot_be_joined(self):
        past = Event.objects.create(
            title="Past Programme",
            summary="Already held.",
            description="This has finished.",
            starts_at=timezone.now() - timedelta(days=2),
            venue="Main Auditorium",
        )
        self.client.force_login(self.brother)
        self.client.post(reverse("events:register", args=[past.slug]))
        self.assertFalse(Registration.objects.filter(event=past).exists())
