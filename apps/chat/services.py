"""
PROMPT 11 - Services du système de Chat MartialComp

Services métier pour la gestion des conversations et messages.
"""

from django.db import transaction
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import get_user_model
from typing import Optional, List, Tuple
import logging

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageReadStatus,
    UserChatSettings,
    MessageReaction,
)

User = get_user_model()
logger = logging.getLogger(__name__)


class ConversationService:
    """
    PROMPT 11 - Service de gestion des conversations.

    Gère la création, modification et récupération des conversations.
    """

    @classmethod
    @transaction.atomic
    def create_direct_conversation(cls, user1: User, user2: User) -> Tuple[Conversation, bool]:
        """
        Crée ou récupère une conversation directe entre deux utilisateurs.

        Args:
            user1: Premier utilisateur
            user2: Deuxième utilisateur

        Returns:
            Tuple (Conversation, created: bool)
        """
        if user1 == user2:
            raise ValidationError("Impossible de créer une conversation avec soi-même.")

        # Vérifier si une conversation existe déjà
        existing = Conversation.objects.filter(
            type=Conversation.ConversationType.DIRECT,
            participants__user=user1
        ).filter(
            participants__user=user2
        ).first()

        if existing:
            return existing, False

        # Créer la nouvelle conversation
        conversation = Conversation.objects.create(
            type=Conversation.ConversationType.DIRECT,
            created_by=user1
        )

        # Ajouter les participants
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=user1,
            role=ConversationParticipant.Role.MEMBER
        )
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=user2,
            role=ConversationParticipant.Role.MEMBER
        )

        logger.info(f"Conversation directe créée entre {user1} et {user2}")
        return conversation, True

    @classmethod
    @transaction.atomic
    def create_group_conversation(
        cls,
        name: str,
        creator: User,
        members: List[User],
        description: str = ""
    ) -> Conversation:
        """
        Crée une conversation de groupe.

        Args:
            name: Nom du groupe
            creator: Utilisateur créateur (sera admin)
            members: Liste des membres à ajouter
            description: Description optionnelle

        Returns:
            Conversation créée
        """
        if not name:
            raise ValidationError("Le nom du groupe est requis.")

        if len(members) < 1:
            raise ValidationError("Au moins un membre est requis.")

        conversation = Conversation.objects.create(
            type=Conversation.ConversationType.GROUP,
            name=name,
            description=description,
            created_by=creator
        )

        # Ajouter le créateur comme admin
        ConversationParticipant.objects.create(
            conversation=conversation,
            user=creator,
            role=ConversationParticipant.Role.ADMIN
        )

        # Ajouter les autres membres
        for member in members:
            if member != creator:
                ConversationParticipant.objects.create(
                    conversation=conversation,
                    user=member,
                    role=ConversationParticipant.Role.MEMBER
                )

        # Message système d'annonce
        MessageService.send_system_message(
            conversation,
            f"{creator.get_full_name() or creator.username} a créé le groupe \"{name}\""
        )

        logger.info(f"Groupe '{name}' créé par {creator} avec {len(members)} membres")
        return conversation

    @classmethod
    @transaction.atomic
    def get_or_create_club_conversation(cls, club) -> Tuple[Conversation, bool]:
        """
        Récupère ou crée la conversation principale d'un club.

        Args:
            club: Instance du club

        Returns:
            Tuple (Conversation, created: bool)
        """
        existing = Conversation.objects.filter(
            type=Conversation.ConversationType.CLUB,
            club=club
        ).first()

        if existing:
            return existing, False

        conversation = Conversation.objects.create(
            type=Conversation.ConversationType.CLUB,
            club=club,
            name=f"Chat {club.name}",
            description=f"Conversation générale du club {club.name}",
            allow_replies=True
        )

        # Ajouter tous les membres du club
        # Note: Adapté selon votre modèle de membres de club
        try:
            from apps.competitions.models import ClubMember
            members = ClubMember.objects.filter(club=club, is_active=True)
            for member in members:
                if hasattr(member, 'user') and member.user:
                    role = ConversationParticipant.Role.ADMIN if member.is_admin else ConversationParticipant.Role.MEMBER
                    ConversationParticipant.objects.get_or_create(
                        conversation=conversation,
                        user=member.user,
                        defaults={'role': role}
                    )
        except Exception as e:
            logger.warning(f"Erreur lors de l'ajout des membres du club: {e}")

        logger.info(f"Conversation de club créée pour {club.name}")
        return conversation, True

    @classmethod
    @transaction.atomic
    def get_or_create_competition_conversation(cls, competition) -> Tuple[Conversation, bool]:
        """
        Récupère ou crée la conversation d'une compétition.

        Args:
            competition: Instance de la compétition

        Returns:
            Tuple (Conversation, created: bool)
        """
        existing = Conversation.objects.filter(
            type=Conversation.ConversationType.COMPETITION,
            competition=competition
        ).first()

        if existing:
            return existing, False

        conversation = Conversation.objects.create(
            type=Conversation.ConversationType.COMPETITION,
            competition=competition,
            name=f"Chat {competition.title}",
            description=f"Discussions autour de la compétition {competition.title}",
            allow_replies=True
        )

        logger.info(f"Conversation de compétition créée pour {competition.title}")
        return conversation, True

    @classmethod
    def add_participant(
        cls,
        conversation: Conversation,
        user: User,
        added_by: User,
        role: str = ConversationParticipant.Role.MEMBER
    ) -> ConversationParticipant:
        """
        Ajoute un participant à une conversation.

        Args:
            conversation: Conversation cible
            user: Utilisateur à ajouter
            added_by: Utilisateur qui ajoute
            role: Rôle du nouveau participant

        Returns:
            ConversationParticipant créé
        """
        # Vérifier les permissions
        if conversation.type == Conversation.ConversationType.DIRECT:
            raise PermissionDenied("Impossible d'ajouter des membres à une conversation directe.")

        # Vérifier que added_by est admin ou modérateur
        try:
            adder_participant = conversation.participants.get(user=added_by, left_at__isnull=True)
            if not adder_participant.is_moderator:
                raise PermissionDenied("Seuls les modérateurs peuvent ajouter des membres.")
        except ConversationParticipant.DoesNotExist:
            raise PermissionDenied("Vous n'êtes pas membre de cette conversation.")

        # Créer ou réactiver le participant
        participant, created = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=user,
            defaults={'role': role}
        )

        if not created and participant.left_at:
            # Réactiver un ancien membre
            participant.left_at = None
            participant.role = role
            participant.save(update_fields=['left_at', 'role'])

        # Message système
        MessageService.send_system_message(
            conversation,
            f"{user.get_full_name() or user.username} a rejoint la conversation"
        )

        return participant

    @classmethod
    def remove_participant(
        cls,
        conversation: Conversation,
        user: User,
        removed_by: User
    ) -> bool:
        """
        Retire un participant d'une conversation.

        Args:
            conversation: Conversation cible
            user: Utilisateur à retirer
            removed_by: Utilisateur qui retire

        Returns:
            True si retiré avec succès
        """
        if conversation.type == Conversation.ConversationType.DIRECT:
            raise PermissionDenied("Impossible de quitter une conversation directe.")

        # Un utilisateur peut se retirer lui-même
        if user != removed_by:
            # Sinon, vérifier les permissions
            try:
                remover_participant = conversation.participants.get(user=removed_by, left_at__isnull=True)
                if not remover_participant.is_admin:
                    raise PermissionDenied("Seuls les admins peuvent retirer des membres.")
            except ConversationParticipant.DoesNotExist:
                raise PermissionDenied("Vous n'êtes pas membre de cette conversation.")

        try:
            participant = conversation.participants.get(user=user, left_at__isnull=True)
            participant.leave()

            # Message système
            if user == removed_by:
                message = f"{user.get_full_name() or user.username} a quitté la conversation"
            else:
                message = f"{user.get_full_name() or user.username} a été retiré par {removed_by.get_full_name() or removed_by.username}"

            MessageService.send_system_message(conversation, message)
            return True

        except ConversationParticipant.DoesNotExist:
            return False

    @classmethod
    def get_user_conversations(cls, user: User, include_left: bool = False):
        """
        Récupère toutes les conversations d'un utilisateur.

        Args:
            user: Utilisateur
            include_left: Inclure les conversations quittées

        Returns:
            QuerySet de Conversation
        """
        queryset = Conversation.objects.filter(
            participants__user=user,
            is_active=True
        )

        if not include_left:
            queryset = queryset.filter(participants__left_at__isnull=True)

        return queryset.prefetch_related(
            Prefetch(
                'participants',
                queryset=ConversationParticipant.objects.select_related('user')
            ),
            Prefetch(
                'messages',
                queryset=Message.objects.filter(is_deleted=False).order_by('-created_at')[:1]
            )
        ).annotate(
            unread_count=Count(
                'messages',
                filter=Q(
                    messages__created_at__gt=models.F('participants__last_read_at'),
                    messages__is_deleted=False
                ) & ~Q(messages__sender=user)
            )
        ).order_by('-last_message_at', '-created_at')

    @classmethod
    def search_conversations(cls, user: User, query: str):
        """
        Recherche dans les conversations d'un utilisateur.

        Args:
            user: Utilisateur
            query: Terme de recherche

        Returns:
            QuerySet de Conversation
        """
        return cls.get_user_conversations(user).filter(
            Q(name__icontains=query) |
            Q(messages__content__icontains=query) |
            Q(participants__user__first_name__icontains=query) |
            Q(participants__user__last_name__icontains=query) |
            Q(participants__user__username__icontains=query)
        ).distinct()


class MessageService:
    """
    PROMPT 11 - Service de gestion des messages.

    Gère l'envoi, la lecture et la suppression des messages.
    """

    @classmethod
    @transaction.atomic
    def send_message(
        cls,
        conversation: Conversation,
        sender: User,
        content: str,
        reply_to: Optional[Message] = None,
        attachments: Optional[List[dict]] = None
    ) -> Message:
        """
        Envoie un message dans une conversation.

        Args:
            conversation: Conversation cible
            sender: Expéditeur
            content: Contenu du message
            reply_to: Message auquel répondre (optionnel)
            attachments: Liste de pièces jointes (optionnel)

        Returns:
            Message créé
        """
        # Vérifier que l'utilisateur est participant actif
        try:
            participant = conversation.participants.get(user=sender, left_at__isnull=True)
        except ConversationParticipant.DoesNotExist:
            raise PermissionDenied("Vous n'êtes pas membre de cette conversation.")

        # Vérifier les permissions de réponse
        if not conversation.allow_replies and not participant.is_moderator:
            raise PermissionDenied("Seuls les modérateurs peuvent envoyer des messages.")

        # Créer le message
        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=content,
            reply_to=reply_to,
            message_type=Message.MessageType.TEXT
        )

        # Traiter les pièces jointes
        if attachments:
            for attachment_data in attachments:
                MessageAttachment.objects.create(
                    message=message,
                    **attachment_data
                )
                if 'file_type' in attachment_data and attachment_data['file_type'] == 'image':
                    message.message_type = Message.MessageType.IMAGE
                else:
                    message.message_type = Message.MessageType.FILE
                message.save(update_fields=['message_type'])

        # Marquer automatiquement comme lu pour l'expéditeur
        participant.mark_as_read()

        logger.debug(f"Message envoyé dans conversation {conversation.id} par {sender}")
        return message

    @classmethod
    def send_system_message(cls, conversation: Conversation, content: str) -> Message:
        """
        Envoie un message système (sans expéditeur).

        Args:
            conversation: Conversation cible
            content: Contenu du message

        Returns:
            Message système créé
        """
        return Message.objects.create(
            conversation=conversation,
            sender=None,
            content=content,
            message_type=Message.MessageType.SYSTEM
        )

    @classmethod
    def mark_as_read(cls, message: Message, user: User) -> bool:
        """
        Marque un message comme lu par un utilisateur.

        Args:
            message: Message à marquer
            user: Utilisateur

        Returns:
            True si marqué avec succès
        """
        if message.sender == user:
            return False  # Pas besoin de marquer ses propres messages

        _, created = MessageReadStatus.objects.get_or_create(
            message=message,
            user=user
        )

        return created

    @classmethod
    def mark_conversation_read(cls, conversation: Conversation, user: User) -> int:
        """
        Marque tous les messages d'une conversation comme lus.

        Args:
            conversation: Conversation
            user: Utilisateur

        Returns:
            Nombre de messages marqués comme lus
        """
        try:
            participant = conversation.participants.get(user=user)
            participant.mark_as_read()

            # Marquer les messages individuellement pour les indicateurs "lu"
            unread_messages = conversation.messages.filter(
                is_deleted=False
            ).exclude(
                sender=user
            ).exclude(
                read_statuses__user=user
            )

            count = 0
            for message in unread_messages:
                MessageReadStatus.objects.get_or_create(message=message, user=user)
                count += 1

            return count

        except ConversationParticipant.DoesNotExist:
            return 0

    @classmethod
    def get_unread_count(cls, user: User) -> int:
        """
        Compte le total des messages non lus pour un utilisateur.

        Args:
            user: Utilisateur

        Returns:
            Nombre de messages non lus
        """
        participations = ConversationParticipant.objects.filter(
            user=user,
            left_at__isnull=True,
            is_muted=False
        )

        total = 0
        for participation in participations:
            if participation.last_read_at:
                count = participation.conversation.messages.filter(
                    created_at__gt=participation.last_read_at,
                    is_deleted=False
                ).exclude(sender=user).count()
            else:
                count = participation.conversation.messages.filter(
                    is_deleted=False
                ).exclude(sender=user).count()
            total += count

        return total

    @classmethod
    def delete_message(cls, message: Message, user: User) -> bool:
        """
        Supprime un message (soft delete).

        Args:
            message: Message à supprimer
            user: Utilisateur qui supprime

        Returns:
            True si supprimé avec succès
        """
        # Seul l'expéditeur ou un admin peut supprimer
        if message.sender != user:
            try:
                participant = message.conversation.participants.get(user=user, left_at__isnull=True)
                if not participant.is_admin:
                    raise PermissionDenied("Vous ne pouvez pas supprimer ce message.")
            except ConversationParticipant.DoesNotExist:
                raise PermissionDenied("Vous n'êtes pas membre de cette conversation.")

        message.soft_delete(user)
        return True

    @classmethod
    def edit_message(cls, message: Message, user: User, new_content: str) -> Message:
        """
        Modifie un message existant.

        Args:
            message: Message à modifier
            user: Utilisateur qui modifie
            new_content: Nouveau contenu

        Returns:
            Message modifié
        """
        if message.sender != user:
            raise PermissionDenied("Vous ne pouvez modifier que vos propres messages.")

        if not message.can_be_edited:
            raise ValidationError("Ce message ne peut plus être modifié.")

        message.content = new_content
        message.mark_as_edited()

        return message

    @classmethod
    def add_reaction(cls, message: Message, user: User, emoji: str) -> MessageReaction:
        """
        Ajoute une réaction à un message.

        Args:
            message: Message cible
            user: Utilisateur
            emoji: Emoji de réaction

        Returns:
            MessageReaction créée
        """
        # Vérifier que l'utilisateur est dans la conversation
        if not message.conversation.participants.filter(user=user, left_at__isnull=True).exists():
            raise PermissionDenied("Vous n'êtes pas membre de cette conversation.")

        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=user,
            emoji=emoji
        )

        return reaction

    @classmethod
    def remove_reaction(cls, message: Message, user: User, emoji: str) -> bool:
        """
        Retire une réaction d'un message.

        Args:
            message: Message cible
            user: Utilisateur
            emoji: Emoji à retirer

        Returns:
            True si retiré avec succès
        """
        deleted, _ = MessageReaction.objects.filter(
            message=message,
            user=user,
            emoji=emoji
        ).delete()

        return deleted > 0

    @classmethod
    def get_conversation_messages(
        cls,
        conversation: Conversation,
        user: User,
        limit: int = 50,
        before_id: Optional[int] = None
    ):
        """
        Récupère les messages d'une conversation avec pagination.

        Args:
            conversation: Conversation
            user: Utilisateur qui demande
            limit: Nombre maximum de messages
            before_id: ID du message avant lequel charger (pagination)

        Returns:
            QuerySet de Message
        """
        # Vérifier l'accès
        if not conversation.participants.filter(user=user).exists():
            raise PermissionDenied("Vous n'avez pas accès à cette conversation.")

        queryset = conversation.messages.filter(
            is_deleted=False
        ).select_related(
            'sender', 'reply_to', 'reply_to__sender'
        ).prefetch_related(
            'attachments',
            'reactions',
            'read_statuses'
        )

        if before_id:
            queryset = queryset.filter(id__lt=before_id)

        return queryset.order_by('-created_at')[:limit]


class ChatSettingsService:
    """
    PROMPT 11 - Service de gestion des paramètres utilisateur.
    """

    @classmethod
    def get_or_create_settings(cls, user: User) -> UserChatSettings:
        """
        Récupère ou crée les paramètres de chat d'un utilisateur.

        Args:
            user: Utilisateur

        Returns:
            UserChatSettings
        """
        settings, _ = UserChatSettings.objects.get_or_create(user=user)
        return settings

    @classmethod
    def update_settings(cls, user: User, **kwargs) -> UserChatSettings:
        """
        Met à jour les paramètres de chat d'un utilisateur.

        Args:
            user: Utilisateur
            **kwargs: Paramètres à mettre à jour

        Returns:
            UserChatSettings mis à jour
        """
        settings = cls.get_or_create_settings(user)

        valid_fields = [
            'notifications_enabled', 'email_notifications', 'push_notifications',
            'sound_enabled', 'theme', 'show_read_receipts',
            'show_typing_indicator', 'show_online_status'
        ]

        for key, value in kwargs.items():
            if key in valid_fields:
                setattr(settings, key, value)

        settings.save()
        return settings

    @classmethod
    def update_last_seen(cls, user: User):
        """
        Met à jour le timestamp de dernière activité.

        Args:
            user: Utilisateur
        """
        settings = cls.get_or_create_settings(user)
        settings.update_last_seen()


# Import pour les annotations
from django.db import models
