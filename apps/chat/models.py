"""
PROMPT 11 - Modèles du système de Chat MartialComp

Types de conversations supportés:
1. Direct : 2 utilisateurs (message privé)
2. Groupe : N utilisateurs (équipe, entraîneurs)
3. Club : Tous les membres du club (annonces)
4. Compétition : Participants + Organisateurs
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import os
import uuid


def chat_attachment_path(instance, filename):
    """Génère un chemin unique pour les pièces jointes."""
    ext = filename.split('.')[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return f"chat_attachments/{instance.message.conversation.id}/{unique_filename}"


class Conversation(models.Model):
    """
    PROMPT 11 - Modèle principal de conversation.

    Supporte plusieurs types de conversations:
    - direct: Entre 2 utilisateurs uniquement
    - group: Groupe personnalisé avec N membres
    - club: Conversation de club (tous les membres)
    - competition: Conversation liée à une compétition
    """

    class ConversationType(models.TextChoices):
        DIRECT = 'direct', _('Message privé')
        GROUP = 'group', _('Groupe')
        CLUB = 'club', _('Club')
        COMPETITION = 'competition', _('Compétition')

    # Identifiant unique pour les URLs
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("UUID")
    )

    type = models.CharField(
        max_length=20,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT,
        verbose_name=_("Type de conversation")
    )

    name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Nom"),
        help_text=_("Nom du groupe (optionnel pour les conversations directes)")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description du groupe ou de la conversation")
    )

    # Image du groupe
    avatar = models.ImageField(
        upload_to='chat_avatars/',
        blank=True,
        null=True,
        verbose_name=_("Avatar du groupe")
    )

    # Métadonnées
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_conversations_created',
        verbose_name=_("Créé par")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Mis à jour le")
    )

    # Relations optionnelles selon le type
    club = models.ForeignKey(
        'competitions.Club',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name=_("Club associé")
    )

    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name=_("Compétition associée")
    )

    # Cache pour le dernier message (optimisation)
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernier message le")
    )

    last_message_preview = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Aperçu du dernier message")
    )

    # Statut
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    # Paramètres de la conversation
    allow_replies = models.BooleanField(
        default=True,
        verbose_name=_("Autoriser les réponses"),
        help_text=_("Si désactivé, seuls les admins peuvent envoyer des messages")
    )

    class Meta:
        app_label = 'chat'
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['club']),
            models.Index(fields=['competition']),
            models.Index(fields=['-last_message_at']),
        ]

    def __str__(self):
        if self.name:
            return self.name
        if self.type == self.ConversationType.DIRECT:
            participants = self.participants.all()[:2]
            names = [p.user.get_full_name() or p.user.username for p in participants]
            return " & ".join(names) if names else _("Conversation directe")
        if self.type == self.ConversationType.CLUB and self.club:
            return f"{self.club.name} - Chat"
        if self.type == self.ConversationType.COMPETITION and self.competition:
            return f"{self.competition.title} - Chat"
        return f"Conversation #{self.id}"

    def get_display_name(self, for_user=None):
        """Retourne le nom à afficher pour un utilisateur donné."""
        if self.type == self.ConversationType.DIRECT and for_user:
            # Pour une conversation directe, afficher l'autre participant
            other = self.participants.exclude(user=for_user).first()
            if other:
                return other.user.get_full_name() or other.user.username
        return str(self)

    def get_unread_count(self, user):
        """Compte les messages non lus pour un utilisateur."""
        try:
            participant = self.participants.get(user=user)
            if participant.last_read_at:
                return self.messages.filter(
                    created_at__gt=participant.last_read_at,
                    is_deleted=False
                ).exclude(sender=user).count()
            return self.messages.filter(is_deleted=False).exclude(sender=user).count()
        except ConversationParticipant.DoesNotExist:
            return 0

    def update_last_message(self, message):
        """Met à jour les informations du dernier message."""
        self.last_message_at = message.created_at
        self.last_message_preview = message.content[:100] if message.content else ""
        self.save(update_fields=['last_message_at', 'last_message_preview'])


class ConversationParticipant(models.Model):
    """
    PROMPT 11 - Participant à une conversation.

    Gère l'appartenance des utilisateurs aux conversations,
    leurs rôles et leurs préférences de notification.
    """

    class Role(models.TextChoices):
        MEMBER = 'member', _('Membre')
        MODERATOR = 'moderator', _('Modérateur')
        ADMIN = 'admin', _('Administrateur')

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_("Conversation")
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_participations',
        verbose_name=_("Utilisateur")
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        verbose_name=_("Rôle")
    )

    # Timestamps
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Rejoint le")
    )

    left_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Quitté le")
    )

    # Préférences
    is_muted = models.BooleanField(
        default=False,
        verbose_name=_("Notifications désactivées")
    )

    is_pinned = models.BooleanField(
        default=False,
        verbose_name=_("Épinglé")
    )

    # Lecture
    last_read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernier lu le")
    )

    # Nickname personnalisé pour la conversation
    nickname = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Surnom"),
        help_text=_("Surnom affiché dans cette conversation")
    )

    class Meta:
        app_label = 'chat'
        verbose_name = _("Participant")
        verbose_name_plural = _("Participants")
        unique_together = ['conversation', 'user']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user} dans {self.conversation}"

    @property
    def is_admin(self):
        """Vérifie si le participant est admin."""
        return self.role == self.Role.ADMIN

    @property
    def is_moderator(self):
        """Vérifie si le participant est modérateur ou admin."""
        return self.role in [self.Role.ADMIN, self.Role.MODERATOR]

    @property
    def is_active(self):
        """Vérifie si le participant est toujours actif."""
        return self.left_at is None

    def mark_as_read(self):
        """Marque la conversation comme lue."""
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])

    def leave(self):
        """Quitte la conversation."""
        self.left_at = timezone.now()
        self.save(update_fields=['left_at'])


class Message(models.Model):
    """
    PROMPT 11 - Message dans une conversation.

    Supporte:
    - Messages texte avec formatage
    - Réponses à d'autres messages
    - Pièces jointes (via MessageAttachment)
    - Soft delete
    """

    class MessageType(models.TextChoices):
        TEXT = 'text', _('Texte')
        SYSTEM = 'system', _('Système')
        IMAGE = 'image', _('Image')
        FILE = 'file', _('Fichier')

    # UUID pour les références externes
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("UUID")
    )

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Conversation")
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='chat_messages_sent',
        verbose_name=_("Expéditeur")
    )

    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        verbose_name=_("Type de message")
    )

    content = models.TextField(
        verbose_name=_("Contenu"),
        help_text=_("Contenu du message (supporte le markdown basique)")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Envoyé le")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Modifié le")
    )

    # Réponse à un autre message
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_("En réponse à")
    )

    # Soft delete
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Supprimé")
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Supprimé le")
    )

    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_messages_deleted',
        verbose_name=_("Supprimé par")
    )

    # Édition
    is_edited = models.BooleanField(
        default=False,
        verbose_name=_("Modifié")
    )

    # Métadonnées JSON (pour les messages système, etc.)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Métadonnées")
    )

    class Meta:
        app_label = 'chat'
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_deleted']),
        ]

    def __str__(self):
        sender_name = self.sender.username if self.sender else _("Système")
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{sender_name}: {preview}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Mettre à jour la conversation après création
        if is_new and not self.is_deleted:
            self.conversation.update_last_message(self)

    def soft_delete(self, user):
        """Suppression douce du message."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def mark_as_edited(self):
        """Marque le message comme édité."""
        self.is_edited = True
        self.save(update_fields=['is_edited', 'updated_at'])

    @property
    def can_be_edited(self):
        """Vérifie si le message peut encore être édité (15 minutes)."""
        if self.is_deleted or self.message_type == self.MessageType.SYSTEM:
            return False
        time_limit = timezone.now() - timezone.timedelta(minutes=15)
        return self.created_at > time_limit


class MessageAttachment(models.Model):
    """
    PROMPT 11 - Pièce jointe à un message.

    Supporte les images, PDFs et documents.
    Limite de taille: 10MB par défaut.
    """

    class FileType(models.TextChoices):
        IMAGE = 'image', _('Image')
        PDF = 'pdf', _('PDF')
        DOCUMENT = 'document', _('Document')
        SPREADSHEET = 'spreadsheet', _('Tableur')
        OTHER = 'other', _('Autre')

    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'csv']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_("Message")
    )

    file = models.FileField(
        upload_to=chat_attachment_path,
        validators=[FileExtensionValidator(allowed_extensions=ALLOWED_EXTENSIONS)],
        verbose_name=_("Fichier")
    )

    file_name = models.CharField(
        max_length=255,
        verbose_name=_("Nom du fichier")
    )

    file_type = models.CharField(
        max_length=20,
        choices=FileType.choices,
        default=FileType.OTHER,
        verbose_name=_("Type de fichier")
    )

    file_size = models.PositiveIntegerField(
        verbose_name=_("Taille (bytes)"),
        help_text=_("Taille du fichier en bytes")
    )

    # Dimensions pour les images
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Largeur")
    )

    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Hauteur")
    )

    # Miniature pour les images
    thumbnail = models.ImageField(
        upload_to='chat_thumbnails/',
        null=True,
        blank=True,
        verbose_name=_("Miniature")
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Téléchargé le")
    )

    class Meta:
        app_label = 'chat'
        verbose_name = _("Pièce jointe")
        verbose_name_plural = _("Pièces jointes")
        ordering = ['uploaded_at']

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        # Déterminer automatiquement le type de fichier
        if not self.file_type or self.file_type == self.FileType.OTHER:
            ext = self.file_name.split('.')[-1].lower() if '.' in self.file_name else ''
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                self.file_type = self.FileType.IMAGE
            elif ext == 'pdf':
                self.file_type = self.FileType.PDF
            elif ext in ['doc', 'docx', 'txt']:
                self.file_type = self.FileType.DOCUMENT
            elif ext in ['xls', 'xlsx', 'csv']:
                self.file_type = self.FileType.SPREADSHEET

        super().save(*args, **kwargs)

    @property
    def is_image(self):
        return self.file_type == self.FileType.IMAGE

    @property
    def file_size_display(self):
        """Affiche la taille de manière lisible."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class MessageReadStatus(models.Model):
    """
    PROMPT 11 - Statut de lecture d'un message.

    Permet de savoir qui a lu quel message et quand.
    Utilisé pour les indicateurs "lu" dans l'interface.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_statuses',
        verbose_name=_("Message")
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_read_messages',
        verbose_name=_("Utilisateur")
    )

    read_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Lu le")
    )

    class Meta:
        app_label = 'chat'
        verbose_name = _("Statut de lecture")
        verbose_name_plural = _("Statuts de lecture")
        unique_together = ['message', 'user']
        indexes = [
            models.Index(fields=['message', 'user']),
        ]

    def __str__(self):
        return f"{self.user} a lu le message {self.message_id}"


class UserChatSettings(models.Model):
    """
    PROMPT 11 - Paramètres de chat par utilisateur.

    Permet à chaque utilisateur de personnaliser
    ses préférences de notification et d'affichage.
    """

    class Theme(models.TextChoices):
        LIGHT = 'light', _('Clair')
        DARK = 'dark', _('Sombre')
        AUTO = 'auto', _('Automatique')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_settings',
        verbose_name=_("Utilisateur")
    )

    # Notifications
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Notifications activées")
    )

    email_notifications = models.BooleanField(
        default=False,
        verbose_name=_("Notifications par email"),
        help_text=_("Recevoir un email pour les messages non lus")
    )

    push_notifications = models.BooleanField(
        default=True,
        verbose_name=_("Notifications push")
    )

    sound_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Sons activés")
    )

    # Préférences d'affichage
    theme = models.CharField(
        max_length=10,
        choices=Theme.choices,
        default=Theme.AUTO,
        verbose_name=_("Thème")
    )

    show_read_receipts = models.BooleanField(
        default=True,
        verbose_name=_("Afficher les confirmations de lecture")
    )

    show_typing_indicator = models.BooleanField(
        default=True,
        verbose_name=_("Afficher 'est en train d'écrire'")
    )

    # Vie privée
    show_online_status = models.BooleanField(
        default=True,
        verbose_name=_("Afficher mon statut en ligne")
    )

    # Dernière activité
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Dernière connexion")
    )

    class Meta:
        app_label = 'chat'
        verbose_name = _("Paramètres de chat")
        verbose_name_plural = _("Paramètres de chat")

    def __str__(self):
        return f"Paramètres de {self.user}"

    def update_last_seen(self):
        """Met à jour le timestamp de dernière activité."""
        self.last_seen = timezone.now()
        self.save(update_fields=['last_seen'])


class MessageReaction(models.Model):
    """
    PROMPT 11 - Réaction à un message (emoji).

    Permet aux utilisateurs de réagir aux messages
    avec des emojis sans envoyer de nouveau message.
    """

    COMMON_REACTIONS = ['👍', '❤️', '😂', '😮', '😢', '🎉', '🙏', '💪']

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name=_("Message")
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_reactions',
        verbose_name=_("Utilisateur")
    )

    emoji = models.CharField(
        max_length=10,
        verbose_name=_("Emoji")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Créé le")
    )

    class Meta:
        app_label = 'chat'
        verbose_name = _("Réaction")
        verbose_name_plural = _("Réactions")
        unique_together = ['message', 'user', 'emoji']

    def __str__(self):
        return f"{self.user} a réagi {self.emoji} à {self.message_id}"
