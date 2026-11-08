from django import forms
from django.core.exceptions import ValidationError

from apps.core.models import Department, LEVEL_CHOICES

from .models import PastQuestion


class PastQuestionForm(forms.ModelForm):
    class Meta:
        model = PastQuestion
        fields = ["faculty", "department", "level", "course_code", "course_title", "session", "file"]
        widgets = {
            "course_code": forms.TextInput(attrs={"placeholder": "e.g. CSC 201"}),
            "course_title": forms.TextInput(attrs={"placeholder": "e.g. Computer Programming II"}),
            "session": forms.TextInput(attrs={"placeholder": "e.g. 2024/2025"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "field-input select")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "field-input file")
            else:
                widget.attrs.setdefault("class", "field-input")
        self.fields["department"].queryset = Department.objects.select_related("faculty").order_by("name")

    def clean(self):
        cleaned = super().clean()
        faculty = cleaned.get("faculty")
        department = cleaned.get("department")
        if faculty and department and department.faculty_id != faculty.id:
            self.add_error("department", "This department does not belong to the selected faculty.")
        return cleaned
