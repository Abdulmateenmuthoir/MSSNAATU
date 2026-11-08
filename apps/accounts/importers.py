import csv
import io
import re

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction

from apps.core.models import Department, Faculty

from .emails import send_credentials
from .models import GENDER_CHOICES, Student, generate_temp_password

GENDER_ALIASES = {
    "m": "M",
    "male": "M",
    "brother": "M",
    "brothers": "M",
    "f": "F",
    "female": "F",
    "sister": "F",
    "sisters": "F",
}


def _normalise_row(row):
    clean = {}
    for key, value in row.items():
        if key is None:
            continue
        clean[re.sub(r"[\s\-]+", "_", key.strip().lower())] = (value or "").strip()
    return clean


def _pick(row, *names):
    for name in names:
        value = row.get(name)
        if value:
            return value
    return ""


def _split_name(row):
    first = _pick(row, "first_name", "firstname", "given_name")
    last = _pick(row, "last_name", "lastname", "surname", "family_name")
    full = _pick(row, "full_name", "name", "student_name")
    if (not first or not last) and full:
        parts = full.split()
        if len(parts) >= 2:
            first = first or parts[0]
            last = last or " ".join(parts[1:])
        elif parts:
            first = first or parts[0]
    return first, last


def _level(value):
    match = re.search(r"\d{3}", value or "")
    return match.group(0) if match else ""


def _resolve_academic(row):
    faculty = None
    department = None
    faculty_value = _pick(row, "faculty", "faculty_code", "faculty_name")
    department_value = _pick(row, "department", "department_code", "dept", "department_name")

    if faculty_value:
        faculty = (
            Faculty.objects.filter(code__iexact=faculty_value).first()
            or Faculty.objects.filter(name__iexact=faculty_value).first()
        )
        if faculty is None:
            raise ValidationError(f"Unknown faculty “{faculty_value}”.")
    if department_value:
        departments = Department.objects.select_related("faculty")
        department = (
            departments.filter(code__iexact=department_value).first()
            or departments.filter(name__iexact=department_value).first()
        )
        if department is None:
            raise ValidationError(f"Unknown department “{department_value}”.")
        if faculty and department.faculty_id != faculty.id:
            raise ValidationError(f"“{department.name}” does not belong to {faculty.name}.")
        faculty = faculty or department.faculty
    return faculty, department


def import_students(csv_file, send_emails=True, max_rows=500):
    """Parse a CSV and create member accounts. Returns (created, errors)."""
    try:
        raw = csv_file.read()
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValidationError("The file is empty or is not a valid CSV.")

    created, errors = [], []
    seen_matric = set()
    seen_email = set()

    for index, raw_row in enumerate(reader, start=2):
        if len(created) >= max_rows:
            errors.append({"row": index, "message": f"Import stopped at {max_rows} rows. Split the file and continue."})
            break
        row = _normalise_row(raw_row)
        if not any(row.values()):
            continue

        first_name, last_name = _split_name(row)
        matric_no = _pick(row, "matric_no", "matric", "matric_number", "student_id", "id").upper()
        email = _pick(row, "email", "email_address", "school_email").lower()
        gender_raw = _pick(row, "gender", "sex").lower()
        level = _level(_pick(row, "level", "class", "year"))

        try:
            if not first_name or not last_name:
                raise ValidationError("First and last name are required.")
            if not matric_no:
                raise ValidationError("Matric number is required.")
            if not re.match(r"^[A-Za-z0-9/\-\.]+$", matric_no):
                raise ValidationError("Matric number contains invalid characters.")
            if not email:
                raise ValidationError("Email is required.")
            validate_email(email)
            gender = GENDER_ALIASES.get(gender_raw)
            if not gender:
                raise ValidationError("Gender must be male/brother (M) or female/sister (F).")
            if level and level not in {choice[0] for choice in Student._meta.get_field("level").choices}:
                raise ValidationError(f"Unsupported level “{level}”.")
            if matric_no in seen_matric:
                raise ValidationError("Duplicate matric number within this file.")
            if email in seen_email:
                raise ValidationError("Duplicate email address within this file.")
            if Student.objects.filter(matric_no__iexact=matric_no).exists():
                raise ValidationError("A student with this matric number already exists.")
            if Student.objects.filter(email__iexact=email).exists():
                raise ValidationError("A student with this email already exists.")

            faculty, department = _resolve_academic(row)
            password = generate_temp_password()
            with transaction.atomic():
                student = Student.objects.create_user(
                    matric_no=matric_no,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    faculty=faculty,
                    department=department,
                    level=level,
                    must_change_password=True,
                )
            emailed = send_credentials(student, password) if send_emails else False
            created.append(
                {
                    "name": student.full_name,
                    "matric_no": student.matric_no,
                    "email": student.email,
                    "password": password,
                    "email_sent": emailed,
                }
            )
            seen_matric.add(matric_no)
            seen_email.add(email)
        except ValidationError as exc:
            errors.append({"row": index, "message": "; ".join(exc.messages)})
        except IntegrityError:
            errors.append({"row": index, "message": "This record conflicts with an existing account."})

    return created, errors
