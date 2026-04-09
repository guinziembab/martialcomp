# -*- coding: utf-8 -*-
"""
URLs de l'application Super Admin.

Structure:
    /superadmin/                    → Dashboard principal
    /superadmin/map/                → Carte du monde
    /superadmin/memberships/        → Gestion des profils membership
    /superadmin/system/             → Monitoring système
    /superadmin/config/             → Configuration
    /superadmin/logs/               → Logs et audit
    /superadmin/api/                → API REST
"""

from django.urls import path, include

app_name = 'superadmin'

# Import des vues
from django.views.generic import TemplateView
from apps.superadmin.decorators import SuperAdminRequiredMixin
from apps.superadmin.views.dashboard import DashboardView
from apps.superadmin.views.map import MapView, MapDataView
from apps.superadmin.views.memberships import (
    MembershipListView,
    MembershipDetailView,
    MembershipCreateView,
    MembershipUpdateView,
    MembershipDeleteView,
    MembershipStatsView,
    MembershipToggleView,
    MembershipDuplicateView,
)
from apps.superadmin.views.system import (
    SystemView,
    RestartServiceView,
    MaintenanceModeView,
    ClearCacheView,
    TriggerBackupView,
    EmergencyStopView,
    RefreshServicesView,
    AlertAcknowledgeView,
    AlertResolveView,
)
from apps.superadmin.views.config import (
    ConfigView,
    GeneralConfigView,
    FeatureFlagsView,
    RegionPricingView,
    EmailConfigView,
    SecurityConfigView,
)
from apps.superadmin.views.logs import (
    LogsView,
    LogsExportView,
    LogDetailView,
    AlertsListView,
    ClearLogsView,
)


class PlaceholderView(SuperAdminRequiredMixin, TemplateView):
    """Vue placeholder temporaire."""
    template_name = 'superadmin/placeholder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = self.kwargs.get('title', 'Super Admin')
        return context


urlpatterns = [
    # Dashboard principal
    path('', DashboardView.as_view(), name='dashboard'),

    # Carte du monde
    path('map/', MapView.as_view(), name='map'),
    path('map/data/', MapDataView.as_view(), name='map_data'),

    # Gestion des memberships
    path('memberships/', MembershipListView.as_view(), name='membership_list'),
    path('memberships/create/', MembershipCreateView.as_view(), name='membership_create'),
    path('memberships/stats/', MembershipStatsView.as_view(), name='membership_stats'),
    path('memberships/<int:pk>/', MembershipDetailView.as_view(), name='membership_detail'),
    path('memberships/<int:pk>/edit/', MembershipUpdateView.as_view(), name='membership_update'),
    path('memberships/<int:pk>/delete/', MembershipDeleteView.as_view(), name='membership_delete'),
    path('memberships/<int:pk>/toggle/', MembershipToggleView.as_view(), name='membership_toggle'),
    path('memberships/<int:pk>/duplicate/', MembershipDuplicateView.as_view(), name='membership_duplicate'),

    # Monitoring système
    path('system/', SystemView.as_view(), name='system'),
    path('system/restart/', RestartServiceView.as_view(), name='system_restart'),
    path('system/maintenance/', MaintenanceModeView.as_view(), name='system_maintenance'),
    path('system/emergency-stop/', EmergencyStopView.as_view(), name='system_emergency_stop'),
    path('system/clear-cache/', ClearCacheView.as_view(), name='system_clear_cache'),
    path('system/backup/', TriggerBackupView.as_view(), name='system_backup'),
    path('system/refresh/', RefreshServicesView.as_view(), name='system_refresh'),
    path('system/alerts/<int:pk>/acknowledge/', AlertAcknowledgeView.as_view(), name='alert_acknowledge'),
    path('system/alerts/<int:pk>/resolve/', AlertResolveView.as_view(), name='alert_resolve'),

    # Configuration
    path('config/', ConfigView.as_view(), name='config'),
    path('config/general/', GeneralConfigView.as_view(), name='config_general'),
    path('config/features/', FeatureFlagsView.as_view(), name='config_features'),
    path('config/regions/', RegionPricingView.as_view(), name='config_regions'),
    path('config/email/', EmailConfigView.as_view(), name='config_email'),
    path('config/security/', SecurityConfigView.as_view(), name='config_security'),

    # Logs et audit
    path('logs/', LogsView.as_view(), name='logs'),
    path('logs/export/', LogsExportView.as_view(), name='logs_export'),
    path('logs/<int:pk>/', LogDetailView.as_view(), name='log_detail'),
    path('logs/clear/', ClearLogsView.as_view(), name='logs_clear'),
    path('alerts/', AlertsListView.as_view(), name='alerts'),

    # API REST
    path('api/', include('apps.superadmin.api.urls')),
]
