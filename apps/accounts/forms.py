from django import forms
from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError

from apps.core.models import Department, Faculty, LEVEL_CHOICES

from .models import GENDER_CHOICES, ROLE_CHOICES, Student


class BaseForm(forms.Form):
    """Adds consistent classes to every widget so templates stay tidy."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "checkbox")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "field-input select")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "field-input file")
            else:
                widget.attrs.setdefault("class", "field-input")
            if field.required and not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("required", True)


class LoginForm(BaseForm):
    identifier = forms.CharField(
        label="Matric number or email",
        widget=forms.TextInput(
            attrs={
                "placeholder": "e.g. AATU/CS/22/001",
                "autofocus": True,
                "autocomplete": "username",
                "spellcheck": "false",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Your password", "autocomplete": "current-password"}),
    )
    remember_me = forms.BooleanField(label="Keep me signed in", required=False, initial=True)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        identifier = cleaned.get("identifier")
        password = cleaned.get("password")
        if identifier and password:
            user = authenticate(self.request, username=identifier, password=password)
            if user is None:
                raise ValidationError("Those details do not match an active account.", code="invalid_login")
            if not user.is_active:
                raise ValidationError("This account is currently inactive. Contact the PRO office.", code="inactive")
            cleaned["user"] = user
        return cleaned


class ForgotPasswordForm(BaseForm):
    identifier = forms.CharField(
        label="Matric number or email",
        widget=forms.TextInput(attrs={"placeholder": "AATU/CS/22/001 or you@example.com", "autofocus": True}),
    )


class SetPasswordForm(BaseForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "At least 8 characters"}),
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "placeholder": "Repeat your new password"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        password = self.cleaned_data["new_password1"]
        if self.user is not None:
            password_validation.validate_password(password, self.user)
        return password

    def clean(self):
        cleaned = super().clean()
        first = cleaned.get("new_password1")
        second = cleaned.get("new_password2")
        if first and second and first != second:
            self.add_error("new_password2", "The two passwords do not match.")
        return cleaned

    def save(self):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        self.user.must_change_password = False
        self.user.save(update_fields=["password", "must_change_password"])
        return self.user


class ChangePasswordForm(SetPasswordForm):
    old_password = forms.CharField(
        label="Current password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password", "placeholder": "Your current password"}),
    )

    def clean_old_password(self):
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise ValidationError("Your current password is not correct.")
        return old_password


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ["phone", "bio", "avatar"]
        widgets = {
            "phone": forms.TextInput(attrs={"placeholder": "+234 800 000 0000"}),
            "bio": forms.Textarea(
                attrs={"rows": 3, "placeholder": "A line or two about you, your interests or your role."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-input")
        self.fields["avatar"].widget.attrs.setdefault("class", "field-input file")


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "first_name",
            "last_name",
            "matric_no",
            "email",
            "gender",
            "faculty",
            "department",
            "level",
            "role",
        ]
        widgets = {
            "matric_no": forms.TextInput(attrs={"placeholder": "AATU/CS/22/001"}),
            "email": forms.EmailInput(attrs={"placeholder": "student@example.com"}),
            "first_name": forms.TextInput(attrs={"placeholder": "First name"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Surname"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-input")
        self.fields["department"].queryset = Department.objects.select_related("faculty")
        self.fields["department"].required = False
        self.fields["faculty"].required = False
        self.fields["level"].required = False

    def clean_matric_no(self):
        return self.cleaned_data["matric_no"].strip().upper()

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class StudentEditForm(StudentForm):
    class Meta(StudentForm.Meta):
        fields = [
            "first_name",
            "last_name",
            "matric_no",
            "email",
            "gender",
            "faculty",
            "department",
            "level",
            "role",
        ]


class CSVImportForm(BaseForm):
    csv_file = forms.FileField(
        label="Student list (CSV)",
        help_text="Columns: full_name or first_name/last_name, email, matric_no, faculty, department, level, gender.",
        widget=forms.FileInput(attrs={"accept": ".csv,text/csv"}),
    )
    send_emails = forms.BooleanField(
        label="Email login details to each student",
        required=False,
        initial=True,
        help_text="Uses the console email backend in development.",
    )


class PromoteForm(BaseForm):
    confirm = forms.BooleanField(
        label="I understand this changes every eligible student's level",
        required=True,
    )
