from django.core.exceptions import PermissionDenied
# Importer toutes les vues pour qu'elles soient accessibles depuis competitions.views

# Vues d'authentification
from .auth import logout_view, login_view, signup_view

# Vues CSRF
from .csrf_views import refresh_csrf_token, csrf_failure, get_csrf_token, test_csrf

# Vues d'accueil
from .welcome import welcome
from .home import home
from .register_view import register_view

# Vues de dashboard (structure modulaire)
from .dashboard.base import dashboard
from .dashboard.admin import admin_dashboard
from .dashboard.club import club_dashboard
from .dashboard.referee import referee_dashboard
from .dashboard.participant import participant_dashboard
from .dashboard.spectator import spectator_dashboard
from .dashboard.pro import dashboard_pro
from .dashboard.manager import manager_dashboard
from .dashboard.federations import federation_dashboard

# Vues de compétitions
from .competitions import (
    competition_list, 
    competition_create, 
    competition_detail,
    competition_update, 
    competition_delete, 
    export_competition_registrations,
    register_for_competition,
    manage_competition_registrations,
    competition_categories,
    get_competition_types,
    get_competition_types_by_discipline
)

# Vues de catégories
from .categories import (
    competition_categories,
    add_category,
    delete_category
)

# Vues de fédérations
from .federations import (
    federation_list,
    federation_detail,
    federation_create,
    federation_update,
    federation_delete,
    federation_competitions,
    federation_judges,
    federation_calendar,
    federation_trainings,
    federation_certifications,
    create_certification,
    certification_detail
)

# Vues de combat
from .combat import (
    liste_configurations,
    creer_configuration,
    modifier_configuration,
    supprimer_configuration,
    liste_equipes,
    creer_equipe,
    detail_equipe,
    modifier_equipe,
    supprimer_equipe,
    ajouter_membre_equipe,
    modifier_membre_equipe,
    supprimer_membre_equipe,
    liste_poules,
    creer_poule,
    detail_poule,
    modifier_poule,
    supprimer_poule,
    generer_poules,
    liste_combats,
    detail_combat,
    creer_combat,
    modifier_combat,
    supprimer_combat,
    demarrer_combat,
    terminer_combat,
    annuler_combat,
    ajouter_action,
    annuler_action,
    interface_combat,
    monitor_match,
    affichage_combat,
    api_statut_combat,
    api_liste_actions
)

# Vues de club (structure modulaire)
from .club.practitioners import (
    practitioners_list,
    practitioner_create,
    practitioner_update,
    practitioner_detail,
    practitioner_delete,
    create_user_for_practitioner,
    link_user_to_practitioner
)

from .club.registrations import (
    registrations_list,
    register_practitioner,
    available_competitions,
    register_multiple_practitioners,
    competition_registration_form,
    club_bulk_registration,
    select_practitioner_for_registration,
    cancel_registration
)

from .club.qualifications import (
    qualification_form,
    judges_list,
    delete_qualification
)

from .club.import_export import (
    import_export_data
)

from .club.profiles import (
    user_profile, 
    practitioner_profile,
    update_practitioner_profile
)

# Vues de juge
from .judge import (
    judge_dashboard,
    judge_profile,
    upcoming_competitions,
    apply_as_judge
)

# Vues d'onboarding
from .onboarding.base import onboarding_start
from .onboarding.role import handle_role_selection
from .onboarding.federations import handle_federation_creation
from .onboarding.club import handle_club_creation, handle_club_details
from .onboarding.categories import handle_categories_setup
from .onboarding.judge import handle_judge_profile
from .onboarding.participant import handle_participant_profile
from .onboarding.final import handle_final_setup

# Vues de notation technique
from .technical_scoring import (
    # Vues pour les managers
    category_scoring_setup,
    assign_judges,
    manage_performances,
    start_performance,
    monitor_performance,
    performance_results,
    category_results,
    
    # Vues pour les juges
    judge_dashboard as technical_judge_dashboard,
    judge_competition_list,
    judge_competition_detail,
    judge_category_view,
    score_performance,
    submit_score,
    judge_settings,
    judge_help,
    
    # APIs
    get_performance_scores,
    get_category_results
)

# Vues pratiquant
from .practitioner_dashboard import (
    dashboard,
    profile,
    activities,
    grades,
    competitions,
    memberships,
    statistics
)

from .practitioner_extra import (
    practitioner_orders,
    practitioner_order_detail,
    practitioner_notifications,
    practitioner_notification_mark_read,
    practitioner_support,
    practitioner_support_detail,
    practitioner_events,
    practitioner_calendar,
    practitioner_calendar_api,
    practitioner_create_ticket,
    practitioner_event_detail,
    practitioner_event_register,
    practitioner_notification_preferences
)

from . import federation_grades
from . import federation_clubs
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# Alias pour la compatibilité avec l'ancien code
club_practitioners = practitioners_list

# Alias pour les vues pratiquant (compatibilité)
practitioner_dashboard = dashboard
practitioner_profile = profile
practitioner_activities = activities
practitioner_grades = grades
practitioner_competitions = competitions
practitioner_memberships = memberships
practitioner_statistics = statistics

# Ces alias ne sont plus nécessaires car les fonctions ont déjà le bon nom
# practitioner_orders = practitioner_orders
# practitioner_order_detail = practitioner_order_detail
# practitioner_notifications = practitioner_notifications
# practitioner_notification_mark_read = practitioner_notification_mark_read
# practitioner_support = practitioner_support
# practitioner_support_detail = practitioner_support_detail
# practitioner_events = practitioner_events
# practitioner_calendar = practitioner_calendar
# practitioner_calendar_api = practitioner_calendar_api

# Liste des vues exportées
__all__ = [
    # Auth
    'logout_view', 
    'login_view',
    'signup_view',
    
    # CSRF
    'refresh_csrf_token',
    'csrf_failure',
    'get_csrf_token',
    'test_csrf',
    
    # Accueil
    'welcome',
    'home',
    'register_view',
    
    # Dashboard
    'dashboard',
    'admin_dashboard',
    'club_dashboard',
    'referee_dashboard',
    'participant_dashboard',
    'spectator_dashboard',
    'dashboard_pro',
    'manager_dashboard',
    'federation_dashboard',
    
    # Compétitions
    'competition_list',
    'competition_create',
    'competition_detail',
    'competition_update',
    'competition_delete',
    'export_competition_registrations',
    'register_for_competition',
    'manage_competition_registrations',
    'competition_categories',
    'get_competition_types',
    'get_competition_types_by_discipline',
    
    # Catégories
    'category_create',
    'category_update',
    'category_delete',
    
    # Fédérations
    'federation_list',
    'federation_detail',
    'federation_create',
    'federation_update',
    'federation_delete',
    'federation_competitions',
    'federation_judges',
    'federation_calendar',
    'federation_trainings',
    'federation_certifications',
    'create_certification',
    'certification_detail',
    
    # Combat
    'liste_configurations',
    'creer_configuration',
    'modifier_configuration',
    'supprimer_configuration',
    'liste_equipes',
    'creer_equipe',
    'detail_equipe',
    'modifier_equipe',
    'supprimer_equipe',
    'ajouter_membre_equipe',
    'modifier_membre_equipe',
    'supprimer_membre_equipe',
    'liste_poules',
    'creer_poule',
    'detail_poule',
    'modifier_poule',
    'supprimer_poule',
    'generer_poules',
    'liste_combats',
    'detail_combat',
    'creer_combat',
    'modifier_combat',
    'supprimer_combat',
    'demarrer_combat',
    'terminer_combat',
    'annuler_combat',
    'ajouter_action',
    'annuler_action',
    'interface_combat',
    'monitor_match',
    'affichage_combat',
    'api_statut_combat',
    'api_liste_actions',
    
    # Club - practitioners
    'practitioners_list',
    'practitioner_form',
    'practitioner_create',
    'practitioner_update',
    'practitioner_detail',
    'practitioner_delete',
    'create_user_for_practitioner',
    'link_user_to_practitioner',
    'club_practitioners',
    
    # Club - registrations
    'registrations_list',
    'register_practitioner',
    'available_competitions',
    'register_multiple_practitioners',
    'competition_registration_form',
    'club_bulk_registration',
    'select_practitioner_for_registration',
    'cancel_registration',
    
    # Club - qualifications
    'qualification_form',
    'judges_list',
    'delete_qualification',
    
    # Club - import/export
    'import_export_data',
    
    # Club - profiles
    'user_profile',
    'practitioner_profile',
    'update_practitioner_profile',
    
    # Juge
    'judge_dashboard',
    'judge_profile',
    'upcoming_competitions',
    'apply_as_judge',
    
    # Onboarding
    'onboarding_start',
    'handle_role_selection',
    'handle_federation_creation',
    'handle_club_creation',
    'handle_club_details',
    'handle_categories_setup',
    'handle_judge_profile',
    'handle_participant_profile',
    'handle_final_setup',
    
    # Notation technique - managers
    'category_scoring_setup',
    'assign_judges',
    'manage_performances',
    'start_performance',
    'monitor_performance',
    'performance_results',
    'category_results',
    
    # Notation technique - juges
    'technical_judge_dashboard',
    'judge_competition_list',
    'judge_competition_detail',
    'judge_category_view',
    'score_performance',
    'submit_score',
    'judge_settings',
    'judge_help',
    
    # Notation technique - APIs
    'get_performance_scores',
    'get_category_results',
    
    # Pratiquant - tableau de bord principal
    'dashboard',
    'profile',
    'activities',
    'grades',
    'competitions',
    'memberships',
    'statistics',
    
    # Pratiquant - fonctionnalités supplémentaires
    'practitioner_orders',
    'practitioner_order_detail',
    'practitioner_notifications',
    'practitioner_notification_mark_read',
    'practitioner_support',
    'practitioner_support_detail',
    'practitioner_events',
    'practitioner_calendar',
    'practitioner_calendar_api',
    'practitioner_create_ticket',
    'practitioner_event_detail',
    'practitioner_event_register',
    'practitioner_notification_preferences'
]
