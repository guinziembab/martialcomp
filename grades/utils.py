"""
Fonctions utilitaires pour l'application grades.
"""
from typing import Union, List, Optional
import logging

from django.http import HttpRequest
from django.db.models import QuerySet

from competitions.models import Discipline, Club

from django.db.models import Max

logger = logging.getLogger(__name__)

def get_user_club(request):
    """Récupère le club associé à l'utilisateur."""
    if hasattr(request.user, 'club') and request.user.club:
        return request.user.club
    
    # Essayer les autres modèles possibles
    club = None
    
    # Vérifier le profil de l'utilisateur
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
        club = request.user.profile.club
    
    # Vérifier si l'utilisateur est propriétaire d'un club
    if not club and hasattr(request.user, 'owned_clubs'):
        club = request.user.owned_clubs.first()
    
    # Dernière tentative - chercher dans les clubs administrés
    if not club and hasattr(request.user, 'club_admin_roles'):
        club_admin = request.user.club_admin_roles.first()
        if club_admin:
            club = club_admin.club
    
    return club

def get_grades_for_discipline(discipline):
    """Récupère tous les grades pour une discipline donnée."""
    from grades.models import Grade
    return Grade.objects.filter(discipline=discipline, is_active=True).order_by('level')

def get_practitioner_grade_history(practitioner):
    """Récupère l'historique complet des grades d'un pratiquant."""
    from grades.models import PractitionerGrade
    return PractitionerGrade.objects.filter(practitioner=practitioner).order_by('-date_obtained')

def get_next_grade(current_grade):
    """Récupère le grade suivant dans la hiérarchie pour une discipline donnée."""
    from grades.models import Grade
    if not current_grade:
        return None
    
    return Grade.objects.filter(
        discipline=current_grade.discipline,
        level__gt=current_grade.level,
        is_active=True
    ).order_by('level').first()