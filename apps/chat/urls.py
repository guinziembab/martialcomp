"""
PROMPT 12 - URLs du système de Chat MartialComp
"""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Page principale du chat
    path('', views.chat_home, name='home'),

    # Détail d'une conversation
    path('<uuid:conversation_uuid>/', views.conversation_detail, name='conversation_detail'),

    # API Messages
    path('send/', views.send_message, name='send_message'),
    path('<uuid:conversation_uuid>/messages/', views.get_messages, name='get_messages'),
    path('<uuid:conversation_uuid>/mark-read/', views.mark_read, name='mark_read'),

    # Gestion des messages
    path('message/<int:message_id>/delete/', views.delete_message, name='delete_message'),
    path('message/<int:message_id>/edit/', views.edit_message, name='edit_message'),
    path('message/<int:message_id>/react/', views.add_reaction, name='add_reaction'),
    path('message/<int:message_id>/unreact/', views.remove_reaction, name='remove_reaction'),

    # Conversations
    path('new/', views.new_conversation, name='new_conversation'),
    path('<uuid:conversation_uuid>/info/', views.conversation_info, name='conversation_info'),
    path('<uuid:conversation_uuid>/leave/', views.leave_conversation, name='leave_conversation'),

    # Recherche
    path('search/users/', views.search_users, name='search_users'),
    path('search/conversations/', views.search_conversations, name='search_conversations'),

    # Paramètres et utilitaires
    path('settings/', views.chat_settings, name='settings'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
]
