from django.urls import path
from apps.competitions.views.competition_types import (
    competition_type_list,
    competition_type_create,
    competition_type_detail,
    competition_type_update,
    competition_type_delete,
    competition_type_api_list,
)

app_name = 'competition_types'

urlpatterns = [
    # Liste des types de compétition
    path('', competition_type_list, name='list'),
    
    # Créer un type de compétition
    path('create/', competition_type_create, name='create'),
    
    # Détail d'un type de compétition
    path('<int:pk>/', competition_type_detail, name='detail'),
    
    # Modifier un type de compétition
    path('<int:pk>/edit/', competition_type_update, name='update'),
    
    # Supprimer un type de compétition
    path('<int:pk>/delete/', competition_type_delete, name='delete'),
    
    # API pour récupérer les types de compétition
    path('api/', competition_type_api_list, name='api_list'),
]