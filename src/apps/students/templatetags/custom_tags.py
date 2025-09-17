# templatetags/custom_tags.py
from django import template

register = template.Library()

@register.filter
def zip_lists(a, b):
    """Zip two lists together for template iteration."""
    return list(zip(a, b))


@register.filter
def lookup_score(scores_dict, key):
    """
    Looks up a score from a scores dict using a 'subject|exam' key.
    Usage in template: row.scores|lookup_score:"Math|Midterm"
    """
    try:
        subject, exam = key.split("|", 1)
        composite_key = f"{subject}|{exam}"
        return scores_dict.get(composite_key, "-")
    except Exception:
        return "-"


@register.simple_tag
def get_score(scores_dict, subject, exam):
    key = f"{subject}|{exam}"
    return scores_dict.get(key, "-")
