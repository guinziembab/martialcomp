from django.urls import path, include
from apps.competitions.views.events import (
    event_list, create_event, event_detail, edit_event, delete_event, import_events,
    register_for_event, cancel_registration, event_participants, archive_event, unarchive_event
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
    
    # Inscription à un événement
    path('<int:event_id>/register/', register_for_event, name='register_for_event'),
    
    # Annuler une inscription
    path('<int:event_id>/cancel/<int:registration_id>/', cancel_registration, name='cancel_registration'),
    
    # Voir les participants d'un événement
    path('<int:event_id>/participants/', event_participants, name='event_participants'),
    
    # Archiver un événement
    path('<int:event_id>/archive/', archive_event, name='archive_event'),
    
    # Désarchiver un événement
    path('<int:event_id>/unarchive/', unarchive_event, name='unarchive_event'),
    
    # Sous-namespace pour la planification (compatibilité)
    path('planning/', include('competitions.urls.event_planning', namespace='planning')),
]

