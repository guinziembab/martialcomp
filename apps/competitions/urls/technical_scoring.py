from django.urls import path
from apps.competitions.views.technical_scoring import (
    technical_scoring_management,
    judge_dashboard,
    judge_competition_list,
    scoring_interface,
    scoring_history,
    scoring_categories,
    # Management views
    category_scoring_setup,
    assign_judges,
    manage_performances,
    start_performance,
    monitor_performance,
    performance_results,
    category_results,
    # Judge views
    judge_competition_detail,
    judge_category_view,
    score_performance,
    submit_score,
    judge_settings,
    judge_help,
    # API views
    get_performance_scores,
    get_category_results
)

app_name = 'technical_scoring'

urlpatterns = [
    # ===== MANAGEMENT DASHBOARD =====
    path('management/', technical_scoring_management, name='management'),
    path('management/<int:competition_id>/', technical_scoring_management, name='management_competition'),
    
    # ===== JUDGE DASHBOARD =====
    path('judge/dashboard/', judge_dashboard, name='judge_dashboard'),
    path('judge/competitions/', judge_competition_list, name='judge_competition_list'),
    path('judge/competition/<int:competition_id>/', judge_competition_detail, name='judge_competition_detail'),
    path('judge/category/<int:category_id>/', judge_category_view, name='judge_category_view'),
    path('judge/settings/', judge_settings, name='judge_settings'),
    path('judge/help/', judge_help, name='judge_help'),
    
    # ===== MANAGEMENT INTERFACES =====
    path('manage/<int:competition_id>/setup/', category_scoring_setup, name='setup'),
    path('manage/<int:competition_id>/assign-judges/', assign_judges, name='assign_judges'),
    path('manage/<int:competition_id>/performances/', manage_performances, name='manage_performances'),
    path('manage/performance/<int:performance_id>/start/', start_performance, name='start_performance'),
    path('manage/performance/<int:performance_id>/monitor/', monitor_performance, name='monitor_performance'),
    
    # ===== SCORING INTERFACE =====
    path('scoring/<int:competition_id>/', scoring_interface, name='scoring_interface'),
    path('scoring/<int:competition_id>/category/<int:category_id>/', scoring_interface, name='scoring_interface_category'),
    path('score/performance/<int:performance_id>/', score_performance, name='score_performance'),
    path('score/submit/', submit_score, name='submit_score'),
    
    # ===== RESULTS AND MONITORING =====
    path('results/performance/<int:performance_id>/', performance_results, name='performance_results'),
    path('results/category/<int:category_id>/', category_results, name='category_results'),
    path('history/', scoring_history, name='scoring_history'),
    path('history/<int:competition_id>/', scoring_history, name='scoring_history_competition'),
    
    # ===== CATEGORIES MANAGEMENT =====
    path('categories/', scoring_categories, name='categories'),
    path('categories/<int:competition_id>/', scoring_categories, name='categories_competition'),
    
    # ===== API ENDPOINTS =====
    path('api/performance/<int:performance_id>/scores/', get_performance_scores, name='api_performance_scores'),
    path('api/category/<int:category_id>/results/', get_category_results, name='api_category_results'),
]