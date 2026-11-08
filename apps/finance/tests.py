from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import DuesCycle, Payment

Student = get_user_model()


class DuesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cycle = DuesCycle.objects.create(
            session="1448/1449 AH",
            amount=Decimal("2000.00"),
            is_active=True,
        )
        cls.student = Student.objects.create_user(
            matric_no="AATU/ACC/26/020",
            email="payer@example.com",
            password="StrongPass2026!",
            first_name="Zainab",
            last_name="Abdulkarim",
            must_change_password=False,
        )
        cls.other = Student.objects.create_user(
            matric_no="AATU/ACC/26/021",
            email="other@example.com",
            password="StrongPass2026!",
            first_name="Nafisah",
            last_name="Giwa",
            must_change_password=False,
        )

    def test_dues_page_requires_login(self):
        response = self.client.get(reverse("finance:dues"))
        self.assertEqual(response.status_code, 302)

    @override_settings(DEBUG=True)
    def test_demo_checkout_records_payment_and_issues_receipt(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("finance:pay"))
        payment = Payment.objects.get(student=self.student, cycle=self.cycle)
        self.assertRedirects(
            response, reverse("finance:demo_checkout", args=[payment.reference])
        )

        response = self.client.post(
            reverse("finance:demo_checkout", args=[payment.reference])
        )
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.SUCCESS)
        self.assertIsNotNone(payment.paid_at)
        self.assertRedirects(
            response, reverse("finance:receipt", args=[payment.reference])
        )
        self.assertEqual(
            self.client.get(reverse("finance:receipt", args=[payment.reference])).status_code,
            200,
        )

    def test_another_member_cannot_open_a_receipt(self):
        payment = Payment.objects.create(
            student=self.student,
            cycle=self.cycle,
            amount=self.cycle.amount,
            status=Payment.SUCCESS,
        )
        self.client.force_login(self.other)
        response = self.client.get(reverse("finance:receipt", args=[payment.reference]))
        self.assertRedirects(response, reverse("finance:dues"))

    def test_successful_payment_cannot_be_paid_twice(self):
        Payment.objects.create(
            student=self.student,
            cycle=self.cycle,
            amount=self.cycle.amount,
            status=Payment.SUCCESS,
        )
        self.client.force_login(self.student)
        response = self.client.post(reverse("finance:pay"))
        self.assertRedirects(response, reverse("finance:dues"))
        self.assertEqual(Payment.objects.filter(student=self.student).count(), 1)
