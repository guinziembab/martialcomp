from django.urls import path
from apps.competitions.views.club.practitioners import (
  practitioners_list, practitioner_detail, practitioner_create, practitioner_update,
  create_user_for_practitioner, link_user_to_practitioner, send_practitioner_credentials, practitioner_delete,
  practitioner_qualifications_add, practitioner_registrations,
  create_practitioner_registration, get_available_competitions, practitioner_toggle_status,
  practitioner_search_ajax, practitioner_filter_options,
  practitioner_record_payment, practitioner_send_reminder, assign_judge_role,
  initiate_transfer, pending_transfers, approve_transfer, reject_transfer, search_clubs_api,
  update_practitioner_roles,
  quick_update_grade, get_grades_for_practitioner
)
from apps.competitions.views.club.registrations import (
  registrations_list, available_competitions, club_bulk_registration, competition_registration_form,
  register_practitioner
)
from apps.competitions.views.club.registration_api import (
  get_categories_by_type_api, competition_registration_simple, unregister_practitioner,
  available_competitions_api, bulk_registration_process,
  get_competition_teams, create_team, update_team, delete_team,
  add_team_member, remove_team_member, update_team_member, reorder_team_members,
  get_incomplete_teams, request_team_fusion, get_fusion_requests,
  accept_team_fusion, reject_team_fusion, cancel_fusion_request,
  merge_teams, generate_license_number_api
)
from apps.competitions.views.club.competitions import club_competitions, club_competition_detail, competition_management_dashboard, api_move_practitioner_category, api_remove_registration
from apps.competitions.views.club.competition_hub import competition_management_hub
from apps.competitions.views.club.competition_demo import competition_management_demo
from apps.competitions.views.club.event_organizer import event_organizer_dashboard, competition_management_detail, save_competition_schedule, toggle_category_completed
from apps.competitions.views.competition_management_v2 import competition_management_v2
from apps.competitions.views.competition_management_pro import (
    competition_management_pro, add_competition_type, delete_competition_type, update_competition_type,
    assign_to_category, remove_from_category, publish_competition, assign_judge, get_competition_stats,
    get_competition_types_api, get_competition_categories_api, get_scoring_stats_api,
    search_users_api, add_judge_to_competition, update_visibility_option
)
from apps.competitions.views.club.judges import judges_list, judge_add
from apps.competitions.views.club.technical_scoring import technical_scoring, competition_scoring
from apps.competitions.views.club.import_export import import_export_data, download_import_template, export_practitioners
from apps.competitions.views.club.training import (
    training_sessions, create_training_session, attendance_list,
    training_programs, create_training_program, edit_training_program,
    create_training_slot
)
from apps.competitions.views.club.results import club_competition_results
from apps.competitions.views.dashboard.club import club_dashboard
from apps.competitions.views.roles import (
    manage_roles, create_role, edit_role, delete_role, assign_role, revoke_role,
    get_club_members_with_roles_api, invite_club_member_api, update_member_role_api, remove_member_role_api,
    assign_role_to_practitioner_api
)
from apps.competitions.views.club.qr_management import club_qr_dashboard, regenerate_qr_code, qr_statistics
from apps.competitions.views.club.direct_registration import direct_club_registration
from apps.competitions.views.club.affiliations import (
    affiliation_action, request_affiliation, affiliation_history,
    request_renewal, my_affiliation_invoices
)

app_name = 'club'

urlpatterns = [
  # Route racine - redirige vers le dashboard
  path('', club_dashboard, name='index'),
  
  # Liste des pratiquants
  path('practitioners/', practitioners_list, name='practitioners'),
  path('practitioners/search/', practitioner_search_ajax, name='practitioner_search'),
  path('practitioners/filter-options/', practitioner_filter_options, name='practitioner_filter_options'),
  path('practitioners/add/', practitioner_create, name='practitioner_add'),
  path('practitioners/<int:pk>/', practitioner_detail, name='practitioner_detail'),
  path('practitioners/<int:pk>/edit/', practitioner_update, name='practitioner_edit'),
  path('practitioners/<int:practitioner_id>/quick-grade/', quick_update_grade, name='quick_update_grade'),
  path('practitioners/<int:practitioner_id>/grades-list/', get_grades_for_practitioner, name='grades_list_for_practitioner'),
  path('practitioners/<int:practitioner_id>/create-user/', create_user_for_practitioner,
name='create_user_for_practitioner'),
  path('practitioners/<int:practitioner_id>/link-user/', link_user_to_practitioner,
name='link_user_to_practitioner'),
  path('practitioners/<int:practitioner_id>/send-credentials/', send_practitioner_credentials, name='send_practitioner_credentials'),
  path('practitioners/<int:practitioner_id>/delete/', practitioner_delete, name='practitioner_delete'),
  path('practitioners/<int:pk>/toggle-status/', practitioner_toggle_status, name='practitioner_toggle_status'),
  path('practitioners/<int:practitioner_id>/qualifications/add/', practitioner_qualifications_add, name='qualification_add'),
  path('practitioners/<int:practitioner_id>/assign-judge/', assign_judge_role, name='assign_judge_role'),
  path('practitioners/<int:practitioner_id>/registrations/', practitioner_registrations, name='practitioner_registrations'),
  path('practitioners/<int:practitioner_id>/registrations/create/', create_practitioner_registration, name='create_practitioner_registration'),
  path('practitioners/<int:practitioner_id>/competitions/', get_available_competitions, name='get_available_competitions'),

  # Actions finances pratiquant
  path('practitioners/<int:pk>/record-payment/', practitioner_record_payment, name='practitioner_record_payment'),
  path('practitioners/<int:pk>/send-reminder/', practitioner_send_reminder, name='practitioner_send_reminder'),

  # Inscriptions
  path('registrations/', registrations_list, name='registrations_list'),
  path('available-competitions/', available_competitions, name='available_competitions'),
  path('available-competitions/api/', available_competitions_api, name='available_competitions_api'),
  path('bulk-registration/', club_bulk_registration, name='bulk_registration'),
  path('bulk-registration/process/', bulk_registration_process, name='bulk_registration_process'),
  path('competition-registration/<int:competition_id>/', competition_registration_simple, name='competition_registration_form'),
  path('competition-registration/<int:competition_id>/old/', competition_registration_form, name='competition_registration_form_old'),
  path('register/<int:competition_id>/', register_practitioner, name='register_practitioner'),
  path('register/<int:competition_id>/<int:practitioner_id>/', register_practitioner, name='register_practitioner_with_id'),
  path('unregister/<int:competition_id>/', unregister_practitioner, name='unregister_practitioner'),

  # Juges
  path('judges/', judges_list, name='judges_list'),
  path('judges/add/', judge_add, name='judge_add'),

  # Fonctionnalités techniques
  path('technical-scoring/', technical_scoring, name='technical_scoring'),
  path('technical-scoring/competition/<int:competition_id>/', competition_scoring, name='competition_scoring'),
  path('import-export/', import_export_data, name='import_export'),
  path('import-export/ajax/', import_export_data, name='import_export_ajax'),
  path('import-export/template/', download_import_template, name='download_import_template'),
  path('import-export/export/', export_practitioners, name='export_practitioners'),
  
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
  path('competitions/demo/', competition_management_demo, name='competition_demo'),
  path('competitions/organizer/', event_organizer_dashboard, name='event_organizer'),
  # Routes spécifiques avec competition_id - doivent être avant la route générique
  path('competitions/<int:competition_id>/manage/', competition_management_detail, name='competition_management_detail'),
  path('api/competitions/<int:competition_id>/schedule/save/', save_competition_schedule, name='save_competition_schedule'),
  path('api/competitions/<int:competition_id>/categories/<int:category_id>/toggle-completed/', toggle_category_completed, name='toggle_category_completed'),
  path('competitions/<int:competition_id>/hub/', competition_management_hub, name='competition_hub'),
  path('competitions/<int:competition_id>/manage/v2/', competition_management_v2, name='competition_management_v2'),
  path('competitions/<int:competition_id>/manage/pro/', competition_management_pro, name='competition_management_pro'),
  # Route générique pour le détail - doit être en dernier
  path('competitions/<int:competition_id>/', club_competition_detail, name='competition_detail'),
  
  # APIs pour la gestion des compétitions
  path('api/move-practitioner/', api_move_practitioner_category, name='api_move_practitioner'),
  path('api/remove-registration/', api_remove_registration, name='api_remove_registration'),
  
  # APIs pour la version Pro
  path('api/competitions/<int:competition_id>/types/', add_competition_type, name='api_add_competition_type'),
  path('api/competitions/<int:competition_id>/types/list/', get_competition_types_api, name='api_get_competition_types'),
  path('api/competitions/<int:competition_id>/categories/list/', get_competition_categories_api, name='api_get_competition_categories'),
  path('api/competitions/<int:competition_id>/pro/delete-type/<int:type_id>/', delete_competition_type, name='api_delete_competition_type'),
  path('api/competitions/<int:competition_id>/pro/update-type/<int:type_id>/', update_competition_type, name='api_update_competition_type'),
  path('api/competitions/<int:competition_id>/assign-category/', assign_to_category, name='api_assign_to_category'),
  path('api/competitions/<int:competition_id>/remove-category/', remove_from_category, name='api_remove_from_category'),
  path('api/competitions/<int:competition_id>/publish/', publish_competition, name='api_publish_competition'),
  path('api/competitions/<int:competition_id>/visibility/', update_visibility_option, name='api_update_visibility'),
  path('api/competitions/<int:competition_id>/assign-judge/', assign_judge, name='api_assign_judge'),
  path('api/competitions/<int:competition_id>/stats/', get_competition_stats, name='api_competition_stats'),
  path('api/competitions/<int:competition_id>/scoring-stats/', get_scoring_stats_api, name='api_scoring_stats'),
  path('api/competitions/<int:competition_id>/search-users/', search_users_api, name='api_search_users'),
  path('api/competitions/<int:competition_id>/add-judge/', add_judge_to_competition, name='api_add_judge'),

  # APIs pour la gestion des équipes
  path('api/competitions/<int:competition_id>/teams/', get_competition_teams, name='api_get_teams'),
  path('api/competitions/<int:competition_id>/teams/create/', create_team, name='api_create_team'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/update/', update_team, name='api_update_team'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/delete/', delete_team, name='api_delete_team'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/members/add/', add_team_member, name='api_add_team_member'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/members/<int:member_id>/remove/', remove_team_member, name='api_remove_team_member'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/members/<int:member_id>/update/', update_team_member, name='api_update_team_member'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/reorder/', reorder_team_members, name='api_reorder_team_members'),

  # APIs pour la fusion d'équipes inter-clubs
  path('api/competitions/<int:competition_id>/teams/incomplete/', get_incomplete_teams, name='api_incomplete_teams'),
  path('api/competitions/<int:competition_id>/teams/merge/', merge_teams, name='api_merge_teams'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/request-fusion/', request_team_fusion, name='api_request_fusion'),
  path('api/competitions/<int:competition_id>/fusion-requests/', get_fusion_requests, name='api_fusion_requests'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/accept-fusion/', accept_team_fusion, name='api_accept_fusion'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/reject-fusion/', reject_team_fusion, name='api_reject_fusion'),
  path('api/competitions/<int:competition_id>/teams/<int:team_id>/cancel-fusion/', cancel_fusion_request, name='api_cancel_fusion'),

  # Dashboard
  path('dashboard/', club_dashboard, name='dashboard'),

  # Gestion des rôles
  path('manage-roles/', manage_roles, name='manage_roles'),
  path('manage-roles/create/', create_role, name='create_role'),
  path('manage-roles/edit/<int:role_id>/', edit_role, name='edit_role'),
  path('manage-roles/delete/<int:role_id>/', delete_role, name='delete_role'),
  path('manage-roles/assign/', assign_role, name='assign_role'),
  path('manage-roles/revoke/<int:user_role_id>/', revoke_role, name='revoke_role'),

  # API Gestion des membres et rôles (pour dashboard club)
  path('api/members-roles/', get_club_members_with_roles_api, name='api_members_roles'),
  path('api/invite-member/', invite_club_member_api, name='api_invite_member'),
  path('api/update-member-role/<int:member_id>/', update_member_role_api, name='api_update_member_role'),
  path('api/remove-member/<int:member_id>/', remove_member_role_api, name='api_remove_member'),
  path('api/assign-role-to-practitioner/', assign_role_to_practitioner_api, name='api_assign_role_to_practitioner'),

  # QR Codes
  path('qr/', club_qr_dashboard, name='qr_dashboard'),
  path('qr/regenerate/<int:club_id>/', regenerate_qr_code, name='regenerate_qr'),
  path('qr/statistics/<int:club_id>/', qr_statistics, name='qr_statistics'),
  
  # Inscription directe
  path('register/', direct_club_registration, name='direct_registration'),

  # Transferts de pratiquants
  path('practitioners/<int:practitioner_id>/transfer/', initiate_transfer, name='initiate_transfer'),
  path('transfers/pending/', pending_transfers, name='pending_transfers'),
  path('transfers/<int:transfer_id>/approve/', approve_transfer, name='approve_transfer'),
  path('transfers/<int:transfer_id>/reject/', reject_transfer, name='reject_transfer'),
  path('api/clubs/search/', search_clubs_api, name='search_clubs_api'),
  path('practitioners/<int:practitioner_id>/update-roles/', update_practitioner_roles, name='update_practitioner_roles'),

  # Affiliations
  path('affiliation/action/', affiliation_action, name='affiliation_action'),
  path('affiliation/request/', request_affiliation, name='request_affiliation'),
  path('affiliations/<int:affiliation_id>/history/', affiliation_history, name='affiliation_history'),
  path('affiliations/<int:affiliation_id>/renew/', request_renewal, name='request_renewal'),
  path('affiliation-invoices/', my_affiliation_invoices, name='my_affiliation_invoices'),
]

