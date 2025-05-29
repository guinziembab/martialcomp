from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

# Configuration du logger
logger = logging.getLogger('django')

User = get_user_model()

class FederationAdministrator(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='federation_admin_roles',
        verbose_name=_("Utilisateur")
    )
    # Conserver le champ federation pour compatibilité avec l'ancien modèle
    federation = models.ForeignKey(
        'Federation', 
        on_delete=models.CASCADE, 
        related_name='administrators',
        verbose_name=_("Fédération"),
        null=True,
        blank=True
    )
    # Ajouter le nouveau champ organization pour la transition
    organization = models.ForeignKey(
        'organizations.Organization',  
        on_delete=models.CASCADE, 
        related_name='federation_administrators',
        verbose_name=_("Organisation"),
        null=True,
        blank=True
    )
    role = models.CharField(
        _("Rôle"), 
        max_length=50,
        choices=[
            ('owner', _('Propriétaire')),
            ('admin', _('Administrateur')),
            ('secretary', _('Secrétaire')),
            ('treasurer', _('Trésorier')),
        ],
        default='admin'
    )
    is_primary = models.BooleanField(_("Administrateur principal"), default=False)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Administrateur de fédération")
        verbose_name_plural = _("Administrateurs de fédération")
        unique_together = [
            ('user', 'federation'),
            ('user', 'organization')
        ]
        
    def __str__(self):
        if self.organization:
            org_name = self.organization.name
        elif self.federation:
            org_name = self.federation.name
        else:
            org_name = "Inconnu"
        return f"{self.user.username} - {org_name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Si c'est défini comme administrateur principal, s'assurer que les autres ne le sont pas
        if self.is_primary:
            if self.organization:
                FederationAdministrator.objects.filter(
                    organization=self.organization,
                    is_primary=True
                ).exclude(id=self.id).update(is_primary=False)
            elif self.federation:
                FederationAdministrator.objects.filter(
                    federation=self.federation,
                    is_primary=True
                ).exclude(id=self.id).update(is_primary=False)
            
        super().save(*args, **kwargs)


class ClubAdministrator(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='club_admin_roles',
        verbose_name=_("Utilisateur")
    )
    # Conserver le champ club pour compatibilité avec l'ancien modèle
    club = models.ForeignKey(
        'Club', 
        on_delete=models.CASCADE, 
        related_name='administrators',
        verbose_name=_("Club"),
        null=True,
        blank=True
    )
    # Ajouter le nouveau champ organization pour la transition
    organization = models.ForeignKey(
        'organizations.Organization',  
        on_delete=models.CASCADE, 
        related_name='club_administrators',
        verbose_name=_("Organisation"),
        null=True,
        blank=True
    )
    role = models.CharField(
        _("Rôle"), 
        max_length=50,
        choices=[
            ('owner', _('Propriétaire')),
            ('admin', _('Administrateur')),
            ('coach', _('Entraîneur')),
            ('secretary', _('Secrétaire')),
        ],
        default='admin'
    )
    is_primary = models.BooleanField(_("Administrateur principal"), default=False)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Administrateur de club")
        verbose_name_plural = _("Administrateurs de club")
        unique_together = [
            ('user', 'club'),
            ('user', 'organization')
        ]
        
    def __str__(self):
        if self.organization:
            org_name = self.organization.name
        elif self.club:
            org_name = self.club.name
        else:
            org_name = "Inconnu"
        return f"{self.user.username} - {org_name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        # Si c'est défini comme administrateur principal, s'assurer que les autres ne le sont pas
        if self.is_primary:
            if self.organization:
                ClubAdministrator.objects.filter(
                    organization=self.organization,
                    is_primary=True
                ).exclude(id=self.id).update(is_primary=False)
            elif self.club:
                ClubAdministrator.objects.filter(
                    club=self.club,
                    is_primary=True
                ).exclude(id=self.id).update(is_primary=False)
            
        super().save(*args, **kwargs)


@receiver(post_save, sender='competitions.UserProfile')
def create_federation_admin_association(sender, instance, created, **kwargs):
    """
    Signal qui crée automatiquement une association FederationAdministrator
    lorsqu'un profil utilisateur est configuré comme 'federation_admin'
    """
    try:
        # Éviter les imports circulaires
        from ..models import Federation
        
        user = instance.user
        
        # Vérifier si c'est un administrateur de fédération
        if instance.role == 'federation_admin':
            # Vérifier s'il existe déjà une association administrateur-fédération
            admin_roles = FederationAdministrator.objects.filter(user=user)
            
            # Si aucune association n'existe encore
            if not admin_roles.exists():
                with transaction.atomic():
                    # 1. Vérifier si l'utilisateur possède déjà une fédération
                    owned_federations = Federation.objects.filter(owner=user)
                    
                    if owned_federations.exists():
                        # Créer une association avec la fédération dont il est propriétaire
                        federation = owned_federations.first()
                        
                        # Créer d'abord l'association avec la fédération existante
                        federation_admin = FederationAdministrator.objects.create(
                            user=user,
                            federation=federation,
                            role='owner',
                            is_primary=True
                        )
                        
                        # Si le module organizations est disponible, trouver l'organisation correspondante
                        try:
                            from organizations.models import Organization
                            organization = Organization.objects.filter(old_federation_id=federation.id).first()
                            
                            if organization:
                                # Mettre à jour avec l'organization correspondante
                                federation_admin.organization = organization
                                federation_admin.save(update_fields=['organization'])
                                logger.info(f"Updated federation admin with organization for user {user.username}")
                        except (ImportError, ModuleNotFoundError) as e:
                            logger.warning(f"Module organizations non disponible: {str(e)}")
                            
                        logger.info(f"Created federation admin role for user {user.username} with federation {federation.id}")
                    else:
                        # 2. Vérifier les fédérations les plus récentes (potentiellement créées dans le processus d'onboarding)
                        recent_federations = Federation.objects.order_by('-created_at')[:5]
                        
                        # Chercher une fédération récente qui pourrait correspondre à cet utilisateur
                        found_match = False
                        for federation in recent_federations:
                            username_lower = user.username.lower() if user.username else ""
                            first_name_lower = user.first_name.lower() if user.first_name else ""
                            last_name_lower = user.last_name.lower() if user.last_name else ""
                            federation_name_lower = federation.name.lower() if federation.name else ""
                            
                            if (username_lower and username_lower in federation_name_lower) or \
                               (first_name_lower and first_name_lower in federation_name_lower) or \
                               (last_name_lower and last_name_lower in federation_name_lower):
                                
                                # Créer d'abord l'association avec la fédération existante
                                federation_admin = FederationAdministrator.objects.create(
                                    user=user,
                                    federation=federation,
                                    role='admin',
                                    is_primary=True
                                )
                                
                                # Si le module organizations est disponible, trouver l'organisation correspondante
                                try:
                                    from organizations.models import Organization
                                    organization = Organization.objects.filter(old_federation_id=federation.id).first()
                                    
                                    if organization:
                                        # Mettre à jour avec l'organization correspondante
                                        federation_admin.organization = organization
                                        federation_admin.save(update_fields=['organization'])
                                        logger.info(f"Updated federation admin with organization for user {user.username}")
                                except (ImportError, ModuleNotFoundError) as e:
                                    logger.warning(f"Module organizations non disponible: {str(e)}")
                                    
                                logger.info(f"Created federation admin role for user {user.username} with matching federation {federation.id}")
                                found_match = True
                                break
                        
                        # Si aucune correspondance trouvée et qu'il existe au moins une fédération récente
                        if not found_match and recent_federations.exists():
                            # Prendre la plus récente comme solution de secours
                            federation = recent_federations.first()
                            
                            # Créer d'abord l'association avec la fédération existante
                            federation_admin = FederationAdministrator.objects.create(
                                user=user,
                                federation=federation,
                                role='admin',
                                is_primary=True
                            )
                            
                            # Si le module organizations est disponible, trouver l'organisation correspondante
                            try:
                                from organizations.models import Organization
                                organization = Organization.objects.filter(old_federation_id=federation.id).first()
                                
                                if organization:
                                    # Mettre à jour avec l'organization correspondante
                                    federation_admin.organization = organization
                                    federation_admin.save(update_fields=['organization'])
                                    logger.info(f"Updated federation admin with organization for user {user.username}")
                            except (ImportError, ModuleNotFoundError) as e:
                                logger.warning(f"Module organizations non disponible: {str(e)}")
                                
                            logger.info(f"Created federation admin role for user {user.username} with latest federation {federation.id}")
        
    except Exception as e:
        logger.error(f"Error creating federation admin association: {str(e)}")


@receiver(post_save, sender='competitions.Federation')
def associate_federation_with_creator(sender, instance, created, **kwargs):
    """
    Signal qui associe automatiquement le créateur d'une fédération
    comme administrateur principal de celle-ci
    """
    if created and hasattr(instance, 'owner') and instance.owner:
        try:
            with transaction.atomic():
                # Créer d'abord l'association avec la fédération existante
                admin_association, created_admin = FederationAdministrator.objects.get_or_create(
                    user=instance.owner,
                    federation=instance,
                    defaults={
                        'role': 'owner',
                        'is_primary': True
                    }
                )
                
                # Si le module organizations est disponible, trouver l'organisation correspondante
                try:
                    from organizations.models import Organization
                    organization = Organization.objects.filter(old_federation_id=instance.id).first()
                    
                    if organization:
                        # Mettre à jour avec l'organization correspondante
                        admin_association.organization = organization
                        admin_association.save(update_fields=['organization'])
                        logger.info(f"Updated federation admin with organization for federation {instance.id}")
                except (ImportError, ModuleNotFoundError) as e:
                    logger.warning(f"Module organizations non disponible: {str(e)}")
                
                # Mise à jour du profil utilisateur si nécessaire
                if hasattr(instance.owner, 'profile'):
                    profile = instance.owner.profile
                    if profile.role != 'federation_admin':
                        profile.role = 'federation_admin'
                        profile.save(update_fields=['role'])
                        logger.info(f"Updated user {instance.owner.username} profile role to federation_admin")
                        
                logger.info(f"Associated federation {instance.id} with owner {instance.owner.username}")
                
        except Exception as e:
            logger.error(f"Error associating federation with creator: {str(e)}")