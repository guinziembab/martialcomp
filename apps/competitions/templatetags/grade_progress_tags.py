# competitions/templatetags/grade_progress_tags.py
"""
Template tags pour le Widget de Progression de Grade
Prompt 1 - Grade Tracking

Usage dans les templates:
    {% load grade_progress_tags %}
    {% grade_progress_widget practitioner discipline=discipline %}
"""

from django import template
from django.utils.translation import gettext_lazy as _
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.inclusion_tag('components/grade_progress_widget.html', takes_context=True)
def grade_progress_widget(context, practitioner, discipline=None, compact=False):
    """
    Affiche le widget de progression vers le prochain grade.

    Args:
        context: Context du template parent
        practitioner: Instance de Practitioner
        discipline: Instance de Discipline (optionnel)
        compact: Mode compact pour les affichages reduits (defaut: False)

    Returns:
        Dictionnaire de context pour le template du widget
    """
    if not practitioner:
        return {
            'has_data': False,
            'error': False,
        }

    try:
        from apps.competitions.services.grade_eligibility import GradeEligibilityService

        # Calculer l'eligibilite
        result = GradeEligibilityService.check_eligibility(practitioner, discipline)

        # Convertir le resultat en donnees pour le template
        return {
            'has_data': True,
            'error': False,
            'compact': compact,
            'practitioner_id': practitioner.id,

            # Statut
            'status': result.status,
            'is_eligible': result.is_eligible,

            # Grades
            'current_grade': result.current_grade,
            'next_grade': result.next_grade,

            # Progression
            'progress_percentage': result.progress_percentage,
            'days_remaining': result.days_remaining,
            'eligibility_date': result.eligibility_date,

            # Raisons bloquantes
            'blocking_reasons': result.blocking_reasons,

            # Exigences
            'requirements_status': [
                {
                    'name': req.name,
                    'description': req.description,
                    'is_mandatory': req.is_mandatory,
                    'is_met': req.is_met,
                    'current_value': req.current_value,
                    'required_value': req.required_value,
                }
                for req in result.requirements_status
            ] if result.requirements_status else [],

            # Examens disponibles
            'available_exams': result.available_exams,
        }

    except ImportError as e:
        logger.error(f"Import error for GradeEligibilityService: {e}")
        return {
            'has_data': False,
            'error': True,
        }
    except Exception as e:
        logger.error(f"Error in grade_progress_widget for practitioner {practitioner.id}: {e}")
        return {
            'has_data': False,
            'error': True,
        }


@register.filter
def grade_color(grade_name):
    """
    Retourne le code couleur CSS pour un nom de grade.

    Usage:
        {{ grade.name|grade_color }}

    Args:
        grade_name: Nom du grade (ex: "Ceinture Jaune")

    Returns:
        Code couleur hexadecimal
    """
    if not grade_name:
        return '#6c757d'

    name_lower = grade_name.lower()

    # Ceintures standards
    color_map = {
        'blanc': '#ffffff',
        'white': '#ffffff',
        'jaune': '#ffd700',
        'yellow': '#ffd700',
        'orange': '#ff8c00',
        'vert': '#228b22',
        'green': '#228b22',
        'bleu': '#1e90ff',
        'blue': '#1e90ff',
        'marron': '#8b4513',
        'brown': '#8b4513',
        'noir': '#000000',
        'black': '#000000',
        'rouge': '#dc143c',
        'red': '#dc143c',
        'violet': '#8a2be2',
        'purple': '#8a2be2',
    }

    for key, color in color_map.items():
        if key in name_lower:
            return color

    return '#6c757d'  # Gris par defaut


@register.filter
def days_to_text(days):
    """
    Convertit un nombre de jours en texte lisible.

    Usage:
        {{ days_remaining|days_to_text }}

    Args:
        days: Nombre de jours

    Returns:
        Texte formate (ex: "3 mois", "45 jours", "Eligible")
    """
    if days is None:
        return ""

    try:
        days = int(days)
    except (ValueError, TypeError):
        return str(days)

    if days <= 0:
        return str(_("Eligible"))
    elif days == 1:
        return str(_("1 jour"))
    elif days < 30:
        return str(_("%(days)d jours") % {'days': days})
    elif days < 60:
        return str(_("1 mois"))
    elif days < 365:
        months = days // 30
        return str(_("%(months)d mois") % {'months': months})
    else:
        years = days // 365
        months = (days % 365) // 30
        if months > 0:
            return str(_("%(years)d an(s) et %(months)d mois") % {'years': years, 'months': months})
        return str(_("%(years)d an(s)") % {'years': years})


@register.filter
def progress_class(percentage):
    """
    Retourne la classe CSS selon le pourcentage de progression.

    Usage:
        <div class="{{ progress_percentage|progress_class }}">

    Args:
        percentage: Pourcentage de progression (0-100)

    Returns:
        Classe CSS (ex: "progress-low", "progress-medium", "progress-high", "progress-complete")
    """
    if percentage is None:
        return "progress-unknown"

    try:
        percentage = float(percentage)
    except (ValueError, TypeError):
        return "progress-unknown"

    if percentage >= 100:
        return "progress-complete"
    elif percentage >= 75:
        return "progress-high"
    elif percentage >= 50:
        return "progress-medium"
    elif percentage >= 25:
        return "progress-low"
    else:
        return "progress-start"


@register.simple_tag
def grade_eligibility_status(practitioner, discipline=None):
    """
    Retourne le statut d'eligibilite simplifie pour un pratiquant.

    Usage:
        {% grade_eligibility_status practitioner discipline as status %}
        {{ status.is_eligible }}

    Args:
        practitioner: Instance de Practitioner
        discipline: Instance de Discipline (optionnel)

    Returns:
        Dictionnaire avec is_eligible, status, days_remaining, progress_percentage
    """
    if not practitioner:
        return {
            'is_eligible': False,
            'status': 'no_data',
            'days_remaining': 0,
            'progress_percentage': 0,
        }

    try:
        from apps.competitions.services.grade_eligibility import GradeEligibilityService

        result = GradeEligibilityService.check_eligibility(practitioner, discipline)

        return {
            'is_eligible': result.is_eligible,
            'status': result.status,
            'days_remaining': result.days_remaining,
            'progress_percentage': result.progress_percentage,
            'next_grade_name': result.next_grade.get('name') if result.next_grade else None,
        }

    except Exception as e:
        logger.error(f"Error in grade_eligibility_status: {e}")
        return {
            'is_eligible': False,
            'status': 'error',
            'days_remaining': 0,
            'progress_percentage': 0,
        }


@register.inclusion_tag('components/grade_progress_bar.html')
def grade_progress_bar(percentage, show_text=True, size='normal'):
    """
    Affiche une barre de progression simple.

    Usage:
        {% grade_progress_bar 75 show_text=True size="small" %}

    Args:
        percentage: Pourcentage de progression (0-100)
        show_text: Afficher le texte du pourcentage (defaut: True)
        size: Taille de la barre - "small", "normal", "large" (defaut: "normal")

    Returns:
        Context pour le template de la barre de progression
    """
    try:
        percentage = float(percentage)
        percentage = max(0, min(100, percentage))  # Clamp entre 0 et 100
    except (ValueError, TypeError):
        percentage = 0

    return {
        'percentage': percentage,
        'show_text': show_text,
        'size': size,
        'progress_class': progress_class(percentage),
    }
