# -*- coding: utf-8 -*-
"""
URL routing pour l'API des groupes de diffusion.
"""

from django.urls import path
from .broadcast_api import (
    BroadcastGroupPreviewView,
    BroadcastGroupListCreateView,
    BroadcastGroupDetailView,
    BroadcastGroupMembersView,
    BroadcastGroupAddMembersView,
    BroadcastGroupRemoveMembersView,
    BroadcastGroupSendView,
    BroadcastMessageListView,
    BroadcastMessageDetailView,
    BroadcastInboxView,
    BroadcastMarkReadView,
)

app_name = 'broadcast_api'

urlpatterns = [
    # Gestion des groupes
    path('groups/', BroadcastGroupListCreateView.as_view(), name='groups_list'),
    path('groups/preview/', BroadcastGroupPreviewView.as_view(), name='groups_preview'),
    path('groups/<uuid:group_uuid>/', BroadcastGroupDetailView.as_view(), name='group_detail'),
    path('groups/<uuid:group_uuid>/members/', BroadcastGroupMembersView.as_view(), name='group_members'),
    path('groups/<uuid:group_uuid>/members/add/', BroadcastGroupAddMembersView.as_view(), name='group_add_members'),
    path('groups/<uuid:group_uuid>/members/remove/', BroadcastGroupRemoveMembersView.as_view(), name='group_remove_members'),
    path('groups/<uuid:group_uuid>/send/', BroadcastGroupSendView.as_view(), name='group_send'),

    # Messages envoyés (pour instructeurs)
    path('messages/', BroadcastMessageListView.as_view(), name='messages_list'),
    path('messages/<uuid:message_uuid>/', BroadcastMessageDetailView.as_view(), name='message_detail'),

    # Boîte de réception (pour pratiquants)
    path('inbox/', BroadcastInboxView.as_view(), name='inbox'),
    path('inbox/<uuid:message_uuid>/read/', BroadcastMarkReadView.as_view(), name='mark_read'),
]
