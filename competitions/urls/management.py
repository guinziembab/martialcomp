from django.urls import path

from competitions.views.management import (
    dashboard, participants, judges, schedule, scoring, results
)

app_name = 'management'

urlpatterns = [
    # Dashboard de gestion
    path('', dashboard.management_dashboard, name='dashboard'),
    path('status-update/<int:competition_id>/', dashboard.competition_status_update, name='competition_status_update'),
    path('category-progress/<int:competition_id>/<int:category_id>/', dashboard.category_progress_update, name='category_progress_update'),
    path('quick-stats/<int:competition_id>/', dashboard.quick_stats, name='quick_stats'),
    
    # Gestion des participants
    path('participants/<int:competition_id>/', participants.participants_list, name='participants_list'),
    path('participants/<int:competition_id>/detail/<int:registration_id>/', participants.participant_detail, name='participant_detail'),
    path('participants/<int:competition_id>/update-status/<int:registration_id>/', participants.update_registration_status, name='update_registration_status'),
    path('participants/<int:competition_id>/bulk-approval/', participants.bulk_approval, name='bulk_approval'),
    path('participants/<int:competition_id>/category-assignment/', participants.category_assignment, name='category_assignment'),
    path('participants/<int:competition_id>/search/', participants.participant_search, name='participant_search'),
    path('participants/<int:competition_id>/club/<int:club_id>/', participants.club_participants, name='club_participants'),
    path('participants/<int:competition_id>/export/', participants.export_participants, name='export_participants'),
    
    # Gestion des juges
    path('judges/<int:competition_id>/', judges.judges_list, name='judges_list'),
    path('judges/<int:competition_id>/detail/<int:assignment_id>/', judges.judge_detail, name='judge_detail'),
    path('judges/<int:competition_id>/add/', judges.add_judge_assignment, name='add_judge_assignment'),
    path('judges/<int:competition_id>/delete/<int:assignment_id>/', judges.delete_judge_assignment, name='delete_judge_assignment'),
    path('judges/<int:competition_id>/bulk-assignment/', judges.bulk_judge_assignment, name='bulk_judge_assignment'),
    path('judges/<int:competition_id>/search/', judges.judge_search, name='judge_search'),
    path('judges/<int:competition_id>/schedule/', judges.judge_schedule, name='judge_schedule'),
    path('judges/<int:competition_id>/stats/', judges.judge_stats, name='judge_stats'),
    
    # Gestion du planning
    path('schedule/<int:competition_id>/', schedule.schedule_overview, name='schedule_overview'),
    path('schedule/<int:competition_id>/edit/', schedule.edit_competition_schedule, name='edit_competition_schedule'),
    path('schedule/<int:competition_id>/tatami/<int:tatami_id>/edit/', schedule.edit_tatami, name='edit_tatami'),
    path('schedule/<int:competition_id>/category/add/', schedule.add_category_schedule, name='add_category_schedule'),
    path('schedule/<int:competition_id>/category/<int:category_schedule_id>/edit/', schedule.edit_category_schedule, name='edit_category_schedule'),
    path('schedule/<int:competition_id>/category/<int:category_schedule_id>/remove/', schedule.remove_category_schedule, name='remove_category_schedule'),
    path('schedule/<int:competition_id>/reorder-categories/', schedule.reorder_categories, name='reorder_categories'),
    path('schedule/<int:competition_id>/category/<int:category_schedule_id>/matches/', schedule.match_schedule, name='match_schedule'),
    path('schedule/<int:competition_id>/category/<int:category_schedule_id>/matches/add/', schedule.add_match_time_slot, name='add_match_time_slot'),
    path('schedule/<int:competition_id>/time-slot/<int:time_slot_id>/edit/', schedule.edit_match_time_slot, name='edit_match_time_slot'),
    path('schedule/<int:competition_id>/time-slot/<int:time_slot_id>/delete/', schedule.delete_match_time_slot, name='delete_match_time_slot'),
    path('schedule/<int:competition_id>/bulk-scheduling/', schedule.bulk_category_scheduling, name='bulk_category_scheduling'),
    path('schedule/<int:competition_id>/optimize/', schedule.optimize_schedule, name='optimize_schedule'),
    path('schedule/<int:competition_id>/conflicts/', schedule.check_schedule_conflicts, name='check_schedule_conflicts'),
    path('schedule/<int:competition_id>/publish/', schedule.publish_schedule, name='publish_schedule'),
    path('schedule/<int:competition_id>/unpublish/', schedule.unpublish_schedule, name='unpublish_schedule'),
    path('schedule/<int:competition_id>/export/', schedule.export_schedule, name='export_schedule'),
    
    # Gestion de la notation
    path('scoring/<int:competition_id>/', scoring.scoring_dashboard, name='scoring_dashboard'),
    path('scoring/<int:competition_id>/category/<int:category_id>/setup/', scoring.category_scoring_setup, name='category_scoring_setup'),
    path('scoring/<int:competition_id>/category/<int:category_id>/criterion/add/', scoring.add_scoring_criterion, name='add_scoring_criterion'),
    path('scoring/<int:competition_id>/criterion/<int:criterion_id>/edit/', scoring.edit_scoring_criterion, name='edit_scoring_criterion'),
    path('scoring/<int:competition_id>/criterion/<int:criterion_id>/delete/', scoring.delete_scoring_criterion, name='delete_scoring_criterion'),
    path('scoring/<int:competition_id>/category/<int:category_id>/reorder-criteria/', scoring.reorder_scoring_criteria, name='reorder_scoring_criteria'),
    path('scoring/<int:competition_id>/category/<int:category_id>/performances/', scoring.manage_performances, name='manage_performances'),
    path('scoring/<int:competition_id>/category/<int:category_id>/performance/add/', scoring.add_performance, name='add_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/edit/', scoring.edit_performance, name='edit_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/delete/', scoring.delete_performance, name='delete_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/start/', scoring.start_performance, name='start_performance'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/end/', scoring.end_performance, name='end_performance'),
    path('scoring/<int:competition_id>/category/<int:category_id>/reorder-performances/', scoring.reorder_performances, name='reorder_performances'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/scores/', scoring.performance_scores, name='performance_scores'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/add-score/', scoring.add_score, name='add_score'),
    path('scoring/<int:competition_id>/score/<int:score_id>/delete/', scoring.delete_score, name='delete_score'),
    path('scoring/<int:competition_id>/category/<int:category_id>/calculate-results/', scoring.calculate_results, name='calculate_results'),
    path('scoring/<int:competition_id>/category/<int:category_id>/results/', scoring.category_results, name='category_results'),
    path('scoring/<int:competition_id>/category/<int:category_id>/export-results/', scoring.export_results, name='export_results'),
    path('scoring/<int:competition_id>/judge/<int:judge_id>/category/<int:category_id>/', scoring.judge_scoring_interface, name='judge_scoring_interface'),
    path('scoring/<int:competition_id>/judge/<int:judge_id>/category/<int:category_id>/performance/<int:performance_id>/save-scores/', scoring.save_judge_scores, name='save_judge_scores'),
    path('scoring/<int:competition_id>/performance/<int:performance_id>/scorecard/', scoring.performance_scorecard, name='performance_scorecard'),
    path('scoring/<int:competition_id>/category/<int:category_id>/statistics/', scoring.scoring_statistics, name='scoring_statistics'),
    path('scoring/<int:competition_id>/generate-all-results/', scoring.generate_all_results, name='generate_all_results'),
    path('scoring/<int:competition_id>/category/<int:category_id>/publish-results/', scoring.publish_results, name='publish_results'),
    path('scoring/<int:competition_id>/category/<int:category_id>/podium/', scoring.podium_view, name='podium_view'),
    
    # Gestion des résultats
    path('results/<int:competition_id>/', results.results_dashboard, name='results_dashboard'),
    path('results/<int:competition_id>/category/<int:category_id>/', results.category_results, name='category_results'),
    path('results/<int:competition_id>/category/<int:category_id>/calculate/', results.calculate_category_results, name='calculate_category_results'),
    path('results/<int:competition_id>/ranking/<int:ranking_id>/edit/', results.edit_ranking, name='edit_ranking'),
    path('results/<int:competition_id>/ranking/<int:ranking_id>/delete/', results.delete_ranking, name='delete_ranking'),
    path('results/<int:competition_id>/all/', results.all_competition_results, name='all_competition_results'),
    path('results/<int:competition_id>/export/', results.export_all_results, name='export_all_results'),
    path('results/<int:competition_id>/clubs/', results.club_results, name='club_results'),
    path('results/<int:competition_id>/publish-all/', results.publish_all_results, name='publish_all_results'),
    path('results/<int:competition_id>/category/<int:category_id>/podium-preview/', results.podium_preview, name='podium_preview'),
    path('results/<int:competition_id>/medals-report/', results.medals_report, name='medals_report'),
    path('results/<int:competition_id>/public-link/', results.public_results_link, name='public_results_link'),
]