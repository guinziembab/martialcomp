from django.urls import path, include
from apps.competitions.views.competitions import (
    competition_list, competition_create, competition_detail, competition_update,
    manage_competition_registrations, register_for_competition
)
from apps.competitions.views.competition_management import (
    add_competition_type, remove_competition_type,
    add_competition_category, remove_competition_category
)
from apps.competitions.views.categories import (
    competition_categories, add_category, delete_category
)
from apps.competitions.views.public import public_competition_registration
from apps.competitions.views.competition_qr import competition_qr_code

app_name = 'competitions'

urlpatterns = [
    # Liste des compétitions
    path('list/', competition_list, name='list'),
    path('', competition_list, name='list'),  # Alias
    
    # Créer une compétition
    path('create/', competition_create, name='create'),
    
    # Détail d'une compétition
    path('<int:pk>/', competition_detail, name='detail'),
    
    # Modification d'une compétition
    path('<int:pk>/update/', competition_update, name='update'),
    
    # Inscription à une compétition
    path('<int:competition_id>/register/', register_for_competition, name='register'),
    
    # Inscription publique à une compétition
    path('<int:competition_id>/public-registration/', public_competition_registration, name='public_registration'),
    
    # QR Code de compétition
    path('<int:competition_id>/qr-code/', competition_qr_code, name='qr_code'),
    
    # Gestion des inscriptions
    path('<int:competition_id>/registrations/', manage_competition_registrations, name='manage_registrations'),
    
    # Gestion des types de compétition
    path('<int:pk>/add-type/', add_competition_type, name='add_type'),
    path('<int:pk>/remove-type/', remove_competition_type, name='remove_type'),
    
    # Gestion des catégories
    path('<int:pk>/add-category/', add_competition_category, name='add_category'),
    path('<int:pk>/remove-category/', remove_competition_category, name='remove_category'),
    path('<int:competition_id>/categories/', competition_categories, name='categories'),
    path('<int:competition_id>/categories/add/', add_category, name='add_category_detailed'),
    path('<int:competition_id>/categories/delete/', delete_category, name='delete_category_detailed'),
    
    # API endpoints
    path('api/', include('apps.competitions.api')),
]