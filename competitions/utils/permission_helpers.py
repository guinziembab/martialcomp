"""
Module d'aide pour vérifier les permissions sans utiliser la table UserRoleAssignment.
Ce module fournit des fonctions alternatives pour vérifier les permissions
sans dépendre de la table de base de données manquante.
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _

from competitions.models import Club


def manual_permission_check(permission_code, context_resolver=None, login_url=None):
    """
    Un décorateur qui vérifie manuellement les permissions sans utiliser la table UserRoleAssignment.
    
    Args:
        permission_code: Code de la permission requise (par exemple 'club.view')
        context_resolver: Fonction qui extrait le contexte (par exemple un club) à partir de la requête
        login_url: URL de redirection si l'utilisateur n'est pas connecté
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            # Si l'utilisateur est superuser, autoriser l'accès
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            # Déterminer le contexte si un resolver est fourni
            context = None
            if context_resolver:
                context = context_resolver(request, *args, **kwargs)
                
            # Vérifier les permissions manuellement selon le code de permission
            if permission_code.startswith('club.'):
                # Pour les permissions liées aux clubs
                if manual_check_club_permission(request.user, permission_code, context):
                    return view_func(request, *args, **kwargs)
            elif permission_code.startswith('competitions.'):
                # Pour les permissions liées aux compétitions
                if manual_check_competition_permission(request.user, permission_code, context):
                    return view_func(request, *args, **kwargs)
            elif permission_code.startswith('federation.'):
                # Pour les permissions liées aux fédérations
                if manual_check_federation_permission(request.user, permission_code, context):
                    return view_func(request, *args, **kwargs)
            else:
                # Pour les autres types de permissions
                if manual_check_generic_permission(request.user, permission_code, context):
                    return view_func(request, *args, **kwargs)
                    
            # Si l'utilisateur n'a pas la permission
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder à cette page."))
            return redirect('competitions:dashboard:index')
            
        return _wrapped_view
    return decorator


def manual_check_club_permission(user, permission_code, club=None):
    """
    Vérifie manuellement si un utilisateur a une permission liée à un club.
    
    Args:
        user: L'utilisateur à vérifier
        permission_code: Le code de la permission (par exemple 'club.view')
        club: Le club concerné (optionnel)
        
    Returns:
        Boolean: True si l'utilisateur a la permission, False sinon
    """
    # Si l'utilisateur est superuser, il a toutes les permissions
    if user.is_superuser:
        return True
        
    # Si l'utilisateur est staff, il a accès à tout
    if user.is_staff:
        return True
        
    # Vérifier si l'utilisateur est propriétaire du club
    if club and club.owner == user:
        return True
        
    # Vérifier si l'utilisateur est admin du club
    if hasattr(user, 'club_admin_roles') and club:
        try:
            return user.club_admin_roles.filter(club=club).exists()
        except:
            pass
    
    # Vérification spécifique pour certaines permissions
    if permission_code == 'club.view':
        # Tout utilisateur connecté peut voir les clubs
        return True
    elif permission_code == 'club.edit' and club:
        # Seul le propriétaire ou un admin peut modifier
        return club.owner == user
    elif permission_code == 'club.register_competition':
        # Vérifier si l'utilisateur est responsable de club
        if club:
            return club.owner == user
        else:
            # Vérifier si l'utilisateur est propriétaire d'un club
            return Club.objects.filter(owner=user).exists()
            
    # Par défaut, refuser l'accès
    return False


def manual_check_competition_permission(user, permission_code, context=None):
    """
    Vérifie manuellement si un utilisateur a une permission liée à une compétition.
    """
    # Si l'utilisateur est superuser, il a toutes les permissions
    if user.is_superuser:
        return True
        
    # Si l'utilisateur est staff, il a accès à tout
    if user.is_staff:
        return True
        
    # Pour les permissions de création/modification/suppression d'objets,
    # seuls les admins devraient y avoir accès
    if permission_code in [
        'competitions.add_combatconfiguration',
        'competitions.change_combatconfiguration',
        'competitions.delete_combatconfiguration',
        'competitions.add_equipe',
        'competitions.change_equipe',
        'competitions.delete_equipe',
        'competitions.add_membreequipe',
        'competitions.change_membreequipe',
        'competitions.delete_membreequipe',
        'competitions.add_poule',
        'competitions.change_poule',
        'competitions.delete_poule',
        'competitions.add_combat',
        'competitions.change_combat',
        'competitions.delete_combat',
        'competitions.add_actioncombat',
        'competitions.delete_actioncombat'
    ]:
        # Vérifier si l'utilisateur est admin de compétition
        if hasattr(user, 'is_competition_admin'):
            return user.is_competition_admin
        elif hasattr(user, 'judge') and user.judge:
            # Les juges ont certaines permissions liées aux combats
            return True
        elif hasattr(user, 'role') and user.role in ['federation_admin', 'competition_manager']:
            # Les admins de fédération et les gestionnaires de compétition ont accès
            return True
        else:
            return False
            
    # Par défaut, refuser l'accès
    return False

def check_combat_permission(user, permission_code):
    """
    Vérifie si un utilisateur a les permissions nécessaires pour les fonctionnalités de combat.
    
    Args:
        user: L'utilisateur à vérifier
        permission_code: Le code de permission (par exemple 'competitions.add_combat')
        
    Returns:
        Boolean: True si autorisé, False sinon
    """
    # Si l'utilisateur est superuser ou staff, il a toutes les permissions
    if user.is_superuser or user.is_staff:
        return True
        
    # Si l'utilisateur est juge
    if hasattr(user, 'judge') and user.judge:
        return True
        
    # Si l'utilisateur est admin de fédération ou gestionnaire de compétition
    if hasattr(user, 'role') and user.role in ['federation_admin', 'competition_manager']:
        return True
        
    # Par défaut, refuser l'accès
    return False


def manual_check_federation_permission(user, permission_code, context=None):
    """
    Vérifie manuellement si un utilisateur a une permission liée à une fédération.
    """
    # Si l'utilisateur est superuser, il a toutes les permissions
    if user.is_superuser:
        return True
        
    # Si l'utilisateur est staff, il a accès à tout
    if user.is_staff:
        return True
        
    # Vérifier si l'utilisateur est admin de fédération
    is_federation_admin = getattr(user, 'role', '') == 'federation_admin'
    
    if is_federation_admin:
        return True
        
    # Par défaut, refuser l'accès
    return False


def manual_check_generic_permission(user, permission_code, context=None):
    """
    Vérifie manuellement si un utilisateur a une permission générique.
    """
    # Si l'utilisateur est superuser, il a toutes les permissions
    if user.is_superuser:
        return True
        
    # Si l'utilisateur est staff, il a accès à tout
    if user.is_staff:
        return True
        
    # Par défaut, refuser l'accès
    return False


def get_user_club(request):
    """
    Récupère le club associé à l'utilisateur de manière uniforme.
    Essaie différentes méthodes pour trouver le club.
    """
    # Si le club est déjà dans la requête (via le décorateur)
    if hasattr(request, 'club') and request.club:
        return request.club
    
    # Si l'utilisateur a un attribut club
    if hasattr(request.user, 'club') and request.user.club:
        return request.user.club
    
    # Si l'utilisateur est propriétaire d'un club
    club = Club.objects.filter(owner=request.user).first()
    if club:
        return club
    
    # Si l'utilisateur est administrateur d'un club
    if hasattr(request.user, 'club_admin_roles'):
        try:
            club_admin = request.user.club_admin_roles.first()
            if club_admin:
                return club_admin.club
        except:
            pass
    
    return None