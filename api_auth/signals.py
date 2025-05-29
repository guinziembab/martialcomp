from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import RefreshToken, AccessTokenLog, DeviceRegistration

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_related_objects(sender, instance, created, **kwargs):
    """
    Signal pour créer les objets associés à un nouvel utilisateur.
    """
    if created:
        # Ce hook pourrait être utilisé pour des initialisations spécifiques
        # pour les nouveaux utilisateurs si nécessaire
        pass


@receiver(pre_save, sender=RefreshToken)
def set_refresh_token_expiry(sender, instance, **kwargs):
    """
    Signal pour définir automatiquement la date d'expiration d'un token 
    de rafraîchissement s'il n'en a pas déjà une.
    """
    if not instance.expires_at:
        from django.conf import settings
        days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
        instance.expires_at = timezone.now() + timezone.timedelta(days=days)


@receiver(pre_save, sender=AccessTokenLog)
def set_access_token_expiry(sender, instance, **kwargs):
    """
    Signal pour définir automatiquement la date d'expiration d'un token 
    d'accès s'il n'en a pas déjà une.
    """
    if not instance.expires_at:
        instance.expires_at = timezone.now() + timezone.timedelta(minutes=60)  # 1 heure par défaut