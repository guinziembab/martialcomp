from django.urls import path
from apps.competitions.views import federations
from apps.competitions.views.competitions import competition_create
from apps.competitions.views.dashboard.federations import (
    federation_manage_clubs, federation_settings
)
from apps.competitions.views.federations import (
    federation_list, federation_detail, federation_create, 
    federation_update, federation_delete, federation_add_club, federation_manage_users,
    federation_remove_club, federation_export_data,
    federation_calendar, federation_competitions, federation_categories,
    federation_users, federation_roles, federation_judges,
    import_export,
    federation_trainings,
    federation_certifications,
    create_certification,
    edit_certification,
    delete_certification,
    certification_registrations,
    review_certification_registration,
    certification_detail,
    create_training,
    training_detail,
    edit_training,
    delete_training,
    # Ajouter les nouvelles vues nécessaires
    create_federation_role,
    update_federation_role,
    delete_federation_role,
    role_users,  # Ajouté ici
    # Exports
    export_clubs,
    export_practitioners,
    import_clubs,
    download_sample_clubs,
    # Grades
    federation_grades,
    # Club
    select_club,
    club_detail
)
# Importation correcte de federation_index depuis le bon module
from apps.competitions.views.dashboard.federations import federation_dashboard, federation_index
from apps.competitions.views import federations
from apps.competitions.views import federation_grades
from apps.competitions.views import federation_clubs

app_name = 'federations'  

urlpatterns = [
    # URLs existantes
    path('', federation_list, name='list'),
    path('create/', federation_create, name='create'),
    
    # Utiliser la vue d'index des fédérations pour le dashboard sans paramètre
    path('dashboard/', federation_index, name='dashboard'), 
    
    # URLs avec paramètres variables
    path('<slug:slug>/', federation_detail, name='detail'),
    path('<slug:slug>/update/', federation_update, name='update'),
    path('<int:pk>/delete/', federation_delete, name='delete'),
    
    # Gestion des utilisateurs et dashboard
    path('<int:federation_id>/manage-users/', federation_manage_users, name='manage_users'),
    path('<int:federation_id>/dashboard/', federation_dashboard, name='federation_dashboard'),
    
    # URLs pour les compétitions
    path('<int:federation_id>/competitions/', federation_competitions, name='competitions'),
    path('<int:federation_id>/create-competition/', competition_create, name='create_competition'),
    path('<int:federation_id>/clubs/<int:club_id>/', club_detail, name='club_detail'),
    
    # URL pour le calendrier
    path('<int:federation_id>/calendar/', federation_calendar, name='calendar'),
    
    # URL pour les catégories
    path('<int:federation_id>/categories/', federation_categories, name='categories'),
    
    # URLs grades
    path('<int:federation_id>/grades/', federation_grades.grades_view, name='grades'),
    path('<int:federation_id>/api/grades/', federation_grades.get_grades_ajax, name='get_grades_ajax'),
    
    # URLs pour la gestion des clubs et utilisateurs
    path('<int:federation_id>/clubs/', federation_manage_clubs, name='clubs'),
    path('<int:federation_id>/users/', federation_users, name='users'),
    path('<int:federation_id>/roles/', federation_roles, name='roles'),
    path('<int:federation_id>/manage-clubs/', federation_clubs.manage_clubs, name='manage_clubs'),
    path('<int:federation_id>/add-club/', federation_clubs.add_club_to_federation, name='add_club'),
    path('<int:federation_id>/remove-club/<int:club_id>/', federation_clubs.remove_club_from_federation, name='remove_club'),
    
    # Gestion des rÃ´les
    path('<int:federation_id>/roles/create/', create_federation_role, name='create_role'),
    path('<int:federation_id>/roles/<int:role_id>/update/', update_federation_role, name='update_role'),
    path('<int:federation_id>/roles/<int:role_id>/delete/', delete_federation_role, name='delete_role'),
    path('<int:federation_id>/roles/<str:role_name>/users/', role_users, name='role_users'),  # Ajouté ici
    
    # Gestion des juges
    path('<int:federation_id>/judges/', federation_judges, name='judges'),
    
    # URLs pour les actions rapides
    path('<int:federation_id>/add-club/', federation_add_club, name='add_club'),
    path('<int:federation_id>/manage-clubs/', federation_manage_clubs, name='manage_clubs'),
    path('<int:federation_id>/remove-club/<int:club_id>/', federation_remove_club, name='remove_club'),
    path('<int:federation_id>/settings/', federation_settings, name='settings'),
    path('<int:federation_id>/export/', federation_export_data, name='export_data'),
    
    # URL pour select_club
    path('<int:federation_id>/competitions/<int:competition_id>/select-club/', select_club, name='select_club'),
    
    # Import/Export
    path('<int:federation_id>/import-export/', import_export, name='import_export'),
    
    # Fonctions d'export/import
    path('<int:federation_id>/export/clubs/', export_clubs, name='export_clubs'),
    path('<int:federation_id>/export/practitioners/', export_practitioners, name='export_practitioners'),
    path('<int:federation_id>/import/clubs/', import_clubs, name='import_clubs'),
    path('<int:federation_id>/download/sample-clubs/', download_sample_clubs, name='download_sample_clubs'),
    
    # URLs de formations
    path('<int:federation_id>/trainings/', federation_trainings, name='trainings'),
    path('<int:federation_id>/trainings/create/', create_training, name='create_training'),
    path('<int:federation_id>/trainings/<int:training_id>/', training_detail, name='training_detail'),
    path('<int:federation_id>/trainings/<int:training_id>/edit/', edit_training, name='edit_training'),
    path('<int:federation_id>/trainings/<int:training_id>/delete/', delete_training, name='delete_training'),
    
    # URLs de certifications
    path('<int:federation_id>/certifications/', federation_certifications, name='certifications'),
    path('<int:federation_id>/certifications/create/', create_certification, name='create_certification'),
    path('<int:federation_id>/certifications/<int:certification_id>/', certification_detail, name='certification_detail'),
    path('<int:federation_id>/certifications/<int:certification_id>/edit/', edit_certification, name='edit_certification'),
    path('<int:federation_id>/certifications/<int:certification_id>/delete/', delete_certification, name='delete_certification'),
    path('<int:federation_id>/certifications/<int:certification_id>/registrations/', certification_registrations, name='certification_registrations'),
    path('<int:federation_id>/certifications/registrations/<int:registration_id>/review/', review_certification_registration, name='review_registration'),
]

