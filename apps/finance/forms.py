from django import forms
from django.utils import timezone

from .models import DuesCycle


class BankReceiptForm(forms.Form):
    receipt = forms.FileField(
        label="Transfer receipt",
        help_text="Upload a JPG, PNG or PDF, up to 5 MB.",
        widget=forms.ClearableFileInput(attrs={"accept": ".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"}),
    )

    def clean_receipt(self):
        upload = self.cleaned_data["receipt"]
        allowed_extensions = {".jpg", ".jpeg", ".png", ".pdf"}
        if upload.size > 5 * 1024 * 1024:
            raise forms.ValidationError("The receipt must be 5 MB or smaller.")
        extension = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
        signatures = {
            "jpg": (b"\xff\xd8\xff",),
            "jpeg": (b"\xff\xd8\xff",),
            "png": (b"\x89PNG\r\n\x1a\n",),
            "pdf": (b"%PDF-",),
        }
        if f".{extension}" not in allowed_extensions:
            raise forms.ValidationError("Upload a JPG, PNG or PDF receipt.")
        header = upload.read(8)
        upload.seek(0)
        if not any(header.startswith(signature) for signature in signatures[extension]):
            raise forms.ValidationError("The uploaded file does not match its file type.")
        return upload


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
