# competitions/templatetags/competition_tags.py
from django import template
from django.apps import apps

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé."""
    return dictionary.get(key, '')

@register.filter
def getattribute(obj, attr_name):
    """Récupère un attribut d'un objet par son nom"""
    try:
        return getattr(obj, attr_name)
    except (AttributeError, KeyError):
        return None

@register.filter
def get_field_errors(obj, field_name):
    """Récupère les erreurs d'un champ de formulaire par son nom"""
    try:
        return obj.errors.get(field_name, "")
    except (AttributeError, KeyError):
        return ""

@register.filter
def get_category_object(category_id):
    """Récupère un objet catégorie par son ID"""
    Category = apps.get_model('competitions', 'CompetitionCategory')
    try:
        return Category.objects.get(id=category_id)
    except (Category.DoesNotExist, ValueError):
        return None