from django import forms

from .models import Comment, NewsletterCampaign, Post


class NewsletterCampaignForm(forms.ModelForm):
    class Meta:
        model = NewsletterCampaign
        fields = ["title", "preview", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Newsletter subject"}),
            "preview": forms.Textarea(attrs={"rows": 2, "placeholder": "A short inbox preview (optional)"}),
            "content": forms.Textarea(attrs={"rows": 16, "placeholder": "Write the newsletter for members and subscribers…"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-input")


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "category", "excerpt", "content", "cover", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "A clear, specific headline"}),
            "excerpt": forms.Textarea(
                attrs={"rows": 2, "placeholder": "One or two sentences for cards and previews"}
            ),
            "content": forms.Textarea(
                attrs={"rows": 16, "placeholder": "Write in Markdown. Use **bold**, lists, > quotes and [links](https://…)."}
            ),
        }

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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Add to the conversation…", "maxlength": 1500}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["body"].widget.attrs.setdefault("class", "field-input")
