from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import transaction
import logging

from .mixins import AdministratorMixin

# Configuration du logger
logger = logging.getLogger(__name__)

class Club(AdministratorMixin, models.Model):
    """
    Modèle représentant un club d'arts martiaux.
    Cette classe est maintenue pour la compatibilité, mais utilise désormais Organization.
    """
    # Informations de base
    name = models.CharField(_("Nom"), max_length=100)
    address = models.CharField(_("Adresse"), max_length=255, blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=20, blank=True)
    
    # Contacts
    contact_phone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    contact_email = models.EmailField(_("Email"), blank=True)
    website = models.URLField(_("Site web"), blank=True)
    
    # Description et médias
    description = models.TextField(_("Description"), blank=True)
    logo = models.ImageField(_("Logo"), upload_to='clubs/logos/', null=True, blank=True)
    banner = models.ImageField(_("Bannière"), upload_to='clubs/banners/', null=True, blank=True)
    
    # Relations
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='owned_clubs',
        verbose_name=_("Propriétaire")
    )
    disciplines = models.ManyToManyField(
        'Discipline', 
        blank=True, 
        related_name='club_disciplines',
        verbose_name=_("Disciplines")
    )
    main_discipline = models.ForeignKey(
        'Discipline', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='main_clubs',
        verbose_name=_("Discipline principale")
    )
    organization = models.ForeignKey(
        'organizations.Organization',  
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='legacy_clubs',
        verbose_name=_("Organisation associée")
    )
    
    # Équipements et installations
    has_equipment = models.BooleanField(_("Équipement d'entraînement"), default=False)
    has_changing_rooms = models.BooleanField(_("Vestiaires"), default=False)
    has_showers = models.BooleanField(_("Douches"), default=False)
    has_parking = models.BooleanField(_("Parking"), default=False)
    
    # Tranches d'âge acceptées
    accepts_children = models.BooleanField(_("Accepte les enfants (4-11 ans)"), default=True)
    accepts_teenagers = models.BooleanField(_("Accepte les adolescents (12-17 ans)"), default=True)
    accepts_adults = models.BooleanField(_("Accepte les adultes (18-59 ans)"), default=True)
    accepts_seniors = models.BooleanField(_("Accepte les seniors (60+ ans)"), default=True)
    
    # Autres informations
    training_hours = models.TextField(_("Horaires d'entraînement"), blank=True, null=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    
    # Multi-tenant migration fields
    is_migrated = models.BooleanField(_("Migré vers multi-tenant"), default=False)
    tenant = models.ForeignKey(
        "multitenant.Tenant", 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="migrated_clubs", 
        verbose_name=_("Tenant associé")
    )
    migration_date = models.DateTimeField(_("Date de migration"), null=True, blank=True)
    
    # Nouveaux champs pour la migration
    country = models.CharField(_("Pays"), max_length=2, blank=True, default='FR')
    timezone = models.CharField(_("Fuseau horaire"), max_length=50, blank=True, default='Europe/Paris')
    currency = models.CharField(_("Devise"), max_length=3, blank=True, default='EUR')
    email = models.EmailField(_("Email principal"), blank=True)
    phone = models.CharField(_("Téléphone principal"), max_length=20, blank=True)
    
    # Suivi des modifications
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True, null=True)
    
    @property
    def as_organization(self):
        """Retourne l'organisation correspondante."""
        try:
            from organizations.models import Organization
            return Organization.objects.filter(old_club_id=self.id).first()
        except (ImportError, ModuleNotFoundError):
            logger.warning("Module organizations non disponible")
            return None
        
    def save(self, *args, **kwargs):
        """Surcharge de save pour synchroniser avec Organization."""
        super().save(*args, **kwargs)
        
        # Synchroniser avec Organization si le module est disponible
        try:
            with transaction.atomic():
                from organizations.models import Organization
                org, created = Organization.objects.get_or_create(
                    old_club_id=self.id,
                    defaults={
                        'name': self.name,
                        'organization_type': 'club',
                        'description': getattr(self, 'description', ''),
                        'email': getattr(self, 'contact_email', ''),
                        'phone': getattr(self, 'contact_phone', ''),
                        'website': getattr(self, 'website', ''),
                        'address': getattr(self, 'address', ''),
                        'city': getattr(self, 'city', ''),
                        'postal_code': getattr(self, 'postal_code', ''),
                        'is_active': getattr(self, 'is_active', True),
                        'created_by': getattr(self, 'owner', None)
                    }
                )
                
                # Mettre à jour les champs modifiables
                if not created:
                    org.name = self.name
                    org.description = getattr(self, 'description', '')
                    org.email = getattr(self, 'contact_email', '')
                    org.phone = getattr(self, 'contact_phone', '')
                    org.website = getattr(self, 'website', '')
                    org.address = getattr(self, 'address', '')
                    org.city = getattr(self, 'city', '')
                    org.postal_code = getattr(self, 'postal_code', '')
                    org.is_active = getattr(self, 'is_active', True)
                    org.save()
                
                # Mise à jour du lien inverse
                if self.organization_id != org.id:
                    self.organization = org
                    # Éviter une boucle infinie en appelant super().save()
                    models.Model.save(self, update_fields=['organization'])
                
                # Synchroniser les disciplines
                if hasattr(org, 'disciplines'):
                    # Effacer les associations existantes pour éviter les doublons
                    org.disciplines.clear()
                    
                    # Ajouter les disciplines du club à l'organisation
                    for discipline in self.disciplines.all():
                        org.disciplines.add(discipline)
                
                # Synchroniser le propriétaire
                if self.owner and hasattr(org, 'members'):
                    from organizations.models import OrganizationMember, OrganizationRole
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
    
    def is_in_good_standing(self):
        """Vérifie si le club est en règle avec ses cotisations fédération"""
        from finances.models import MembershipFee, PaymentAttempt
        from django.utils import timezone
        
        # Vérifier si le club a une affiliation active
        if hasattr(self, 'organization') and self.organization:
            # Vérifier les affiliations actives
            active_affiliations = self.organization.parent_affiliations.filter(
                is_active=True,
                parent_organization__organization_type='national_federation'
            )
            
            if not active_affiliations.exists():
                return False
            
            # Vérifier les cotisations payées
            current_year = timezone.now().year
            membership_fees = MembershipFee.objects.filter(
                member=self.organization,
                year=current_year,
                is_paid=True
            )
            
            if membership_fees.exists():
                return True
                
            # Vérifier également les paiements réussis
            has_paid_fees = PaymentAttempt.objects.filter(
                transaction__membership_fees__member=self.organization,
                transaction__membership_fees__year=current_year,
                status='succeeded'
            ).exists()
            
            return has_paid_fees
        
        # Méthode legacy si pas d'organization
        if hasattr(self, 'federation') and self.federation:
            # Vérifier les cotisations directs au club
            current_year = timezone.now().year
            has_paid_fees = MembershipFee.objects.filter(
                club=self,
                year=current_year,
                is_paid=True
            ).exists()
            
            return has_paid_fees
        
        return False
    
    class Meta:
        verbose_name = _("Club")
        verbose_name_plural = _("Clubs")
        ordering = ['name']


class ClubTeam(models.Model):
    """
    Modèle représentant une équipe d'un club participant à une compétition.
    """
    name = models.CharField(_("Nom de l'équipe"), max_length=100)
    organization = models.ForeignKey(
        'organizations.Organization',  
        on_delete=models.CASCADE, 
        related_name='club_teams', 
        verbose_name=_('Organisation')
    )
    # Ajouter un champ club pour la transition
    club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teams',
        verbose_name=_("Club (obsolète)")
    )
    competition = models.ForeignKey(
        'Competition', 
        on_delete=models.CASCADE, 
        related_name='competition_teams', 
        verbose_name=_("Compétition")
    )
    members = models.ManyToManyField(
        User, 
        related_name='team_memberships', 
        verbose_name=_("Membres")
    )

    def __str__(self):
        return f"{self.name} - {self.organization.name}"

    class Meta:
        verbose_name = _("Équipe de club")
        verbose_name_plural = _("Équipes de club")
        
    def save(self, *args, **kwargs):
        """Assure la synchronisation entre club et organization."""
        super().save(*args, **kwargs)
        
        # Si club est défini mais organization ne l'est pas, essayer de trouver l'organization correspondante
        if self.club and not self.organization:
            org = self.club.as_organization
            if org:
                self.organization = org
                models.Model.save(self, update_fields=['organization'])
        
        # Si organization est définie mais club ne l'est pas, essayer de trouver le club correspondant
        elif self.organization and not self.club:
            try:
                # Rechercher un club correspondant à cette organisation
                club = Club.objects.filter(id=getattr(self.organization, 'old_club_id', None)).first()
                if club:
                    self.club = club
                    models.Model.save(self, update_fields=['club'])
            except Exception as e:
                logger.error(f"Erreur lors de la recherche du club: {str(e)}")