from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get dictionary item by key"""
    if not dictionary:
        return ""
    if key not in dictionary:
        return ""
    return dictionary.get(key, "")