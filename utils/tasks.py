from celery import shared_task
from django.conf import settings
from .email_service import send_email_template, send_bulk_emails
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_bulk_emails_task(template_name, context_list, subject, recipient_field='email', from_email=None):
    """
    Tâche pour envoyer des e-mails en masse de manière asynchrone
    
    Args:
        template_name (str): Nom du template
        context_list (list): Liste de dictionnaires contenant le contexte pour chaque e-mail
        subject (str): Objet de l'e-mail
        recipient_field (str): Nom du champ dans le contexte contenant l'e-mail du destinataire
        from_email (str): Adresse d'expédition (optionnel)
    """
    try:
        success_count, error_count = send_bulk_emails(
            template_name, context_list, subject, recipient_field, from_email
        )
        logger.info(f"Tâche d'envoi en masse terminée: {success_count} succès, {error_count} échecs")
        return success_count, error_count
    except Exception as e:
        logger.error(f"Erreur dans la tâche d'envoi en masse: {str(e)}")
        return 0, len(context_list)

@shared_task
def send_payment_reminders():
    """Tâche périodique pour envoyer des rappels de paiement pour les factures en retard"""
    try:
        from payment.models import PaymentAttempt
        
        # Trouver les paiements en retard (plus de 7 jours)
        today = date.today()
        overdue_payments = PaymentAttempt.objects.filter(
            status='pending',
            created_at__lt=today - timedelta(days=7)
        )
        
        for payment in overdue_payments:
            days_overdue = (today - payment.created_at.date()).days
            
            # Envoyer le rappel
            context = {
                'payer_name': payment.get_payer_name(),
                'payment_reference': payment.reference,
                'payment_date': payment.created_at.strftime('%d/%m/%Y'),
                'amount': payment.amount,
                'currency': payment.currency,
                'days_overdue': days_overdue,
                'payment_type': payment.get_payment_type_display(),
                'accounting_contact': 'finance@martialcomp.com'
            }
            
            send_email_template(
                'payment_reminder',
                context,
                f"Rappel de paiement - {payment.reference}",
                [payment.get_recipient_email()]
            )
            
            logger.info(f"Rappel de paiement envoyé pour {payment.reference}")
        
        return len(overdue_payments)
    except Exception as e:
        logger.error(f"Erreur dans la tâche de rappel de paiement: {str(e)}")
        return 0

@shared_task
def send_competition_reminders():
    """Tâche périodique pour envoyer des rappels de compétition"""
    try:
        from competitions.models import Competition
        from datetime import datetime, timedelta
        
        # Trouver les compétitions dans les 7 prochains jours
        today = datetime.now().date()
        upcoming_competitions = Competition.objects.filter(
            date__gte=today,
            date__lte=today + timedelta(days=7)
        )
        
        for competition in upcoming_competitions:
            days_until_competition = (competition.date - today).days
            
            for participant in competition.participants.all():
                context = {
                    'participant_name': participant.get_full_name(),
                    'competition_name': competition.name,
                    'competition_date': competition.date.strftime('%d/%m/%Y'),
                    'competition_location': competition.location,
                    'days_until_competition': days_until_competition,
                    'weigh_in_time': competition.weigh_in_time.strftime('%H:%M') if competition.weigh_in_time else 'À confirmer',
                    'required_documents': 'Carte d\'identité, licence sportive, certificat médical'
                }
                
                send_email_template(
                    'competition_reminder',
                    context,
                    f"Rappel - Compétition {competition.name} dans {days_until_competition} jour(s)",
                    [participant.email]
                )
            
            logger.info(f"Rappels de compétition envoyés pour {competition.name}")
        
        return len(upcoming_competitions)
    except Exception as e:
        logger.error(f"Erreur dans la tâche de rappel de compétition: {str(e)}")
        return 0

@shared_task
def send_subscription_expiry_reminders():
    """Tâche périodique pour envoyer des rappels d'expiration d'abonnement"""
    try:
        from payment.models import Subscription
        from datetime import datetime, timedelta
        
        # Trouver les abonnements qui expirent dans les 30 prochains jours
        today = datetime.now().date()
        expiring_subscriptions = Subscription.objects.filter(
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30),
            status='active'
        )
        
        for subscription in expiring_subscriptions:
            days_until_expiry = (subscription.end_date - today).days
            
            context = {
                'subscriber_name': subscription.user.get_full_name(),
                'subscription_name': subscription.plan.name,
                'expiry_date': subscription.end_date.strftime('%d/%m/%Y'),
                'days_until_expiry': days_until_expiry,
                'renewal_link': f"{settings.SITE_URL}/payment/renew/{subscription.id}/"
            }
            
            send_email_template(
                'subscription_expiry_reminder',
                context,
                f"Votre abonnement {subscription.plan.name} expire dans {days_until_expiry} jour(s)",
                [subscription.user.email]
            )
            
            logger.info(f"Rappel d'expiration d'abonnement envoyé pour {subscription.id}")
        
        return len(expiring_subscriptions)
    except Exception as e:
        logger.error(f"Erreur dans la tâche de rappel d'expiration d'abonnement: {str(e)}")
        return 0 