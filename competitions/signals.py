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
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

# Vous pouvez ajouter d'autres signaux selon vos besoins

# Signal pour créer automatiquement un QR code lors de la création d'un pratiquant
@receiver(post_save, sender=Practitioner)
def create_practitioner_qr_code(sender, instance, created, **kwargs):
    if created:
        from .models import PractitionerQRCode
        # Utiliser get_or_create pour éviter les doublons
        PractitionerQRCode.objects.get_or_create(practitioner=instance)

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