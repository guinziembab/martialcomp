# competitions/templatetags/grade_tags.py
from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def filter_for_practitioner(history_list, practitioner):
    """Filtre l'historique pour un pratiquant spécifique."""
    return [h for h in history_list if h.practitioner == practitioner]

@register.filter
def filter_recent_months(history_list, months):
    """Filtre l'historique pour les X derniers mois."""
    cutoff_date = timezone.now().date() - timedelta(days=30*months)
    return [h for h in history_list if h.obtained_date >= cutoff_date]

@register.filter
def filter_no_grade(practitioners_list):
    """Filtre les pratiquants sans grade."""
    return [p for p in practitioners_list if not p.grade]

@register.filter
def find_belt_stripe_color(belt_name):
    """Extrait la couleur de la barrette à partir du nom du grade."""
    belt_name = belt_name.lower()
    if 'rouge' in belt_name:
        return '#FF0000'
    if 'bleu' in belt_name:
        return '#0000FF'
    if 'vert' in belt_name:
        return '#008000'
    if 'jaune' in belt_name:
        return '#FFFF00'
    if 'orange' in belt_name:
        return '#FFA500'
    if 'noir' in belt_name:
        return '#000000'
    return '#000000'  # Couleur par défaut