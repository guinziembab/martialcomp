"""
Système d'isolation des données pour MartialComp
Gère la séparation des données entre organisations
"""

from django.db import models
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class OrganizationIsolationMixin:
    """
    Mixin pour isoler les données par organisation
    """
    
    def get_user_organization(self, user):
        """Retourne l'organisation de l'utilisateur"""
        try:
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=user)
            return profile.organization
        except UserProfile.DoesNotExist:
            return None
    
    def get_organization_filter(self, user):
        """Retourne le filtre d'organisation pour les requêtes"""
        org = self.get_user_organization(user)
        if org:
            return Q(organization=org)
        return Q()
    
    def filter_by_organization(self, queryset, user):
        """Filtre un queryset par organisation"""
        if user.is_superuser or user.is_staff:
            return queryset
        
        org_filter = self.get_organization_filter(user)
        if org_filter:
            return queryset.filter(org_filter)
        
        # Si pas d'organisation, retourner queryset vide
        return queryset.none()


class OrganizationSecurityMiddleware(MiddlewareMixin):
    """
    Middleware de sécurité qui s'assure qu'aucune requête ne peut accéder 
    aux données d'autres organisations.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        # Injecter l'organisation de l'utilisateur dans la requête
        # Vérifier d'abord si l'attribut user existe (ajouté par AuthenticationMiddleware)
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.user_organization = self.get_user_organization(request.user)
        else:
            request.user_organization = None
        
        response = self.get_response(request)
        return response
    
    def get_user_organization(self, user):
        """Récupère l'organisation principale de l'utilisateur."""
        try:
            # Via le profil utilisateur
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=user)
            if profile.organization:
                return profile.organization
            
            # Via les memberships actifs si pas d'organisation dans le profil
            from apps.membership.models import MembershipSubscription
            subscription = MembershipSubscription.objects.filter(
                practitioner__user=user,
                status='active'
            ).select_related('package__organization').first()
            
            return subscription.package.organization if subscription else None
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération de l'organisation pour {user.username}: {e}")
            return None
    
    def process_request(self, request):
        """Traite la requête et ajoute l'organisation au contexte"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.user_organization = self.get_user_organization(request.user)
            if not request.user_organization and not (request.user.is_superuser or request.user.is_staff):
                logger.warning(f"Utilisateur {request.user.username} sans organisation")
        else:
            request.user_organization = None


# Maintien du middleware existant pour compatibilité
class OrganizationMiddleware(OrganizationSecurityMiddleware):
    """Alias pour compatibilité avec l'ancien middleware"""
    pass


def require_organization_access(user, organization=None):
    """
    Vérifie que l'utilisateur a accès à l'organisation
    """
    if user.is_superuser or user.is_staff:
        return True
    
    try:
        from apps.competitions.models.users import UserProfile
        user_profile = UserProfile.objects.get(user=user)
        user_org = user_profile.organization
        
        if organization and user_org != organization:
            return False
        
        return user_org is not None
    except UserProfile.DoesNotExist:
        return False


def get_organization_queryset(model_class, user, **filters):
    """
    Retourne un queryset filtré par organisation
    """
    if user.is_superuser or user.is_staff:
        return model_class.objects.filter(**filters)
    
    try:
        from apps.competitions.models.users import UserProfile
        from apps.competitions.models import Organization
        profile = UserProfile.objects.get(user=user)
        if profile.organization:
            # Cas spécial : si le modèle EST Organization, filtrer par ID
            if model_class == Organization:
                filters['id'] = profile.organization.id
            else:
                # Cas normal : filtrer par le champ organization
                filters['organization'] = profile.organization
            return model_class.objects.filter(**filters)
        else:
            return model_class.objects.none()
    except UserProfile.DoesNotExist:
        return model_class.objects.none()


class OrganizationSecureManager(models.Manager):
    """
    Manager qui filtre automatiquement par organisation.
    """
    
    def get_queryset(self):
        return super().get_queryset()
    
    def for_organization(self, organization):
        """Filtre explicitement par organisation."""
        if not organization:
            return self.none()
        return self.get_queryset().filter(
            organization=organization
        )
    
    def for_user(self, user):
        """Filtre par l'organisation de l'utilisateur."""
        if not user or not user.is_authenticated:
            return self.none()
        
        user_org = getattr(user, '_cached_organization', None)
        if not user_org:
            user_org = self._get_user_organization(user)
            user._cached_organization = user_org
        
        return self.for_organization(user_org)
    
    def _get_user_organization(self, user):
        """Récupère l'organisation de l'utilisateur."""
        try:
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=user)
            if profile.organization:
                return profile.organization
            
            from apps.membership.models import MembershipSubscription
            subscription = MembershipSubscription.objects.filter(
                practitioner__user=user,
                status='active'
            ).select_related('package__organization').first()
            
            return subscription.package.organization if subscription else None
        except Exception:
            return None


# Maintien du manager existant pour compatibilité
class IsolatedModelManager(OrganizationSecureManager):
    """Alias pour compatibilité avec l'ancien manager"""
    pass


class OrganizationSecurityMixin:
    """
    Mixin qui garantit que les vues ne montrent que les données 
    de l'organisation de l'utilisateur.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Si le modèle a un champ organization, filtrer automatiquement
        if hasattr(queryset.model, 'organization'):
            user_org = getattr(self.request.user, '_cached_organization', None)
            if not user_org:
                user_org = self._get_user_organization()
                self.request.user._cached_organization = user_org
            
            if user_org:
                return queryset.filter(organization=user_org)
            else:
                return queryset.none()
        
        return queryset
    
    def _get_user_organization(self):
        """Récupère l'organisation de l'utilisateur."""
        if not self.request.user.is_authenticated:
            return None
        
        try:
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=self.request.user)
            if profile.organization:
                return profile.organization
            
            from apps.membership.models import MembershipSubscription
            subscription = MembershipSubscription.objects.filter(
                practitioner__user=self.request.user,
                status='active'
            ).select_related('package__organization').first()
            
            return subscription.package.organization if subscription else None
        except Exception:
            return None


class CompetitionVisibilityMixin:
    """
    Mixin spécial pour les compétitions qui permet la visibilité 
    inter-organisations pour les participants.
    """
    
    def get_participants_organizations(self, competition):
        """Récupère les organisations des participants à une compétition."""
        try:
            from apps.competitions.models import CompetitionRegistration
            
            registrations = CompetitionRegistration.objects.filter(
                competition=competition,
                status='confirmed'
            ).select_related('practitioner__organization')
            
            return [reg.practitioner.organization for reg in registrations if reg.practitioner.organization]
        except ImportError:
            return []


def log_organization_access(view_func):
    """Décorator qui log tous les accès aux données d'organisation."""
    
    def wrapper(request, *args, **kwargs):
        security_logger = logging.getLogger('security.organization_access')
        
        user_org = getattr(request.user, '_cached_organization', None)
        
        # Logger l'accès
        security_logger.info(
            f"Organization access: user={request.user.username}, "
            f"user_org={user_org.name if user_org else 'None'}, "
            f"view={view_func.__name__}, "
            f"path={request.path}"
        )
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


class OrganizationSecureAdminMixin:
    """
    Mixin pour sécuriser l'interface Django Admin par organisation
    """
    
    def get_queryset(self, request):
        """Filtre le queryset par l'organisation de l'utilisateur"""
        qs = super().get_queryset(request)
        
        # Les superuser voient tout
        if request.user.is_superuser:
            return qs
        
        # Déterminer le champ d'organisation à utiliser
        org_field = self._get_organization_field(qs.model)
        if org_field:
            user_org = self._get_user_organization(request.user)
            if user_org:
                filter_kwargs = {org_field: user_org}
                return qs.filter(**filter_kwargs)
            else:
                return qs.none()
        
        return qs
    
    def _get_organization_field(self, model):
        """Détermine le champ d'organisation à utiliser pour ce modèle"""
        if hasattr(model, 'organization'):
            return 'organization'
        elif hasattr(model, 'organizing_organization'):
            return 'organizing_organization'
        return None
    
    def _get_user_organization(self, user):
        """Récupère l'organisation de l'utilisateur"""
        try:
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=user)
            if profile.organization:
                return profile.organization
            
            from apps.membership.models import MembershipSubscription
            subscription = MembershipSubscription.objects.filter(
                practitioner__user=user,
                status='active'
            ).select_related('package__organization').first()
            
            return subscription.package.organization if subscription else None
        except Exception:
            return None
    
    def has_view_permission(self, request, obj=None):
        """Vérifie les permissions de vue"""
        if not super().has_view_permission(request, obj):
            return False
        
        if obj:
            org_field = self._get_organization_field(obj.__class__)
            if org_field:
                user_org = self._get_user_organization(request.user)
                obj_org = getattr(obj, org_field, None)
                return request.user.is_superuser or obj_org == user_org
        
        return True
    
    def has_change_permission(self, request, obj=None):
        """Vérifie les permissions de modification"""
        if not super().has_change_permission(request, obj):
            return False
        
        if obj:
            org_field = self._get_organization_field(obj.__class__)
            if org_field:
                user_org = self._get_user_organization(request.user)
                obj_org = getattr(obj, org_field, None)
                return request.user.is_superuser or obj_org == user_org
        
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Vérifie les permissions de suppression"""
        if not super().has_delete_permission(request, obj):
            return False
        
        if obj:
            org_field = self._get_organization_field(obj.__class__)
            if org_field:
                user_org = self._get_user_organization(request.user)
                obj_org = getattr(obj, org_field, None)
                return request.user.is_superuser or obj_org == user_org
        
        return True


def isolation_required(view_func):
    """
    Décorateur pour forcer l'isolation des vues
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        try:
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=request.user)
            if not profile.organization:
                raise PermissionDenied("Organisation requise pour accéder à cette ressource")
        except UserProfile.DoesNotExist:
            raise PermissionDenied("Profil utilisateur requis")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper



