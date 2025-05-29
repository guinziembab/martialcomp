from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permet d'accéder aux clés d'un dictionnaire dans un template Django,
    particulièrement utile pour les clés contenant des caractères spéciaux.
    
    Usage: {{ mydict|get_item:"key-with-hyphen" }}
    """
    return dictionary.get(key, '')