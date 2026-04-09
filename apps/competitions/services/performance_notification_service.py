"""
Service pour les notifications de performances à venir.
Gère les rappels automatiques pour les juges concernant les performances à noter.
"""

import logging
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse

from .notification_service import NotificationService
from ..models.notifications import Notification, NotificationPreference

logger = logging.getLogger(__name__)
User = get_user_model()


class PerformanceNotificationService:
    """
    Service pour gérer les notifications concernant les performances à venir.
    """

    @staticmethod
    def check_upcoming_performances():
        """
        Vérifie les performances à venir et crée des notifications pour les juges assignés.
        
        Cette méthode doit être appelée périodiquement (tâche cron ou Celery beat).
        Elle crée des notifications pour :
        - Performances dans 1 heure
        - Performances dans 15 minutes
        - Performances en cours
        """
        try:
            from ..models.unified_scoring import Performance
            from ..models.judging import JudgeAssignment
            
            now = timezone.now()
            
            # Définir les intervalles de rappel
            one_hour_later = now + timedelta(hours=1)
            fifteen_minutes_later = now + timedelta(minutes=15)
            
            # Trouver les performances à venir dans les prochaines heures
            upcoming_performances = Performance.objects.filter(
                status=Performance.PENDING,
                start_time__gte=now,
                start_time__lte=one_hour_later
            ).select_related('category', 'competition', 'practitioner')
            
            notifications_created = 0
            
            for performance in upcoming_performances:
                # Récupérer les juges assignés à cette catégorie
                try:
                    # Utiliser JudgeAssignment depuis judging.py
                    from ..models.judging import JudgeAssignment as JudgeAssignmentModel
                    
                    judge_assignments = JudgeAssignmentModel.objects.filter(
                        category=performance.category,
                        status='confirmed'
                    ).select_related('judge')
                    
                    for assignment in judge_assignments:
                        judge = assignment.judge
                        
                        # Vérifier les préférences de rappel
                        prefs, _ = NotificationPreference.objects.get_or_create(
                            user=judge,
                            defaults={
                                'email_enabled': True,
                                'competition_notifications': True,
                            }
                        )
                        
                        if not prefs.competition_notifications:
                            continue
                        
                        # Calculer le temps jusqu'à la performance
                        time_until = performance.start_time - now
                        time_until_minutes = int(time_until.total_seconds() / 60)
                        
                        # Créer des notifications pour différents intervalles
                        notification_created = False
                        
                        # Notification 1 heure avant
                        if 55 <= time_until_minutes <= 65:  # Entre 55 et 65 minutes
                            notification_created = PerformanceNotificationService._create_performance_notification(
                                judge, performance, '1_hour_before', time_until_minutes
                            )
                        
                        # Notification 15 minutes avant
                        elif 10 <= time_until_minutes <= 20:  # Entre 10 et 20 minutes
                            notification_created = PerformanceNotificationService._create_performance_notification(
                                judge, performance, '15_minutes_before', time_until_minutes
                            )
                        
                        # Notification en cours
                        elif performance.start_time <= now <= performance.start_time + timedelta(minutes=5):
                            notification_created = PerformanceNotificationService._create_performance_notification(
                                judge, performance, 'in_progress', 0
                            )
                        
                        if notification_created:
                            notifications_created += 1
                            
                except Exception as e:
                    logger.error(f"Erreur lors de la création de notifications pour performance {performance.id}: {e}")
                    continue
            
            logger.info(f"{notifications_created} notifications de performances créées")
            return notifications_created
            
        except ImportError as e:
            logger.warning(f"Modèles de performance non disponibles: {e}")
            return 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des performances à venir: {e}", exc_info=True)
            return 0

    @staticmethod
    def _create_performance_notification(judge, performance, reminder_type, time_until_minutes):
        """
        Crée une notification pour une performance à venir.
        
        Args:
            judge: Instance de User (juge)
            performance: Instance de Performance
            reminder_type: Type de rappel ('1_hour_before', '15_minutes_before', 'in_progress')
            time_until_minutes: Nombre de minutes jusqu'à la performance
            
        Returns:
            bool: True si la notification a été créée, False sinon
        """
        try:
            # Vérifier si une notification similaire existe déjà
            existing_notification = Notification.objects.filter(
                user=judge,
                title__contains=performance.practitioner.full_name if hasattr(performance, 'practitioner') else 'Performance',
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).first()
            
            if existing_notification:
                # Ne pas créer de doublon
                return False
            
            # Préparer le message selon le type de rappel
            if reminder_type == '1_hour_before':
                title = f"Performance à noter dans 1 heure"
                message = (
                    f"La performance de {performance.practitioner.full_name if hasattr(performance, 'practitioner') else 'un pratiquant'} "
                    f"dans la catégorie {performance.category.name if hasattr(performance, 'category') and performance.category else 'N/A'} "
                    f"commence dans environ 1 heure."
                )
                priority = 'important'
            elif reminder_type == '15_minutes_before':
                title = f"Performance à noter dans {time_until_minutes} minutes"
                message = (
                    f"Performance à noter dans {time_until_minutes} minutes : "
                    f"{performance.practitioner.full_name if hasattr(performance, 'practitioner') else 'un pratiquant'} "
                    f"- {performance.category.name if hasattr(performance, 'category') and performance.category else 'N/A'}"
                )
                priority = 'critical'
            else:  # 'in_progress'
                title = f"Performance en cours de notation"
                message = (
                    f"La performance de {performance.practitioner.full_name if hasattr(performance, 'practitioner') else 'un pratiquant'} "
                    f"est en cours. Veuillez accéder à l'interface de notation."
                )
                priority = 'critical'
            
            # Générer le lien vers l'interface de notation
            try:
                if hasattr(performance, 'category') and performance.category:
                    action_url = reverse('competitions:management:judge_scoring_interface', kwargs={
                        'competition_id': performance.competition.id if hasattr(performance, 'competition') else 0,
                        'category_id': performance.category.id,
                        'judge_id': judge.id,
                    })
                else:
                    action_url = reverse('competitions:management:scoring_dashboard', kwargs={
                        'competition_id': performance.competition.id if hasattr(performance, 'competition') else 0,
                    })
            except Exception as url_error:
                logger.warning(f"Erreur génération URL pour performance {performance.id}: {url_error}")
                action_url = None
            
            # Créer la notification
            notification = Notification.objects.create(
                user=judge,
                title=title,
                message=message,
                notification_type='warning' if reminder_type != 'in_progress' else 'error',
                priority=priority,
                action_url=action_url,
                action_text='Accéder à l\'interface de notation',
            )
            
            # Envoyer via WebSocket si disponible
            try:
                from .notification_service import NotificationService
                NotificationService.send_websocket_notification(judge, notification)
            except Exception as ws_error:
                logger.debug(f"WebSocket non disponible pour notification: {ws_error}")
            
            logger.debug(
                f"Notification de performance créée pour {judge.username} - "
                f"Performance #{performance.id} ({reminder_type})"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de notification de performance: {e}", exc_info=True)
            return False

    @staticmethod
    def check_missed_performances():
        """
        Vérifie les performances manquées (déjà commencées mais pas notées).
        
        Returns:
            int: Nombre de notifications créées
        """
        try:
            from ..models.unified_scoring import Performance
            from ..models.judging import JudgeAssignment
            
            now = timezone.now()
            
            # Performances en cours ou terminées mais pas encore notées
            missed_performances = Performance.objects.filter(
                status__in=[Performance.IN_PROGRESS, Performance.COMPLETED],
                start_time__lt=now,
                start_time__gte=now - timedelta(hours=2)  # Dans les 2 dernières heures
            ).select_related('category', 'competition', 'practitioner')
            
            notifications_created = 0
            
            for performance in missed_performances:
                # Vérifier si le juge a déjà soumis des scores
                # (simplifié - à améliorer selon la structure réelle)
                
                try:
                    from ..models.judging import JudgeAssignment as JudgeAssignmentModel
                    
                    judge_assignments = JudgeAssignmentModel.objects.filter(
                        category=performance.category,
                        status='confirmed'
                    ).select_related('judge')
                    
                    for assignment in judge_assignments:
                        judge = assignment.judge
                        
                        # Vérifier les préférences
                        prefs, _ = NotificationPreference.objects.get_or_create(
                            user=judge,
                            defaults={
                                'competition_notifications': True,
                            }
                        )
                        
                        if not prefs.competition_notifications:
                            continue
                        
                        # Créer notification pour performance manquée
                        notification_created = PerformanceNotificationService._create_missed_performance_notification(
                            judge, performance
                        )
                        
                        if notification_created:
                            notifications_created += 1
                            
                except Exception as e:
                    logger.error(f"Erreur lors de la création de notifications pour performance manquée {performance.id}: {e}")
                    continue
            
            logger.info(f"{notifications_created} notifications de performances manquées créées")
            return notifications_created
            
        except ImportError as e:
            logger.warning(f"Modèles de performance non disponibles: {e}")
            return 0
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des performances manquées: {e}", exc_info=True)
            return 0

    @staticmethod
    def _create_missed_performance_notification(judge, performance):
        """
        Crée une notification pour une performance manquée.
        
        Args:
            judge: Instance de User
            performance: Instance de Performance
            
        Returns:
            bool: True si créée, False sinon
        """
        try:
            # Vérifier si notification existe déjà
            existing = Notification.objects.filter(
                user=judge,
                title__contains='Performance manquée',
                created_at__gte=timezone.now() - timedelta(hours=1)
            ).first()
            
            if existing:
                return False
            
            title = "Performance à noter"
            message = (
                f"La performance de {performance.practitioner.full_name if hasattr(performance, 'practitioner') else 'un pratiquant'} "
                f"dans la catégorie {performance.category.name if hasattr(performance, 'category') and performance.category else 'N/A'} "
                f"n'a pas encore été notée."
            )
            
            # Générer le lien
            try:
                if hasattr(performance, 'category') and performance.category:
                    action_url = reverse('competitions:management:judge_scoring_interface', kwargs={
                        'competition_id': performance.competition.id if hasattr(performance, 'competition') else 0,
                        'category_id': performance.category.id,
                        'judge_id': judge.id,
                    })
                else:
                    action_url = None
            except:
                action_url = None
            
            notification = Notification.objects.create(
                user=judge,
                title=title,
                message=message,
                notification_type='warning',
                priority='important',
                action_url=action_url,
                action_text='Noter maintenant',
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur création notification performance manquée: {e}")
            return False
