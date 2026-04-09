"""
Fonctions utilitaires pour l'application grades.
"""
from typing import Union, List, Optional
import logging

from django.http import HttpRequest
from django.db.models import QuerySet

from apps.competitions.models import Discipline, Club, Federation
from django.db.models import Max
from apps.grades.models import Grade  # Correction ici

logger = logging.getLogger(__name__)

def get_user_club(request):
    """Récupère le club ou l'organisation associée à l'utilisateur."""
    
    # Si l'organisation est déjà dans la requête (via le middleware)
    if hasattr(request, 'user_organization') and request.user_organization:
        return request.user_organization
    
    # Vérifier via UserProfile (comme le middleware)
    try:
        from apps.competitions.models.users import UserProfile
        profile = UserProfile.objects.get(user=request.user)
        if profile.organization:
            return profile.organization
    except:
        pass
    
    # Vérifier via MembershipSubscription actif
    try:
        from apps.membership.models import MembershipSubscription
        subscription = MembershipSubscription.objects.filter(
            practitioner__user=request.user,
            status='active'
        ).select_related('package__organization').first()
        
        if subscription and subscription.package.organization:
            return subscription.package.organization
    except:
        pass
    
    # Ancienne logique comme fallback
    if hasattr(request.user, 'club') and request.user.club:
        return request.user.club
    
    # Vérifier le profil de l'utilisateur
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
        club = request.user.profile.club
        if club:
            return club
    
    # Vérifier si l'utilisateur est propriétaire d'un club
    if hasattr(request.user, 'owned_clubs'):
        club = request.user.owned_clubs.first()
        if club:
            return club
    
    # Dernière tentative - chercher dans les clubs administrés
    if hasattr(request.user, 'club_admin_roles'):
        club_admin = request.user.club_admin_roles.first()
        if club_admin:
            return club_admin.club
    
    return None

def get_user_federation(request):
    """Récupère la fédération associée à l'utilisateur."""
    if hasattr(request.user, 'federation') and request.user.federation:
        return request.user.federation
    
    # Essayer les autres modèles possibles
    federation = None
    
    # Vérifier le profil de l'utilisateur
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'federation'):
        federation = request.user.profile.federation
    
    # Vérifier si l'utilisateur est propriétaire d'une fédération
    if not federation and hasattr(request.user, 'owned_federations'):
        federation = request.user.owned_federations.first()
    
    # Dernière tentative - chercher dans les fédérations administrées
    if not federation and hasattr(request.user, 'federation_admin_roles'):
        federation_admin = request.user.federation_admin_roles.first()
        if federation_admin:
            federation = federation_admin.federation
    
    return federation

def get_grades_for_discipline(discipline):
    """Récupère tous les grades pour une discipline donnée."""
    return Grade.objects.filter(discipline=discipline, is_active=True).order_by('level')

def get_practitioner_grade_history(practitioner):
    """Récupère l'historique complet des grades d'un pratiquant."""
    from apps.grades.models import PractitionerGrade
    return PractitionerGrade.objects.filter(practitioner=practitioner).order_by('-date_obtained')

def get_next_grade(current_grade):
    """Récupère le grade suivant dans la hiérarchie pour une discipline donnée."""
    if not current_grade:
        return None
    
    return Grade.objects.filter(
        discipline=current_grade.discipline,
        level__gt=current_grade.level,
        is_active=True
    ).order_by('level').first()

def check_grade_eligibility(current_grade, min_grade, max_grade):
    """Vérifie si un grade actuel est éligible pour une catégorie donnée."""
    if not current_grade:
        return False
    
    # Si pas de grade minimum requis, toujours éligible
    if not min_grade and not max_grade:
        return True
    
    current_level = current_grade.level if hasattr(current_grade, 'level') else 0
    
    # Vérifier le grade minimum
    if min_grade:
        min_level = min_grade.level if hasattr(min_grade, 'level') else 0
        if current_level < min_level:
            return False
    
    # Vérifier le grade maximum
    if max_grade:
        max_level = max_grade.level if hasattr(max_grade, 'level') else 999
        if current_level > max_level:
            return False
    
    return True