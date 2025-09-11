from django.utils import timezone
from datetime import timedelta
from .models import (
    SubscriptionPlan, OrganizationSubscription, Payment, 
    PaymentMethod, PaymentError, Refund
)
from apps.organizations.models import Organization
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service de gestion des abonnements"""
    
    @staticmethod
    def create_trial_subscription(organization, plan_type='basic'):
        """Crée un abonnement d'essai pour une organisation"""
        try:
            # Récupérer le plan par défaut
            plan = SubscriptionPlan.objects.filter(
                plan_type=plan_type,
                is_active=True
            ).first()
            
            if not plan:
                # Créer un plan par défaut si aucun n'existe
                plan = SubscriptionPlan.objects.create(
                    name="Plan Basique",
                    plan_type=plan_type,
                    price=0.00,
                    trial_days=30,
                    description="Plan d'essai gratuit de 30 jours",
                    features=["Accès complet Ã  la plateforme", "Support client"]
                )
            
            # Créer l'abonnement d'essai
            subscription = OrganizationSubscription.objects.create(
                organization=organization,
                plan=plan,
                status='trial',
                trial_start=timezone.now(),
                trial_end=timezone.now() + timedelta(days=plan.trial_days)
            )
            
            logger.info(f"Abonnement d'essai créé pour {organization.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'abonnement d'essai: {e}")
            raise
    
    @staticmethod
    def check_subscription_status(organization):
        """Vérifie le statut de l'abonnement d'une organisation"""
        try:
            subscription = OrganizationSubscription.objects.filter(
                organization=organization
            ).first()
            
            if not subscription:
                return None
            
            # Vérifier si l'essai a expiré
            if subscription.status == 'trial' and not subscription.is_trial_active:
                subscription.status = 'expired'
                subscription.save()
                logger.info(f"Essai expiré pour {organization.name}")
            
            return subscription
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du statut: {e}")
            return None
    
    @staticmethod
    def upgrade_subscription(subscription, new_plan):
        """Met Ã  niveau un abonnement"""
        try:
            subscription.plan = new_plan
            subscription.status = 'active'
            subscription.subscription_start = timezone.now()
            subscription.subscription_end = timezone.now() + timedelta(days=30)
            subscription.save()
            
            logger.info(f"Abonnement mis Ã  niveau pour {subscription.organization.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise Ã  niveau: {e}")
            raise
    
    @staticmethod
    def cancel_subscription(subscription):
        """Annule un abonnement"""
        try:
            subscription.status = 'cancelled'
            subscription.auto_renew = False
            subscription.save()
            
            logger.info(f"Abonnement annulé pour {subscription.organization.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation: {e}")
            raise

class PaymentService:
    """Service de gestion des paiements"""
    
    @staticmethod
    def create_payment(subscription, payment_method, amount, currency='EUR'):
        """Crée un nouveau paiement"""
        try:
            payment = Payment.objects.create(
                subscription=subscription,
                payment_method=payment_method,
                amount=amount,
                currency=currency
            )
            
            logger.info(f"Paiement créé: {payment.transaction_id}")
            return payment
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du paiement: {e}")
            raise
    
    @staticmethod
    def process_payment(payment):
        """Traite un paiement"""
        try:
            # Simulation du traitement de paiement
            payment.status = 'processing'
            payment.save()
            
            # Ici, vous intégreriez votre passerelle de paiement
            # Pour l'exemple, on simule un succès
            payment.status = 'completed'
            payment.save()
            
            # Mettre Ã  jour l'abonnement
            subscription = payment.subscription
            subscription.status = 'active'
            subscription.subscription_start = timezone.now()
            subscription.subscription_end = timezone.now() + timedelta(days=30)
            subscription.save()
            
            logger.info(f"Paiement traité avec succès: {payment.transaction_id}")
            return payment
            
        except Exception as e:
            payment.status = 'failed'
            payment.save()
            
            PaymentError.objects.create(
                payment=payment,
                error_code='PROCESSING_ERROR',
                error_message=str(e)
            )
            
            logger.error(f"Erreur lors du traitement du paiement: {e}")
            raise
    
    @staticmethod
    def create_refund(payment, amount, reason):
        """Crée un remboursement"""
        try:
            refund = Refund.objects.create(
                payment=payment,
                amount=amount,
                reason=reason
            )
            
            logger.info(f"Remboursement créé: {refund.refund_id}")
            return refund
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du remboursement: {e}")
            raise

class TrialService:
    """Service de gestion des périodes d'essai"""
    
    @staticmethod
    def get_trial_info(organization):
        """Récupère les informations d'essai d'une organisation"""
        subscription = OrganizationSubscription.objects.filter(
            organization=organization
        ).first()
        
        if not subscription:
            return None
        
        return {
            'status': subscription.status,
            'is_trial_active': subscription.is_trial_active,
            'days_remaining': subscription.days_remaining,
            'trial_end': subscription.trial_end,
            'plan_name': subscription.plan.name,
            'plan_price': subscription.plan.price
        }
    
    @staticmethod
    def extend_trial(subscription, additional_days=7):
        """Prolonge la période d'essai"""
        try:
            subscription.trial_end += timedelta(days=additional_days)
            subscription.save()
            
            logger.info(f"Essai prolongé de {additional_days} jours pour {subscription.organization.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Erreur lors de la prolongation de l'essai: {e}")
            raise
    
    @staticmethod
    def convert_trial_to_paid(subscription, payment_method):
        """Convertit un essai en abonnement payant"""
        try:
            # Créer le premier paiement
            payment = PaymentService.create_payment(
                subscription=subscription,
                payment_method=payment_method,
                amount=subscription.plan.price
            )
            
            # Traiter le paiement
            PaymentService.process_payment(payment)
            
            logger.info(f"Essai converti en abonnement payant pour {subscription.organization.name}")
            return subscription
            
        except Exception as e:
            logger.error(f"Erreur lors de la conversion: {e}")
            raise

class NotificationService:
    """Service de notifications pour les abonnements"""
    
    @staticmethod
    def send_trial_expiry_notification(subscription):
        """Envoie une notification d'expiration d'essai"""
        # Ici, vous intégreriez votre système de notifications
        # (email, SMS, push notifications, etc.)
        logger.info(f"Notification d'expiration d'essai envoyée pour {subscription.organization.name}")
    
    @staticmethod
    def send_payment_success_notification(payment):
        """Envoie une notification de succès de paiement"""
        logger.info(f"Notification de succès de paiement envoyée pour {payment.subscription.organization.name}")
    
    @staticmethod
    def send_payment_failure_notification(payment):
        """Envoie une notification d'échec de paiement"""
        logger.info(f"Notification d'échec de paiement envoyée pour {payment.subscription.organization.name}") 

