from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django import template

register = template.Library()

@register.simple_tag
def header(level, content):
    return mark_safe(
        "<h{0}><a class=\"header\" name=\"{1}\">{2}</a></h{0}>"\
        .format(level, slugify(content), escape(content))
    )

@register.simple_tag
def h1(content):
    return header(1, content)
