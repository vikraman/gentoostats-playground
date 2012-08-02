from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# The following is taken from gentoolkit.flag, I've copied it here for
# performance reasons (importing it from gentoolkit is slow).
def reduce_flag(flag):
    """Absolute value function for a USE flag

    @type flag: string
    @param flag: the use flag to absolute.
    @rtype: string
    @return absolute USE flag
    """

    if flag[0] in ["+", "-"]:
        return flag[1:]
    else:
        return flag

@register.filter()
def format_use_flags(installation):
    """Prints USE flags with span information"""

    use    = installation.use.values_list('name', flat=True)
    iuse   = installation.iuse.values_list('name', flat=True)
    pkguse = installation.pkguse.values_list('name', flat=True)

    # Remove '-' and '+' from IUSE use flags:
    iuse = [reduce_flag(f) for f in iuse]

    result_list = []
    for f in iuse:
        if f in pkguse:
            if f in use:
                # Selected & Enabled:
                use_class = 'use-selected'
            else:
                # Selected but not enabled:
                use_class = 'use-invalid'
        elif f in use:
            # Not Selected but enabled:
            use_class = 'use-enabled'
        else:
            # Add a '-' to help colour-blind people:
            f = '-' + f

            if f in pkguse:
                # Manually disabled:
                use_class = 'use-unselected'
            else:
                # Simply disabled:
                use_class = 'use-disabled'

        result_list.append(
            '<span class="%s">%s</span>' % (use_class, escape(f))
        )

    return mark_safe(" ".join(result_list))
