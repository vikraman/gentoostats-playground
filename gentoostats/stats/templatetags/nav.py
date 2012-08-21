import re

from django import template
from django.core.urlresolvers import reverse

register = template.Library()

def remove_quotes(s):
    """
    >>> remove_quotes('"hello"')
    'hello'
    """

    if s[0] == s[-1] and s[0] in ('"', "'"):
        return s[1:-1]
    else:
        return s

@register.tag
def nav_link(parser, token):
    """
    Example usage: {% nav_link 'stats:about_url' 'About' %}

    Note: requires 'django.core.context_processors.request' in
    TEMPLATE_CONTEXT_PROCESSORS.
    """

    try:
        tag_name, url, name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires 2 arguments" % token.contents.split()[0])

    return NavLink(remove_quotes(url), remove_quotes(name))

class NavLink(template.Node):
    def __init__(self, url, name):
        self.url  = url
        self.name = name

    def render(self, context):
        reverse_url = reverse(self.url)

        active = ''
        if reverse_url in ('', '/'):
            if reverse_url == context['request'].path:
                active = 'class="current" '
        elif context['request'].path.startswith(reverse_url):
            active = 'class="current" '

        return '<a %shref="%s">%s</a>' % (active, reverse_url, self.name)
