from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from organizations.models import Organization, OrganizationMember, OrganizationRole

class AdministratorMixin:
    """Mixin pour ajouter des méthodes d'administrateur aux modèles."""
    
    def get_administrators(self):
        """Récupère tous les administrateurs de l'entité."""
        User = get_user_model()
        
        if hasattr(self, 'administrators'):
            return User.objects.filter(
                id__in=self.administrators.values_list('user_id', flat=True)
            )
        return User.objects.none()
    
    def get_primary_administrator(self):
        """Récupère l'administrateur principal de l'entité."""
        if hasattr(self, 'administrators'):
            admin = self.administrators.filter(is_primary=True).first()
            if admin:
                return admin.user
        
        if hasattr(self, 'owner'):
            return self.owner
        
        return None


class OrganizationScopedModel(models.Model):
    """
    Classe abstraite pour tous les modèles nécessitant une isolation organisationnelle.
    Tous les modèles contenant des données spécifiques à une organisation doivent hériter de cette classe.
    """
    # La relation peut pointer vers différentes entités selon le modèle
    # La plupart utiliseront organization, mais certains peuvent utiliser club ou federation
    organization = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.CASCADE,
        verbose_name=_("Organisation"),
        help_text=_("L'organisation à laquelle appartient cet élément")
    )
    
    class Meta:
        abstract = True
        
    def is_accessible_by(self, user):
        """
        Vérifie si l'utilisateur a accès à cette ressource.
        
        Args:
            user: L'utilisateur à vérifier
            
        Returns:
            bool: True si l'utilisateur a accès, False sinon
        """
        # Accès admin global
        if user.is_superuser or user.is_staff:
            return True
            
        # Vérifier si l'utilisateur a une organisation associée
        if not hasattr(user, 'organization') or not user.organization:
            return False
            
        # Vérifier l'organisation
        return self.organization_id == user.organization.id
        
    def check_access(self, user):
        """
        Vérifie l'accès et lève une exception si l'utilisateur n'a pas accès.
        
        Args:
            user: L'utilisateur à vérifier
            
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas accès
        """
        if not self.is_accessible_by(user):
            raise PermissionDenied(
                _("Vous n'avez pas accès à cette ressource")
            )


class ClubScopedModel(models.Model):
    """
    Classe abstraite pour tous les modèles nécessitant une isolation au niveau club.
    """
    club = models.ForeignKey(
        'competitions.Club', 
        on_delete=models.CASCADE,
        verbose_name=_("Club"),
        help_text=_("Le club auquel appartient cet élément")
    )
    
    class Meta:
        abstract = True
        
    def is_accessible_by(self, user):
        """
        Vérifie si l'utilisateur a accès à cette ressource.
        
        Args:
            user: L'utilisateur à vérifier
            
        Returns:
            bool: True si l'utilisateur a accès, False sinon
        """
        # Accès admin global
        if user.is_superuser or user.is_staff:
            return True
            
        # Vérifier si l'utilisateur a un club associé
        if not hasattr(user, 'club') or not user.club:
            return False
            
        # Vérifier le club
        return self.club_id == user.club.id
        
    def check_access(self, user):
        """
        Vérifie l'accès et lève une exception si l'utilisateur n'a pas accès.
        
        Args:
            user: L'utilisateur à vérifier
            
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas accès
        """
        if not self.is_accessible_by(user):
            raise PermissionDenied(
                _("Vous n'avez pas accès à cette ressource")
            )


class FederationScopedModel(models.Model):
    """
    Classe abstraite pour tous les modèles nécessitant une isolation au niveau fédération.
    """
    federation = models.ForeignKey(
        'competitions.Federation', 
        on_delete=models.CASCADE,
        verbose_name=_("Fédération"),
        help_text=_("La fédération à laquelle appartient cet élément")
    )
    
    class Meta:
        abstract = True
        
    def is_accessible_by(self, user):
        """
        Vérifie si l'utilisateur a accès à cette ressource.
        
        Args:
            user: L'utilisateur à vérifier
            
        Returns:
            bool: True si l'utilisateur a accès, False sinon
        """
        # Accès admin global
        if user.is_superuser or user.is_staff:
            return True
            
        # Vérifier si l'utilisateur a une fédération associée
        if not hasattr(user, 'federation') or not user.federation:
            return False
            
        # Vérifier la fédération
        return self.federation_id == user.federation.id
        
    def check_access(self, user):
        """
        Vérifie l'accès et lève une exception si l'utilisateur n'a pas accès.
        
        Args:
            user: L'utilisateur à vérifier
            
        Raises:
            PermissionDenied: Si l'utilisateur n'a pas accès
        """
        if not self.is_accessible_by(user):
            raise PermissionDenied(
                _("Vous n'avez pas accès à cette ressource")
            )


class OrganizationScopedManager(models.Manager):
    """
    Manager pour filtrer automatiquement les objets par organisation.
    """
    def for_organization(self, organization):
        """
        Filtre les objets par organisation.
        
        Args:
            organization: L'organisation à filtrer
            
        Returns:
            QuerySet: Les objets filtrés
        """
        return self.filter(organization=organization)
    
    def for_user(self, user):
        """
        Filtre les objets par l'organisation de l'utilisateur.
        
        Args:
            user: L'utilisateur dont l'organisation est utilisée pour le filtrage
            
        Returns:
            QuerySet: Les objets filtrés
        """
        if not user.is_authenticated:
            return self.none()
            
        if user.is_superuser or user.is_staff:
            # Les admins peuvent voir tous les objets
            return self.all()
            
        if not hasattr(user, 'organization') or not user.organization:
            return self.none()
            
        return self.filter(organization=user.organization)


class ClubScopedManager(models.Manager):
    """
    Manager pour filtrer automatiquement les objets par club.
    """
    def for_club(self, club):
        """
        Filtre les objets par club.
        
        Args:
            club: Le club à filtrer
            
        Returns:
            QuerySet: Les objets filtrés
        """
        return self.filter(club=club)
    
    def for_user(self, user):
        """
        Filtre les objets par le club de l'utilisateur.
        
        Args:
            user: L'utilisateur dont le club est utilisé pour le filtrage
            
        Returns:
            QuerySet: Les objets filtrés
        """
        if not user.is_authenticated:
            return self.none()
            
        if user.is_superuser or user.is_staff:
            # Les admins peuvent voir tous les objets
            return self.all()
            
        if not hasattr(user, 'club') or not user.club:
            return self.none()
            
        return self.filter(club=user.club)


class FederationScopedManager(models.Manager):
    """
    Manager pour filtrer automatiquement les objets par fédération.
    """
    def for_federation(self, federation):
        """
        Filtre les objets par fédération.
        
        Args:
            federation: La fédération à filtrer
            
        Returns:
            QuerySet: Les objets filtrés
        """
        return self.filter(federation=federation)
    
    def for_user(self, user):
        """
        Filtre les objets par la fédération de l'utilisateur.
        
        Args:
            user: L'utilisateur dont la fédération est utilisée pour le filtrage
            
        Returns:
            QuerySet: Les objets filtrés
        """
        if not user.is_authenticated:
            return self.none()
            
        if user.is_superuser or user.is_staff:
            # Les admins peuvent voir tous les objets
            return self.all()
            
        if not hasattr(user, 'federation') or not user.federation:
            return self.none()
            
        return self.filter(federation=user.federation)


class SharedResourceModel(models.Model):
    """
    Classe abstraite pour les ressources pouvant être partagées entre organisations.
    """
    owner_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='%(class)s_owned',
        verbose_name=_("Organisation propriétaire")
    )
    shared_with = models.ManyToManyField(
        'organizations.Organization',
        related_name='%(class)s_shared',
        verbose_name=_("Partagé avec"),
        blank=True
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("Public"),
        help_text=_("Si activé, cette ressource est visible par toutes les organisations")
    )
    
    class Meta:
        abstract = True
        
    def is_accessible_by(self, user):
        """
        Vérifie si l'utilisateur a accès à cette ressource.
        
        Args:
            user: L'utilisateur à vérifier
            
        Returns:
            bool: True si l'utilisateur a accès, False sinon
        """
        # Accès admin global
        if user.is_superuser or user.is_staff:
            return True
            
        # Ressource publique
        if self.is_public:
            return True
            
        # Vérifier si l'utilisateur a une organisation associée
        if not hasattr(user, 'organization') or not user.organization:
            return False
            
        # Vérifier si l'utilisateur est le propriétaire
        if self.owner_organization_id == user.organization.id:
            return True
            
        # Vérifier si l'organisation de l'utilisateur est dans la liste de partage
        return self.shared_with.filter(id=user.organization.id).exists()


class SharedResourceManager(models.Manager):
    """
    Manager pour les ressources partagées entre organisations.
    """
    def accessible_by(self, user):
        """
        Filtre les objets accessibles par l'utilisateur.
        
        Args:
            user: L'utilisateur pour lequel filtrer
            
        Returns:
            QuerySet: Les objets accessibles par l'utilisateur
        """
        if not user.is_authenticated:
            return self.filter(is_public=True)
            
        if user.is_superuser or user.is_staff:
            # Les admins peuvent voir tous les objets
            return self.all()
            
        if not hasattr(user, 'organization') or not user.organization:
            return self.filter(is_public=True)
            
        # Ressources publiques + possédées + partagées avec l'organisation de l'utilisateur
        return self.filter(
            models.Q(is_public=True) |
            models.Q(owner_organization=user.organization) |
            models.Q(shared_with=user.organization)
        ).distinct()