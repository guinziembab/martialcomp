from django.urls import path
from django.conf import settings
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
    get_category_results,
    # PROMPT 8: Feuille de notation
    scoring_sheet,
    get_provisional_ranking,
    lock_scores,
    submit_performance_score,
    get_performance_criteria,
    # PROMPT 9: Pavé numérique de notation
    save_score,
    get_numpad_context,
    # PROMPT 10: Verrouillage et classement
    lock_judge_scores,
    get_lock_status,
    get_ranking_with_ties,
    check_can_modify_score,
    # Reset scores (pour les tests)
    reset_category_scores,
    # Analyse de neutralité des juges
    judge_neutrality,
    judge_neutrality_api,
)
from apps.competitions.views.session_workflow import (
    session_start, session_stop, session_validate, session_close,
    session_progress, head_judge_panel, admin_sessions_dashboard,
)
from apps.competitions.views.placateur import (
    placateur_login, placateur_logout, placateur_categories,
    placateur_call_list_page, placateur_call_list_api, placateur_call_action,
)
# PROMPT 9: Demo views (only in DEBUG mode)
from apps.competitions.views.demo_numpad import (
    demo_numpad_view,
    demo_get_criteria,
    demo_save_score,
    demo_get_ranking,
    demo_reset_scores,
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

    # ===== PROMPT 8: FEUILLE DE NOTATION =====
    path('sheet/category/<int:category_id>/', scoring_sheet, name='scoring_sheet'),
    path('api/category/<int:category_id>/ranking/', get_provisional_ranking, name='api_provisional_ranking'),
    path('api/category/<int:category_id>/lock/', lock_scores, name='api_lock_scores'),
    path('api/performance/<int:performance_id>/submit/', submit_performance_score, name='api_submit_score'),
    path('api/performance/<int:performance_id>/criteria/', get_performance_criteria, name='api_performance_criteria'),

    # ===== PROMPT 9: PAVÉ NUMÉRIQUE DE NOTATION =====
    path('save-score/', save_score, name='save_score'),
    path(
        'api/numpad/<int:performance_id>/<int:criterion_id>/',
        get_numpad_context,
        name='api_numpad_context'
    ),

    # ===== PROMPT 9: DÉMONSTRATION (DEBUG uniquement) =====
    path('demo/', demo_numpad_view, name='demo_numpad'),
    path('demo/criteria/<int:performance_id>/', demo_get_criteria, name='demo_criteria'),
    path('demo/save-score/', demo_save_score, name='demo_save_score'),
    path('demo/ranking/<int:category_id>/', demo_get_ranking, name='demo_ranking'),
    path('demo/reset/', demo_reset_scores, name='demo_reset'),

    # ===== PROMPT 10: VERROUILLAGE ET CLASSEMENT =====
    path(
        'api/category/<int:category_id>/lock-judge/',
        lock_judge_scores,
        name='api_lock_judge_scores'
    ),
    path(
        'api/category/<int:category_id>/lock-status/',
        get_lock_status,
        name='api_lock_status'
    ),
    path(
        'api/category/<int:category_id>/ranking-ties/',
        get_ranking_with_ties,
        name='api_ranking_with_ties'
    ),
    path(
        'api/performance/<int:performance_id>/can-modify/',
        check_can_modify_score,
        name='api_can_modify_score'
    ),

    # ===== RESET SCORES (pour les tests) =====
    path(
        'api/category/<int:category_id>/reset-scores/',
        reset_category_scores,
        name='api_reset_scores'
    ),

    # ===== ANALYSE DE NEUTRALITÉ DES JUGES =====
    path('neutrality/', judge_neutrality, name='judge_neutrality'),
    path('neutrality/<int:competition_id>/', judge_neutrality, name='judge_neutrality_competition'),
    path('api/neutrality/<int:competition_id>/', judge_neutrality_api, name='api_judge_neutrality'),

    # ===== SESSION WORKFLOW (Juge Principal) =====
    path('session/<int:session_id>/start/', session_start, name='session_start'),
    path('session/<int:session_id>/stop/', session_stop, name='session_stop'),
    path('session/<int:session_id>/validate/', session_validate, name='session_validate'),
    path('session/<int:session_id>/close/', session_close, name='session_close'),
    path('session/<int:session_id>/progress/', session_progress, name='session_progress'),
    path('session/<int:session_id>/head-judge/', head_judge_panel, name='head_judge_panel'),
    path('sessions/<int:competition_id>/', admin_sessions_dashboard, name='admin_sessions_dashboard'),

    # ===== PLACATEUR (accès public via token + PIN) =====
    path('placateur/<uuid:token>/login/', placateur_login, name='placateur_login'),
    path('placateur/<uuid:token>/logout/', placateur_logout, name='placateur_logout'),
    path('placateur/<uuid:token>/categories/', placateur_categories, name='placateur_categories'),
    path('placateur/<uuid:token>/category/<int:category_id>/', placateur_call_list_page, name='placateur_call_list'),
    path('placateur/<uuid:token>/category/<int:category_id>/api/', placateur_call_list_api, name='placateur_call_list_api'),
    path('placateur/<uuid:token>/call/<int:call_status_id>/action/', placateur_call_action, name='placateur_call_action'),
]
