# -*- coding: utf-8 -*-
from django.urls import path

from apps.competitions.views import event_planning
from apps.competitions.views import event_planning_simple

app_name = 'event_planning'

urlpatterns = [
    # Liste des sondages
    path('polls/', event_planning_simple.poll_list_simple, name='poll_list'),
    
    # Détails d'un sondage
    path('polls/<uuid:poll_id>/', event_planning.poll_detail, name='poll_detail'),
    
    # Création d'un nouveau sondage
    path('polls/create/', event_planning_simple.create_poll_simple, name='create_poll'),
    path('events/<uuid:event_id>/polls/create/', event_planning_simple.create_poll_simple, name='create_event_poll'),
    
    # Ã‰dition d'un sondage
    path('polls/<uuid:poll_id>/edit/', event_planning.edit_poll, name='edit_poll'),
    
    # Actions sur un sondage
    path('poll-options/<uuid:option_id>/respond/', event_planning.poll_respond, name='poll_respond'),
    path('polls/<uuid:poll_id>/finalize/<uuid:option_id>/', event_planning.finalize_poll, name='finalize_poll'),
    path('polls/<uuid:poll_id>/cancel/', event_planning.cancel_poll, name='cancel_poll'),
    
    # Résultats d'un sondage
    path('polls/<uuid:poll_id>/results/', event_planning.poll_results, name='poll_results'),
    
    # Partage public d'un sondage
    path('p/<str:share_code>/', event_planning.public_poll, name='public_poll'),
    
    # Gestion des rappels d'événements
    path('events/<uuid:event_id>/reminders/', event_planning.event_reminders, name='event_reminders'),
    path('events/<uuid:event_id>/reminders/create/', event_planning.create_reminder, name='create_reminder'),
    path('reminders/<uuid:reminder_id>/edit/', event_planning.edit_reminder, name='edit_reminder'),
    path('reminders/<uuid:reminder_id>/delete/', event_planning.delete_reminder, name='delete_reminder'),
    
    # Statistiques des événements
    path('events/<uuid:event_id>/statistics/', event_planning.event_statistics, name='event_statistics'),
]

