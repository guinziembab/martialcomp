"""
PROMPT 11 - Signaux du système de Chat MartialComp

Gestion des actions automatiques lors d'événements.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

from .models import (
    Message,
    Conversation,
    ConversationParticipant,
    UserChatSettings,
)

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_chat_settings(sender, instance, created, **kwargs):
    """
    Crée automatiquement les paramètres de chat lors de la création d'un utilisateur.
    """
    if created:
        UserChatSettings.objects.get_or_create(user=instance)
        logger.debug(f"Chat settings créés pour {instance.username}")


@receiver(post_save, sender=Message)
def update_conversation_on_message(sender, instance, created, **kwargs):
    """
    Met à jour la conversation après l'envoi d'un message.
    """
    if created and not instance.is_deleted:
        # La mise à jour est déjà faite dans Message.save()
        # Ici on peut ajouter d'autres actions (notifications, etc.)
        pass


@receiver(post_delete, sender=ConversationParticipant)
def handle_participant_removal(sender, instance, **kwargs):
    """
    Gère les actions après le retrait d'un participant.
    """
    conversation = instance.conversation

    # Si c'était une conversation directe et qu'il ne reste plus qu'un participant,
    # désactiver la conversation
    if conversation.type == Conversation.ConversationType.DIRECT:
        remaining = conversation.participants.filter(left_at__isnull=True).count()
        if remaining < 2:
            conversation.is_active = False
            conversation.save(update_fields=['is_active'])
            logger.info(f"Conversation directe {conversation.id} désactivée (moins de 2 participants)")


# Signal personnalisé pour les notifications (à implémenter avec votre système de notifications)
# from django.dispatch import Signal
# message_sent = Signal()  # Paramètres: message, conversation, sender
