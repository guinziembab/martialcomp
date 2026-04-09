from django.urls import path, include
from apps.competitions.views.events import (
    event_list, create_event, event_detail, edit_event, delete_event, import_events,
    register_for_event, public_register_for_event, cancel_registration,
    event_participants, archive_event, unarchive_event,
    # Vues pour les événements récurrents
    recurrence_preview, occurrence_list, occurrence_detail,
    occurrence_edit, occurrence_cancel, occurrence_attendance,
    generate_occurrences,
    event_duplicate
)

app_name = 'events'

urlpatterns = [
    # Liste des événements
    path('list/', event_list, name='event_list'),
    path('', event_list, name='event_list'),  # Alias
    
    # Créer un événement
    path('create/', create_event, name='create_event'),
    
    # Détail d'un événement
    path('<int:event_id>/', event_detail, name='event_detail'),
    
    # Modifier un événement
    path('<int:event_id>/edit/', edit_event, name='edit_event'),
    
    # Supprimer un événement
    path('<int:event_id>/delete/', delete_event, name='delete_event'),
    
    # Importer des événements
    path('import/', import_events, name='import_events'),
    
    # Inscription à un événement (utilisateur connecté)
    path('<int:event_id>/register/', register_for_event, name='register_for_event'),

    # Inscription publique (sans compte)
    path('<int:event_id>/public-register/', public_register_for_event, name='public_register_for_event'),
    
    # Annuler une inscription
    path('<int:event_id>/cancel/<int:registration_id>/', cancel_registration, name='cancel_registration'),
    
    # Voir les participants d'un événement
    path('<int:event_id>/participants/', event_participants, name='event_participants'),
    
    # Archiver un événement
    path('<int:event_id>/archive/', archive_event, name='archive_event'),
    
    # Désarchiver un événement
    path('<int:event_id>/unarchive/', unarchive_event, name='unarchive_event'),

    # Dupliquer un événement
    path('<int:event_id>/duplicate/', event_duplicate, name='duplicate'),
    
    # Sous-namespace pour la planification (compatibilité)
    path('planning/', include('apps.competitions.urls.event_planning', namespace='planning')),

    # =========================================================================
    # URLS POUR LES ÉVÉNEMENTS RÉCURRENTS
    # =========================================================================

    # API prévisualisation des dates de récurrence (AJAX)
    path('recurrence/preview/', recurrence_preview, name='recurrence_preview'),

    # Liste des occurrences d'un événement
    path('<int:event_id>/occurrences/', occurrence_list, name='occurrence_list'),

    # Générer manuellement les occurrences
    path('<int:event_id>/occurrences/generate/', generate_occurrences, name='generate_occurrences'),

    # Détail d'une occurrence
    path('occurrence/<int:occurrence_id>/', occurrence_detail, name='occurrence_detail'),

    # Modifier une occurrence
    path('occurrence/<int:occurrence_id>/edit/', occurrence_edit, name='occurrence_edit'),

    # Annuler une occurrence
    path('occurrence/<int:occurrence_id>/cancel/', occurrence_cancel, name='occurrence_cancel'),

    # Pointage des présences pour une occurrence
    path('occurrence/<int:occurrence_id>/attendance/', occurrence_attendance, name='occurrence_attendance'),
]

