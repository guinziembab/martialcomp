# -*- coding: utf-8 -*-
"""
Services pour le système d'adhésion MartialComp v2.0
Logique métier et workflows automatisés
"""

from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.translation import gettext as _
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    MembershipPackage, MembershipSubscription, MembershipWorkflow,
    OnlineMembershipForm, MembershipFormSubmission, MembershipAlert
)
from apps.competitions.models import Organization, Practitioner

logger = logging.getLogger(__name__)


class MembershipService:
    """
    Service principal pour la gestion des adhésions
    """

    @staticmethod
    def create_subscription(
        practitioner: Practitioner,
        package: MembershipPackage,
        start_date: datetime = None,
        created_by: User = None,
        custom_price: Decimal = None,
        notes: str = ""
    ) -> MembershipSubscription:
        """
        Crée une nouvelle souscription d'adhésion
        """
        if not start_date:
            start_date = timezone.now().date()
        
        end_date = package.calculate_next_renewal_date(start_date)
        price = custom_price or package.base_price
        
        with transaction.atomic():
            # Suspendre les anciennes souscriptions actives
            MembershipSubscription.objects.filter(
                practitioner=practitioner,
                status='active'
            ).update(status='suspended')
            
            # Créer la nouvelle souscription
            subscription = MembershipSubscription.objects.create(
                practitioner=practitioner,
                package=package,
                start_date=start_date,
                end_date=end_date,
                renewal_date=end_date,
                status='active',
                price_paid=price,
                currency=package.currency,
                notes=notes,
                created_by=created_by
            )
            
            # Déclencher les workflows
            MembershipService._trigger_workflows('new_subscription', subscription)
            
            logger.info(f"Nouvelle souscription créée: {subscription}")
            return subscription

    @staticmethod
    def renew_subscription(
        subscription: MembershipSubscription,
        renewed_by: User = None,
        custom_price: Decimal = None
    ) -> MembershipSubscription:
        """
        Renouvelle une souscription existante
        """
        with transaction.atomic():
            old_end_date = subscription.end_date
            new_end_date = subscription.package.calculate_next_renewal_date(old_end_date)
            price = custom_price or subscription.package.base_price
            
            # Mettre à jour la souscription
            subscription.end_date = new_end_date
            subscription.renewal_date = new_end_date
            subscription.status = 'active'
            subscription.price_paid = price
            subscription.updated_at = timezone.now()
            subscription.save()
            
            # Déclencher les workflows
            MembershipService._trigger_workflows('renewal_completed', subscription)
            
            logger.info(f"Souscription renouvelée: {subscription}")
            return subscription

    @staticmethod
    def process_form_submission(
        submission: MembershipFormSubmission,
        processed_by: User
    ) -> Optional[MembershipSubscription]:
        """
        Traite une soumission de formulaire d'adhésion
        """
        with transaction.atomic():
            try:
                # Vérifier si un pratiquant existe déjà
                practitioner = MembershipService._get_or_create_practitioner(
                    submission.email,
                    submission.first_name,
                    submission.last_name,
                    submission.date_of_birth,
                    submission.form.organization
                )
                
                # Créer la souscription
                subscription = MembershipService.create_subscription(
                    practitioner=practitioner,
                    package=submission.selected_package,
                    created_by=processed_by,
                    notes=f"Créé depuis le formulaire: {submission.form.name}"
                )
                
                # Mettre à jour la soumission
                submission.status = 'completed'
                submission.processed_by = processed_by
                submission.created_subscription = subscription
                submission.processing_notes = "Souscription créée avec succès"
                submission.save()
                
                logger.info(f"Soumission traitée avec succès: {submission}")
                return subscription
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement de la soumission {submission}: {e}")
                submission.status = 'rejected'
                submission.processed_by = processed_by
                submission.processing_notes = f"Erreur: {str(e)}"
                submission.save()
                raise

    @staticmethod
    def check_expiring_subscriptions(days_ahead: int = 14) -> List[MembershipSubscription]:
        """
        Vérifie les souscriptions qui expirent dans les jours à venir
        """
        expiry_date = timezone.now().date() + timedelta(days=days_ahead)
        
        expiring_subscriptions = MembershipSubscription.objects.filter(
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=timezone.now().date()
        ).select_related('practitioner', 'package')
        
        for subscription in expiring_subscriptions:
            MembershipService._trigger_workflows('expiry_warning', subscription)
            
            # Créer une alerte si elle n'existe pas déjà
            MembershipAlert.objects.get_or_create(
                subscription=subscription,
                alert_type='expiry_warning',
                defaults={
                    'title': _('Adhésion bientôt expirée'),
                    'message': _(
                        'L\'adhésion de {} expire le {}.'
                    ).format(
                        subscription.practitioner.get_full_name(),
                        subscription.end_date.strftime('%d/%m/%Y')
                    ),
                    'priority': 'high'
                }
            )
        
        return list(expiring_subscriptions)

    @staticmethod
    def auto_renew_eligible_subscriptions() -> List[MembershipSubscription]:
        """
        Renouvelle automatiquement les souscriptions éligibles
        """
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        eligible_subscriptions = MembershipSubscription.objects.filter(
            status='active',
            auto_renew=True,
            package__auto_renewal=True,
            end_date=tomorrow
        ).select_related('practitioner', 'package')
        
        renewed_subscriptions = []
        for subscription in eligible_subscriptions:
            try:
                renewed = MembershipService.renew_subscription(subscription)
                renewed_subscriptions.append(renewed)
                logger.info(f"Auto-renouvellement réussi: {subscription}")
            except Exception as e:
                logger.error(f"Échec auto-renouvellement {subscription}: {e}")
                MembershipAlert.objects.create(
                    subscription=subscription,
                    alert_type='renewal_reminder',
                    title=_('Échec du renouvellement automatique'),
                    message=_('Le renouvellement automatique a échoué: {}').format(str(e)),
                    priority='urgent'
                )
        
        return renewed_subscriptions

    @staticmethod
    def get_membership_stats(organization: Organization) -> Dict:
        """
        Retourne les statistiques d'adhésion pour une organisation
        """
        today = timezone.now().date()
        
        # Souscriptions actives
        active_subscriptions = MembershipSubscription.objects.filter(
            package__organization=organization,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        )
        
        # Statistiques de base
        stats = {
            'total_active': active_subscriptions.count(),
            'total_packages': MembershipPackage.objects.filter(
                organization=organization, is_active=True
            ).count(),
            'expiring_soon': active_subscriptions.filter(
                end_date__lte=today + timedelta(days=30)
            ).count(),
            'revenue_this_month': 0,
            'new_this_month': 0,
            'renewal_rate': 0
        }
        
        # Revenus du mois
        month_start = today.replace(day=1)
        monthly_subscriptions = MembershipSubscription.objects.filter(
            package__organization=organization,
            created_at__gte=month_start
        )
        
        stats['revenue_this_month'] = float(
            sum(sub.price_paid for sub in monthly_subscriptions)
        )
        stats['new_this_month'] = monthly_subscriptions.count()
        
        # Répartition par package
        package_stats = {}
        for subscription in active_subscriptions:
            package_name = subscription.package.name
            if package_name not in package_stats:
                package_stats[package_name] = 0
            package_stats[package_name] += 1
        
        stats['package_distribution'] = package_stats
        
        return stats

    @staticmethod
    def _get_or_create_practitioner(
        email: str,
        first_name: str,
        last_name: str,
        date_of_birth: datetime,
        organization: Organization
    ) -> Practitioner:
        """
        Récupère ou crée un pratiquant
        """
        # Essayer de trouver un utilisateur existant
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Créer un nouvel utilisateur
            username = f"{first_name.lower()}.{last_name.lower()}"
            # S'assurer que le nom d'utilisateur est unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
        
        # Récupérer ou créer le pratiquant
        practitioner, created = Practitioner.objects.get_or_create(
            user=user,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': date_of_birth,
                'organization': organization
            }
        )
        
        return practitioner

    @staticmethod
    def _trigger_workflows(trigger_type: str, subscription: MembershipSubscription):
        """
        Déclenche les workflows applicables
        """
        workflows = MembershipWorkflow.objects.filter(
            organization=subscription.package.organization,
            trigger_type=trigger_type,
            is_active=True
        )
        
        for workflow in workflows:
            # Vérifier si le workflow s'applique à ce package
            if (workflow.applicable_packages.exists() and 
                subscription.package not in workflow.applicable_packages.all()):
                continue
            
            try:
                MembershipService._execute_workflow_action(workflow, subscription)
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution du workflow {workflow}: {e}")

    @staticmethod
    def _execute_workflow_action(
        workflow: MembershipWorkflow, 
        subscription: MembershipSubscription
    ):
        """
        Exécute l'action d'un workflow
        """
        action_type = workflow.action_type
        action_content = workflow.action_content
        
        if action_type == 'send_email':
            MembershipService._send_workflow_email(workflow, subscription, action_content)
        elif action_type == 'create_notification':
            MembershipService._create_workflow_notification(workflow, subscription, action_content)
        elif action_type == 'suspend_membership':
            subscription.status = 'suspended'
            subscription.save()
        elif action_type == 'create_task':
            MembershipService._create_workflow_task(workflow, subscription, action_content)
        
        logger.info(f"Action de workflow exécutée: {workflow.name} pour {subscription}")

    @staticmethod
    def _send_workflow_email(
        workflow: MembershipWorkflow,
        subscription: MembershipSubscription,
        config: Dict
    ):
        """
        Envoie un email via workflow
        """
        subject = config.get('subject', f'Information sur votre adhésion')
        template = config.get('template', 'membership/emails/default.html')
        
        context = {
            'subscription': subscription,
            'practitioner': subscription.practitioner,
            'package': subscription.package,
            'organization': subscription.package.organization
        }
        
        try:
            message = render_to_string(template, context)
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[subscription.practitioner.user.email],
                html_message=message
            )
        except Exception as e:
            logger.error(f"Erreur envoi email workflow: {e}")

    @staticmethod
    def _create_workflow_notification(
        workflow: MembershipWorkflow,
        subscription: MembershipSubscription,
        config: Dict
    ):
        """
        Crée une notification via workflow
        """
        title = config.get('title', 'Notification adhésion')
        message = config.get('message', 'Notification concernant votre adhésion')
        
        # Créer une alerte
        MembershipAlert.objects.create(
            subscription=subscription,
            alert_type='package_upgrade',  # Type par défaut
            title=title,
            message=message,
            priority=config.get('priority', 'medium')
        )

    @staticmethod
    def _create_workflow_task(
        workflow: MembershipWorkflow,
        subscription: MembershipSubscription,
        config: Dict
    ):
        """
        Crée une tâche via workflow (si module task_management disponible)
        """
        try:
            from apps.task_management.models import Task, Board
            
            board_name = config.get('board', 'Adhésions')
            board, created = Board.objects.get_or_create(
                name=board_name,
                organization=subscription.package.organization
            )
            
            Task.objects.create(
                title=config.get('title', f'Adhésion - {subscription.practitioner}'),
                description=config.get('description', ''),
                board=board,
                created_by=subscription.created_by,
                priority=config.get('priority', 'medium')
            )
        except ImportError:
            logger.warning("Module task_management non disponible pour créer une tâche")


class MembershipAnalyticsService:
    """
    Service d'analyse des données d'adhésion
    """

    @staticmethod
    def get_retention_rate(organization: Organization, period_months: int = 12) -> Dict:
        """
        Calcule le taux de rétention des adhérents
        """
        cutoff_date = timezone.now().date() - timedelta(days=period_months * 30)
        
        # Souscriptions créées dans la période
        subscriptions = MembershipSubscription.objects.filter(
            package__organization=organization,
            created_at__gte=cutoff_date
        )
        
        total = subscriptions.count()
        if total == 0:
            return {'retention_rate': 0, 'total_analyzed': 0}
        
        # Souscriptions qui ont été renouvelées ou sont encore actives
        retained = subscriptions.filter(
            models.Q(status='active') | 
            models.Q(membershipsubscription__status='active', created_at__gt=models.F('end_date'))
        ).count()
        
        return {
            'retention_rate': (retained / total) * 100,
            'total_analyzed': total,
            'retained': retained
        }

    @staticmethod
    def get_popular_packages(organization: Organization) -> List[Dict]:
        """
        Retourne les packages les plus populaires
        """
        from django.db.models import Count
        
        packages = MembershipPackage.objects.filter(
            organization=organization
        ).annotate(
            subscription_count=Count('subscriptions')
        ).order_by('-subscription_count')[:10]
        
        return [
            {
                'name': package.name,
                'subscription_count': package.subscription_count,
                'category': package.get_category_display(),
                'price': float(package.base_price)
            }
            for package in packages
        ]

    @staticmethod
    def get_revenue_trend(
        organization: Organization,
        months: int = 12
    ) -> List[Dict]:
        """
        Analyse de tendance des revenus
        """
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth
        
        start_date = timezone.now().date() - timedelta(days=months * 30)
        
        revenue_by_month = MembershipSubscription.objects.filter(
            package__organization=organization,
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total_revenue=Sum('price_paid'),
            subscription_count=Count('id')
        ).order_by('month')
        
        return [
            {
                'month': item['month'].strftime('%Y-%m'),
                'revenue': float(item['total_revenue'] or 0),
                'subscriptions': item['subscription_count']
            }
            for item in revenue_by_month
        ]