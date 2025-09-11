from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import PaymentAttempt, Subscription
from utils.email_service import EmailTemplates
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=PaymentAttempt)
def notify_payment_status(sender, instance, created, **kwargs):
    """Envoie des e-mails de notification lors de changements de statut de paiement"""
    if not created and hasattr(instance, '_state') and instance._state.fields_cache.get('status') != instance.status:
        # Un paiement existant a changé de statut
        try:
            if instance.status == 'succeeded':
                EmailTemplates.send_payment_success(instance)
                logger.info(f"Email de succès de paiement envoyé pour {instance.reference}")
            elif instance.status == 'failed':
                EmailTemplates.send_payment_failed(instance)
                logger.info(f"Email d'échec de paiement envoyé pour {instance.reference}")
            elif instance.status == 'pending':
                # Optionnel : envoyer un email pour les paiements en attente
                logger.info(f"Paiement en attente pour {instance.reference}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de paiement {instance.reference}: {str(e)}")

@receiver(post_save, sender=Subscription)
def notify_subscription_payment(sender, instance, created, **kwargs):
    """Envoie un email de reçu pour les paiements d'abonnement"""
    if created and instance.payment_attempt and instance.payment_attempt.status == 'succeeded':
        try:
            EmailTemplates.send_subscription_receipt(instance, instance.payment_attempt)
            logger.info(f"Email de reçu d'abonnement envoyé pour {instance.id}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'abonnement {instance.id}: {str(e)}") 
