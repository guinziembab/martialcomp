from django.urls import path, include
from django.shortcuts import redirect
from apps.competitions.views.competitions import (
    competition_list, competition_create, competition_detail, competition_update,
    competition_change_status, competition_delete, competition_duplicate,
    manage_competition_registrations, register_for_competition, export_competition_registrations
)
from apps.competitions.views.competition_management import (
    add_competition_type, remove_competition_type,
    add_competition_category, remove_competition_category, update_competition_category
)
from apps.competitions.views.categories import (
    competition_categories, add_category, delete_category, get_discipline_grades
)
from apps.competitions.views.category_management import (
    manage_categories, add_category as add_category_simple,
    delete_category as delete_category_simple,
    merge_categories, toggle_practitioner_role, split_category,
    remove_practitioner_from_category
)
from apps.competitions.views.public import public_competition_registration
from apps.competitions.views.competition_qr import competition_qr_code
from apps.competitions.views.club.registration_api import get_categories_by_type_api, get_category_registrations_api

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

    # Changement rapide de statut
    path('<int:pk>/change-status/', competition_change_status, name='change_status'),

    # Suppression d'une compétition
    path('<int:pk>/delete/', competition_delete, name='delete'),

    # Duplication d'une compétition
    path('<int:pk>/duplicate/', competition_duplicate, name='duplicate'),

    # Inscription à une compétition
    path('<int:competition_id>/register/', register_for_competition, name='register'),
    
    # Inscription publique à une compétition
    path('<int:competition_id>/public-registration/', public_competition_registration, name='public_registration'),
    
    # QR Code de compétition
    path('<int:competition_id>/qr-code/', competition_qr_code, name='qr_code'),
    
    # Gestion des inscriptions
    path('<int:competition_id>/registrations/', manage_competition_registrations, name='manage_registrations'),
    path('<int:competition_id>/registrations/export/', export_competition_registrations, name='export_registrations'),
    
    # Gestion des types de compétition
    path('<int:pk>/add-type/', add_competition_type, name='add_type'),
    path('<int:pk>/remove-type/', remove_competition_type, name='remove_type'),
    
    # Gestion des catégories
    path('<int:pk>/add-category/', add_competition_category, name='add_category'),
    path('<int:pk>/remove-category/', remove_competition_category, name='remove_category'),
    path('<int:competition_id>/categories/', competition_categories, name='categories'),
    path('<int:competition_id>/categories/add/', add_category, name='add_category_detailed'),
    path('<int:pk>/categories/add-detailed/', add_competition_category, name='add_category_detailed_ajax'),
    path('<int:competition_id>/categories/delete/', delete_category, name='delete_category_detailed'),
    path('<int:pk>/categories/delete-detailed/', remove_competition_category, name='delete_category_detailed_ajax'),
    path('<int:pk>/categories/update-detailed/', update_competition_category, name='update_category_detailed_ajax'),
    path('<int:competition_id>/api/grades/', get_discipline_grades, name='get_discipline_grades'),
    
    # API pour récupérer les catégories par type
    path('<int:competition_id>/api/categories/<int:type_id>/',
         lambda request, competition_id, type_id: get_categories_by_type_api(request, competition_id, type_id),
         name='api_categories_by_type'),

    # API pour récupérer les inscriptions d'une catégorie
    path('<int:competition_id>/api/category/<int:category_id>/registrations/',
         lambda request, competition_id, category_id: get_category_registrations_api(request, competition_id, category_id),
         name='api_category_registrations'),
    
    # Gestion simplifiée des catégories
    path('<int:competition_id>/manage-categories/', manage_categories, name='manage_categories'),
    path('<int:competition_id>/categories/add-simple/', add_category_simple, name='add_category_simple'),
    path('<int:competition_id>/categories/delete-simple/', delete_category_simple, name='delete_category_simple'),
    path('<int:competition_id>/categories/merge/', merge_categories, name='merge_categories'),
    path('<int:competition_id>/categories/split/', split_category, name='split_category'),
    path('<int:competition_id>/categories/remove-practitioner/', remove_practitioner_from_category, name='remove_practitioner_from_category'),
    path('<int:competition_id>/toggle-role/', toggle_practitioner_role, name='toggle_role'),

    # Redirection pour l'ancienne URL de planning (compatibilité)
    path('<int:competition_id>/schedule/overview/', 
         lambda request, competition_id: redirect('competitions:management:schedule_overview', competition_id=competition_id, permanent=False),
         name='schedule_overview_legacy'),
    
    # API endpoints
    path('api/', include('apps.competitions.api')),
]