from django import template

register = template.Library()

@register.filter
def endswith(value, arg):
    """
    Vérifie si la valeur se termine par l'argument.
    
    Usage:
        {% if file.url|endswith:'.pdf' %}
            <!-- Afficher un PDF -->
        {% endif %}
    """
    if value is None:
        return False
    return value.endswith(arg)

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using the key.
    Usage: {{ mydict|get_item:item_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(str(key)) if isinstance(key, int) else dictionary.get(key)


@register.filter
def split(value, arg):
    """
    Splits a string into a list on the specified delimiter
    """
    return value.split(arg)

@register.filter
def strip(value):
    """
    Strips whitespace from the beginning and end of a string
    """
    return value.strip() if value else value