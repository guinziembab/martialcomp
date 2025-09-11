from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, Practitioner, Club, Competition, Federation
from apps.competitions.models import Organization
from apps.competitions.utils.subdomain_generator import create_organization_tenant
from apps.competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
import logging
logger = logging.getLogger(__name__)

# Exemple de signal pour créer automatiquement un profil utilisateur lors de la création d'un utilisateur
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if not hasattr(instance, 'userprofile'):
            UserProfile.objects.create(user=instance)

# Exemple de signal pour sauvegarder le profil utilisateur lorsque l'utilisateur est sauvegardé
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        if hasattr(instance, 'userprofile') and instance.userprofile is not None:
            instance.userprofile.save()
    except UserProfile.DoesNotExist:
        # Créer le profil s'il n'existe pas
        UserProfile.objects.create(user=instance)
    except Exception as e:
        # Log l'erreur mais ne pas empêcher la sauvegarde de l'utilisateur
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la sauvegarde du profil utilisateur pour {instance}: {e}")

# Vous pouvez ajouter d'autres signaux selon vos besoins

# Signal pour créer automatiquement un QR code lors de la création d'un pratiquant
# TEMPORAIREMENT DÉSACTIVÉ pour éviter les conflits lors de l'onboarding
# @receiver(post_save, sender=Practitioner)
def create_practitioner_qr_code_disabled(sender, instance, created, **kwargs):
    if created:
        from .models import PractitionerQRCode
        try:
            # Vérifier si un QR code existe déjà pour ce practitioner
            if not PractitionerQRCode.objects.filter(practitioner=instance).exists():
                # Utiliser get_or_create pour éviter les doublons
                # Fix for PostgreSQL boolean field - explicitly convert to bool
                qr_code, created_qr = PractitionerQRCode.objects.get_or_create(
                    practitioner=instance,
                    defaults={
                        "is_active": True,
                        "is_federation_validated": False
                    }
                )
                if created_qr:
                    logging.getLogger(__name__).info(f"QR Code créé pour {instance}")
        except Exception as e:
            # Log l'erreur mais ne pas empêcher la création du pratiquant
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du QR code pour {instance}: {e}")

# Signal pour valider automatiquement les QR codes lorsqu'un club devient en règle
@receiver(post_save, sender=Club)
def validate_club_qr_codes(sender, instance, **kwargs):
    from .models import PractitionerQRCode
    
    # Si le club est maintenant en règle, valider tous les QR codes
    if hasattr(instance, 'is_in_good_standing') and instance.is_in_good_standing():
        PractitionerQRCode.objects.filter(
            practitioner__organization=instance.organization,
            is_federation_validated=False
        ).update(
            is_federation_validated=True,
            federation_validation_date=timezone.now()
        )

# Signal pour créer automatiquement des QR codes d'organisation
@receiver(post_save, sender=Club)
def create_club_organization_qr_codes(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement des QR codes lors de la création d'un club.
    Ce signal complète le système de génération automatique de sites.
    """
    if created:
        try:
            from apps.competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
            
            # Générer les QR codes pour le club
            qr_codes = generate_organization_qr_codes_set(instance)
            
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"QR codes générés pour le club {instance.name}: {list(qr_codes.keys())}")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la génération des QR codes pour le club {instance.name}: {e}")

# Signal pour les organisations créées via les vues de création rapide
# Signal réactivé pour la création automatique des sous-domaines
@receiver(post_save, sender='organizations.Organization')
def ensure_organization_site_creation_enabled(sender, instance, created, **kwargs):
    """
    Signal de sécurité pour s'assurer que les sites d'organisation sont créés.
    Agit comme un filet de sécurité si le signal principal échoue.
    """
    if created:
        try:
            # Vérifier si un tenant existe déjà
            from apps.multitenant.models import Tenant
            existing_tenant = Tenant.objects.filter(
                name=instance.name,
                is_active=True
            ).first()
            
            if not existing_tenant:
                # Déclencher manuellement la création si pas déjà fait
                from apps.organizations.signals import create_organization_tenant
                from apps.competitions.utils.subdomain_generator import SubdomainGenerator
                
                generator = SubdomainGenerator()
                subdomain = generator.generate_subdomain(instance)
                tenant = create_organization_tenant(instance, subdomain)
                
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Site de sécurité créé pour l'organisation {instance.name}: {tenant.domain}")
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur dans le signal de sécurité pour {instance.name}: {e}")

# Signal pour créer automatiquement un sous-domaine lors de la création d'une fédération
@receiver(post_save, sender=Federation)
def create_federation_subdomain(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement un sous-domaine lors de la création d'une fédération.
    """
    if created:
        try:
            # Générer un sous-domaine basé sur le nom de la fédération
            from django.utils.text import slugify
            import re
            
            # Nettoyer le nom pour créer un sous-domaine valide
            base_subdomain = slugify(instance.name).replace('-', '')[:20]  # Limiter à 20 caractères
            base_subdomain = re.sub(r'[^a-z0-9]', '', base_subdomain.lower())
            
            if not base_subdomain:
                base_subdomain = f"federation{instance.id}"
            
            # Vérifier l'unicité et ajouter un suffixe si nécessaire
            subdomain = base_subdomain
            counter = 1
            
            # Vérifier si le sous-domaine existe déjà
            from django.contrib.sites.models import Site
            while Site.objects.filter(domain__startswith=f"{subdomain}.").exists():
                subdomain = f"{base_subdomain}{counter}"
                counter += 1
            
            # Créer le site/sous-domaine pour la fédération
            full_domain = f"{subdomain}.martialcomp.com"
            
            site, site_created = Site.objects.get_or_create(
                domain=full_domain,
                defaults={
                    'name': f"Site {instance.name}",
                }
            )
            
            if site_created:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Sous-domaine créé pour la fédération {instance.name}: {full_domain}")
            
            # Optionnel: Stocker le sous-domaine dans le modèle si un champ existe
            if hasattr(instance, 'subdomain'):
                instance.subdomain = subdomain
                instance.save(update_fields=['subdomain'])
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du sous-domaine pour la fédération {instance.name}: {e}")

# Signal pour créer automatiquement les FederationAdministrator lors de la création d'une fédération
@receiver(post_save, sender=Federation)
def create_federation_administrator(sender, instance, created, **kwargs):
    """
    Signal pour créer automatiquement un FederationAdministrator 
    quand une fédération est créée avec un propriétaire.
    """
    if created and instance.owner:
        try:
            from .models import FederationAdministrator
            
            # Créer l'administrateur de fédération
            admin, admin_created = FederationAdministrator.objects.get_or_create(
                user=instance.owner,
                federation=instance,
                defaults={
                    'role': 'admin',
                    'is_active': True,
                    'appointment_date': timezone.now().date()
                }
            )
            
            if admin_created:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Administrateur de fédération créé: {instance.owner.username} pour {instance.name}")
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création de l'administrateur pour la fédération {instance.name}: {e}")

@receiver(post_save, sender=Organization)
def create_organization_tenant_and_qr(sender, instance, created, **kwargs):
    if created:
        tenant = create_organization_tenant(instance)
        qr_codes = generate_organization_qr_codes_set(instance)
        logger.info(f"Site créé pour {instance.name}: {tenant.domain}")

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Competition, CompetitionRegistration
from utils.email_service import EmailTemplates
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=CompetitionRegistration)
def notify_competition_registration(sender, instance, created, **kwargs):
    """Envoie un email de confirmation lors de l'inscription à une compétition"""
    if created:
        try:
            EmailTemplates.send_competition_confirmation(instance, instance.competition)
            logger.info(f"Email de confirmation de compétition envoyé pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de compétition {instance.id}: {str(e)}")

@receiver(post_save, sender=Competition)
def notify_competition_update(sender, instance, created, **kwargs):
    """Envoie des e-mails lors de la mise à jour d'une compétition"""
    if not created and hasattr(instance, '_state'):
        # Vérifier si des champs importants ont changé
        changed_fields = []
        for field in ['title', 'start_date', 'end_date', 'venue_name']:
            if hasattr(instance, f'_state') and getattr(instance._state, 'fields_cache', {}).get(field) != getattr(instance, field):
                changed_fields.append(field)
        
        if changed_fields:
            try:
                from utils.email_service import send_email_template
                
                for registration in instance.registrations.all():
                    context = {
                        'participant_name': registration.practitioner.full_name,
                        'competition_name': instance.title,
                        'change_details': f"Modifications apportées : {', '.join(changed_fields)}",
                        'change_date': instance.updated_at.strftime('%d/%m/%Y') if hasattr(instance, 'updated_at') else 'Aujourd\'hui',
                        'organizer_contact': instance.organizing_organization.email if hasattr(instance, 'organizing_organization') and instance.organizing_organization else 'contact@martialcomp.com'
                    }
                    
                    send_email_template(
                        'competition_change',
                        context,
                        f"Modification importante - {instance.title}",
                        [registration.practitioner.user.email]
                    )
                
                logger.info(f"Emails de modification de compétition envoyés pour {instance.title}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi des emails de modification de compétition {instance.title}: {str(e)}")