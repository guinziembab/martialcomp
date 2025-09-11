from django.urls import path
from apps.competitions.views.dashboard.federations import federation_dashboard, federation_manage_clubs
from apps.competitions.views.federations_debug import federation_clubs_debug
from apps.competitions.views.federations import (
    federation_list, 
    federation_detail,
    federation_calendar,
    federation_competitions,
    federation_categories,
    federation_users,
    federation_roles,
    federation_judges,
    federation_create_competition,
    federation_settings,
    import_export,
    export_clubs,
    export_practitioners,
    download_sample_clubs,
    import_clubs,
    federation_add_club,
    federation_club_detail,
    federation_remove_club,
    federation_grades,
    federation_trainings,
    federation_certifications,
    federation_certification_detail,
    federation_examens,
    create_examen,
    edit_examen,
    delete_examen,
    examen_detail,
    federation_update,
    federation_delete,
    create_federation_role,
    update_federation_role,
    delete_federation_role,
    create_training,
    edit_training,
    delete_training,
    training_detail,
    start_training,
    complete_training,
    create_certification,
    edit_certification,
    delete_certification,
    role_users
)

app_name = 'federations'

urlpatterns = [
  # Liste des fédérations
  path('', federation_list, name='list'),
  path('list/', federation_list, name='federation_list'),

  # Dashboard d'une fédération spécifique
  path('<int:federation_id>/dashboard/', federation_dashboard, name='federation_dashboard'),
  
  # Routes de gestion fédération
  path('<int:federation_id>/calendar/', federation_calendar, name='calendar'),
  path('<int:federation_id>/competitions/', federation_competitions, name='competitions'),
  path('<int:federation_id>/create-competition/', federation_create_competition, name='create_competition'),
  path('<int:federation_id>/categories/', federation_categories, name='categories'),
  path('<int:federation_id>/users/', federation_users, name='users'),
  path('<int:federation_id>/roles/', federation_roles, name='roles'),
  path('<int:federation_id>/judges/', federation_judges, name='judges'),
  
  # Clubs d'une fédération
  path('<int:federation_id>/clubs/', federation_manage_clubs, name='clubs'),
  path('<int:federation_id>/clubs-debug/', federation_clubs_debug, name='clubs_debug'),
  path('<int:federation_id>/add-club/', federation_add_club, name='add_club'),
  path('<int:federation_id>/clubs/<int:club_id>/', federation_club_detail, name='club_detail'),
  path('<int:federation_id>/remove-club/<int:club_id>/', federation_remove_club, name='remove_club'),
  
  # Grades, formations et certifications
  path('<int:federation_id>/grades/', federation_grades, name='grades'),
  path('<int:federation_id>/trainings/', federation_trainings, name='trainings'),
  path('<int:federation_id>/certifications/', federation_certifications, name='certifications'),
  
  # Federation CRUD
  path('<int:pk>/update/', federation_update, name='update'),
  path('<int:pk>/delete/', federation_delete, name='delete'),
  
  # Role management  
  path('<int:federation_id>/create-role/', create_federation_role, name='create_role'),
  path('<int:federation_id>/roles/<int:role_id>/update/', update_federation_role, name='update_role'),
  path('<int:federation_id>/roles/<int:role_id>/delete/', delete_federation_role, name='delete_role'),
  path('<int:federation_id>/role-users/<str:role_name>/', role_users, name='role_users'),
  
  # Training management
  path('<int:federation_id>/create-training/', create_training, name='create_training'),
  path('<int:federation_id>/trainings/<int:training_id>/edit/', edit_training, name='edit_training'),
  path('<int:federation_id>/trainings/<int:training_id>/delete/', delete_training, name='delete_training'),
  path('<int:federation_id>/trainings/<int:training_id>/detail/', training_detail, name='training_detail'),
  path('<int:federation_id>/trainings/<int:training_id>/start/', start_training, name='start_training'),
  path('<int:federation_id>/trainings/<int:training_id>/complete/', complete_training, name='complete_training'),
  
  # Certification management  
  path('<int:federation_id>/create-certification/', create_certification, name='create_certification'),
  path('<int:federation_id>/certifications/<int:certification_id>/edit/', edit_certification, name='edit_certification'),
  path('<int:federation_id>/certifications/<int:certification_id>/delete/', delete_certification, name='delete_certification'),
  path('<int:federation_id>/certifications/<int:certification_id>/detail/', federation_certification_detail, name='certification_detail'),
  
  # Exam management
  path('<int:federation_id>/examens/', federation_examens, name='examens'),
  path('<int:federation_id>/create-examen/', create_examen, name='create_examen'),
  path('<int:federation_id>/examens/<int:examen_id>/edit/', edit_examen, name='edit_examen'),
  path('<int:federation_id>/examens/<int:examen_id>/delete/', delete_examen, name='delete_examen'),
  path('<int:federation_id>/examens/<int:examen_id>/detail/', examen_detail, name='examen_detail'),
  
  # Paramètres et configuration
  path('<int:federation_id>/settings/', federation_settings, name='settings'),
  path('<int:federation_id>/import-export/', import_export, name='import_export'),
  
  # Import/Export
  path('<int:federation_id>/export/clubs/', export_clubs, name='export_clubs'),
  path('<int:federation_id>/export/practitioners/', export_practitioners, name='export_practitioners'),
  path('<int:federation_id>/download-sample/clubs/', download_sample_clubs, name='download_sample_clubs'),
  path('<int:federation_id>/import/clubs/', import_clubs, name='import_clubs'),
]