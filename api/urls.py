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

# Recent notifications (placeholder)
urlpatterns += [
    path('notifications/recent/', views.recent_notifications, name='recent_notifications'),
]

if _DOCS_AVAILABLE:
    urlpatterns.append(path('docs/', include_docs_urls(title='MartialComp API')))  # type: ignore