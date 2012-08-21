from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django import template

register = template.Library()

@register.filter
def get_unicode(obj):
    """Returns the Unicode representation of an object."""
    return unicode(obj)

@register.filter(is_safe=False)
def append(value, arg):
    """Combines two strings."""
    try:
        return unicode(value) + unicode(arg)
    except Exception:
        return ''

@register.simple_tag
def header(level, content):
    """Produces a named HTML header."""
    return mark_safe(
        "<h{0}><a class=\"header\" name=\"{1}\">{2}</a></h{0}>"\
        .format(level, slugify(content), escape(content))
    )

@register.simple_tag
def h1(content):
    """Produces a named <h1> header."""
    return header(1, content)

@register.simple_tag
def h2(content):
    """Produces a named <h2> header."""
    return header(2, content)
