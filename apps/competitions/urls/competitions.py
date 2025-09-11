from django.urls import path, include
from apps.competitions.views.competitions import (
    competition_list, competition_create, competition_detail, 
    manage_competition_registrations, register_for_competition
)

app_name = 'competitions'

urlpatterns = [
    # Liste des compétitions
    path('list/', competition_list, name='list'),
    path('', competition_list, name='list'),  # Alias
    
    # Créer une compétition
    path('create/', competition_create, name='create'),
    
    # Détail d'une compétition
    path('<int:pk>/', competition_detail, name='detail'),
    
    # Inscription à une compétition
    path('<int:competition_id>/register/', register_for_competition, name='register'),
    
    # Gestion des inscriptions
    path('<int:competition_id>/registrations/', manage_competition_registrations, name='manage_registrations'),
    
    # API endpoints
    path('api/', include('apps.competitions.api')),
]

