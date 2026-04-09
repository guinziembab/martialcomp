"""
PROMPT 12 - Vues du système de Chat MartialComp

Interface utilisateur pour la messagerie interne.
"""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q, Count, Max, Prefetch, OuterRef, Subquery
from django.utils import timezone
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from datetime import timedelta

from .models import (
    Conversation,
    ConversationParticipant,
    Message,
    MessageAttachment,
    MessageReadStatus,
    UserChatSettings,
    MessageReaction,
)
from .services import ConversationService, MessageService, ChatSettingsService

User = get_user_model()


@login_required
def chat_home(request):
    """
    PROMPT 12 - Page principale du chat.

    Affiche la liste des conversations et la première conversation active.
    """
    # Mettre à jour le last_seen
    ChatSettingsService.update_last_seen(request.user)

    # Récupérer les conversations de l'utilisateur
    conversations = ConversationService.get_user_conversations(request.user)

    # Compter les messages non lus totaux
    total_unread = MessageService.get_unread_count(request.user)

    # Sélectionner la première conversation si disponible
    active_conversation = None
    messages = []

    if conversations.exists():
        active_conversation = conversations.first()
        messages = MessageService.get_conversation_messages(
            active_conversation,
            request.user,
            limit=50
        )
        # Marquer comme lu
        MessageService.mark_conversation_read(active_conversation, request.user)

    context = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': reversed(list(messages)) if messages else [],
        'total_unread': total_unread,
    }

    return render(request, 'chat/home.html', context)


@login_required
def conversation_detail(request, conversation_uuid):
    """
    PROMPT 12 - Détail d'une conversation.

    Charge une conversation spécifique avec ses messages.
    """
    conversation = get_object_or_404(Conversation, uuid=conversation_uuid)

    # Vérifier que l'utilisateur est participant
    if not conversation.participants.filter(user=request.user, left_at__isnull=True).exists():
        return HttpResponseForbidden(_("Vous n'avez pas accès à cette conversation."))

    # Mettre à jour le last_seen
    ChatSettingsService.update_last_seen(request.user)

    # Récupérer les messages
    messages = MessageService.get_conversation_messages(
        conversation,
        request.user,
        limit=50
    )

    # Marquer comme lu
    MessageService.mark_conversation_read(conversation, request.user)

    # Récupérer toutes les conversations pour la sidebar
    conversations = ConversationService.get_user_conversations(request.user)
    total_unread = MessageService.get_unread_count(request.user)

    context = {
        'conversations': conversations,
        'active_conversation': conversation,
        'messages': reversed(list(messages)),
        'total_unread': total_unread,
    }

    # Si c'est une requête AJAX, renvoyer uniquement la partie conversation
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('chat/partials/conversation_content.html', context, request=request)
        return JsonResponse({
            'success': True,
            'html': html,
            'conversation_name': conversation.get_display_name(request.user),
        })

    return render(request, 'chat/home.html', context)


@login_required
@require_POST
def send_message(request):
    """
    PROMPT 12 - Envoyer un message (AJAX).
    """
    try:
        data = json.loads(request.body)
        conversation_uuid = data.get('conversation_uuid')
        content = data.get('content', '').strip()
        reply_to_id = data.get('reply_to_id')

        if not conversation_uuid or not content:
            return JsonResponse({
                'success': False,
                'error': _("Conversation et contenu requis.")
            }, status=400)

        conversation = get_object_or_404(Conversation, uuid=conversation_uuid)

        # Vérifier la réponse
        reply_to = None
        if reply_to_id:
            reply_to = Message.objects.filter(id=reply_to_id, conversation=conversation).first()

        # Envoyer le message
        message = MessageService.send_message(
            conversation=conversation,
            sender=request.user,
            content=content,
            reply_to=reply_to
        )

        # Rendre le HTML du message
        message_html = render_to_string(
            'chat/partials/message.html',
            {'message': message, 'user': request.user},
            request=request
        )

        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'uuid': str(message.uuid),
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'sender_name': message.sender.get_full_name() or message.sender.username,
                'is_mine': True,
            },
            'html': message_html,
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_GET
def get_messages(request, conversation_uuid):
    """
    PROMPT 12 - Récupérer les nouveaux messages (polling).
    """
    conversation = get_object_or_404(Conversation, uuid=conversation_uuid)

    # Vérifier l'accès
    if not conversation.participants.filter(user=request.user, left_at__isnull=True).exists():
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)

    since = request.GET.get('since')
    before_id = request.GET.get('before_id')
    limit = int(request.GET.get('limit', 20))

    queryset = conversation.messages.filter(is_deleted=False).select_related('sender', 'reply_to')

    if since:
        try:
            since_dt = timezone.datetime.fromisoformat(since.replace('Z', '+00:00'))
            queryset = queryset.filter(created_at__gt=since_dt)
        except ValueError:
            pass

    if before_id:
        queryset = queryset.filter(id__lt=int(before_id))

    messages = queryset.order_by('-created_at')[:limit]

    # Marquer comme lu
    MessageService.mark_conversation_read(conversation, request.user)

    messages_data = []
    for msg in reversed(list(messages)):
        messages_data.append({
            'id': msg.id,
            'uuid': str(msg.uuid),
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'sender_id': msg.sender.id if msg.sender else None,
            'sender_name': msg.sender.get_full_name() or msg.sender.username if msg.sender else _('Système'),
            'is_mine': msg.sender == request.user,
            'is_system': msg.message_type == Message.MessageType.SYSTEM,
            'is_edited': msg.is_edited,
            'html': render_to_string(
                'chat/partials/message.html',
                {'message': msg, 'user': request.user},
                request=request
            ),
        })

    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'conversation_uuid': str(conversation.uuid),
    })


@login_required
def new_conversation(request):
    """
    PROMPT 12 - Créer une nouvelle conversation.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conversation_type = data.get('type', 'direct')
            user_ids = data.get('user_ids', [])
            name = data.get('name', '')

            if not user_ids:
                return JsonResponse({
                    'success': False,
                    'error': _("Sélectionnez au moins un destinataire.")
                }, status=400)

            users = User.objects.filter(id__in=user_ids)

            if conversation_type == 'direct' and len(users) == 1:
                # Conversation directe
                conversation, created = ConversationService.create_direct_conversation(
                    request.user, users.first()
                )
            else:
                # Conversation de groupe
                if not name:
                    # Générer un nom automatique
                    names = [u.get_full_name() or u.username for u in users[:3]]
                    name = ", ".join(names)
                    if len(users) > 3:
                        name += f" +{len(users) - 3}"

                conversation = ConversationService.create_group_conversation(
                    name=name,
                    creator=request.user,
                    members=list(users)
                )

            return JsonResponse({
                'success': True,
                'conversation_uuid': str(conversation.uuid),
                'redirect_url': f'/chat/{conversation.uuid}/',
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    # GET: Afficher le formulaire de nouvelle conversation
    return render(request, 'chat/new_conversation.html')


@login_required
@require_GET
def search_users(request):
    """
    PROMPT 12 - Rechercher des utilisateurs pour nouvelle conversation.
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'users': []})

    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id)[:20]

    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'full_name': user.get_full_name() or user.username,
            'email': user.email,
            'avatar_url': getattr(user, 'avatar_url', None) or '/static/img/default-avatar.png',
        })

    return JsonResponse({'users': users_data})


@login_required
@require_GET
def search_conversations(request):
    """
    PROMPT 12 - Rechercher dans les conversations.
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        conversations = ConversationService.get_user_conversations(request.user)[:10]
    else:
        conversations = ConversationService.search_conversations(request.user, query)[:10]

    conversations_data = []
    for conv in conversations:
        conversations_data.append({
            'uuid': str(conv.uuid),
            'name': conv.get_display_name(request.user),
            'type': conv.type,
            'last_message': conv.last_message_preview,
            'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
            'unread_count': conv.get_unread_count(request.user),
        })

    return JsonResponse({'conversations': conversations_data})


@login_required
@require_POST
def mark_read(request, conversation_uuid):
    """
    PROMPT 12 - Marquer une conversation comme lue.
    """
    conversation = get_object_or_404(Conversation, uuid=conversation_uuid)

    if not conversation.participants.filter(user=request.user).exists():
        return JsonResponse({'success': False}, status=403)

    count = MessageService.mark_conversation_read(conversation, request.user)

    return JsonResponse({
        'success': True,
        'marked_count': count,
    })


@login_required
@require_POST
def delete_message(request, message_id):
    """
    PROMPT 12 - Supprimer un message.
    """
    message = get_object_or_404(Message, id=message_id)

    try:
        MessageService.delete_message(message, request.user)
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)


@login_required
@require_POST
def edit_message(request, message_id):
    """
    PROMPT 12 - Modifier un message.
    """
    message = get_object_or_404(Message, id=message_id)

    try:
        data = json.loads(request.body)
        new_content = data.get('content', '').strip()

        if not new_content:
            return JsonResponse({
                'success': False,
                'error': _("Le contenu ne peut pas être vide.")
            }, status=400)

        message = MessageService.edit_message(message, request.user, new_content)

        return JsonResponse({
            'success': True,
            'content': message.content,
            'is_edited': message.is_edited,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)


@login_required
@require_POST
def add_reaction(request, message_id):
    """
    PROMPT 12 - Ajouter une réaction à un message.
    """
    message = get_object_or_404(Message, id=message_id)

    try:
        data = json.loads(request.body)
        emoji = data.get('emoji', '')

        if not emoji:
            return JsonResponse({
                'success': False,
                'error': _("Emoji requis.")
            }, status=400)

        reaction = MessageService.add_reaction(message, request.user, emoji)

        return JsonResponse({
            'success': True,
            'reaction_id': reaction.id,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)


@login_required
@require_POST
def remove_reaction(request, message_id):
    """
    PROMPT 12 - Retirer une réaction d'un message.
    """
    message = get_object_or_404(Message, id=message_id)

    try:
        data = json.loads(request.body)
        emoji = data.get('emoji', '')

        success = MessageService.remove_reaction(message, request.user, emoji)

        return JsonResponse({'success': success})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)


@login_required
def get_unread_count(request):
    """
    PROMPT 12 - Récupérer le nombre de messages non lus (pour le badge).
    """
    count = MessageService.get_unread_count(request.user)
    return JsonResponse({'count': count})


@login_required
def conversation_info(request, conversation_uuid):
    """
    PROMPT 12 - Informations sur une conversation (participants, etc.).
    """
    conversation = get_object_or_404(Conversation, uuid=conversation_uuid)

    if not conversation.participants.filter(user=request.user).exists():
        return JsonResponse({'success': False}, status=403)

    participants = []
    for p in conversation.participants.filter(left_at__isnull=True).select_related('user'):
        participants.append({
            'id': p.user.id,
            'username': p.user.username,
            'full_name': p.user.get_full_name() or p.user.username,
            'role': p.role,
            'is_admin': p.is_admin,
            'joined_at': p.joined_at.isoformat(),
        })

    return JsonResponse({
        'success': True,
        'conversation': {
            'uuid': str(conversation.uuid),
            'name': conversation.name,
            'type': conversation.type,
            'created_at': conversation.created_at.isoformat(),
            'participants_count': len(participants),
        },
        'participants': participants,
    })


@login_required
@require_POST
def leave_conversation(request, conversation_uuid):
    """
    PROMPT 12 - Quitter une conversation.
    """
    conversation = get_object_or_404(Conversation, uuid=conversation_uuid)

    try:
        ConversationService.remove_participant(conversation, request.user, request.user)
        return JsonResponse({
            'success': True,
            'redirect_url': '/chat/',
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=403)


@login_required
def chat_settings(request):
    """
    PROMPT 12 - Paramètres du chat.
    """
    settings = ChatSettingsService.get_or_create_settings(request.user)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            settings = ChatSettingsService.update_settings(request.user, **data)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    return JsonResponse({
        'notifications_enabled': settings.notifications_enabled,
        'email_notifications': settings.email_notifications,
        'sound_enabled': settings.sound_enabled,
        'theme': settings.theme,
        'show_read_receipts': settings.show_read_receipts,
        'show_typing_indicator': settings.show_typing_indicator,
        'show_online_status': settings.show_online_status,
    })
