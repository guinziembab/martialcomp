from django.urls import path
from ..views.technical_scoring import (
    # Vues pour les managers
    category_scoring_setup,
    assign_judges,
    manage_performances,
    start_performance,
    monitor_performance,
    performance_results,
    category_results,
    
    # Vues pour les juges
    judge_dashboard,
    judge_competition_list,
    judge_competition_detail,
    judge_category_view,
    score_performance,
    submit_score,
    judge_settings,
    judge_help,

    
    # APIs
    get_performance_scores,
    get_category_results,
)

# Import spécifique de apply_as_judge depuis judge.py au lieu de technical_scoring.py
from ..views.judge import apply_as_judge, judge_applications_status

app_name = 'technical_scoring'

urlpatterns = [
    # URLs pour les managers
    path('category/<int:category_id>/setup/', 
         category_scoring_setup, 
         name='category_scoring_setup'),
    
    path('category/<int:category_id>/judges/', 
         assign_judges, 
         name='assign_judges'),
    
    path('category/<int:category_id>/performances/', 
         manage_performances, 
         name='manage_performances'),
    
    path('performance/<int:performance_id>/start/', 
         start_performance, 
         name='start_performance'),
    
    path('performance/<int:performance_id>/monitor/', 
         monitor_performance, 
         name='monitor_performance'),
    
    path('performance/<int:performance_id>/results/', 
         performance_results, 
         name='performance_results'),
    
    path('category/<int:category_id>/results/', 
         category_results, 
         name='category_results'),
    
    # URLs pour les juges
    path('judge/dashboard/', 
         judge_dashboard, 
         name='judge_dashboard'),
    
    path('judge/competitions/', 
         judge_competition_list, 
         name='judge_competition_list'),
    
    path('judge/competition/<int:competition_id>/', 
         judge_competition_detail,
         name='judge_competition_detail'),
    
    path('judge/category/<int:category_id>/', 
         judge_category_view,
         name='judge_category_view'),
    
    path('judge/performance/<int:performance_id>/score/', 
         score_performance, 
         name='score_performance'),
    
    path('judge/performance/<int:performance_id>/submit/', 
         submit_score,
         name='submit_score'),
    
    path('judge/settings/', 
         judge_settings,
         name='judge_settings'),
    
    path('judge/help/', 
         judge_help,
         name='judge_help'),
    
    path('judge/apply/', 
         apply_as_judge,  # Maintenant importé depuis judge.py
         name='apply_as_judge'),
    
    path('judge/applications/status/', 
         judge_applications_status, 
         name='judge_applications_status'),
    
    # APIs pour les mises à jour en temps réel
    path('api/performance/<int:performance_id>/scores/', 
         get_performance_scores,
         name='api_performance_scores'),
    
    path('api/category/<int:category_id>/results/', 
         get_category_results,
         name='api_category_results'),
]