from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

Student = get_user_model()


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = Student.objects.create_user(
            matric_no="AATU/CSC/26/001",
            email="student@example.com",
            password="StrongPass2026!",
            first_name="Aisha",
            last_name="Bello",
            gender="F",
            must_change_password=False,
        )

    def test_login_with_matric_number(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "AATU/CSC/26/001", "password": "StrongPass2026!"},
        )
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "student@example.com", "password": "StrongPass2026!"},
        )
        self.assertRedirects(response, reverse("dashboard:home"))

    def test_wrong_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": "student@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "do not match")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])

    def test_forgot_password_sends_one_email(self):
        response = self.client.post(
            reverse("accounts:password_forgot"), {"identifier": self.student.email}
        )
        self.assertRedirects(response, reverse("accounts:password_forgot_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset", mail.outbox[0].subject.lower())


class PasswordSetupTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = Student.objects.create_user(
            matric_no="AATU/MEE/26/002",
            email="new.student@example.com",
            password="Temporary2026!",
            first_name="Yusuf",
            last_name="Ibrahim",
            must_change_password=True,
        )

    def test_first_login_redirects_to_password_setup(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"identifier": self.student.email, "password": "Temporary2026!"},
        )
        self.assertRedirects(response, reverse("accounts:password_setup"))

    def test_middleware_blocks_dashboard_until_a_decision(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, reverse("accounts:password_setup"))

    def test_student_can_continue_with_temporary_password(self):
        self.client.force_login(self.student)
        response = self.client.post(reverse("accounts:password_setup_skip"))
        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertEqual(self.client.get(reverse("dashboard:home")).status_code, 200)

    def test_student_can_set_a_new_password(self):
        self.client.force_login(self.student)
        response = self.client.post(
            reverse("accounts:password_setup"),
            {
                "new_password1": "BrandNewPass2026!",
                "new_password2": "BrandNewPass2026!",
            },
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        self.student.refresh_from_db()
        self.assertFalse(self.student.must_change_password)
        self.assertTrue(self.student.check_password("BrandNewPass2026!"))


class PermissionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = Student.objects.create_user(
            matric_no="AATU/CSC/26/040",
            email="member@example.com",
            password="StrongPass2026!",
            first_name="Musa",
            last_name="Danjuma",
            must_change_password=False,
        )
        cls.admin = Student.objects.create_user(
            matric_no="AATU/ADM/26/001",
            email="admin@example.com",
            password="StrongPass2026!",
            first_name="Ahmad",
            last_name="Bello",
            role="admin",
            must_change_password=False,
        )

    def test_member_cannot_open_the_people_manager(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("people:list"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "not yours to open", status_code=403)

    def test_administrator_can_open_the_people_manager(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("people:list"))
        self.assertEqual(response.status_code, 200)
