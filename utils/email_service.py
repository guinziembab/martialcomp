from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_email_template(template_name, context, subject, recipient_list, from_email=None, attachments=None):
    """
    Fonction générique pour envoyer des e-mails avec templates HTML et texte
    
    Args:
        template_name (str): Nom du template sans extension
        context (dict): Contexte pour le rendu du template
        subject (str): Objet de l'e-mail
        recipient_list (list): Liste des destinataires
        from_email (str): Adresse d'expédition (optionnel)
        attachments (list): Liste de tuples (filename, content, mimetype) pour les pièces jointes
    """
    try:
        # Rendre le template HTML
        html_content = render_to_string(f'emails/html/{template_name}.html', context)
        
        # Rendre le template texte ou utiliser strip_tags si le template texte n'existe pas
        try:
            text_content = render_to_string(f'emails/txt/{template_name}.txt', context)
        except:
            # Si le template texte n'existe pas, utiliser strip_tags sur le HTML
            text_content = strip_tags(html_content)
        
        # Utiliser l'email par défaut si aucun n'est spécifié
        if not from_email:
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com')
        
        # Créer le message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=recipient_list
        )
        
        # Ajouter la version HTML
        msg.attach_alternative(html_content, "text/html")
        
        # Ajouter les pièces jointes si fournies
        if attachments:
            for filename, content, mimetype in attachments:
                msg.attach(filename, content, mimetype)
        
        # Envoyer l'email
        msg.send()
        
        logger.info(f"Email envoyé avec succès: {subject} à {recipient_list}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email {subject}: {str(e)}")
        return False

def send_bulk_emails(template_name, context_list, subject, recipient_field='email', from_email=None):
    """
    Fonction pour envoyer des e-mails en masse
    
    Args:
        template_name (str): Nom du template
        context_list (list): Liste de dictionnaires contenant le contexte pour chaque e-mail
        subject (str): Objet de l'e-mail
        recipient_field (str): Nom du champ dans le contexte contenant l'e-mail du destinataire
        from_email (str): Adresse d'expédition (optionnel)
    """
    success_count = 0
    error_count = 0
    
    for context in context_list:
        recipient = context.get(recipient_field)
        if recipient:
            if send_email_template(template_name, context, subject, [recipient], from_email):
                success_count += 1
            else:
                error_count += 1
    
    logger.info(f"Envoi en masse terminé: {success_count} succès, {error_count} échecs")
    return success_count, error_count

class EmailTemplates:
    """Classe contenant les templates d'emails prédéfinis"""
    
    @staticmethod
    def send_welcome_email(user, confirmation_link):
        """Envoie l'email de bienvenue avec confirmation de compte"""
        context = {
            'first_name': user.first_name,
            'confirmation_link': confirmation_link,
            'user_role': user.get_role_display() if hasattr(user, 'get_role_display') else 'Utilisateur'
        }
        
        return send_email_template(
            'welcome_confirmation',
            context,
            'Bienvenue sur MartialComp - Confirmez votre compte',
            [user.email]
        )
    
    @staticmethod
    def send_password_reset_email(user, reset_link):
        """Envoie l'email de réinitialisation de mot de passe"""
        context = {
            'first_name': user.first_name,
            'reset_password_link': reset_link
        }
        
        return send_email_template(
            'password_reset',
            context,
            'MartialComp - Réinitialisation de votre mot de passe',
            [user.email]
        )
    
    @staticmethod
    def send_competition_confirmation(participant, competition):
        """Envoie l'email de confirmation d'inscription à une compétition"""
        context = {
            'participant_name': participant.get_full_name(),
            'competition_name': competition.name,
            'competition_date': competition.date.strftime('%d/%m/%Y'),
            'competition_location': competition.location,
            'categories': ', '.join([cat.name for cat in participant.categories.all()]),
            'competitor_number': participant.competitor_number,
            'weigh_in_time': competition.weigh_in_time.strftime('%H:%M') if competition.weigh_in_time else 'À confirmer',
            'category_start_time': 'À confirmer',  # À calculer selon le programme
            'required_documents': 'Carte d\'identité, licence sportive, certificat médical'
        }
        
        return send_email_template(
            'competition_confirmation',
            context,
            f'Confirmation d\'inscription - {competition.name}',
            [participant.email]
        )
    
    @staticmethod
    def send_payment_success(payment):
        """Envoie l'email de confirmation de paiement réussi"""
        context = {
            'payer_name': payment.get_payer_name(),
            'payment_reference': payment.reference,
            'payment_date': payment.created_at.strftime('%d/%m/%Y %H:%M'),
            'amount': payment.amount,
            'currency': payment.currency,
            'payment_method': payment.get_payment_method_display(),
            'payment_type': payment.get_payment_type_display(),
            'payment_details': payment.get_payment_details()
        }
        
        return send_email_template(
            'payment_success',
            context,
            f'Confirmation de paiement - {payment.reference}',
            [payment.get_recipient_email()]
        )
    
    @staticmethod
    def send_payment_failed(payment):
        """Envoie l'email de notification d'échec de paiement"""
        context = {
            'payer_name': payment.get_payer_name(),
            'payment_reference': payment.reference,
            'payment_attempt_date': payment.created_at.strftime('%d/%m/%Y %H:%M'),
            'amount': payment.amount,
            'currency': payment.currency,
            'payment_method': payment.get_payment_method_display(),
            'payment_type': payment.get_payment_type_display(),
            'failure_reason': payment.failure_reason or 'Erreur technique',
            'support_contact': 'support@martialcomp.com'
        }
        
        return send_email_template(
            'payment_failed',
            context,
            f'Échec de paiement - {payment.reference}',
            [payment.get_recipient_email()]
        )
    
    @staticmethod
    def send_subscription_receipt(subscription, payment):
        """Envoie l'email de reçu pour un paiement d'abonnement"""
        context = {
            'subscriber_name': subscription.user.get_full_name(),
            'subscription_name': subscription.plan.name,
            'payment_date': payment.created_at.strftime('%d/%m/%Y'),
            'amount': payment.amount,
            'currency': payment.currency,
            'next_payment_date': subscription.next_billing_date.strftime('%d/%m/%Y') if subscription.next_billing_date else 'À confirmer'
        }
        
        return send_email_template(
            'subscription_receipt',
            context,
            f'Reçu de paiement - Abonnement {subscription.plan.name}',
            [subscription.user.email]
        ) 