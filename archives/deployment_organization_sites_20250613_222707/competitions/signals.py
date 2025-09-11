from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, Practitioner, Club, Competition

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
@receiver(post_save, sender=Practitioner)
def create_practitioner_qr_code(sender, instance, created, **kwargs):
    if created:
        from .models import PractitionerQRCode
        try:
            # Vérifier si un QR code existe déjà
            if not hasattr(instance, "qr_code"):
                # Utiliser get_or_create pour éviter les doublons
                # Fix for PostgreSQL boolean field - explicitly convert to bool
                qr_code, created_qr = PractitionerQRCode.objects.get_or_create(
                    practitioner=instance,
                    defaults={
                        "is_active": bool(True),
                        "is_federation_validated": bool(False)
                    }
                )
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
            from competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
            
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
@receiver(post_save, sender='organizations.Organization')
def ensure_organization_site_creation(sender, instance, created, **kwargs):
    """
    Signal de sécurité pour s'assurer que les sites d'organisation sont créés.
    Agit comme un filet de sécurité si le signal principal échoue.
    """
    if created:
        try:
            # Vérifier si un tenant existe déjà
            from multitenant.models import Tenant
            existing_tenant = Tenant.objects.filter(
                name=instance.name,
                is_active=True
            ).first()
            
            if not existing_tenant:
                # Déclencher manuellement la création si pas déjà fait
                from organizations.signals import create_organization_tenant
                from competitions.utils.subdomain_generator import SubdomainGenerator
                
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