"""
URLs pour l'interface d'administration super-admin.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.TenantDashboardView.as_view(), name='admin-dashboard'),
    path('tenant/create/', views.TenantCreateView.as_view(), name='admin-tenant-create'),
    path('tenant/<uuid:pk>/', views.TenantDetailView.as_view(), name='admin-tenant-detail'),
    path('tenant/<uuid:pk>/update/', views.TenantUpdateView.as_view(), name='admin-tenant-update'),
    path('tenant/<uuid:pk>/toggle/', views.TenantToggleStatusView.as_view(), name='admin-tenant-toggle'),
    path('tenant/<uuid:tenant_id>/domain/create/', views.DomainCreateView.as_view(), name='admin-domain-create'),
    path('domain/<int:pk>/update/', views.DomainUpdateView.as_view(), name='admin-domain-update'),
    path('domain/<int:pk>/delete/', views.DomainDeleteView.as_view(), name='admin-domain-delete'),
    path('tenant/<uuid:tenant_id>/feature/create/', views.TenantFeatureCreateView.as_view(), name='admin-feature-create'),
    path('feature/<int:pk>/toggle/', views.TenantFeatureToggleView.as_view(), name='admin-feature-toggle'),
    path('tenant/<uuid:tenant_id>/payments/', views.TenantPaymentsView.as_view(), name='admin-tenant-payments'),
    path('system-health/', views.SystemHealthView.as_view(), name='admin-system-health'),
]