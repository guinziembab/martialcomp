from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from utils.email_service import send_email_template
import logging

logger = logging.getLogger(__name__)

class FinanceEmails:
    """Classe pour gérer les e-mails liés aux finances"""
    
    @staticmethod
    def send_invoice_email(invoice, template='invoice_available'):
        """Envoie un e-mail de notification pour une facture"""
        try:
            context = {
                'client_name': invoice.client.get_full_name(),
                'invoice_number': invoice.number,
                'invoice_date': invoice.issue_date.strftime('%d/%m/%Y'),
                'total_amount': invoice.total_amount,
                'currency': invoice.currency,
                'due_date': invoice.due_date.strftime('%d/%m/%Y'),
                'accounting_contact': getattr(settings, 'ACCOUNTING_EMAIL', 'finance@martialcomp.com')
            }
            
            subject = f"Votre facture {invoice.number} est disponible"
            
            return send_email_template(
                template,
                context,
                subject,
                [invoice.client.email]
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de facture {invoice.number}: {str(e)}")
            return False
    
    @staticmethod
    def send_refund_confirmation(refund):
        """Envoie un e-mail de confirmation de remboursement"""
        try:
            context = {
                'client_name': refund.client.get_full_name(),
                'refund_reference': refund.reference,
                'refund_date': refund.processed_date.strftime('%d/%m/%Y'),
                'refund_amount': refund.amount,
                'currency': refund.currency,
                'refund_method': refund.get_method_display(),
                'refund_reason': refund.reason,
                'customer_service_contact': getattr(settings, 'CUSTOMER_SERVICE_EMAIL', 'support@martialcomp.com')
            }
            
            subject = f"Confirmation de remboursement - {refund.reference}"
            
            return send_email_template(
                'refund_confirmation',
                context,
                subject,
                [refund.client.email]
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email de remboursement {refund.reference}: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_reminder(invoice):
        """Envoie un e-mail de rappel de paiement pour une facture en retard"""
        try:
            from datetime import date
            
            today = date.today()
            days_overdue = (today - invoice.due_date).days
            
            context = {
                'client_name': invoice.client.get_full_name(),
                'invoice_number': invoice.number,
                'invoice_date': invoice.issue_date.strftime('%d/%m/%Y'),
                'total_amount': invoice.total_amount,
                'currency': invoice.currency,
                'due_date': invoice.due_date.strftime('%d/%m/%Y'),
                'days_overdue': days_overdue,
                'accounting_contact': getattr(settings, 'ACCOUNTING_EMAIL', 'finance@martialcomp.com')
            }
            
            subject = f"Rappel de paiement - Facture {invoice.number}"
            
            return send_email_template(
                'payment_reminder',
                context,
                subject,
                [invoice.client.email]
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rappel de paiement {invoice.number}: {str(e)}")
            return False
    
    @staticmethod
    def send_subscription_receipt(subscription, payment):
        """Envoie un e-mail de reçu pour un paiement d'abonnement"""
        try:
            context = {
                'subscriber_name': subscription.user.get_full_name(),
                'subscription_name': subscription.plan.name,
                'payment_date': payment.created_at.strftime('%d/%m/%Y'),
                'amount': payment.amount,
                'currency': payment.currency,
                'next_payment_date': subscription.next_billing_date.strftime('%d/%m/%Y') if subscription.next_billing_date else 'Ã€ confirmer'
            }
            
            subject = f"Reçu de paiement - Abonnement {subscription.plan.name}"
            
            return send_email_template(
                'subscription_receipt',
                context,
                subject,
                [subscription.user.email]
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du reçu d'abonnement {subscription.id}: {str(e)}")
            return False 
