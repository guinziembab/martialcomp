from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging

from .models import Family, FamilyMember

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Family)
def create_family_default_data(sender, instance, created, **kwargs):
    """
    Signal déclenché lors de la création d'une famille.
    Ajoute automatiquement le responsable principal comme membre.
    """
    if created:
        try:
            # Ajouter le responsable principal comme membre parent
            FamilyMember.objects.get_or_create(
                family=instance,
                user=instance.primary_responsible,
                defaults={
                    'role': 'parent',
                    'can_manage_others': True,
                    'can_make_payments': True,
                    'is_active': True,
                }
            )
            logger.info(f"Famille '{instance.family_name}' créée avec le responsable {instance.primary_responsible}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des données par défaut pour la famille {instance.id}: {e}")


@receiver(pre_delete, sender=Family)
def handle_family_deletion(sender, instance, **kwargs):
    """
    Signal déclenché avant la suppression d'une famille.
    Log l'événement pour audit.
    """
    logger.warning(f"Suppression de la famille '{instance.family_name}' (ID: {instance.id})")
    

@receiver(post_save, sender=FamilyMember)
def handle_family_member_changes(sender, instance, created, **kwargs):
    """
    Signal déclenché lors de changements sur les membres de famille.
    """
    if created:
        logger.info(f"Nouveau membre ajouté Ã  la famille '{instance.family.family_name}': {instance.get_display_name()} ({instance.get_role_display()})")
    else:
        logger.info(f"Membre modifié dans la famille '{instance.family.family_name}': {instance.get_display_name()}")


@receiver(pre_delete, sender=FamilyMember)
def handle_family_member_deletion(sender, instance, **kwargs):
    """
    Signal déclenché avant la suppression d'un membre de famille.
    """
    # Vérifier qu'on ne supprime pas le responsable principal
    if instance.user == instance.family.primary_responsible:
        logger.warning(f"Tentative de suppression du responsable principal de la famille '{instance.family.family_name}'")
    else:
        logger.info(f"Suppression du membre '{instance.get_display_name()}' de la famille '{instance.family.family_name}'")
