# -*- coding: utf-8 -*-
from django.urls import path, include

from competitions.views import events

app_name = 'events'

urlpatterns = [
    # List and CRUD operations for events
    path('', events.event_list, name='event_list'),
    path('create/', events.create_event, name='create_event'),
    path('<int:event_id>/', events.event_detail, name='event_detail'),
    path('<int:event_id>/edit/', events.edit_event, name='edit_event'),
    path('<int:event_id>/delete/', events.delete_event, name='delete_event'),
    path('<int:event_id>/archive/', events.archive_event, name='archive_event'),
    path('<int:event_id>/unarchive/', events.unarchive_event, name='unarchive_event'),
    
    # Event registration
    path('<int:event_id>/register/', events.register_for_event, name='register_for_event'),
    path('<int:event_id>/registration/<int:registration_id>/cancel/', events.cancel_registration, name='cancel_registration'),
    
    # Event participant management
    path('<int:event_id>/participants/', events.event_participants, name='event_participants'),
    path('<int:event_id>/participants/<int:participant_id>/edit/', events.edit_participant, name='edit_participant'),
    path('<int:event_id>/participants/<int:participant_id>/remove/', events.remove_participant, name='remove_participant'),
    
    # Event feedback
    path('<int:event_id>/feedback/', events.event_feedback, name='event_feedback'),
    path('<int:event_id>/feedback/submit/', events.submit_feedback, name='submit_feedback'),
    path('<int:event_id>/feedback/results/', events.feedback_results, name='feedback_results'),
    
    # Import and export events
    path('import/', events.import_events, name='import_events'),
    path('export/', events.export_events, name='export_events'),
    
    # Event notifications
    path('<int:event_id>/notify/', events.event_notify, name='event_notify'),
    
    # Event planning functionality (polls, reminders, etc.)
    path('planning/', include(('competitions.urls.event_planning', 'competitions'), namespace='planning')),
    
    # Event surveys
    path('surveys/', include(('competitions.urls.event_surveys', 'competitions.urls'), namespace='surveys')),
]