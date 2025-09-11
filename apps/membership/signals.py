# -*- coding: utf-8 -*-
"""
Signaux pour le système d'adhésion MartialComp v2.0
Automatisation des workflows et notifications
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import logging

from .models import MembershipSubscription, MembershipAlert, MembershipFormSubmission
from .services import MembershipService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=MembershipSubscription)
def handle_subscription_created(sender, instance, created, **kwargs):
    """
    Actions à effectuer lors de la création d'une souscription
    """
    if created:
        logger.info(f"Nouvelle souscription créée: {instance}")
        
        # Déclencher les workflows de nouvelle souscription
        try:
            MembershipService._trigger_workflows('new_subscription', instance)
        except Exception as e:
            logger.error(f"Erreur lors du déclenchement des workflows: {e}")


@receiver(pre_save, sender=MembershipSubscription)
def handle_subscription_status_change(sender, instance, **kwargs):
    """
    Actions à effectuer lors du changement de statut d'une souscription
    """
    if instance.pk:  # Instance existante
        try:
            old_instance = MembershipSubscription.objects.get(pk=instance.pk)
            
            # Détecter les changements de statut
            if old_instance.status != instance.status:
                logger.info(f"Changement de statut: {old_instance.status} -> {instance.status} pour {instance}")
                
                # Actions spécifiques selon le nouveau statut
                if instance.status == 'expired':
                    MembershipService._trigger_workflows('expiry_warning', instance)
                elif instance.status == 'cancelled':
                    MembershipService._trigger_workflows('cancellation', instance)
                    
        except MembershipSubscription.DoesNotExist:
            pass  # Nouvelle instance


@receiver(post_save, sender=MembershipFormSubmission)
def handle_form_submission_created(sender, instance, created, **kwargs):
    """
    Actions à effectuer lors de la soumission d'un formulaire
    """
    if created:
        logger.info(f"Nouvelle soumission de formulaire: {instance}")
        
        # Créer une notification pour les administrateurs
        try:
            MembershipAlert.objects.create(
                subscription=None,  # Pas encore de souscription associée
                alert_type='package_upgrade',  # Type générique pour les soumissions
                title=f'Nouvelle demande d\'adhésion - {instance.selected_package.name}',
                message=f'{instance.full_name} ({instance.email}) a soumis une demande d\'adhésion pour le package "{instance.selected_package.name}".',
                priority='medium'
            )
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'alerte: {e}")