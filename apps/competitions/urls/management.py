from django.urls import path
from apps.competitions.views.management import scoring, schedule, dashboard, participants, judges, results, podium, cockpit

app_name = 'management'

urlpatterns = [
    # ===== DASHBOARD =====
    path('<int:competition_id>/dashboard/', dashboard.management_dashboard, name='dashboard'),
    path('<int:competition_id>/cancel/', dashboard.competition_status_update, name='cancel_competition'),

    # ===== COCKPIT (Tableau de pilotage) =====
    path('<int:competition_id>/cockpit/', cockpit.competition_cockpit, name='cockpit'),
    path('<int:competition_id>/cockpit/api/', cockpit.cockpit_api, name='cockpit_api'),
    path('<int:competition_id>/cockpit/create-aire/', cockpit.cockpit_create_aire, name='cockpit_create_aire'),
    path('<int:competition_id>/cockpit/delete-aire/', cockpit.cockpit_delete_aire, name='cockpit_delete_aire'),
    path('<int:competition_id>/cockpit/assign-judge/', cockpit.cockpit_assign_judge, name='cockpit_assign_judge'),
    path('<int:competition_id>/cockpit/assign-category/', cockpit.cockpit_assign_category, name='cockpit_assign_category'),
    path('<int:competition_id>/cockpit/unassign-category/', cockpit.cockpit_unassign_category, name='cockpit_unassign_category'),
    path('<int:competition_id>/cockpit/create-placateur/', cockpit.cockpit_create_placateur, name='cockpit_create_placateur'),
    path('<int:competition_id>/cockpit/assign-placateur/', cockpit.cockpit_assign_placateur, name='cockpit_assign_placateur'),
    path('<int:competition_id>/cockpit/judge-action/', cockpit.cockpit_judge_action, name='cockpit_judge_action'),
    path('<int:competition_id>/cockpit/category/<int:category_id>/registrations/', cockpit.cockpit_category_registrations, name='cockpit_category_registrations'),
    path('<int:competition_id>/cockpit/close-session/<int:session_id>/', cockpit.cockpit_close_session, name='cockpit_close_session'),
    path('<int:competition_id>/status-update/', dashboard.competition_status_update, name='competition_status_update'),
    
    # ===== PARTICIPANTS =====
    # URLs spécifiques AVANT les URLs générales pour éviter les conflits de matching
    path('<int:competition_id>/participants/detail/<int:registration_id>/', participants.participant_detail, name='participant_detail'),
    path('<int:competition_id>/participants/search/', participants.participant_search, name='participant_search'),
    path('<int:competition_id>/participants/export/', participants.export_participants, name='export_participants'),
    path('<int:competition_id>/participants/club/<int:club_id>/', participants.club_participants, name='club_participants'),
    path('<int:competition_id>/participants/bulk-approval/', participants.bulk_approval, name='bulk_approval'),
    path('<int:competition_id>/participants/bulk-action/', participants.bulk_action_participants, name='bulk_action_participants'),
    path('<int:competition_id>/participants/category-assignment/', participants.category_assignment, name='category_assignment'),
    path('<int:competition_id>/participants/<int:registration_id>/approve/', participants.approve_participant, name='approve_participant'),
    path('<int:competition_id>/participants/<int:registration_id>/reject/', participants.reject_participant, name='reject_participant'),
    path('<int:competition_id>/participants/<int:registration_id>/delete/', participants.delete_participant, name='delete_participant'),
    path('<int:competition_id>/participants/<int:registration_id>/assign-categories/', participants.assign_categories, name='assign_categories'),
    path('<int:competition_id>/participants/<int:registration_id>/update-status/', participants.update_registration_status, name='update_registration_status'),
    # URL générale en dernier
    path('<int:competition_id>/participants/', participants.participants_list, name='participants'),
    
    # ===== JUDGES =====
    path('<int:competition_id>/judges/', judges.judges_list, name='judges'),
    path('<int:competition_id>/judges/add/', judges.add_judge_assignment, name='add_judge'),
    path('<int:competition_id>/judges/detail/<int:assignment_id>/', judges.judge_detail, name='judge_detail'),
    path('<int:competition_id>/judges/remove/<int:user_id>/', judges.remove_judge_from_competition, name='remove_judge'),
    path('<int:competition_id>/judges/remove-registration/<int:registration_id>/', judges.remove_judge_registration, name='remove_judge_registration'),
    path('<int:competition_id>/judges/assignment/<int:assignment_id>/delete/', judges.delete_judge_assignment, name='delete_judge_assignment'),
    
    # ===== RESULTS =====
    path('<int:competition_id>/results/', results.results_dashboard, name='results'),
    path('<int:competition_id>/results/all/', results.all_competition_results, name='all_competition_results'),
    path('<int:competition_id>/results/club/', results.club_results, name='club_results'),
    path('<int:competition_id>/results/medals/', results.medals_report, name='medals_report'),
    path('<int:competition_id>/results/share/', results.public_results_link, name='public_results_link'),
    path('<int:competition_id>/results/publish/', results.publish_all_results, name='publish_all_results'),
    path('<int:competition_id>/results/category/<int:category_id>/', results.category_results, name='category_results'),
    path('<int:competition_id>/results/category/<int:category_id>/calculate/', results.calculate_category_results, name='calculate_category_results'),
    path('<int:competition_id>/results/category/<int:category_id>/podium/', results.podium_preview, name='podium_preview'),
    path('<int:competition_id>/results/export/', results.export_all_results, name='export_all_results'),
    
    # ===== SCORING DASHBOARD =====
    path('scoring/<int:competition_id>/', scoring.scoring_dashboard, name='scoring_dashboard'),
    path('scoring/<int:competition_id>/category/<int:category_id>/scores-api/', scoring.category_scores_api, name='category_scores_api'),
    path('scoring/<int:competition_id>/global-setup/', scoring.competition_scoring_global_setup, name='competition_scoring_global'),
    
    # ===== CATEGORY SCORING SETUP =====
    path('scoring/<int:competition_id>/category/<int:category_id>/setup/',
         scoring.category_scoring_setup, name='category_scoring_setup'),
    path('scoring/<int:competition_id>/category/<int:category_id>/statistics/',
         scoring.scoring_statistics, name='scoring_statistics'),
    path('scoring/<int:competition_id>/admin/',
         scoring.scoring_dashboard, name='admin_scoring_interface'),
    path('scoring/<int:competition_id>/admin/category/<int:category_id>/',
         scoring.category_scoring_setup, name='admin_scoring_interface_category'),

    # ===== SCORING CRITERIA =====
    path('scoring/<int:competition_id>/category/<int:category_id>/criterion/add/',
         scoring.add_scoring_criterion, name='add_scoring_criterion'),
    path('scoring/<int:competition_id>/criterion/<int:criterion_id>/edit/',
         scoring.edit_scoring_criterion, name='edit_scoring_criterion'),
    path('scoring/<int:competition_id>/criterion/<int:criterion_id>/delete/',
         scoring.delete_scoring_criterion, name='delete_scoring_criterion'),
    
    # ===== JUDGE SCORING INTERFACE =====
    path('scoring/<int:competition_id>/category/<int:category_id>/judge/<int:judge_id>/', 
         scoring.judge_scoring_interface, name='judge_scoring_interface'),
    
    # ===== MANAGE PERFORMANCES =====
    path('scoring/<int:competition_id>/category/<int:category_id>/performances/',
         scoring.manage_performances, name='manage_performances'),
    path('scoring/<int:competition_id>/category/<int:category_id>/performances/add/',
         scoring.add_performance, name='add_performance'),
    path('scoring/<int:competition_id>/category/<int:category_id>/performances/reorder/',
         scoring.reorder_performances, name='reorder_performances'),

    # ===== PERFORMANCE MANAGEMENT =====
    path('scoring/<int:competition_id>/performance/<int:performance_id>/start/',
         scoring.start_performance, name='start_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/end/',
         scoring.end_performance, name='end_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/edit/',
         scoring.edit_performance, name='edit_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/delete/',
         scoring.delete_performance, name='delete_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/scores/',
         scoring.performance_scores, name='performance_scores'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/scorecard/',
         scoring.performance_scorecard, name='performance_scorecard'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/add-score/',
         scoring.add_score, name='add_score'),
    path('scoring/<int:competition_id>/score/<int:score_id>/delete/',
         scoring.delete_score, name='delete_score'),
    
    # ===== SAVE JUDGE SCORES =====
    path('scoring/<int:competition_id>/category/<int:category_id>/judge/<int:judge_id>/performance/<int:performance_id>/save/', 
         scoring.save_judge_scores, name='save_judge_scores'),
    
    # ===== RESULTS =====
    path('scoring/<int:competition_id>/category/<int:category_id>/results/',
         scoring.category_results, name='category_results'),
    path('scoring/<int:competition_id>/category/<int:category_id>/calculate/',
         scoring.calculate_results, name='calculate_results'),
    path('scoring/<int:competition_id>/category/<int:category_id>/launch-tour2/',
         scoring.launch_tour2, name='launch_tour2'),
    path('scoring/<int:competition_id>/category/<int:category_id>/close-tour2/',
         scoring.close_tour2, name='close_tour2'),
    path('scoring/<int:competition_id>/category/<int:category_id>/publish/',
         scoring.publish_results, name='publish_results'),
    path('scoring/<int:competition_id>/category/<int:category_id>/podium/',
         scoring.podium_view, name='podium_view'),
    path('scoring/<int:competition_id>/category/<int:category_id>/export/',
         scoring.export_results, name='export_results'),

    # ===== GENERATE ALL RESULTS =====
    path('scoring/<int:competition_id>/generate-results/',
         scoring.generate_all_results, name='generate_all_results'),
    
    # ===== REORDER CRITERIA =====
    path('scoring/<int:competition_id>/category/<int:category_id>/reorder-criteria/', 
         scoring.reorder_scoring_criteria, name='reorder_scoring_criteria'),
    
    # ===== SCHEDULE MANAGEMENT =====
    path('schedule/<int:competition_id>/', schedule.schedule_overview, name='schedule'),
    path('schedule/<int:competition_id>/overview/', schedule.schedule_overview, name='schedule_overview'),
    path('schedule/<int:competition_id>/edit/', schedule.edit_competition_schedule, name='schedule_edit'),
    path('schedule/<int:competition_id>/publish/', schedule.publish_schedule, name='schedule_publish'),
    path('schedule/<int:competition_id>/category/add/', schedule.add_category_schedule, name='add_category_schedule'),
    path('schedule/<int:competition_id>/category/<int:category_schedule_id>/edit/', schedule.edit_category_schedule, name='edit_category_schedule'),
    path('schedule/<int:competition_id>/category/<int:category_schedule_id>/remove/', schedule.remove_category_schedule, name='remove_category_schedule'),
    path('schedule/<int:competition_id>/category/<int:category_schedule_id>/matches/', schedule.match_schedule, name='match_schedule'),
    path('schedule/<int:competition_id>/bulk-schedule/', schedule.bulk_category_scheduling, name='bulk_category_scheduling'),
    path('schedule/<int:competition_id>/optimize/', schedule.optimize_schedule, name='optimize_schedule'),
    path('schedule/<int:competition_id>/conflicts/', schedule.check_schedule_conflicts, name='check_schedule_conflicts'),
    path('schedule/<int:competition_id>/export/', schedule.export_schedule, name='export_schedule'),
    path('schedule/<int:competition_id>/api/category-info/', schedule.api_category_info, name='api_category_info'),
    path('schedule/<int:competition_id>/api/quick-add/', schedule.api_quick_add_category, name='api_quick_add_category'),
    path('schedule/<int:competition_id>/api/next-time/', schedule.api_get_next_available_time, name='api_next_available_time'),

    # ===== PODIUM MANAGEMENT =====
    path('<int:competition_id>/category/<int:category_id>/podium/', podium.podium_management, name='podium_management'),
    path('<int:competition_id>/category/<int:category_id>/podium/add/', podium.add_podium_entry, name='add_podium_entry'),
    path('<int:competition_id>/category/<int:category_id>/podium/<int:entry_id>/remove/', podium.remove_podium_entry, name='remove_podium_entry'),
    path('<int:competition_id>/category/<int:category_id>/podium/<int:entry_id>/update/', podium.update_podium_entry, name='update_podium_entry'),
    path('<int:competition_id>/category/<int:category_id>/podium/display/', podium.podium_display, name='podium_display'),
    path('<int:competition_id>/category/<int:category_id>/podium/ceremony/', podium.podium_ceremony, name='podium_ceremony'),
    path('<int:competition_id>/category/<int:category_id>/podium/api/available-practitioners/', podium.get_available_practitioners, name='api_available_practitioners'),

    # ===== QUICK ACTIONS =====
    path('<int:competition_id>/add-category/', dashboard.management_dashboard, name='add_category'),  # Redirection vers dashboard
    path('<int:competition_id>/start/', dashboard.management_dashboard, name='start_competition'),  # Redirection vers dashboard

    # ===== COMPETITION CLOSURE =====
    path('<int:competition_id>/close/', dashboard.close_competition, name='close_competition'),
    path('<int:competition_id>/close/api/', dashboard.close_competition_api, name='close_competition_api'),
]
