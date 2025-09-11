# templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def zip_lists(a, b):
    """Zip two lists together for template iteration."""
    return list(zip(a, b))
