from django import forms

from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "title",
            "summary",
            "description",
            "starts_at",
            "ends_at",
            "venue",
            "flyer",
            "registration_deadline",
            "capacity",
            "eligibility",
            "is_published",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Annual Qur'an Competition"}),
            "summary": forms.Textarea(attrs={"rows": 2, "placeholder": "A single line for cards and previews"}),
            "description": forms.Textarea(
                attrs={"rows": 10, "placeholder": "Markdown is supported. Describe the programme, speakers and what to expect."}
            ),
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "registration_deadline": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "venue": forms.TextInput(attrs={"placeholder": "e.g. AATU Main Auditorium"}),
            "capacity": forms.NumberInput(attrs={"placeholder": "Leave empty for unlimited"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "checkbox")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "field-input select")
            elif isinstance(widget, forms.FileInput):
                widget.attrs.setdefault("class", "field-input file")
            else:
                widget.attrs.setdefault("class", "field-input")
        for name in ("starts_at", "ends_at", "registration_deadline"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]

    def clean(self):
        cleaned = super().clean()
        starts = cleaned.get("starts_at")
        deadline = cleaned.get("registration_deadline")
        ends = cleaned.get("ends_at")
        if starts and ends and ends < starts:
            self.add_error("ends_at", "The end time cannot be before the start time.")
        if starts and deadline and deadline > starts:
            self.add_error("registration_deadline", "Registration must close on or before the event starts.")
        return cleaned
