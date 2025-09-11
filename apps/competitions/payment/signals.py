from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Payment, PaymentConfig, PaymentRefund


@receiver(post_save, sender=Payment)
def payment_status_changed(sender, instance, created, **kwargs):
    """Signal déclenché quand le statut d'un paiement change."""
    
    if created:
        # Nouveau paiement créé
        print(f"Nouveau paiement créé: {instance.id}")
        
    elif instance.status == 'succeeded' and not instance.paid_at:
        # Paiement réussi - mettre Ã  jour paid_at
        instance.paid_at = timezone.now()
        instance.save(update_fields=['paid_at'])
        
        # Ici on pourrait ajouter d'autres actions :
        # - Envoyer un email de confirmation
        # - Créer une facture
        # - Mettre Ã  jour les statistiques
        # - etc.
        
    elif instance.status in ['failed', 'cancelled']:
        # Paiement échoué ou annulé
        print(f"Paiement {instance.status}: {instance.id}")


@receiver(post_save, sender=PaymentRefund)
def refund_status_changed(sender, instance, created, **kwargs):
    """Signal déclenché quand le statut d'un remboursement change."""
    
    if created:
        print(f"Nouveau remboursement créé: {instance.id}")
        
    elif instance.status == 'succeeded' and not instance.processed_at:
        # Remboursement traité
        instance.processed_at = timezone.now()
        instance.save(update_fields=['processed_at'])
        
        # Mettre Ã  jour le statut du paiement
        instance.payment.status = 'refunded'
        instance.payment.save(update_fields=['status'])


@receiver(post_save, sender=PaymentConfig)
def payment_config_changed(sender, instance, created, **kwargs):
    """Signal déclenché quand la configuration de paiement change."""
    
    if created:
        print(f"Nouvelle configuration de paiement pour {instance.organization.name}")
        
    else:
        print(f"Configuration de paiement mise Ã  jour pour {instance.organization.name}")
        
        # Ici on pourrait :
        # - Valider la configuration
        # - Tester la connexion Ã  la passerelle
        # - Envoyer une notification
        # - etc.


@receiver(pre_save, sender=Payment)
def validate_payment_amount(sender, instance, **kwargs):
    """Validation du montant du paiement avant sauvegarde."""
    
    if instance.organization:
        try:
            config = PaymentConfig.objects.get(organization=instance.organization)
            
            if instance.amount < config.minimum_amount:
                raise ValueError(
                    f"Le montant minimum est de {config.minimum_amount} {instance.currency}"
                )
            
            if instance.amount > config.maximum_amount:
                raise ValueError(
                    f"Le montant maximum est de {config.maximum_amount} {instance.currency}"
                )
                
        except PaymentConfig.DoesNotExist:
            pass 
