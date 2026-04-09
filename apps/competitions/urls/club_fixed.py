from django.urls import path
from apps.competitions.views.club.practitioners import (
    practitioners_list, practitioner_detail, practitioner_create, practitioner_update,
    create_user_for_practitioner, link_user_to_practitioner, practitioner_delete,
    practitioner_qualifications_add, practitioner_registrations,
    create_practitioner_registration, get_available_competitions
)
from apps.competitions.views.club.registrations import (
    registrations_list, available_competitions, club_bulk_registration, competition_registration_form,
    register_practitioner
)
from apps.competitions.views.club.competitions import club_competitions, competition_management_dashboard, api_move_practitioner_category, api_remove_registration

# Imports optionnels
try:
    from apps.competitions.views.club.competition_demo import competition_management_demo
except ImportError:
    competition_management_demo = None

try:
    from apps.competitions.views.club.event_organizer import event_organizer_dashboard, competition_management_detail
except ImportError:
    event_organizer_dashboard = None
    competition_management_detail = None

from apps.competitions.views.club.judges import judges_list, judge_add
from apps.competitions.views.club.technical_scoring import technical_scoring, competition_scoring
from apps.competitions.views.club.import_export import import_export_data
from apps.competitions.views.club.training import (
    training_sessions, create_training_session, attendance_list,
    training_programs, create_training_program, edit_training_program,
    create_training_slot
)
from apps.competitions.views.club.results import club_competition_results
from apps.competitions.views.dashboard.club import club_dashboard
from apps.competitions.views.roles import manage_roles, create_role, edit_role, delete_role, assign_role, revoke_role
from apps.competitions.views.club.qr_management import club_qr_dashboard, regenerate_qr_code, qr_statistics
from apps.competitions.views.club.direct_registration import direct_club_registration

# Imports de debug
try:
    from apps.competitions.views.club.debug_practitioners import debug_practitioner_access
except ImportError:
    debug_practitioner_access = None

try:
    from apps.competitions.views.club.test_permissions import test_permissions_view
except ImportError:
    test_permissions_view = None

app_name = 'club'

urlpatterns = [
    # Liste des pratiquants
    path('practitioners/', practitioners_list, name='practitioners'),
    path('practitioners/add/', practitioner_create, name='practitioner_add'),
    path('practitioners/<int:pk>/', practitioner_detail, name='practitioner_detail'),
    path('practitioners/<int:pk>/edit/', practitioner_update, name='practitioner_edit'),
    path('practitioners/<int:practitioner_id>/create-user/', create_user_for_practitioner,
         name='create_user_for_practitioner'),
    path('practitioners/<int:practitioner_id>/link-user/', link_user_to_practitioner,
         name='link_user_to_practitioner'),
    path('practitioners/<int:practitioner_id>/delete/', practitioner_delete, name='practitioner_delete'),
    path('practitioners/<int:practitioner_id>/qualifications/add/', practitioner_qualifications_add, name='qualification_add'),
    path('practitioners/<int:practitioner_id>/registrations/', practitioner_registrations, name='practitioner_registrations'),
    path('practitioners/<int:practitioner_id>/registrations/create/', create_practitioner_registration, name='create_practitioner_registration'),
    path('practitioners/<int:practitioner_id>/competitions/', get_available_competitions, name='get_available_competitions'),

    # Inscriptions
    path('registrations/', registrations_list, name='registrations_list'),
    path('available-competitions/', available_competitions, name='available_competitions'),
    path('bulk-registration/', club_bulk_registration, name='bulk_registration'),
    path('competition-registration/<int:competition_id>/', competition_registration_form, name='competition_registration_form'),
    path('register/<int:competition_id>/', register_practitioner, name='register_practitioner'),
    path('register/<int:competition_id>/<int:practitioner_id>/', register_practitioner, name='register_practitioner_with_id'),

    # Juges
    path('judges/', judges_list, name='judges_list'),
    path('judges/add/', judge_add, name='judge_add'),

    # Fonctionnalités techniques
    path('technical-scoring/', technical_scoring, name='technical_scoring'),
    path('technical-scoring/competition/<int:competition_id>/', competition_scoring, name='competition_scoring'),
    path('import-export/', import_export_data, name='import_export'),
    
    # Sessions d'entraînement
    path('training-sessions/', training_sessions, name='training_sessions'),
    path('training-sessions/create/', create_training_session, name='create_training_session'),
    path('training-sessions/<int:session_id>/attendance/', attendance_list, name='attendance_list'),
    
    # Training programs
    path('training-programs/', training_programs, name='training_programs'),
    path('training-programs/create/', create_training_program, name='create_training_program'),
    path('training-programs/<int:program_id>/edit/', edit_training_program, name='edit_training_program'),
    
    # Training slots
    path('training-slots/create/', create_training_slot, name='create_training_slot'),
    
    path('results/', club_competition_results, name='results'),

    # Compétitions
    path('competitions/', club_competitions, name='competitions'),
    path('club-competitions/', club_competitions, name='club_competitions'),
    path('competitions/management/', competition_management_dashboard, name='competition_management'),
    
    # APIs pour la gestion des compétitions
    path('api/move-practitioner/', api_move_practitioner_category, name='api_move_practitioner'),
    path('api/remove-registration/', api_remove_registration, name='api_remove_registration'),

    # Dashboard
    path('dashboard/', club_dashboard, name='dashboard'),

    # Gestion des rôles
    path('manage-roles/', manage_roles, name='manage_roles'),
    path('manage-roles/create/', create_role, name='create_role'),
    path('manage-roles/edit/<int:role_id>/', edit_role, name='edit_role'),
    path('manage-roles/delete/<int:role_id>/', delete_role, name='delete_role'),
    path('manage-roles/assign/', assign_role, name='assign_role'),
    path('manage-roles/revoke/<int:user_role_id>/', revoke_role, name='revoke_role'),
    
    # QR Codes
    path('qr/', club_qr_dashboard, name='qr_dashboard'),
    path('qr/regenerate/<int:club_id>/', regenerate_qr_code, name='regenerate_qr'),
    path('qr/statistics/<int:club_id>/', qr_statistics, name='qr_statistics'),
    
    # Inscription directe
    path('register/', direct_club_registration, name='direct_registration'),
]

# Ajouter les URLs optionnelles si les vues existent
if competition_management_demo:
    urlpatterns.append(path('competitions/demo/', competition_management_demo, name='competition_demo'))

if event_organizer_dashboard:
    urlpatterns.append(path('competitions/organizer/', event_organizer_dashboard, name='event_organizer'))

if competition_management_detail:
    urlpatterns.append(path('competitions/<int:competition_id>/manage/', competition_management_detail, name='competition_management_detail'))

if debug_practitioner_access:
    urlpatterns.append(path('debug-practitioners/', debug_practitioner_access, name='debug_practitioners'))

if test_permissions_view:
    urlpatterns.append(path('test-permissions/', test_permissions_view, name='test_permissions'))