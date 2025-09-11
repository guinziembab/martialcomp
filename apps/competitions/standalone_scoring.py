from django.urls import path
from apps.competitions.views.standalone_scoring import (
    # Judge views
    JudgeScoreEntryView,
    JudgePerformanceListView,
    JudgeSubmitScoresView,
    JudgeSettingsView,
    
    # Admin/Manager views
    StandaloneScoringDashboardView,
    PerformanceCreateView,
    PerformanceUpdateView,
    PerformanceDetailView,
    PerformanceListView,
    ManagePerformanceStatusView,
    ScoringSystemListView,
    ScoringSystemCreateView,
    ScoringSystemUpdateView,
    ScoringCriterionListView,
    ScoringCriterionCreateView,
    ScoringCriterionUpdateView,
    CategoryScoringConfigView,
    ResultsCalculationView,
    RankingsListView,
    RankingsPublishView,
    CreateRankingSnapshotView,
)

# URLs for judge scoring interface
judge_patterns = [
    path('judge/performances/', JudgePerformanceListView.as_view(), name='judge_performances'),
    path('judge/score/<int:performance_id>/', JudgeScoreEntryView.as_view(), name='judge_score_entry'),
    path('judge/submit/<int:performance_id>/', JudgeSubmitScoresView.as_view(), name='judge_submit_scores'),
    path('judge/settings/', JudgeSettingsView.as_view(), name='judge_settings'),
]

# URLs for competition admin/manager
manager_patterns = [
    # Dashboard
    path('dashboard/', StandaloneScoringDashboardView.as_view(), name='scoring_dashboard'),
    
    # Performance management
    path('performances/', PerformanceListView.as_view(), name='performance_list'),
    path('performances/create/', PerformanceCreateView.as_view(), name='performance_create'),
    path('performances/<int:pk>/', PerformanceDetailView.as_view(), name='performance_detail'),
    path('performances/<int:pk>/update/', PerformanceUpdateView.as_view(), name='performance_update'),
    path('performances/<int:pk>/status/', ManagePerformanceStatusView.as_view(), name='performance_status'),
    
    # Scoring system management
    path('systems/', ScoringSystemListView.as_view(), name='scoring_system_list'),
    path('systems/create/', ScoringSystemCreateView.as_view(), name='scoring_system_create'),
    path('systems/<int:pk>/update/', ScoringSystemUpdateView.as_view(), name='scoring_system_update'),
    
    # Criteria management
    path('criteria/', ScoringCriterionListView.as_view(), name='scoring_criterion_list'),
    path('criteria/create/', ScoringCriterionCreateView.as_view(), name='scoring_criterion_create'),
    path('criteria/<int:pk>/update/', ScoringCriterionUpdateView.as_view(), name='scoring_criterion_update'),
    
    # Category configuration
    path('categories/<int:category_id>/config/', CategoryScoringConfigView.as_view(), name='category_scoring_config'),
    
    # Results and rankings
    path('results/calculate/<int:category_id>/', ResultsCalculationView.as_view(), name='calculate_results'),
    path('rankings/<int:category_id>/', RankingsListView.as_view(), name='rankings_list'),
    path('rankings/<int:category_id>/publish/', RankingsPublishView.as_view(), name='rankings_publish'),
    path('rankings/<int:category_id>/snapshot/', CreateRankingSnapshotView.as_view(), name='create_ranking_snapshot'),
]

# Define the app name for namespace
app_name = 'standalone_scoring'

# Combine all URL patterns
urlpatterns = judge_patterns + manager_patterns
