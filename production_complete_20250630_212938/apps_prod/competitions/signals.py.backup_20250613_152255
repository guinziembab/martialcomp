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
        UserProfile.objects.create(user=instance)
    except Exception as e:
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
                qr_code, created_qr = PractitionerQRCode.objects.get_or_create(
                    practitioner=instance,
                    defaults={"is_active": True}
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