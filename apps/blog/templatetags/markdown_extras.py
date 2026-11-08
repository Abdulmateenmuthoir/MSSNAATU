from django import template
from django.utils.safestring import mark_safe
import markdown as md

register = template.Library()


@register.filter
def markdownify(value):
    if not value:
        return ""
    html = md.markdown(
        value,
        extensions=["extra", "sane_lists", "nl2br"],
        output_format="html5",
    )
    return mark_safe(html)


@register.filter
def category_label(value):
    return dict(
        [
            ("news", "News"),
            ("editorial", "Editorial"),
            ("campus", "Campus"),
            ("deen", "Deen"),
            ("society", "Society"),
        ]
    ).get(value, value.title())
