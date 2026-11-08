from django import forms
from django.utils import timezone

from .models import DuesCycle


class DuesCycleForm(forms.ModelForm):
    class Meta:
        model = DuesCycle
        fields = ["session", "amount", "due_date", "note", "is_active"]
        widgets = {
            "session": forms.TextInput(attrs={"placeholder": "e.g. 1449/1450 AH"}),
            "amount": forms.NumberInput(attrs={"placeholder": "2000", "step": "50"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "note": forms.TextInput(attrs={"placeholder": "Optional note shown to members"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "checkbox")
            else:
                field.widget.attrs.setdefault("class", "field-input")
        self.fields["due_date"].input_formats = ["%Y-%m-%d"]

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < timezone.localdate():
            raise forms.ValidationError("The due date cannot be in the past.")
        return due_date

    def save(self, commit=True):
        cycle = super().save(commit=False)
        if commit:
            if cycle.is_active:
                DuesCycle.objects.exclude(pk=cycle.pk).update(is_active=False)
            cycle.save()
        return cycle
