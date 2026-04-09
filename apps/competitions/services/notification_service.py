"""
Service de gestion des notifications pour les compétitions.
Gère la création, l'envoi et la récupération des notifications.
Intègre l'envoi d'emails pour les notifications importantes.
"""

import logging
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db.models import Q
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Import pour WebSocket (si disponible)
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False

from apps.competitions.models.notifications import Notification, NotificationPreference

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Service pour gérer les notifications des compétitions.
    Gère la création, l'envoi via WebSocket, et la récupération des notifications.
    """

    @staticmethod
    def create_assignment_notification(judge_assignment):
        """
        Crée une notification d'assignation de juge.
        
        Args:
            judge_assignment: Instance de JudgeAssignment
            
        Returns:
            Notification: Instance créée ou None en cas d'erreur
        """
        try:
            if not judge_assignment.judge:
                logger.warning(f"Pas de juge associé à l'assignation {judge_assignment.id}")
                return None
            
            # Vérifier les préférences utilisateur
            prefs, _ = NotificationPreference.objects.get_or_create(
                user=judge_assignment.judge,
                defaults={
                    'email_enabled': True,
                    'competition_notifications': True,
                }
            )
            
            # Si l'utilisateur ne souhaite pas recevoir ces notifications, on arrête
            if not prefs.competition_notifications:
                logger.debug(
                    f"Notifications désactivées pour {judge_assignment.judge.username} - "
                    f"Assignation {judge_assignment.id} ignorée"
                )
                return None
            
            # Préparer les informations pour la notification
            competition_name = (
                judge_assignment.competition.title 
                if hasattr(judge_assignment.competition, 'title') 
                else str(judge_assignment.competition)
            )
            category_name = (
                judge_assignment.category.name 
                if judge_assignment.category 
                else "Compétition générale"
            )
            role_display = (
                judge_assignment.get_role_display() 
                if hasattr(judge_assignment, 'get_role_display') 
                else judge_assignment.role
            )
            
            # Créer le message de notification
            title = f"Assignation comme juge - {competition_name}"
            message = (
                f"Vous avez été assigné comme {role_display} pour la catégorie '{category_name}' "
                f"de la compétition '{competition_name}'."
            )
            
            # Ajouter des informations supplémentaires si disponibles
            if judge_assignment.start_time:
                from django.utils import formats
                message += f"\n\nHeure de début prévue : {formats.date_format(judge_assignment.start_time, 'd/m/Y à H:i')}"
            
            # Générer le lien vers l'interface de notation
            try:
                if judge_assignment.category:
                    # Lien vers l'interface de notation spécifique à la catégorie
                    action_url = reverse('competitions:management:judge_scoring_interface', kwargs={
                        'competition_id': judge_assignment.competition.id,
                        'category_id': judge_assignment.category.id,
                        'judge_id': judge_assignment.judge.id,
                    })
                else:
                    # Lien vers le dashboard scoring général
                    action_url = reverse('competitions:management:scoring_dashboard', kwargs={
                        'competition_id': judge_assignment.competition.id,
                    })
            except Exception as url_error:
                # En cas d'erreur de génération d'URL, utiliser le dashboard général
                logger.warning(f"Erreur génération URL pour assignation {judge_assignment.id}: {url_error}")
                try:
                    action_url = reverse('competitions:dashboard')
                except:
                    action_url = None
            
            # Créer la notification
            notification = Notification.objects.create(
                user=judge_assignment.judge,
                title=title,
                message=message,
                notification_type='info',
                priority='important',
                action_url=action_url,
                action_text='Accéder à l\'interface de notation',
            )
            
            logger.info(
                f"Notification créée pour {judge_assignment.judge.username} - "
                f"Assignation #{judge_assignment.id} ({competition_name} - {category_name})"
            )

            # Envoyer via WebSocket si disponible
            if CHANNELS_AVAILABLE:
                NotificationService.send_websocket_notification(
                    judge_assignment.judge,
                    notification
                )

            # Envoyer aussi par email si les préférences le permettent
            if prefs.email_enabled:
                NotificationService.send_judge_assignment_email(judge_assignment)

            return notification
            
        except Exception as e:
            logger.error(
                f"Erreur lors de la création de notification pour assignation #{judge_assignment.id}: {e}",
                exc_info=True
            )
            return None

    @staticmethod
    def send_websocket_notification(user, notification):
        """
        Envoie une notification via WebSocket à un utilisateur.
        
        Args:
            user: Instance de User
            notification: Instance de Notification
        """
        if not CHANNELS_AVAILABLE:
            logger.debug("Channels non disponible - notification WebSocket ignorée")
            return
        
        try:
            channel_layer = get_channel_layer()
            if not channel_layer:
                logger.debug("Channel layer non configuré - notification WebSocket ignorée")
                return
            
            # Nom du groupe pour les notifications utilisateur
            group_name = f"notifications_user_{user.id}"
            
            # Préparer les données de la notification
            notification_data = {
                'type': 'notification_message',
                'notification': {
                    'id': notification.id,
                    'title': notification.title,
                    'message': notification.message,
                    'notification_type': notification.notification_type,
                    'priority': notification.priority,
                    'action_url': notification.action_url,
                    'action_text': notification.action_text,
                    'created_at': notification.created_at.isoformat(),
                    'is_read': notification.is_read,
                }
            }
            
            # Envoyer la notification au groupe
            async_to_sync(channel_layer.group_send)(
                group_name,
                notification_data
            )
            
            logger.debug(f"Notification WebSocket envoyée à {user.username} (groupe: {group_name})")
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'envoi de notification WebSocket: {e}")

    @staticmethod
    def get_unread_notifications(user, limit=20):
        """
        Récupère les notifications non lues pour un utilisateur.
        
        Args:
            user: Instance de User
            limit: Nombre maximum de notifications à retourner (défaut: 20)
            
        Returns:
            QuerySet: Notifications non lues et non expirées
        """
        try:
            notifications = Notification.objects.filter(
                user=user,
                is_read=False
            ).exclude(
                Q(expires_at__lt=timezone.now()) if Notification.objects.filter(
                    expires_at__isnull=False
                ).exists() else Q()
            ).order_by('-created_at')[:limit]
            
            return notifications
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des notifications pour {user.username}: {e}")
            return Notification.objects.none()

    @staticmethod
    def get_notification_count(user):
        """
        Récupère le nombre de notifications non lues pour un utilisateur.
        
        Args:
            user: Instance de User
            
        Returns:
            int: Nombre de notifications non lues
        """
        try:
            count = Notification.objects.filter(
                user=user,
                is_read=False
            ).exclude(
                Q(expires_at__lt=timezone.now()) if Notification.objects.filter(
                    expires_at__isnull=False
                ).exists() else Q()
            ).count()
            
            return count
            
        except Exception as e:
            logger.error(f"Erreur lors du comptage des notifications pour {user.username}: {e}")
            return 0

    @staticmethod
    def mark_as_read(notification_id, user=None):
        """
        Marque une notification comme lue.
        
        Args:
            notification_id: ID de la notification
            user: Instance de User (optionnel, pour sécurité)
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            notification = Notification.objects.get(id=notification_id)
            
            # Vérifier que l'utilisateur est le propriétaire si fourni
            if user and notification.user != user:
                logger.warning(
                    f"Tentative de marquer comme lu une notification appartenant à un autre utilisateur: "
                    f"notification {notification_id}, utilisateur {user.username}"
                )
                return False
            
            if not notification.is_read:
                notification.mark_as_read()
                logger.debug(f"Notification {notification_id} marquée comme lue")
                return True
            else:
                logger.debug(f"Notification {notification_id} était déjà lue")
                return True
                
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} introuvable")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du marquage comme lu de la notification {notification_id}: {e}")
            return False

    @staticmethod
    def mark_all_as_read(user):
        """
        Marque toutes les notifications non lues d'un utilisateur comme lues.
        
        Args:
            user: Instance de User
            
        Returns:
            int: Nombre de notifications marquées comme lues
        """
        try:
            updated = Notification.objects.filter(
                user=user,
                is_read=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            logger.info(f"{updated} notifications marquées comme lues pour {user.username}")
            return updated
            
        except Exception as e:
            logger.error(f"Erreur lors du marquage en masse des notifications pour {user.username}: {e}")
            return 0

    @staticmethod
    def get_recent_notifications(user, limit=10):
        """
        Récupère les notifications récentes (lues et non lues) pour un utilisateur.
        
        Args:
            user: Instance de User
            limit: Nombre maximum de notifications à retourner (défaut: 10)
            
        Returns:
            QuerySet: Notifications récentes
        """
        try:
            notifications = Notification.objects.filter(
                user=user
            ).exclude(
                Q(expires_at__lt=timezone.now()) if Notification.objects.filter(
                    expires_at__isnull=False
                ).exists() else Q()
            ).order_by('-created_at')[:limit]
            
            return notifications
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des notifications récentes pour {user.username}: {e}")
            return Notification.objects.none()

    @staticmethod
    def delete_expired_notifications():
        """
        Supprime les notifications expirées.
        
        Returns:
            int: Nombre de notifications supprimées
        """
        try:
            deleted, _ = Notification.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()
            
            if deleted > 0:
                logger.info(f"{deleted} notifications expirées supprimées")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des notifications expirées: {e}")
            return 0

    # ============================================================================
    # NOTIFICATIONS POUR LA GESTION DES RÔLES
    # ============================================================================

    @staticmethod
    def create_role_assignment_notification(membership, action='pending'):
        """
        Crée une notification pour une attribution de rôle.

        Args:
            membership: Instance de OrganizationMember
            action: 'pending', 'approved', 'rejected'

        Returns:
            Notification: Instance créée ou None en cas d'erreur
        """
        try:
            user = membership.user
            if not user:
                logger.warning(f"Pas d'utilisateur associé au membership {membership.id}")
                return None

            # Vérifier les préférences utilisateur
            prefs, _ = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'email_enabled': True,
                    'competition_notifications': True,
                }
            )

            org_name = membership.organization.name if membership.organization else "l'organisation"
            role_display = membership.get_role_display() if hasattr(membership, 'get_role_display') else membership.role

            if action == 'pending':
                title = f"Demande de rôle {role_display} en cours"
                message = (
                    f"Votre demande pour le rôle '{role_display}' dans {org_name} "
                    f"est en attente de validation par un administrateur."
                )
                notification_type = 'info'
                priority = 'normal'
                action_url = None
                action_text = None

            elif action == 'approved':
                title = f"Rôle {role_display} approuvé"
                message = (
                    f"Votre rôle '{role_display}' dans {org_name} a été approuvé. "
                    f"Vous pouvez maintenant accéder aux fonctionnalités associées."
                )
                notification_type = 'success'
                priority = 'important'
                try:
                    from django.urls import reverse
                    action_url = membership.get_dashboard_url() or reverse('competitions:dashboard')
                except:
                    action_url = '/competitions/dashboard/'
                action_text = 'Accéder au dashboard'

            elif action == 'rejected':
                title = f"Rôle {role_display} refusé"
                reason = membership.rejection_reason or "Aucun motif spécifié"
                message = (
                    f"Votre demande pour le rôle '{role_display}' dans {org_name} a été refusée. "
                    f"Motif : {reason}"
                )
                notification_type = 'warning'
                priority = 'important'
                action_url = None
                action_text = None

            else:
                logger.warning(f"Action de notification inconnue: {action}")
                return None

            # Créer la notification
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                action_url=action_url,
                action_text=action_text,
            )

            logger.info(
                f"Notification rôle créée pour {user.username} - "
                f"Action: {action}, Rôle: {role_display}, Org: {org_name}"
            )

            # Envoyer via WebSocket si disponible
            if CHANNELS_AVAILABLE:
                NotificationService.send_websocket_notification(user, notification)

            # Envoyer aussi par email si les préférences le permettent
            if prefs.email_enabled:
                NotificationService.send_role_assignment_email(membership, action)

            return notification

        except Exception as e:
            logger.error(
                f"Erreur lors de la création de notification de rôle pour membership #{membership.id}: {e}",
                exc_info=True
            )
            return None

    @staticmethod
    def create_pending_approval_notification(membership, admin_users):
        """
        Crée des notifications pour les administrateurs quand une demande de rôle est soumise.

        Args:
            membership: Instance de OrganizationMember (la demande)
            admin_users: Liste d'utilisateurs administrateurs à notifier

        Returns:
            list: Liste des notifications créées
        """
        try:
            notifications = []
            applicant_name = (
                membership.user.get_full_name() or membership.user.username
                if membership.user else "Un utilisateur"
            )
            org_name = membership.organization.name if membership.organization else "l'organisation"
            role_display = membership.get_role_display() if hasattr(membership, 'get_role_display') else membership.role

            title = f"Nouvelle demande de rôle à valider"
            message = (
                f"{applicant_name} a demandé le rôle '{role_display}' dans {org_name}. "
                f"Veuillez examiner cette demande."
            )

            try:
                from django.urls import reverse
                action_url = reverse('competitions:pending_role_approvals')
            except:
                action_url = '/competitions/roles/pending-approvals/'

            for admin_user in admin_users:
                try:
                    notification = Notification.objects.create(
                        user=admin_user,
                        title=title,
                        message=message,
                        notification_type='info',
                        priority='important',
                        action_url=action_url,
                        action_text='Voir les demandes',
                    )
                    notifications.append(notification)

                    if CHANNELS_AVAILABLE:
                        NotificationService.send_websocket_notification(admin_user, notification)

                    logger.debug(f"Notification admin créée pour {admin_user.username}")

                except Exception as e:
                    logger.warning(f"Erreur notification admin {admin_user.username}: {e}")

            logger.info(f"{len(notifications)} notifications admin créées pour membership #{membership.id}")

            # Envoyer aussi des emails aux administrateurs
            NotificationService.send_admin_pending_approval_email(membership, admin_users)

            return notifications

        except Exception as e:
            logger.error(f"Erreur notifications admin pour membership #{membership.id}: {e}", exc_info=True)
            return []

    # ============================================================================
    # ENVOI D'EMAILS
    # ============================================================================

    @staticmethod
    def send_email(user, subject, template_name, context, fail_silently=True):
        """
        Envoie un email à un utilisateur en utilisant un template HTML.

        Args:
            user: Instance de User
            subject: Sujet de l'email
            template_name: Nom du template (sans extension, ex: 'role_assignment_pending')
            context: Dictionnaire de contexte pour le template
            fail_silently: Si True, les erreurs sont loggées mais pas levées

        Returns:
            bool: True si l'email a été envoyé, False sinon
        """
        try:
            if not user.email:
                logger.warning(f"Pas d'email pour l'utilisateur {user.username}")
                return False

            # Vérifier les préférences email de l'utilisateur
            prefs, _ = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={'email_enabled': True, 'competition_notifications': True}
            )

            if not prefs.email_enabled:
                logger.debug(f"Emails désactivés pour {user.username}")
                return False

            # Préparer le contexte
            site_url = getattr(settings, 'SITE_URL', 'https://martialcomp.com')
            context.update({
                'user': user,
                'site_url': site_url,
            })

            # Charger et rendre le template HTML
            template_path = f'competitions/emails/{template_name}.html'
            try:
                html_content = render_to_string(template_path, context)
            except Exception as template_error:
                logger.error(f"Erreur template {template_path}: {template_error}")
                return False

            # Version texte (strip HTML)
            text_content = strip_tags(html_content)

            # Créer et envoyer l'email
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'MartialComp <noreply@martialcomp.com>')

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=fail_silently)

            logger.info(f"Email envoyé à {user.email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Erreur envoi email à {user.username}: {e}", exc_info=True)
            if not fail_silently:
                raise
            return False

    @staticmethod
    def send_role_assignment_email(membership, action='pending'):
        """
        Envoie un email pour une attribution de rôle.

        Args:
            membership: Instance de OrganizationMember
            action: 'pending', 'approved', 'rejected'

        Returns:
            bool: True si l'email a été envoyé
        """
        try:
            user = membership.user
            if not user:
                return False

            org_name = membership.organization.name if membership.organization else "l'organisation"
            role_display = membership.get_role_display() if hasattr(membership, 'get_role_display') else membership.role

            # Préparer le contexte selon l'action
            context = {
                'organization_name': org_name,
                'role_display': role_display,
                'created_at': membership.created_at if hasattr(membership, 'created_at') else timezone.now(),
            }

            if action == 'pending':
                subject = f"[MartialComp] Demande de rôle {role_display} en cours"
                template_name = 'role_assignment_pending'

            elif action == 'approved':
                subject = f"[MartialComp] Rôle {role_display} approuvé"
                template_name = 'role_assignment_approved'
                context.update({
                    'approved_by': membership.approved_by,
                    'approved_at': membership.approved_at,
                })
                # URL vers le dashboard
                try:
                    action_url = membership.get_dashboard_url() or reverse('competitions:dashboard')
                    context['action_url'] = f"{getattr(settings, 'SITE_URL', '')}{action_url}"
                except:
                    context['action_url'] = f"{getattr(settings, 'SITE_URL', '')}/competitions/dashboard/"

            elif action == 'rejected':
                subject = f"[MartialComp] Demande de rôle {role_display} refusée"
                template_name = 'role_assignment_rejected'
                context.update({
                    'rejection_reason': membership.rejection_reason or "Aucun motif spécifié",
                    'rejected_at': membership.approved_at or timezone.now(),
                })

            else:
                logger.warning(f"Action email inconnue: {action}")
                return False

            return NotificationService.send_email(user, subject, template_name, context)

        except Exception as e:
            logger.error(f"Erreur email rôle pour membership #{membership.id}: {e}", exc_info=True)
            return False

    @staticmethod
    def send_admin_pending_approval_email(membership, admin_users):
        """
        Envoie un email aux administrateurs pour une demande de rôle en attente.

        Args:
            membership: Instance de OrganizationMember
            admin_users: Liste d'utilisateurs administrateurs

        Returns:
            int: Nombre d'emails envoyés
        """
        try:
            sent_count = 0
            applicant = membership.user
            org_name = membership.organization.name if membership.organization else "l'organisation"
            role_display = membership.get_role_display() if hasattr(membership, 'get_role_display') else membership.role

            # URL vers la page d'approbation
            try:
                action_url = reverse('competitions:pending_role_approvals')
                full_action_url = f"{getattr(settings, 'SITE_URL', '')}{action_url}"
            except:
                full_action_url = f"{getattr(settings, 'SITE_URL', '')}/competitions/roles/pending-approvals/"

            # Pratiquant associé si disponible
            practitioner = None
            if hasattr(membership, 'practitioner') and membership.practitioner:
                practitioner = membership.practitioner

            subject = f"[MartialComp] Nouvelle demande de rôle à valider - {org_name}"

            for admin_user in admin_users:
                try:
                    context = {
                        'admin_user': admin_user,
                        'applicant': applicant,
                        'practitioner': practitioner,
                        'organization_name': org_name,
                        'role_display': role_display,
                        'created_at': membership.created_at if hasattr(membership, 'created_at') else timezone.now(),
                        'action_url': full_action_url,
                    }

                    if NotificationService.send_email(admin_user, subject, 'admin_pending_approval', context):
                        sent_count += 1

                except Exception as e:
                    logger.warning(f"Erreur email admin {admin_user.username}: {e}")

            logger.info(f"{sent_count} emails admin envoyés pour membership #{membership.id}")
            return sent_count

        except Exception as e:
            logger.error(f"Erreur emails admin pour membership #{membership.id}: {e}", exc_info=True)
            return 0

    @staticmethod
    def send_judge_assignment_email(judge_assignment):
        """
        Envoie un email pour une assignation de juge.

        Args:
            judge_assignment: Instance de JudgeAssignment

        Returns:
            bool: True si l'email a été envoyé
        """
        try:
            if not judge_assignment.judge:
                return False

            competition_name = (
                judge_assignment.competition.title
                if hasattr(judge_assignment.competition, 'title')
                else str(judge_assignment.competition)
            )
            category_name = (
                judge_assignment.category.name
                if judge_assignment.category
                else "Compétition générale"
            )
            role_display = (
                judge_assignment.get_role_display()
                if hasattr(judge_assignment, 'get_role_display')
                else judge_assignment.role
            )

            # URL vers l'interface de notation
            try:
                if judge_assignment.category:
                    action_url = reverse('competitions:management:judge_scoring_interface', kwargs={
                        'competition_id': judge_assignment.competition.id,
                        'category_id': judge_assignment.category.id,
                        'judge_id': judge_assignment.judge.id,
                    })
                else:
                    action_url = reverse('competitions:management:scoring_dashboard', kwargs={
                        'competition_id': judge_assignment.competition.id,
                    })
                full_action_url = f"{getattr(settings, 'SITE_URL', '')}{action_url}"
            except:
                full_action_url = f"{getattr(settings, 'SITE_URL', '')}/competitions/dashboard/"

            context = {
                'judge': judge_assignment.judge,
                'competition_name': competition_name,
                'category_name': category_name,
                'role_display': role_display,
                'start_time': judge_assignment.start_time,
                'action_url': full_action_url,
            }

            subject = f"[MartialComp] Assignation comme juge - {competition_name}"
            return NotificationService.send_email(judge_assignment.judge, subject, 'judge_assignment', context)

        except Exception as e:
            logger.error(f"Erreur email assignation juge #{judge_assignment.id}: {e}", exc_info=True)
            return False
