"""
PROMPT 11 - Interface d'administration du système de Chat MartialComp
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db.models import Count

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageReadStatus,
    UserChatSettings,
    MessageReaction,
)


class ConversationParticipantInline(admin.TabularInline):
    """Inline pour les participants d'une conversation."""
    model = ConversationParticipant
    extra = 0
    readonly_fields = ('joined_at', 'last_read_at')
    raw_id_fields = ('user',)
    fields = ('user', 'role', 'is_muted', 'is_pinned', 'joined_at', 'left_at', 'last_read_at')


class MessageInline(admin.TabularInline):
    """Inline pour les derniers messages d'une conversation."""
    model = Message
    extra = 0
    max_num = 10
    readonly_fields = ('sender', 'content_preview', 'created_at', 'is_deleted')
    fields = ('sender', 'content_preview', 'created_at', 'is_deleted')
    ordering = ('-created_at',)

    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = _("Aperçu")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Administration des conversations."""

    list_display = (
        'id', 'type_badge', 'name_display', 'participants_count',
        'messages_count', 'last_message_at', 'is_active'
    )
    list_filter = ('type', 'is_active', 'created_at')
    search_fields = ('name', 'uuid', 'participants__user__username', 'participants__user__email')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'last_message_at', 'last_message_preview')
    raw_id_fields = ('created_by', 'club', 'competition')
    date_hierarchy = 'created_at'
    inlines = [ConversationParticipantInline, MessageInline]

    fieldsets = (
        (None, {
            'fields': ('uuid', 'type', 'name', 'description', 'avatar')
        }),
        (_('Relations'), {
            'fields': ('created_by', 'club', 'competition'),
            'classes': ('collapse',)
        }),
        (_('Paramètres'), {
            'fields': ('is_active', 'allow_replies')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at', 'last_message_at', 'last_message_preview'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _participants_count=Count('participants', distinct=True),
            _messages_count=Count('messages', distinct=True)
        )

    def type_badge(self, obj):
        colors = {
            'direct': '#3498db',
            'group': '#9b59b6',
            'club': '#27ae60',
            'competition': '#e74c3c',
        }
        color = colors.get(obj.type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = _("Type")
    type_badge.admin_order_field = 'type'

    def name_display(self, obj):
        return str(obj)
    name_display.short_description = _("Nom")

    def participants_count(self, obj):
        return obj._participants_count
    participants_count.short_description = _("Participants")
    participants_count.admin_order_field = '_participants_count'

    def messages_count(self, obj):
        return obj._messages_count
    messages_count.short_description = _("Messages")
    messages_count.admin_order_field = '_messages_count'


class MessageAttachmentInline(admin.TabularInline):
    """Inline pour les pièces jointes d'un message."""
    model = MessageAttachment
    extra = 0
    readonly_fields = ('uploaded_at', 'file_size_display')
    fields = ('file', 'file_name', 'file_type', 'file_size_display', 'uploaded_at')

    def file_size_display(self, obj):
        return obj.file_size_display
    file_size_display.short_description = _("Taille")


class MessageReactionInline(admin.TabularInline):
    """Inline pour les réactions à un message."""
    model = MessageReaction
    extra = 0
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Administration des messages."""

    list_display = (
        'id', 'conversation_link', 'sender_display', 'content_preview',
        'message_type', 'created_at', 'status_badges'
    )
    list_filter = ('message_type', 'is_deleted', 'is_edited', 'created_at')
    search_fields = ('content', 'sender__username', 'conversation__name', 'uuid')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'deleted_at')
    raw_id_fields = ('conversation', 'sender', 'reply_to', 'deleted_by')
    date_hierarchy = 'created_at'
    inlines = [MessageAttachmentInline, MessageReactionInline]

    fieldsets = (
        (None, {
            'fields': ('uuid', 'conversation', 'sender', 'message_type')
        }),
        (_('Contenu'), {
            'fields': ('content', 'reply_to', 'metadata')
        }),
        (_('Statut'), {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by', 'is_edited')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def conversation_link(self, obj):
        url = reverse('admin:chat_conversation_change', args=[obj.conversation.id])
        return format_html('<a href="{}">{}</a>', url, obj.conversation)
    conversation_link.short_description = _("Conversation")

    def sender_display(self, obj):
        if obj.sender:
            return obj.sender.get_full_name() or obj.sender.username
        return format_html('<em style="color: #888;">Système</em>')
    sender_display.short_description = _("Expéditeur")

    def content_preview(self, obj):
        preview = obj.content[:80]
        if len(obj.content) > 80:
            preview += "..."
        if obj.is_deleted:
            return format_html('<del style="color: #999;">{}</del>', preview)
        return preview
    content_preview.short_description = _("Contenu")

    def status_badges(self, obj):
        badges = []
        if obj.is_deleted:
            badges.append('<span style="color: #e74c3c;">🗑️</span>')
        if obj.is_edited:
            badges.append('<span style="color: #f39c12;">✏️</span>')
        if obj.attachments.exists():
            badges.append('<span style="color: #3498db;">📎</span>')
        if obj.reactions.exists():
            badges.append(f'<span style="color: #9b59b6;">💬{obj.reactions.count()}</span>')
        return format_html(' '.join(badges)) if badges else '-'
    status_badges.short_description = _("Statut")


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    """Administration des participants."""

    list_display = (
        'id', 'user', 'conversation', 'role_badge', 'is_muted',
        'is_pinned', 'joined_at', 'is_active_display'
    )
    list_filter = ('role', 'is_muted', 'is_pinned', 'joined_at')
    search_fields = ('user__username', 'user__email', 'conversation__name')
    raw_id_fields = ('conversation', 'user')
    readonly_fields = ('joined_at', 'last_read_at')

    def role_badge(self, obj):
        colors = {
            'admin': '#e74c3c',
            'moderator': '#f39c12',
            'member': '#3498db',
        }
        color = colors.get(obj.role, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 10px;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = _("Rôle")
    role_badge.admin_order_field = 'role'

    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #27ae60;">✓ Actif</span>')
        return format_html('<span style="color: #e74c3c;">✗ Parti</span>')
    is_active_display.short_description = _("Statut")


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    """Administration des pièces jointes."""

    list_display = (
        'id', 'file_name', 'file_type_badge', 'file_size_display',
        'message_link', 'uploaded_at'
    )
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('file_name', 'message__content')
    raw_id_fields = ('message',)
    readonly_fields = ('uploaded_at', 'file_size_display')

    def file_type_badge(self, obj):
        icons = {
            'image': '🖼️',
            'pdf': '📕',
            'document': '📄',
            'spreadsheet': '📊',
            'other': '📁',
        }
        icon = icons.get(obj.file_type, '📁')
        return f"{icon} {obj.get_file_type_display()}"
    file_type_badge.short_description = _("Type")

    def file_size_display(self, obj):
        return obj.file_size_display
    file_size_display.short_description = _("Taille")

    def message_link(self, obj):
        url = reverse('admin:chat_message_change', args=[obj.message.id])
        return format_html('<a href="{}">Message #{}</a>', url, obj.message.id)
    message_link.short_description = _("Message")


@admin.register(UserChatSettings)
class UserChatSettingsAdmin(admin.ModelAdmin):
    """Administration des paramètres utilisateur."""

    list_display = (
        'user', 'notifications_enabled', 'email_notifications',
        'sound_enabled', 'theme', 'last_seen'
    )
    list_filter = ('notifications_enabled', 'email_notifications', 'theme')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)
    readonly_fields = ('last_seen',)

    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('Notifications'), {
            'fields': ('notifications_enabled', 'email_notifications', 'push_notifications', 'sound_enabled')
        }),
        (_('Affichage'), {
            'fields': ('theme', 'show_read_receipts', 'show_typing_indicator')
        }),
        (_('Vie privée'), {
            'fields': ('show_online_status', 'last_seen')
        }),
    )


@admin.register(MessageReaction)
class MessageReactionAdmin(admin.ModelAdmin):
    """Administration des réactions."""

    list_display = ('id', 'emoji', 'user', 'message_link', 'created_at')
    list_filter = ('emoji', 'created_at')
    search_fields = ('user__username', 'message__content')
    raw_id_fields = ('message', 'user')
    readonly_fields = ('created_at',)

    def message_link(self, obj):
        url = reverse('admin:chat_message_change', args=[obj.message.id])
        preview = obj.message.content[:50]
        return format_html('<a href="{}">{}</a>', url, preview)
    message_link.short_description = _("Message")


@admin.register(MessageReadStatus)
class MessageReadStatusAdmin(admin.ModelAdmin):
    """Administration des statuts de lecture."""

    list_display = ('id', 'user', 'message_preview', 'read_at')
    list_filter = ('read_at',)
    search_fields = ('user__username', 'message__content')
    raw_id_fields = ('message', 'user')
    readonly_fields = ('read_at',)

    def message_preview(self, obj):
        return obj.message.content[:50]
    message_preview.short_description = _("Message")
