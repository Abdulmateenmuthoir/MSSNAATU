from django import forms

from .models import (
    VOLUNTEER_COURSE_CHOICES,
    VOLUNTEER_FORM_TEAM_CHOICES,
    VOLUNTEER_ROLE_CHOICES_BY_TEAM,
    VOLUNTEER_ROLE_GROUP_CHOICES,
    VolunteerApplication,
    ContactMessage,
)


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your full name"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com"}),
            "subject": forms.TextInput(attrs={"placeholder": "What is this about?"}),
            "message": forms.Textarea(attrs={"rows": 5, "placeholder": "How can the office help?"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-input")


class NewsletterForm(forms.Form):
    name = forms.CharField(
        label="Name",
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Enter your full name", "autocomplete": "name"}),
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field-input"


class VolunteerApplicationForm(forms.ModelForm):
    team = forms.ChoiceField(choices=[("", "Select a team"), *VOLUNTEER_FORM_TEAM_CHOICES])
    team_role = forms.ChoiceField(choices=[("", "Select a role"), *VOLUNTEER_ROLE_GROUP_CHOICES])
    courses = forms.MultipleChoiceField(
        choices=VOLUNTEER_COURSE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = VolunteerApplication
        fields = ["team", "team_role", "courses", "work_sample", "publication_url", "has_no_publication", "message"]
        widgets = {
            "team": forms.Select(),
            "publication_url": forms.URLInput(attrs={"placeholder": "https://example.com/your-work"}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us briefly about your experience or interest."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selected_team = self.data.get(self.add_prefix("team")) if self.is_bound else self.initial.get("team", "")
        if not selected_team and self.instance.pk:
            selected_team = self.instance.team
        if selected_team in VOLUNTEER_ROLE_CHOICES_BY_TEAM:
            self.fields["team_role"].choices = [
                ("", "Select a role"),
                *VOLUNTEER_ROLE_CHOICES_BY_TEAM[selected_team],
            ]
        else:
            self.fields["team_role"].choices = [("", "Choose a team first")]
        self.fields["team"].widget.attrs["data-volunteer-team"] = ""
        self.fields["team_role"].widget.attrs["data-volunteer-role"] = ""
        self.fields["work_sample"].widget.attrs["data-volunteer-work-sample"] = ""
        self.fields["work_sample"].widget.attrs["data-existing-work"] = "true" if self.instance.work_sample else "false"
        self.fields["work_sample"].required = False
        self.fields["work_sample"].widget.attrs.update({
            "accept": ".pdf,.doc,.docx,.ppt,.pptx,.zip,.jpg,.jpeg,.png,.webp,.mp4,.mov",
            "class": "field-input",
        })
        self.fields["has_no_publication"].label = "No publication yet"
        for name, field in self.fields.items():
            if name == "courses":
                continue
            if name == "has_no_publication":
                field.widget.attrs["class"] = "checkbox"
            elif name != "work_sample":
                field.widget.attrs["class"] = "field-input"

    def clean(self):
        cleaned = super().clean()
        team = cleaned.get("team")
        team_role = cleaned.get("team_role")
        courses = cleaned.get("courses") or []
        work_sample = cleaned.get("work_sample")
        publication_url = cleaned.get("publication_url")
        no_publication = cleaned.get("has_no_publication")

        if team_role == "graphics_designer" and not work_sample and not self.instance.work_sample:
            self.add_error("work_sample", "A work sample is required for Graphics Designer applications.")
        if team_role == "article_writer" and not no_publication and not publication_url:
            self.add_error("publication_url", "Add a link to a previous publication, or select ‘No publication yet’.")
        if team_role == "tutor" and not courses:
            self.add_error("courses", "Select at least one course you can tutor.")
        return cleaned

    def save(self, commit=True):
        application = super().save(commit=False)
        application.courses = self.cleaned_data.get("courses", []) if self.cleaned_data.get("team_role") == "tutor" else []
        if self.cleaned_data.get("team_role") != "article_writer":
            application.publication_url = ""
            application.has_no_publication = False
        if commit:
            application.save()
        return application
