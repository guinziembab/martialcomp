"""
Système de notifications familiales centralisées pour MartialComp.
Gère les notifications push, email et SMS pour les familles.
"""

from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta
import logging
import json

from .models import Family, FamilyMember, FamilyEvent

# Import conditionnel du système de notifications existant
try:
    from apps.competitions.models.notifications import Notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

logger = logging.getLogger(__name__)


class FamilyNotificationService:
    """Service principal pour les notifications familiales."""
    
    NOTIFICATION_TYPES = {
        'event_reminder': {
            'title': _("Rappel d'événement"),
            'template': 'family_event_reminder',
            'priority': 'high'
        },
        'payment_due': {
            'title': _("Paiement en attente"),
            'template': 'family_payment_due',
            'priority': 'high'
        },
        'registration_opening': {
            'title': _("Ouverture d'inscription"),
            'template': 'family_registration_opening',
            'priority': 'medium'
        },
        'family_invite': {
            'title': _("Invitation familiale"),
            'template': 'family_invite',
            'priority': 'medium'
        },
        'member_achievement': {
            'title': _("Succès d'un membre"),
            'template': 'family_member_achievement',
            'priority': 'low'
        },
        'schedule_change': {
            'title': _("Changement de planning"),
            'template': 'family_schedule_change',
            'priority': 'high'
        },
        'weekly_summary': {
            'title': _("Résumé hebdomadaire"),
            'template': 'family_weekly_summary',
            'priority': 'low'
        }
    }
    
    def __init__(self, family):
        self.family = family
    
    def send_family_notification(self, notification_type, context=None, recipients=None, 
                               channels=['email', 'in_app'], send_immediately=True):
        """
        Envoie une notification Ã  la famille.
        
        Args:
            notification_type (str): Type de notification
            context (dict): Contexte pour le template
            recipients (list): Liste des membres Ã  notifier (None = tous)
            channels (list): Canaux de notification ['email', 'sms', 'push', 'in_app']
            send_immediately (bool): Envoyer immédiatement ou programmer
            
        Returns:
            dict: Résultat de l'envoi
        """
        if notification_type not in self.NOTIFICATION_TYPES:
            raise ValueError(f"Type de notification inconnu: {notification_type}")
        
        notification_config = self.NOTIFICATION_TYPES[notification_type]
        
        # Préparer le contexte
        if context is None:
            context = {}
        
        context.update({
            'family': self.family,
            'family_name': self.family.family_name,
            'notification_type': notification_type,
            'timestamp': timezone.now()
        })
        
        # Déterminer les destinataires
        if recipients is None:
            target_members = self.family.get_active_members().filter(
                receive_family_notifications=True
            )
        else:
            target_members = self.family.get_active_members().filter(
                id__in=recipients,
                receive_family_notifications=True
            )
        
        results = {
            'success': True,
            'notification_type': notification_type,
            'total_recipients': target_members.count(),
            'sent_channels': {},
            'errors': []
        }
        
        try:
            with transaction.atomic():
                # Envoyer via chaque canal demandé
                for channel in channels:
                    channel_result = self._send_via_channel(
                        channel, notification_config, context, target_members
                    )
                    results['sent_channels'][channel] = channel_result
                
                # Enregistrer dans l'historique
                self._log_notification(notification_type, context, target_members, results)
                
                logger.info(f"Notification familiale envoyée: {notification_type} Ã  {target_members.count()} membres")
                
        except Exception as e:
            results['success'] = False
            results['errors'].append(str(e))
            logger.error(f"Erreur envoi notification familiale {notification_type}: {e}")
        
        return results
    
    def _send_via_channel(self, channel, notification_config, context, target_members):
        """Envoie la notification via un canal spécifique."""
        channel_results = {
            'channel': channel,
            'sent_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        for member in target_members:
            try:
                if channel == 'email':
                    self._send_email_notification(member, notification_config, context)
                elif channel == 'sms':
                    self._send_sms_notification(member, notification_config, context)
                elif channel == 'push':
                    self._send_push_notification(member, notification_config, context)
                elif channel == 'in_app':
                    self._send_in_app_notification(member, notification_config, context)
                
                channel_results['sent_count'] += 1
                
            except Exception as e:
                channel_results['failed_count'] += 1
                channel_results['errors'].append({
                    'member': member.user.get_full_name(),
                    'error': str(e)
                })
        
        return channel_results
    
    def _send_email_notification(self, member, notification_config, context):
        """Envoie une notification par email."""
        if not member.user.email:
            raise ValueError("Aucune adresse email pour ce membre")
        
        template_name = notification_config['template']
        context['member'] = member
        context['user'] = member.user
        
        # Rendre les templates HTML et texte
        html_content = render_to_string(
            f'family_management/notifications/{template_name}.html',
            context
        )
        text_content = strip_tags(html_content)
        
        # Créer l'email
        subject = f"[{self.family.family_name}] {notification_config['title']}"
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com'),
            to=[member.user.email]
        )
        email.attach_alternative(html_content, "text/html")
        
        # Envoyer
        email.send()
        
        logger.debug(f"Email envoyé Ã  {member.user.email}: {subject}")
    
    def _send_sms_notification(self, member, notification_config, context):
        """Envoie une notification par SMS."""
        # Récupérer le numéro de téléphone
        phone = None
        if hasattr(member, 'practitioner') and member.practitioner:
            phone = member.practitioner.phone
        elif hasattr(member.user, 'profile'):
            phone = getattr(member.user.profile, 'phone', None)
        
        if not phone:
            raise ValueError("Aucun numéro de téléphone pour ce membre")
        
        # Préparer le message SMS
        template_name = f'family_management/notifications/{notification_config["template"]}.txt'
        message = render_to_string(template_name, context)
        
        # Limitation SMS (160 caractères)
        if len(message) > 160:
            message = message[:157] + "..."
        
        # Intégration avec un service SMS (Ã  adapter selon le fournisseur)
        self._send_sms_via_provider(phone, message)
        
        logger.debug(f"SMS envoyé Ã  {phone}: {message[:50]}...")
    
    def _send_sms_via_provider(self, phone, message):
        """Envoie le SMS via le fournisseur configuré."""
        # Implémentation spécifique au fournisseur SMS
        # Exemple avec Twilio, Ã  adapter selon les besoins
        
        if hasattr(settings, 'TWILIO_ACCOUNT_SID'):
            try:
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                
                message = client.messages.create(
                    body=message,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
                
                return message.sid
            except ImportError:
                logger.warning("Twilio non disponible, SMS non envoyé")
        else:
            logger.debug(f"SMS simulé vers {phone}: {message}")
    
    def _send_push_notification(self, member, notification_config, context):
        """Envoie une notification push."""
        # Implémentation pour les notifications push
        # Peut utiliser Firebase, OneSignal, etc.
        
        push_data = {
            'title': notification_config['title'],
            'body': render_to_string(
                f'family_management/notifications/{notification_config["template"]}_push.txt',
                context
            ),
            'icon': '/static/img/family_icon.png',
            'data': {
                'family_id': str(self.family.id),
                'notification_type': context['notification_type'],
                'url': f'/families/family/{self.family.id}/'
            }
        }
        
        # Envoyer via le service push configuré
        self._send_push_via_service(member.user, push_data)
    
    def _send_push_via_service(self, user, push_data):
        """Envoie la notification push via le service configuré."""
        # Implémentation spécifique au service push
        logger.debug(f"Push notification simulée pour {user.username}: {push_data['title']}")
    
    def _send_in_app_notification(self, member, notification_config, context):
        """Envoie une notification in-app."""
        if not NOTIFICATIONS_AVAILABLE:
            logger.warning("Système de notifications in-app non disponible")
            return
        
        # Créer la notification in-app
        notification = Notification.objects.create(
            user=member.user,
            title=notification_config['title'],
            message=render_to_string(
                f'family_management/notifications/{notification_config["template"]}_short.txt',
                context
            ),
            notification_type='family',
            priority=notification_config['priority'],
            metadata={
                'family_id': str(self.family.id),
                'family_name': self.family.family_name,
                'notification_subtype': context['notification_type']
            }
        )
        
        logger.debug(f"Notification in-app créée pour {member.user.username}: {notification.title}")
    
    def _log_notification(self, notification_type, context, target_members, results):
        """Enregistre la notification dans l'historique."""
        # Créer un log de notification (peut Ãªtre un modèle dédié)
        log_data = {
            'family_id': str(self.family.id),
            'notification_type': notification_type,
            'recipients_count': target_members.count(),
            'success': results['success'],
            'timestamp': timezone.now().isoformat(),
            'context_summary': {
                'type': notification_type,
                'has_event': 'event' in context,
                'has_payment': 'payment' in context
            }
        }
        
        logger.info(f"Notification familiale loggée: {json.dumps(log_data)}")
    
    def schedule_reminder(self, event, reminder_time, reminder_type='event_reminder'):
        """Programme un rappel pour un événement."""
        # Calculer le délai
        if isinstance(reminder_time, int):
            # reminder_time en heures avant l'événement
            reminder_datetime = event.start_date - timedelta(hours=reminder_time)
        else:
            # reminder_time est un datetime spécifique
            reminder_datetime = reminder_time
        
        # Contexte pour le rappel
        context = {
            'event': event,
            'reminder_hours': reminder_time if isinstance(reminder_time, int) else None
        }
        
        # Programmer le rappel (Ã  implémenter avec Celery ou équivalent)
        self._schedule_notification_task(reminder_type, context, reminder_datetime)
        
        logger.info(f"Rappel programmé pour {reminder_datetime}: {event.title}")
    
    def _schedule_notification_task(self, notification_type, context, scheduled_time):
        """Programme une tÃ¢che de notification (avec Celery par exemple)."""
        # Implémentation avec un système de tÃ¢ches asynchrones
        
        try:
            # Exemple avec Celery (Ã  adapter)
            from .tasks import send_family_notification_task
            
            send_family_notification_task.apply_async(
                args=[str(self.family.id), notification_type, context],
                eta=scheduled_time
            )
        except ImportError:
            logger.warning("Système de tÃ¢ches non disponible, notification immédiate")
            # Fallback: programmer avec un système simple
            self._simple_schedule(notification_type, context, scheduled_time)
    
    def _simple_schedule(self, notification_type, context, scheduled_time):
        """Système de programmation simple sans Celery."""
        # Stockage simple des tÃ¢ches programmées
        # Ã€ implémenter selon les besoins
        pass
    
    def send_weekly_summary(self):
        """Envoie le résumé hebdomadaire Ã  la famille."""
        from .calendar_service import FamilyCalendarService
        
        # Récupérer les données de la semaine
        start_date = timezone.now().date() - timedelta(days=7)
        end_date = timezone.now().date()
        
        calendar_service = FamilyCalendarService(self.family)
        week_data = calendar_service.get_consolidated_calendar(start_date, end_date)
        
        # Préparer les statistiques
        stats = {
            'total_events': sum(len(events) for events in week_data['events_by_date'].values()),
            'competitions': 0,
            'family_events': 0,
            'upcoming_payments': self.family.payment_groups.filter(is_paid=False).count()
        }
        
        # Compter par type
        for events in week_data['events_by_date'].values():
            for event in events:
                if event['type'] == 'competition':
                    stats['competitions'] += 1
                elif event['type'] == 'family_event':
                    stats['family_events'] += 1
        
        # Ã‰vénements Ã  venir
        upcoming_events = calendar_service.get_upcoming_events(days_ahead=7)
        
        context = {
            'week_data': week_data,
            'stats': stats,
            'upcoming_events': upcoming_events[:5],  # Top 5
            'week_start': start_date,
            'week_end': end_date
        }
        
        return self.send_family_notification(
            'weekly_summary',
            context=context,
            channels=['email']
        )
    
    def notify_payment_reminder(self, payment_group, days_before_due=3):
        """Envoie un rappel de paiement."""
        context = {
            'payment_group': payment_group,
            'amount': payment_group.total_amount,
            'description': payment_group.description,
            'days_before_due': days_before_due
        }
        
        # Notifier seulement les membres qui peuvent gérer les paiements
        payment_managers = self.family.get_active_members().filter(
            can_make_payments=True
        )
        
        return self.send_family_notification(
            'payment_due',
            context=context,
            recipients=[member.id for member in payment_managers],
            channels=['email', 'in_app', 'push']
        )
    
    def notify_event_reminder(self, event, hours_before=24):
        """Envoie un rappel d'événement."""
        context = {
            'event': event,
            'hours_before': hours_before,
            'event_datetime': event.start_date
        }
        
        # Notifier les membres concernés par l'événement
        if hasattr(event, 'concerned_members'):
            concerned_member_ids = list(event.concerned_members.values_list('id', flat=True))
        else:
            # Notifier toute la famille
            concerned_member_ids = None
        
        return self.send_family_notification(
            'event_reminder',
            context=context,
            recipients=concerned_member_ids,
            channels=['email', 'push', 'sms']
        )
    
    def get_notification_preferences(self, member):
        """Récupère les préférences de notification d'un membre."""
        # Peut Ãªtre étendu avec un modèle dédié aux préférences
        return {
            'email': True,
            'sms': hasattr(member.practitioner, 'phone') if member.practitioner else False,
            'push': True,
            'in_app': member.receive_family_notifications,
            'frequency': 'immediate',  # immediate, daily, weekly
            'types': {
                'event_reminder': True,
                'payment_due': member.can_make_payments,
                'family_invite': True,
                'weekly_summary': True
            }
        }


class FamilyNotificationManager:
    """Gestionnaire global des notifications familiales."""
    
    @staticmethod
    def send_to_multiple_families(families, notification_type, context=None, **kwargs):
        """Envoie une notification Ã  plusieurs familles."""
        results = []
        
        for family in families:
            service = FamilyNotificationService(family)
            result = service.send_family_notification(notification_type, context, **kwargs)
            result['family_id'] = str(family.id)
            results.append(result)
        
        return {
            'total_families': len(families),
            'successful_sends': sum(1 for r in results if r['success']),
            'failed_sends': sum(1 for r in results if not r['success']),
            'detailed_results': results
        }
    
    @staticmethod
    def send_organization_announcement(organization, message, families=None):
        """Envoie une annonce de l'organisation Ã  ses familles."""
        if families is None:
            families = Family.objects.filter(organization=organization, is_active=True)
        
        context = {
            'organization': organization,
            'message': message,
            'announcement': True
        }
        
        return FamilyNotificationManager.send_to_multiple_families(
            families,
            'family_invite',  # Réutiliser ce type pour les annonces
            context=context,
            channels=['email', 'in_app']
        )

