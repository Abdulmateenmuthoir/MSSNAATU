import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.models import Department, Faculty

from .models import PastQuestion

Student = get_user_model()

TEMP_MEDIA = tempfile.mkdtemp(prefix="mssnaatu-test-media-")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.faculty = Faculty.objects.create(name="Faculty of Computing", code="SCICT")
        cls.department = Department.objects.create(
            faculty=cls.faculty, name="Computer Science", code="CSC"
        )
        cls.member = Student.objects.create_user(
            matric_no="AATU/CSC/26/030",
            email="reader@example.com",
            password="StrongPass2026!",
            first_name="Aisha",
            last_name="Bello",
            must_change_password=False,
        )
        cls.question = PastQuestion.objects.create(
            faculty=cls.faculty,
            department=cls.department,
            level="200",
            course_code="CSC 201",
            course_title="Computer Programming II",
            session="2024/2025",
            uploaded_by=cls.member,
            file=SimpleUploadedFile("csc201.pdf", b"%PDF-1.4 test", content_type="application/pdf"),
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def test_library_pages_are_public(self):
        self.assertEqual(self.client.get(reverse("library:list")).status_code, 200)
        self.assertEqual(
            self.client.get(reverse("library:detail", args=[self.question.pk])).status_code,
            200,
        )

    def test_download_requires_login(self):
        response = self.client.get(reverse("library:download", args=[self.question.pk]))
        self.assertEqual(response.status_code, 302)

    def test_member_can_download_and_counter_increases(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("library:download", args=[self.question.pk]))
        self.assertEqual(response.status_code, 200)
        self.question.refresh_from_db()
        self.assertEqual(self.question.downloads, 1)
