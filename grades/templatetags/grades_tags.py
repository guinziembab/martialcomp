from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé."""
    if not dictionary:
        return None
    
    # Tentative de conversion en int si c'est une clé numérique
    try:
        key = int(key)
    except (ValueError, TypeError):
        pass
    
    return dictionary.get(key)