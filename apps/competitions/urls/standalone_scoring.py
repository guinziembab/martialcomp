from django.urls import path
from apps.competitions.views.standalone_scoring import (
    # Judge Views
    JudgePerformanceListView,
    JudgeScoreEntryView,
    JudgeSubmitScoresView,
    JudgeSettingsView,
    
    # Admin Views
    StandaloneScoringDashboardView,
    ResultsCalculationView,
    RankingsListView,
    PerformanceCreateView,
    PerformanceUpdateView,
    PerformanceDetailView,
    ScoringSystemCreateView,
    ScoringSystemUpdateView,
    ScoringCriterionListView,
    ScoringCriterionCreateView,
    ScoringCriterionUpdateView,
    CategoryScoringConfigView,
)

app_name = 'standalone_scoring'

urlpatterns = [
    # ===== JUDGE INTERFACES =====
    path('judge/performances/', JudgePerformanceListView.as_view(), name='judge_performances'),
    path('judge/score/<int:performance_id>/', JudgeScoreEntryView.as_view(), name='judge_score_entry'),
    path('judge/submit-scores/<int:performance_id>/', JudgeSubmitScoresView.as_view(), name='judge_submit_scores'),
    path('judge/settings/', JudgeSettingsView.as_view(), name='judge_settings'),
    
    # ===== ADMIN INTERFACES =====
    path('admin/dashboard/', StandaloneScoringDashboardView.as_view(), name='admin_dashboard'),
    path('admin/calculate-results/', ResultsCalculationView.as_view(), name='calculate_results'),
    path('admin/rankings/', RankingsListView.as_view(), name='rankings'),
    
    # ===== PERFORMANCE MANAGEMENT =====
    path('admin/performances/create/', PerformanceCreateView.as_view(), name='performance_create'),
    path('admin/performances/<int:pk>/edit/', PerformanceUpdateView.as_view(), name='performance_update'),
    path('admin/performances/<int:pk>/', PerformanceDetailView.as_view(), name='performance_detail'),
    path('admin/performances/', JudgePerformanceListView.as_view(), name='performance_list'),
    
    # ===== SCORING SYSTEM MANAGEMENT =====
    path('admin/scoring-systems/create/', ScoringSystemCreateView.as_view(), name='scoring_system_create'),
    path('admin/scoring-systems/<int:pk>/edit/', ScoringSystemUpdateView.as_view(), name='scoring_system_update'),
    
    # ===== SCORING CRITERION MANAGEMENT =====
    path('admin/scoring-criteria/create/', ScoringCriterionCreateView.as_view(), name='scoring_criterion_create'),
    path('admin/scoring-criteria/<int:pk>/edit/', ScoringCriterionUpdateView.as_view(), name='scoring_criterion_update'),
    path('admin/scoring-criteria/', ScoringCriterionListView.as_view(), name='scoring_criterion_list'),
    
    # ===== CATEGORY SCORING CONFIG =====
    path('admin/category-scoring-config/<int:category_id>/', CategoryScoringConfigView.as_view(), name='category_scoring_config'),
]
