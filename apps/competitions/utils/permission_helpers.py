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

from apps.competitions.models import Club


def manual_permission_check(permission_code, context_resolver=None, login_url=None):
    """
    Un décorateur qui vérifie manuellement les permissions sans utiliser la table UserRoleAssignment.
    
    Args:
        permission_code: Code de la permission requise (par exemple 'club.view')
        context_resolver: Fonction qui extrait le contexte (par exemple un club) Ã  partir de la requÃªte
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
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder Ã  cette page."))
            # Redirection vers l'URL de tableau de bord - CORRECTION
            try:
                # Essaie d'abord d'utiliser 'competitions:dashboard:dashboard' qui semble Ãªtre la bonne URL
                return redirect('competitions:dashboard:dashboard')
            except:
                try:
                    # Si cela échoue, essaie avec une URL absolue
                    return redirect('/competitions/dashboard/')
                except:
                    # Si tout échoue, redirige vers la page d'accueil
                    return redirect('/')
            
        return _wrapped_view
    return decorator


def manual_check_club_permission(user, permission_code, club=None):
    """
    Vérifie manuellement si un utilisateur a une permission liée Ã  un club.
    
    Args:
        user: L'utilisateur Ã  vérifier
        permission_code: Le code de la permission (par exemple 'club.view')
        club: Le club concerné (optionnel)
        
    Returns:
        Boolean: True si l'utilisateur a la permission, False sinon
    """
    # Si l'utilisateur est superuser, il a toutes les permissions
    if user.is_superuser:
        return True
        
    # Si l'utilisateur est staff, il a accès Ã  tout
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
    elif permission_code == 'club.manage_competitions':
        # Pour la gestion des compétitions, permettre l'accès si l'utilisateur est propriétaire d'un club
        # ou si l'utilisateur est staff
        if user.is_staff or user.is_superuser:
            return True
        # Vérifier si l'utilisateur est propriétaire d'un club
        if Club.objects.filter(owner=user).exists():
            return True
        # Si un club est fourni, vérifier si l'utilisateur en est propriétaire
        if club and club.owner == user:
            return True
        # Par défaut, permettre l'accès si l'utilisateur est connecté
        # (pour permettre l'accès aux compétitions publiées)
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
    Vérifie manuellement si un utilisateur a une permission liée Ã  une compétition.
    """
    # Si l'utilisateur est superuser, il a toutes les permissions
    if user.is_superuser:
        return True
        
    # Si l'utilisateur est staff, il a accès Ã  tout
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
        user: L'utilisateur Ã  vérifier
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
    Vérifie manuellement si un utilisateur a une permission liée Ã  une fédération.
    """
    # Si l'utilisateur est superuser, il a toutes les permissions
    if user.is_superuser:
        return True
        
    # Si l'utilisateur est staff, il a accès Ã  tout
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
        
    # Si l'utilisateur est staff, il a accès Ã  tout
    if user.is_staff:
        return True
        
    # Par défaut, refuser l'accès
    return False


def get_user_club(request):
    """
    Récupère le club associé Ã  l'utilisateur de manière uniforme.
    Essaie différentes méthodes pour trouver le club.
    """
    # Si le club est déjÃ  dans la requÃªte (via le décorateur)
    if hasattr(request, 'club') and request.club:
        return request.club
    
    # Si l'utilisateur a un attribut club
    if hasattr(request.user, 'club') and request.user.club:
        return request.user.club
    
    # Si l'utilisateur est propriétaire d'un club - utiliser SQL brut pour éviter modeltranslation
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id FROM competitions_club WHERE owner_id = %s LIMIT 1
        """, [request.user.id])
        row = cursor.fetchone()
        if row:
            try:
                # Charger le club avec une requête SQL minimale
                club = Club.objects.raw('SELECT * FROM competitions_club WHERE id = %s', [row[0]])[0]
                return club
            except:
                pass
    
    # Si l'utilisateur est administrateur d'un club
    if hasattr(request.user, 'club_admin_roles'):
        try:
            club_admin = request.user.club_admin_roles.first()
            if club_admin:
                return club_admin.club
        except:
            pass

    # Fallback: via practitioner → organization → club
    if hasattr(request.user, 'practitioners'):
        try:
            practitioner = request.user.practitioners.first()
            if practitioner and practitioner.organization_id:
                club = Club.objects.filter(organization=practitioner.organization).first()
                if club:
                    return club
        except:
            pass

    return None


# ============================================================================
# DISCIPLINE ISOLATION HELPERS - Phase 1 Security
# ============================================================================

import logging
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

logger = logging.getLogger('discipline_isolation')


def get_user_organization(user):
    """
    Recupere l'organisation principale de l'utilisateur.
    Cherche dans l'ordre: Federation admin, Club owner, Club admin, Practitioner.

    Args:
        user: L'utilisateur Django

    Returns:
        Organization ou None
    """
    if not user or not user.is_authenticated:
        return None

    if user.is_superuser:
        return None  # Superuser voit tout, pas besoin d'org

    try:
        # 1. Verifier si l'utilisateur est admin d'une federation
        from apps.organizations.models import Organization

        # Via le profil utilisateur
        if hasattr(user, 'profile') and user.profile:
            profile = user.profile
            if hasattr(profile, 'organization') and profile.organization:
                return profile.organization

        # 2. Verifier si l'utilisateur est proprietaire d'un club
        from apps.competitions.models import Club
        club = Club.objects.filter(owner=user).first()
        if club:
            # Retourner l'organisation du club
            if hasattr(club, 'organization') and club.organization:
                return club.organization
            # Ou le club lui-meme s'il est une organisation
            org = Organization.objects.filter(id=club.id).first()
            if org:
                return org

        # 3. Verifier via les administrateurs de club
        if hasattr(user, 'club_admin_roles'):
            admin_role = user.club_admin_roles.first()
            if admin_role and admin_role.club:
                if hasattr(admin_role.club, 'organization'):
                    return admin_role.club.organization

        # 4. Verifier via le practitioner
        if hasattr(user, 'practitioner') and user.practitioner:
            practitioner = user.practitioner
            if hasattr(practitioner, 'club') and practitioner.club:
                if hasattr(practitioner.club, 'organization'):
                    return practitioner.club.organization

    except Exception as e:
        logger.warning(f"Error getting user organization for {user}: {e}")

    return None


def get_user_disciplines(user, organization=None):
    """
    Retourne les disciplines accessibles pour un utilisateur.

    Args:
        user: L'utilisateur Django
        organization: Organisation optionnelle (si deja connue)

    Returns:
        QuerySet de Discipline ou Discipline.objects.none()
    """
    from apps.competitions.models import Discipline

    if not user or not user.is_authenticated:
        return Discipline.objects.none()

    if user.is_superuser:
        return Discipline.objects.filter(is_active=True)

    if not organization:
        organization = get_user_organization(user)

    if organization and hasattr(organization, 'disciplines'):
        return organization.disciplines.filter(is_active=True)

    # Fallback: chercher via le club
    try:
        from apps.competitions.models import Club
        club = Club.objects.filter(owner=user).first()
        if club and hasattr(club, 'disciplines'):
            return club.disciplines.filter(is_active=True)
    except Exception:
        pass

    return Discipline.objects.none()


def check_discipline_access(user, discipline, organization=None, log_access=False, request=None, action='view', resource_type='', resource_id=None):
    """
    Verifie si un utilisateur peut acceder a une discipline.
    PHASE 3: Optionnellement log l'acces pour audit.

    Args:
        user: L'utilisateur Django
        discipline: La Discipline a verifier
        organization: Organisation optionnelle
        log_access: Si True, enregistre l'acces dans DisciplineAccessLog
        request: HttpRequest optionnel (pour extraire IP)
        action: Type d'action (view, edit, create, delete, export, api_access)
        resource_type: Type de ressource accedee (ex: 'Grade', 'Practitioner')
        resource_id: ID de la ressource

    Returns:
        bool: True si acces autorise, False sinon
    """
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    if not discipline:
        return True  # Pas de discipline = pas de restriction

    accessible_disciplines = get_user_disciplines(user, organization)
    allowed = accessible_disciplines.filter(id=discipline.id).exists()

    # PHASE 3: Log l'acces si demande
    if log_access and discipline:
        try:
            from apps.core.models import DisciplineAccessLog
            if allowed:
                # Log acces autorise (optionnel, peut generer beaucoup de logs)
                pass  # Ne log que les refus par defaut
            else:
                # Log acces refuse
                DisciplineAccessLog.log_denied_access(
                    user=user,
                    discipline=discipline,
                    action=action,
                    request=request,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    reason='Discipline not in user accessible disciplines'
                )
        except Exception as e:
            logger.warning(f"Failed to log discipline access: {e}")

    return allowed


def filter_queryset_by_user_disciplines(queryset, user, discipline_field='discipline'):
    """
    Filtre un queryset par les disciplines accessibles de l'utilisateur.
    SECURISE: Retourne queryset.none() en cas d'erreur.

    Args:
        queryset: Le queryset a filtrer
        user: L'utilisateur Django
        discipline_field: Nom du champ discipline (ex: 'discipline', 'discipline_id')

    Returns:
        QuerySet filtre
    """
    if not user or not user.is_authenticated:
        return queryset.none()

    if user.is_superuser:
        return queryset

    try:
        accessible_disciplines = get_user_disciplines(user)

        if not accessible_disciplines.exists():
            logger.warning(f"User {user} has no accessible disciplines - returning empty queryset")
            return queryset.none()

        # Construire le filtre dynamiquement
        if discipline_field.endswith('_id'):
            filter_kwargs = {f'{discipline_field}__in': accessible_disciplines.values_list('id', flat=True)}
        else:
            filter_kwargs = {f'{discipline_field}__in': accessible_disciplines}

        return queryset.filter(**filter_kwargs)

    except Exception as e:
        logger.critical(f"Discipline isolation FAILED for user {user}: {e}")
        # SECURITE: En cas d'erreur, retourner queryset vide
        return queryset.none()


def get_discipline_ids_for_user(user):
    """
    Retourne la liste des IDs de disciplines accessibles.
    Utile pour les requetes SQL directes.

    Args:
        user: L'utilisateur Django

    Returns:
        list: Liste des IDs de disciplines
    """
    disciplines = get_user_disciplines(user)
    return list(disciplines.values_list('id', flat=True))


class DisciplineAccessMixin(LoginRequiredMixin):
    """
    Mixin pour les vues qui necessite une verification d'acces par discipline.

    Usage:
        class MyView(DisciplineAccessMixin, DetailView):
            model = Grade
            discipline_field = 'discipline'  # Optionnel, defaut: 'discipline'
    """
    discipline_field = 'discipline'

    def get_queryset(self):
        """Filtre le queryset par les disciplines accessibles."""
        queryset = super().get_queryset()
        return filter_queryset_by_user_disciplines(
            queryset,
            self.request.user,
            self.discipline_field
        )

    def get_object(self, queryset=None):
        """Verifie l'acces a l'objet par discipline."""
        obj = super().get_object(queryset)

        # Verifier l'acces a la discipline de l'objet
        discipline = getattr(obj, self.discipline_field, None)
        if discipline and not check_discipline_access(
            self.request.user,
            discipline,
            log_access=True,
            request=self.request,
            action='view',
            resource_type=obj.__class__.__name__,
            resource_id=obj.pk
        ):
            logger.warning(
                f"User {self.request.user} denied access to {obj} "
                f"(discipline: {discipline})"
            )
            raise PermissionDenied("Acces a cette discipline non autorise")

        return obj


class DisciplineFormMixin:
    """
    Mixin pour les formulaires qui necessite un filtrage des disciplines.

    Usage:
        class MyForm(DisciplineFormMixin, forms.ModelForm):
            def __init__(self, *args, user=None, organization=None, **kwargs):
                self.user = user
                self.organization = organization
                super().__init__(*args, **kwargs)
                self.filter_discipline_fields()
    """
    discipline_fields = ['discipline', 'disciplines', 'primary_discipline', 'secondary_disciplines']

    def filter_discipline_fields(self):
        """Filtre tous les champs discipline par l'organisation de l'utilisateur."""
        if not hasattr(self, 'user') or not self.user:
            return

        accessible_disciplines = get_user_disciplines(
            self.user,
            getattr(self, 'organization', None)
        )

        for field_name in self.discipline_fields:
            if field_name in self.fields:
                self.fields[field_name].queryset = accessible_disciplines


def secure_discipline_api_view(view_func):
    """
    Decorateur pour securiser les vues API avec filtrage par discipline.

    Usage:
        @secure_discipline_api_view
        def my_api_view(request):
            # request.accessible_disciplines contient les disciplines accessibles
            # request.discipline_ids contient les IDs
            pass
    """
    from functools import wraps
    from django.contrib.auth.decorators import login_required

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Ajouter les disciplines accessibles a la requete
        request.accessible_disciplines = get_user_disciplines(request.user)
        request.discipline_ids = get_discipline_ids_for_user(request.user)

        # Si l'utilisateur n'a acces a aucune discipline (et n'est pas superuser)
        if not request.user.is_superuser and not request.discipline_ids:
            from django.http import JsonResponse
            return JsonResponse({
                'error': 'No accessible disciplines',
                'results': []
            }, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper

