"""
Filtres custom simplifiés pour les templates dashboard
"""
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplie une valeur par un argument"""
    try:
        return float(value or 0) * float(arg or 1)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divise une valeur par un argument"""
    try:
        if float(arg or 1) == 0:
            return 0
        return float(value or 0) / float(arg or 1)
    except (ValueError, TypeError):
        return 0

@register.filter
def calc_percentage_safe(value, total):
    """Calcule le pourcentage de manière sécurisée"""
    try:
        value = float(value or 0)
        total = float(total or 1)
        if total == 0:
            return 0
        percentage = (value / total) * 100
        return min(100, max(0, round(percentage, 1)))
    except (ValueError, TypeError):
        return 0

@register.filter
def safe_int(value, default=0):
    """Convertit en entier de manière sécurisée"""
    try:
        return int(value or default)
    except (ValueError, TypeError):
        return default

@register.filter
def safe_float(value, default=0.0):
    """Convertit en float de manière sécurisée"""
    try:
        return float(value or default)
    except (ValueError, TypeError):
        return default


@register.filter
def subtract(value, arg):
    """Soustrait arg de value"""
    try:
        return float(value or 0) - float(arg or 0)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_filter(value, arg):
    """Additionne value et arg"""
    try:
        return float(value or 0) + float(arg or 0)
    except (ValueError, TypeError):
        return 0

@register.filter
def length_filter(value):
    """Retourne la longueur d'une liste/string"""
    try:
        return len(value)
    except (TypeError, AttributeError):
        return 0

@register.filter
def default_if_none(value, default):
    """Retourne default si value est None"""
    return default if value is None else value

@register.filter
def percentage(value, total):
    """Calcule le pourcentage"""
    try:
        if float(total or 1) == 0:
            return 0
        return (float(value or 0) / float(total or 1)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def currency_format(value):
    """Formate en devise"""
    try:
        return f"{float(value or 0):,.2f}€".replace(',', ' ')
    except (ValueError, TypeError):
        return "0,00€"

@register.filter
def truncate_words(value, max_words):
    """Tronque à un nombre maximum de mots"""
    try:
        words = str(value).split()
        if len(words) <= max_words:
            return value
        return ' '.join(words[:max_words]) + '...'
    except:
        return value

@register.filter
def get_range(value):
    """Crée une range pour les templates"""
    try:
        return range(int(value or 0))
    except (ValueError, TypeError):
        return range(0)

@register.filter
def modulo(value, arg):
    """Opération modulo"""
    try:
        return int(value or 0) % int(arg or 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def absolute(value):
    """Valeur absolue"""
    try:
        return abs(float(value or 0))
    except (ValueError, TypeError):
        return 0

@register.filter
def round_number(value, decimals=0):
    """Arrondit un nombre"""
    try:
        return round(float(value or 0), int(decimals))
    except (ValueError, TypeError):
        return 0

@register.filter
def json_encode(value):
    """Encode en JSON pour JavaScript"""
    import json
    try:
        return json.dumps(value)
    except:
        return '""'

@register.filter
def split_by(value, delimiter):
    """Divise une chaîne"""
    try:
        return str(value).split(delimiter)
    except:
        return [str(value)]

@register.filter
def join_by(value, delimiter):
    """Joint une liste"""
    try:
        return delimiter.join(str(item) for item in value)
    except:
        return str(value)

@register.filter
def first_item(value):
    """Premier élément d'une liste"""
    try:
        return value[0] if value else None
    except (TypeError, IndexError):
        return None

@register.filter
def last_item(value):
    """Dernier élément d'une liste"""
    try:
        return value[-1] if value else None
    except (TypeError, IndexError):
        return None
