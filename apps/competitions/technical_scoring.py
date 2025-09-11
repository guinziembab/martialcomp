from apps.competitions.views.technical_scoring import (
    category_scoring_setup,
    assign_judges,
    judge_competition_detail,
    submit_score,
    judge_settings,
    judge_help,
    manage_performances,
    start_performance,
    monitor_performance,
    performance_results,
    category_results,
    judge_dashboard,
    judge_category_view,
    judge_competition_list,
    score_performance,
    public_results,
    get_performance_scores,
    get_category_results,
)

from apps.competitions.views.judge import apply_as_judge, judge_applications_status

from django.urls import path

app_name = 'technical_scoring'

urlpatterns = [
    # Configuration et setup
    path('setup/<int:category_id>/', category_scoring_setup, name='setup'),
    path('assign-judges/<int:category_id>/', assign_judges, name='assign_judges'),
    
    # Vues pour juges
    path('judge/dashboard/', judge_dashboard, name='judge_dashboard'),
    path('judge/competitions/', judge_competition_list, name='judge_competition_list'),
    path('judge/competition/<int:competition_id>/', judge_competition_detail, name='judge_competition_detail'),
    path('judge/category/<int:category_id>/', judge_category_view, name='judge_category_view'),
    path('judge/settings/', judge_settings, name='judge_settings'),
    path('judge/help/', judge_help, name='judge_help'),
    
    # Gestion des performances
    path('performances/<int:category_id>/', manage_performances, name='manage_performances'),
    path('performance/<int:performance_id>/start/', start_performance, name='start_performance'),
    path('performance/<int:performance_id>/monitor/', monitor_performance, name='monitor_performance'),
    path('performance/<int:performance_id>/results/', performance_results, name='performance_results'),
    path('performance/<int:performance_id>/score/', score_performance, name='score_performance'),
    path('performance/<int:performance_id>/submit-score/', submit_score, name='submit_score'),
    
    # Résultats
    path('category/<int:category_id>/results/', category_results, name='category_results'),
    path('category/<int:category_id>/public-results/', public_results, name='public_results'),
    
    # API
    path('api/performance/<int:performance_id>/scores/', get_performance_scores, name='get_performance_scores'),
    path('api/category/<int:category_id>/results/', get_category_results, name='get_category_results'),
]

