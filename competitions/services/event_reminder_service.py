# -*- coding: utf-8 -*-
import logging
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.urls import reverse

from competitions.models.event import Event, EventParticipant
from competitions.models.event_planning import EventReminder

logger = logging.getLogger(__name__)

class ReminderService:
    """Service pour l'envoi des rappels d'événements."""

    @staticmethod
    def get_due_reminders():
        """
        Récupère tous les rappels dont l'envoi est dû.
        
        Un rappel est considéré comme dû lorsque :
        - Il est activé
        - Il n'a pas encore été envoyé
        - Sa date d'envoi planifiée est passée
        """
        # Utiliser directement la méthode is_due du modèle EventReminder
        # qui est maintenant définie dans event_planning.py
        reminders = EventReminder.objects.filter(
            is_enabled=True,
            is_sent=False
        )
        
        due_reminders = []
        for reminder in reminders:
            if reminder.is_due:
                due_reminders.append(reminder.id)
        
        if due_reminders:
            return EventReminder.objects.filter(id__in=due_reminders)
        
        return EventReminder.objects.none()

    @staticmethod
    def send_reminder(reminder):
        """
        Envoie un rappel spécifique à ses destinataires.
        Gère les différents types de rappels (email, SMS, notification).
        
        Retourne un dictionnaire avec les résultats de l'envoi.
        """
        if reminder.is_sent:
            return {"success": False, "message": "Ce rappel a déjà été envoyé."}
        
        # Récupérer les destinataires
        recipients = reminder.get_recipient_list()
        
        if not recipients.exists():
            return {"success": False, "message": "Aucun destinataire trouvé pour ce rappel."}
        
        # Préparer les statistiques d'envoi
        delivery_status = {
            "total": recipients.count(),
            "sent": 0,
            "failed": 0,
            "details": []
        }
        
        # Préparer le contexte pour les templates
        event = reminder.event
        context = {
            "event": event,
            "reminder": reminder,
            "event_url": settings.SITE_URL + reverse("competitions:events:event_detail", kwargs={"event_id": event.id}),
        }
        
        # Envoyer selon le type de rappel
        try:
            for recipient in recipients:
                # Ajouter le destinataire au contexte
                recipient_context = {**context, "recipient": recipient}
                
                if reminder.reminder_type in ['email', 'all']:
                    success = ReminderService._send_email_reminder(reminder, recipient, recipient_context)
                    if success:
                        delivery_status["sent"] += 1
                    else:
                        delivery_status["failed"] += 1
                    
                    delivery_status["details"].append({
                        "recipient_id": recipient.id,
                        "recipient_email": recipient.email,
                        "type": "email",
                        "success": success
                    })
                
                if reminder.reminder_type in ['sms', 'all']:
                    success = ReminderService._send_sms_reminder(reminder, recipient, recipient_context)
                    if success:
                        delivery_status["sent"] += 1
                    else:
                        delivery_status["failed"] += 1
                    
                    delivery_status["details"].append({
                        "recipient_id": recipient.id,
                        "recipient_phone": getattr(recipient, "phone", None),
                        "type": "sms",
                        "success": success
                    })
                
                if reminder.reminder_type in ['notification', 'all']:
                    success = ReminderService._send_notification_reminder(reminder, recipient, recipient_context)
                    if success:
                        delivery_status["sent"] += 1
                    else:
                        delivery_status["failed"] += 1
                    
                    delivery_status["details"].append({
                        "recipient_id": recipient.id,
                        "type": "notification",
                        "success": success
                    })
            
            # Marquer le rappel comme envoyé
            with transaction.atomic():
                reminder.is_sent = True
                reminder.sent_at = timezone.now()
                reminder.delivery_status = delivery_status
                reminder.save()
            
            return {
                "success": True, 
                "message": f"Rappel envoyé avec succès à {delivery_status['sent']} destinataires. "
                          f"{delivery_status['failed']} échecs.",
                "delivery_status": delivery_status
            }
        
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rappel {reminder.id}: {str(e)}")
            return {"success": False, "message": f"Erreur lors de l'envoi: {str(e)}"}

    @staticmethod
    def _send_email_reminder(reminder, recipient, context):
        """Envoie un rappel par email."""
        try:
            subject = reminder.title
            
            # Rendre le template HTML si disponible, sinon utiliser le message brut
            try:
                html_content = render_to_string('competitions/emails/event_reminder.html', context)
                text_content = strip_tags(html_content)
            except:
                html_content = reminder.message.replace('\n', '<br>')
                text_content = reminder.message
            
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = recipient.email
            
            if not to_email:
                logger.warning(f"Pas d'email pour le destinataire {recipient.id}")
                return False
            
            # Créer un email avec contenu HTML et texte
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email]
            )
            email.attach_alternative(html_content, "text/html")
            
            # Ajouter des pièces jointes si nécessaire (à implémenter si besoin)
            
            # Envoyer l'email
            email.send()
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur d'envoi d'email pour {recipient.email}: {str(e)}")
            return False

    @staticmethod
    def _send_sms_reminder(reminder, recipient, context):
        """
        Envoie un rappel par SMS.
        
        Pour l'implémentation réelle, il faudrait intégrer un service SMS comme Twilio.
        Cette fonction est un exemple et devrait être adaptée selon le fournisseur choisi.
        """
        try:
            # Récupérer le numéro de téléphone du destinataire
            phone_number = None
            if hasattr(recipient, 'profile') and hasattr(recipient.profile, 'phone'):
                phone_number = recipient.profile.phone
            elif hasattr(recipient, 'phone'):
                phone_number = recipient.phone
            
            if not phone_number:
                logger.warning(f"Pas de numéro de téléphone pour le destinataire {recipient.id}")
                return False
            
            # Préparer le contenu du SMS
            sms_content = reminder.message
            if len(sms_content) > 160:
                # Limiter à 160 caractères pour un SMS standard
                sms_content = sms_content[:157] + "..."
            
            # Ici, il faudrait appeler un service d'envoi de SMS
            # Exemple avec Twilio (nécessite l'installation de la bibliothèque twilio)
            """
            from twilio.rest import Client
            
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            message = client.messages.create(
                body=sms_content,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            
            return message.sid is not None
            """
            
            # Pour les besoins de cet exemple, simulons un succès
            logger.info(f"Simulé: SMS envoyé à {phone_number} - Contenu: {sms_content}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur d'envoi de SMS: {str(e)}")
            return False

    @staticmethod
    def _send_notification_reminder(reminder, recipient, context):
        """
        Envoie une notification in-app.
        
        Cette fonction dépend d'un système de notification qui devrait être
        implémenté dans l'application (par exemple via WebSockets ou un service
        de notifications persistantes).
        """
        try:
            # Ici, l'implémentation dépendra du système de notification utilisé
            # Exemple simple avec un modèle de notification
            from competitions.models.notifications import Notification
            
            notification = Notification(
                user=recipient,
                title=reminder.title,
                message=reminder.message,
                event=reminder.event,
                notification_type='event_reminder',
                source_id=str(reminder.id)
            )
            notification.save()
            
            # Ici on pourrait également envoyer une notification en temps réel
            # via WebSockets si l'application supporte cela
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur d'envoi de notification: {str(e)}")
            return False

    @staticmethod
    def process_all_due_reminders():
        """
        Traite tous les rappels dont l'envoi est dû.
        
        Cette fonction est destinée à être appelée par un job planifié
        (par exemple via Celery ou une tâche cron).
        
        Retourne un résumé des envois effectués.
        """
        reminders = ReminderService.get_due_reminders()
        
        results = {
            "total": reminders.count(),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for reminder in reminders:
            result = ReminderService.send_reminder(reminder)
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "reminder_id": reminder.id,
                "event_id": reminder.event.id,
                "event_title": reminder.event.title,
                "success": result["success"],
                "message": result["message"]
            })
        
        logger.info(f"Traitement des rappels terminé: {results['successful']} succès, {results['failed']} échecs")
        return results

    @staticmethod
    def create_email_template(path='competitions/emails/event_reminder.html'):
        """
        Crée un template d'email par défaut pour les rappels d'événements.
        Cette fonction est utilitaire et n'est pas destinée à être appelée en production.
        """
        import os
        from django.template.loader import get_template
        
        template_content = """{% load i18n %}
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ reminder.title }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background-color: #007bff;
            color: white;
            padding: 15px 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            background-color: #f9f9f9;
            padding: 20px;
            border: 1px solid #ddd;
            border-top: none;
            border-radius: 0 0 5px 5px;
        }
        .event-details {
            background-color: white;
            padding: 15px;
            margin: 20px 0;
            border: 1px solid #eee;
            border-radius: 5px;
        }
        .button {
            display: inline-block;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 5px;
            margin-top: 15px;
            text-align: center;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #777;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ reminder.title }}</h1>
        </div>
        <div class="content">
            <p>{% translate "Bonjour" %} {{ recipient.get_full_name|default:recipient.username }},</p>
            
            <div class="message">
                {{ reminder.message|linebreaks }}
            </div>
            
            <div class="event-details">
                <h2>{{ event.title }}</h2>
                <p><strong>{% translate "Date" %}:</strong> {{ event.start_date|date:"d/m/Y" }}
                {% if event.start_time %} {% translate "à" %} {{ event.start_time|time:"H:i" }}{% endif %}
                {% if event.end_date and event.end_date != event.start_date %}
                    {% translate "au" %} {{ event.end_date|date:"d/m/Y" }}
                {% endif %}
                {% if event.end_time %} {% translate "jusqu'à" %} {{ event.end_time|time:"H:i" }}{% endif %}
                </p>
                
                {% if event.location %}
                <p><strong>{% translate "Lieu" %}:</strong> {{ event.location }}</p>
                {% endif %}
                
                {% if event.description %}
                <p><strong>{% translate "Description" %}:</strong> {{ event.description|truncatewords:30 }}</p>
                {% endif %}
            </div>
            
            <a href="{{ event_url }}" class="button">{% translate "Voir l'événement" %}</a>
            
            <p>{% translate "À bientôt !" %}</p>
        </div>
        <div class="footer">
            <p>{% translate "Cet email a été envoyé automatiquement, merci de ne pas y répondre." %}</p>
            <p>© {% now "Y" %} MartialComp</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Vérifier si le répertoire existe
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Écrire le template
        with open(path, 'w') as file:
            file.write(template_content)
        
        return f"Template créé à {path}"


# Interface pour appel depuis un job Celery ou similaire
def send_due_reminders():
    """
    Fonction pour appeler depuis un task scheduler comme Celery.
    """
    return ReminderService.process_all_due_reminders()


def send_specific_reminder(reminder_id):
    """
    Fonction pour envoyer un rappel spécifique, à appeler depuis un job scheduler.
    """
    try:
        reminder = EventReminder.objects.get(id=reminder_id)
        return ReminderService.send_reminder(reminder)
    except EventReminder.DoesNotExist:
        return {"success": False, "message": f"Rappel {reminder_id} introuvable."}
    except Exception as e:
        return {"success": False, "message": str(e)}