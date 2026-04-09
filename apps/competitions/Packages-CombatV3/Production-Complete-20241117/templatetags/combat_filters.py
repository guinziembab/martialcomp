"""
Filtres personnalisés pour les templates de combat
"""
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Récupère un élément d'un dictionnaire avec une clé
    Usage: {{ dict|get_item:key }}
    """
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(str(key))
    return None

@register.filter
def format_score(value):
    """
    Formate un score en supprimant les décimales inutiles
    """
    try:
        score = float(value)
        if score == int(score):
            return str(int(score))
        return f"{score:.2f}".rstrip('0').rstrip('.')
    except:
        return value

@register.filter
def abs_value(value):
    """
    Retourne la valeur absolue
    """
    try:
        return abs(float(value))
    except:
        return value

@register.filter
def subtract(value, arg):
    """
    Soustrait arg de value
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def format_time(seconds):
    """
    Formate un nombre de secondes en format MM:SS
    Usage: {{ combat.duree_combat|format_time }}
    """
    if seconds is None:
        return "02:00"
    
    try:
        seconds = int(float(seconds))
        if seconds < 0:
            seconds = 0
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"
    except (ValueError, TypeError):
        # Si la valeur n'est pas un nombre, retourner la valeur par défaut
        return "02:00"