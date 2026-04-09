from django.core.exceptions import PermissionDenied
from django.urls import path, include
from . import views

# Make API docs optional only when coreapi is installed and explicitly enabled
import os
_DOCS_AVAILABLE = False
try:
    import coreapi  # type: ignore
    from rest_framework.documentation import include_docs_urls  # type: ignore
    if os.getenv('ENABLE_API_DOCS') in {'1', 'true', 'True'}:
        _DOCS_AVAILABLE = True
except Exception:
    _DOCS_AVAILABLE = False

urlpatterns = [
    # Health / info for connectivity checks
    path('health/', views.health, name='api_health'),
    path('info/', views.info, name='api_info'),
    # Minimal mobile endpoints to eliminate 404 in app
    path('v1/mobile/dashboard/', views.MobileDashboardView.as_view(), name='mobile_dashboard_min'),
    # Dashboard spécifique par rôle
    path('v1/mobile/dashboard/admin/', views.MobileDashboardView.as_view(), name='mobile_dashboard_admin'),
    path('v1/mobile/dashboard/practitioner/', views.PractitionerDashboardView.as_view(), name='mobile_dashboard_practitioner'),
    path('v1/mobile/dashboard/participant/', views.PractitionerDashboardView.as_view(), name='mobile_dashboard_participant'),
    # Liste unifiée des événements (compétitions + événements club)
    path('v1/mobile/events/', views.MobileEventsListView.as_view(), name='mobile_events_list'),
    path('payment/methods/', views.PaymentMethodsView.as_view(), name='payment_methods_min'),
    # API d'authentification
    path('v1/auth/', include('api_auth.urls', namespace='api_auth_v1')),
    path('generate-certificate-number/', views.generate_certificate_number, name='generate_certificate_number'),
]

urlpatterns += [
    path('generate-license-number/', views.generate_license_number, name='generate_license_number'),
]

# Expose organizations API under /api/
from apps.organizations.views.api import OrganizationListView, OrganizationDashboardView, MembersListView  # type: ignore
from apps.finances.rest_api import (
    CurrencyPreferredView,
    CurrencyRatesView,
    CurrencyConvertView,
)  # type: ignore
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
urlpatterns += [
    path('organizations/', OrganizationListView.as_view(), name='organizations_list_api'),
    path('organizations/dashboard/', OrganizationDashboardView.as_view(), name='organizations_dashboard_api'),
]

# Expose competitions API under /api/competitions/
urlpatterns += [
    path('competitions/', include('apps.competitions.api')),
]

# Expose grades API under /api/grades/
urlpatterns += [
    path('grades/', include('apps.grades.api')),
]

# Expose finances API under /api/finances/
urlpatterns += [
    path('finances/', include('apps.finances.rest_api')),
]

# v1 aliases for mobile clients expecting versioned paths
urlpatterns += [
    path('v1/grades/', include('apps.grades.api')),
    path('v1/finances/', include('apps.finances.rest_api')),
]

# Mobile grades endpoints (for buttons in mobile app)
from apps.grades.api import PractitionerGradesView, GradeExamsView, GradesListView
urlpatterns += [
    path('v1/mobile/grades/', PractitionerGradesView.as_view(), name='mobile_practitioner_grades'),
    path('v1/mobile/grades/my-grades/', PractitionerGradesView.as_view(), name='mobile_my_grades'),
    path('v1/mobile/grades/exams/', GradeExamsView.as_view(), name='mobile_grade_exams'),
    path('v1/mobile/grades/progression/', PractitionerGradesView.as_view(), name='mobile_grade_progression'),
    path('v1/mobile/grades/list/', GradesListView.as_view(), name='mobile_grades_list'),
]

# Dedicated currency v1 endpoints (flat paths)
urlpatterns += [
    path('v1/currency/preferred/', CurrencyPreferredView.as_view(), name='v1_currency_preferred'),
    path('v1/currency/rates/',     CurrencyRatesView.as_view(),     name='v1_currency_rates'),
    path('v1/currency/convert/',   CurrencyConvertView.as_view(),   name='v1_currency_convert'),
    # Members listing for current organization
    path('v1/members/', MembersListView.as_view(), name='v1_members_list'),
]

# Expose minimal shop API under /api/shop/
try:
    urlpatterns += [
        path('shop/', include('apps.shop.api')),
    ]
except Exception:
    # If shop app not available, silently ignore
    pass

# Notifications API (full REST endpoints for mobile)
urlpatterns += [
    path('notifications/', views.NotificationsAPIView.as_view(), name='notifications_list'),
    path('notifications/recent/', views.recent_notifications, name='recent_notifications'),
    path('notifications/<int:notification_id>/', views.NotificationDetailAPIView.as_view(), name='notification_detail'),
    path('notifications/mark-read/', views.NotificationMarkReadAPIView.as_view(), name='notification_mark_read'),
    path('notifications/mark-read/<int:notification_id>/', views.NotificationMarkReadAPIView.as_view(), name='notification_mark_read_single'),
    path('notifications/delete/', views.NotificationDeleteAPIView.as_view(), name='notification_delete'),
    path('notifications/preferences/', views.NotificationPreferencesAPIView.as_view(), name='notification_preferences'),
    path('notifications/settings/', views.NotificationPreferencesAPIView.as_view(), name='notification_settings'),
]

# Mobile Palmares API endpoint
urlpatterns += [
    path('v1/mobile/palmares/', views.MobilePalmaresView.as_view(), name='mobile_palmares'),
]

# Mobile Combats API endpoint
urlpatterns += [
    path('v1/mobile/combats/', views.MobileCombatsView.as_view(), name='mobile_combats'),
]

# Broadcast Groups API (groupes de diffusion pour instructeurs)
urlpatterns += [
    path('v1/broadcast/', include('api.broadcast_urls', namespace='broadcast_api')),
]

# Attendance API (gestion des présences et déclarations d'absence)
urlpatterns += [
    path('v1/attendance/', include('api.attendance_urls', namespace='attendance_api')),
]

# Onboarding API (sélection de rôle et configuration initiale)
urlpatterns += [
    path('v1/onboarding/', include('api.onboarding_urls', namespace='onboarding_api')),
]

# Social Auth API (authentification Google/Facebook/Apple pour mobile)
from apps.competitions.api.social_auth import SocialAuthTokenExchangeView
urlpatterns += [
    path('v1/auth/social/token/', SocialAuthTokenExchangeView.as_view(), name='social_auth_token'),
]

# Judge API endpoints (Mobile App)
urlpatterns += [
    path('v1/judge/can-access/', views.JudgeCanAccessView.as_view(), name='judge_can_access'),
    path('v1/judge/profile/', views.JudgeProfileView.as_view(), name='judge_profile'),
    path('v1/judge/dashboard/', views.JudgeDashboardAPIView.as_view(), name='judge_dashboard'),
    path('v1/judge/assignments/', views.JudgeAssignmentsView.as_view(), name='judge_assignments'),
    path('v1/judge/assignments/<int:assignment_id>/respond/', views.JudgeAssignmentRespondView.as_view(), name='judge_assignment_respond'),
    path('v1/judge/performances/pending/', views.JudgePendingPerformancesView.as_view(), name='judge_pending_performances'),
    path('v1/judge/performances/history/', views.JudgePerformanceHistoryView.as_view(), name='judge_performance_history'),
    path('v1/judge/performances/<int:performance_id>/score/', views.JudgePerformanceScoreView.as_view(), name='judge_performance_score'),
    path('v1/judge/combat-areas/', views.JudgeCombatAreasView.as_view(), name='judge_combat_areas'),
    path('v1/judge/settings/', views.JudgeSettingsView.as_view(), name='judge_settings'),
    path('v1/judge/switch-mode/', views.JudgeSwitchModeView.as_view(), name='judge_switch_mode'),
]

# Federation API endpoints (Mobile App)
urlpatterns += [
    path('v1/mobile/federation/clubs/', views.FederationAffiliatedClubsView.as_view(), name='federation_affiliated_clubs'),
    path('v1/mobile/federation/clubs/invite/', views.FederationInviteClubView.as_view(), name='federation_invite_club'),
    path('v1/mobile/federation/judges/', views.FederationJudgesView.as_view(), name='federation_judges'),
    path('v1/mobile/federation/grades/', views.FederationGradesView.as_view(), name='federation_grades'),
    path('v1/mobile/federation/results/', views.FederationResultsView.as_view(), name='federation_results'),
]

# Family Management API (Mobile App)
urlpatterns += [
    path('family-management/', views.FamilyManagementAPIView.as_view(), name='family_management_api'),
]

# Coach Dashboard API endpoints (Mobile App)
urlpatterns += [
    path('v1/coach/dashboard/', views.CoachDashboardAPIView.as_view(), name='coach_dashboard'),
    path('v1/coach/students/', views.CoachStudentsAPIView.as_view(), name='coach_students'),
    path('v1/coach/sessions/', views.CoachSessionsAPIView.as_view(), name='coach_sessions'),
]

# Subscription Info API endpoint (Mobile App)
urlpatterns += [
    path('v1/subscription/info/', views.SubscriptionInfoView.as_view(), name='subscription_info'),
]

# =============================================================================
# Mobile API Endpoints (QR, Offline, Documents, Training, Communication)
# =============================================================================
try:
    urlpatterns += [
        # Include all mobile API endpoints
        path('', include('api.mobile_urls')),
    ]
except ImportError as e:
    import logging
    logging.getLogger(__name__).warning(f"Mobile API not loaded: {e}")

if _DOCS_AVAILABLE:
    urlpatterns.append(path('docs/', include_docs_urls(title='MartialComp API')))  # type: ignore