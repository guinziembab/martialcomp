from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import URLValidator
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

from .mixins import AdministratorMixin

# Configuration du logger
logger = logging.getLogger(__name__)

User = get_user_model()

class Federation(AdministratorMixin, models.Model):
    """
    Modèle représentant une fédération d'arts martiaux.
    Cette classe est maintenue pour la compatibilité, mais utilise désormais Organization.
    """
    name = models.CharField(_("Nom"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True, blank=True)
    description = models.TextField(_("Description"), blank=True)
    country = models.CharField(_("Pays"), max_length=100, blank=True)
    address = models.CharField(_("Adresse"), max_length=255, blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=20, blank=True)
    logo = models.ImageField(_("Logo"), upload_to='federations/logos/', null=True, blank=True)
    website = models.URLField(_("Site web"), blank=True, validators=[URLValidator()])
    contact_email = models.EmailField(_("Email de contact"), blank=True)
    contact_phone = models.CharField(_("Téléphone de contact"), max_length=20, blank=True)
    founding_date = models.DateField(_("Date de fondation"), null=True, blank=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Relation avec le propriétaire
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_federations',
        verbose_name=_("Propriétaire (déprécié)")
    )
    
    # Relation ManyToMany avec les disciplines
    disciplines = models.ManyToManyField(
        'Discipline',
        related_name='federation_disciplines',
        verbose_name=_("Disciplines"),
        blank=True
    )
    
    # Ajout d'un champ pointant vers l'organisation
    organization = models.ForeignKey(
        'organizations.Organization',  
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='legacy_federations',
        verbose_name=_("Organisation associée")
    )
    
    @property
    def as_organization(self):
        """Retourne l'organisation correspondante."""
        try:
            from organizations.models import Organization
            return Organization.objects.filter(old_federation_id=self.id).first()
        except (ImportError, ModuleNotFoundError):
            logger.warning("Module organizations non disponible")
            return None

    def save(self, *args, **kwargs):
        """Génère un slug unique si nécessaire et synchronise avec Organization."""
        if not self.slug:
            self.slug = slugify(self.name)
            
            # Vérifier l'unicité du slug
            counter = 1
            original_slug = self.slug
            while Federation.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        # Appeler la méthode save du parent
        super().save(*args, **kwargs)
        
        # Synchroniser avec Organization
        try:
            with transaction.atomic():
                from organizations.models import Organization, OrganizationMember, OrganizationRole
                org, created = Organization.objects.get_or_create(
                    old_federation_id=self.id,
                    defaults={
                        'name': self.name,
                        'organization_type': 'national_federation',
                        'description': self.description,
                        'email': self.contact_email,
                        'phone': self.contact_phone,
                        'website': self.website,
                        'address': self.address,
                        'city': self.city,
                        'country': self.country,
                        'postal_code': self.postal_code,
                        'is_active': self.is_active,
                        'created_by': self.owner
                    }
                )
                
                # Mettre à jour les champs modifiables
                if not created:
                    org.name = self.name
                    org.description = self.description
                    org.email = self.contact_email
                    org.phone = self.contact_phone
                    org.website = self.website
                    org.address = self.address
                    org.city = self.city
                    org.country = self.country
                    org.postal_code = self.postal_code
                    org.is_active = self.is_active
                    org.save()
                
                # Mise à jour du lien inverse
                if not self.organization or self.organization_id != org.id:
                    self.organization = org
                    # Éviter une boucle infinie en appelant super().save()
                    models.Model.save(self, update_fields=['organization'])
                
                # Synchroniser les disciplines
                if hasattr(org, 'disciplines'):
                    # Effacer les associations existantes pour éviter les doublons
                    org.disciplines.clear()
                    
                    # Ajouter les disciplines de la fédération à l'organisation
                    for discipline in self.disciplines.all():
                        org.disciplines.add(discipline)
                
                # Synchroniser le propriétaire
                if self.owner and hasattr(org, 'members'):
                    OrganizationMember.objects.get_or_create(
                        organization=org,
                        user=self.owner,
                        defaults={
                            'role': OrganizationRole.OWNER,
                            'can_manage_members': True,
                            'can_edit_organization': True,
                            'can_manage_competitions': True
                        }
                    )
        except (ImportError, ModuleNotFoundError):
            logger.warning("Module organizations non disponible pour la synchronisation")
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation avec Organization: {str(e)}")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Fédération")
        verbose_name_plural = _("Fédérations")
        ordering = ['name']

    @classmethod
    def from_organization(cls, organization):
        """
        Crée ou met à jour une instance Federation à partir d'une Organization.
        Utile pour la migration ou la synchronisation inverse.
        """
        if not organization or not hasattr(organization, 'old_federation_id'):
            return None
            
        try:
            with transaction.atomic():
                # Récupérer la fédération existante ou en créer une nouvelle
                federation, created = cls.objects.get_or_create(
                    id=organization.old_federation_id,
                    defaults={
                        'name': organization.name,
                        'description': organization.description,
                        'country': getattr(organization, 'country', ''),
                        'address': getattr(organization, 'address', ''),
                        'city': getattr(organization, 'city', ''),
                        'postal_code': getattr(organization, 'postal_code', ''),
                        'website': getattr(organization, 'website', ''),
                        'contact_email': getattr(organization, 'email', ''),
                        'contact_phone': getattr(organization, 'phone', ''),
                        'is_active': getattr(organization, 'is_active', True),
                        'owner': getattr(organization, 'created_by', None),
                        'organization': organization
                    }
                )
                
                # Si la fédération existait déjà, mettre à jour ses attributs
                if not created:
                    federation.name = organization.name
                    federation.description = organization.description
                    federation.country = getattr(organization, 'country', federation.country)
                    federation.address = getattr(organization, 'address', federation.address)
                    federation.city = getattr(organization, 'city', federation.city)
                    federation.postal_code = getattr(organization, 'postal_code', federation.postal_code)
                    federation.website = getattr(organization, 'website', federation.website)
                    federation.contact_email = getattr(organization, 'email', federation.contact_email)
                    federation.contact_phone = getattr(organization, 'phone', federation.contact_phone)
                    federation.is_active = getattr(organization, 'is_active', federation.is_active)
                    federation.organization = organization
                    
                    # Utiliser save() pour éviter les boucles infinies
                    models.Model.save(federation)
                
                # Synchroniser les disciplines
                if hasattr(organization, 'disciplines'):
                    # Effacer les associations existantes
                    federation.disciplines.clear()
                    
                    # Ajouter les disciplines de l'organisation à la fédération
                    for discipline in organization.disciplines.all():
                        federation.disciplines.add(discipline)
                
                # Synchroniser le propriétaire
                if hasattr(organization, 'members'):
                    from organizations.models import OrganizationMember
                    owner_member = OrganizationMember.objects.filter(
                        organization=organization,
                        role=OrganizationRole.OWNER
                    ).first()
                    
                    if owner_member:
                        federation.owner = owner_member.user
                        models.Model.save(federation, update_fields=['owner'])
                
                return federation
        except Exception as e:
            logger.error(f"Erreur lors de la création/mise à jour de Federation à partir d'Organization: {str(e)}")
            return None