# -*- coding: utf-8 -*-
"""
Vues de l'application Super Admin.

Les vues sont importées individuellement pour éviter les erreurs d'importation
circulaire et permettre une implémentation progressive.
"""

# Dashboard (Phase 2)
from apps.superadmin.views.dashboard import DashboardView

# Carte du monde (Phase 3)
from apps.superadmin.views.map import MapView, MapDataView

# Gestion Memberships (Phase 4)
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

# Monitoring Système (Phase 5)
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

# Configuration (Phase 6)
from apps.superadmin.views.config import (
    ConfigView,
    GeneralConfigView,
    FeatureFlagsView,
    RegionPricingView,
    EmailConfigView,
    SecurityConfigView,
)

# Logs et Audit (Phase 7)
from apps.superadmin.views.logs import (
    LogsView,
    LogsExportView,
    LogDetailView,
    AlertsListView,
    ClearLogsView,
)

__all__ = [
    'DashboardView',
    'MapView',
    'MapDataView',
    'MembershipListView',
    'MembershipDetailView',
    'MembershipCreateView',
    'MembershipUpdateView',
    'MembershipDeleteView',
    'MembershipStatsView',
    'MembershipToggleView',
    'MembershipDuplicateView',
    'SystemView',
    'RestartServiceView',
    'MaintenanceModeView',
    'ClearCacheView',
    'TriggerBackupView',
    'EmergencyStopView',
    'RefreshServicesView',
    'AlertAcknowledgeView',
    'AlertResolveView',
    # Config
    'ConfigView',
    'GeneralConfigView',
    'FeatureFlagsView',
    'RegionPricingView',
    'EmailConfigView',
    'SecurityConfigView',
    # Logs
    'LogsView',
    'LogsExportView',
    'LogDetailView',
    'AlertsListView',
    'ClearLogsView',
]
