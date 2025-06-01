"""
URL configuration for multi-tenant functionality
"""
from django.urls import path, include
from .. import core_views, views_monitoring
from ..admin import views as admin_views
from ..views.security_views import SecurityDashboardView, SecurityReportListView, SecurityReportDetailView, RunSecurityAuditView, SecurityViolationsView, DownloadSecurityReportView
from ..views.resource_views import (
    ResourceUsageView, UpgradePlanView, ResourceLimitExceededView, 
    ResourceAPIView, ResourceDashboardView, ResourceQuotaAPIView, ResourceAdminView
)

app_name = 'multitenant'

urlpatterns = [
    # API endpoints
    path('api/tenant-info/', core_views.tenant_info_view, name='tenant_info'),
    
    # Tenant management
    path('dashboard/', core_views.tenant_dashboard_view, name='tenant_dashboard'),
    path('settings/', core_views.tenant_settings_view, name='tenant_settings'),
    path('billing/', core_views.tenant_billing_view, name='tenant_billing'),
    
    # Onboarding
    path('onboarding/', core_views.tenant_onboarding_view, name='tenant_onboarding'),
    
    # Payment
    path('payment/setup/', core_views.payment_setup_view, name='payment_setup'),
    path('payment/success/', core_views.payment_success_view, name='payment_success'),
    path('payment/cancel/', core_views.payment_cancel_view, name='payment_cancel'),
    
    # Webhooks
    path('webhook/<str:provider>/', core_views.webhook_view, name='webhook'),
    
    # Subscriptions
    path('subscriptions/', include('multitenant.urls.subscription', namespace='subscription')),
    
    # Monitoring
    path('health/', views_monitoring.health_check_view, name='health_check'),
    path('health/tenant/', views_monitoring.tenant_health_check_view, name='tenant_health'),
    path('health/all/', views_monitoring.all_tenants_health_view, name='all_tenants_health'),
    path('metrics/', views_monitoring.tenant_metrics_view, name='tenant_metrics'),
    path('metrics/<uuid:tenant_id>/', views_monitoring.tenant_metrics_view, name='tenant_metrics_specific'),
    path('monitoring/dashboard/', views_monitoring.monitoring_dashboard_data, name='monitoring_dashboard'),
    path('activity/report/', views_monitoring.report_activity, name='report_activity'),
    path('system/status/', views_monitoring.system_status_view, name='system_status'),
    
    # URLs pour l'interface d'administration super-admin
    path('admin/', include([
        path('', admin_views.TenantDashboardView.as_view(), name='admin-dashboard'),
        path('tenant/create/', admin_views.TenantCreateView.as_view(), name='admin-tenant-create'),
        path('tenant/<uuid:pk>/', admin_views.TenantDetailView.as_view(), name='admin-tenant-detail'),
        path('tenant/<uuid:pk>/update/', admin_views.TenantUpdateView.as_view(), name='admin-tenant-update'),
        path('tenant/<uuid:pk>/toggle/', admin_views.TenantToggleStatusView.as_view(), name='admin-tenant-toggle'),
        path('tenant/<uuid:tenant_id>/domain/create/', admin_views.DomainCreateView.as_view(), name='admin-domain-create'),
        path('domain/<int:pk>/update/', admin_views.DomainUpdateView.as_view(), name='admin-domain-update'),
        path('domain/<int:pk>/delete/', admin_views.DomainDeleteView.as_view(), name='admin-domain-delete'),
        path('tenant/<uuid:tenant_id>/feature/create/', admin_views.TenantFeatureCreateView.as_view(), name='admin-feature-create'),
        path('feature/<int:pk>/toggle/', admin_views.TenantFeatureToggleView.as_view(), name='admin-feature-toggle'),
        path('tenant/<uuid:tenant_id>/payments/', admin_views.TenantPaymentsView.as_view(), name='admin-tenant-payments'),
        path('system-health/', admin_views.SystemHealthView.as_view(), name='admin-system-health'),
        
        # Security administration
        path('security/', include([
            path('', SecurityDashboardView.as_view(), name='security_dashboard'),
            path('reports/', SecurityReportListView.as_view(), name='security_reports'),
            path('reports/<str:report_id>/', SecurityReportDetailView.as_view(), name='security_report_detail'),
            path('reports/<str:report_id>/download/', DownloadSecurityReportView.as_view(), name='download_security_report'),
            path('audit/run/', RunSecurityAuditView.as_view(), name='run_security_audit'),
            path('violations/', SecurityViolationsView.as_view(), name='security_violations'),
        ])),
    ])),
    
    # Resource management
    path('resources/', include([
        path('', ResourceDashboardView.as_view(), name='resource_dashboard'),
        path('usage/', ResourceUsageView.as_view(), name='resource_usage'),
        path('upgrade/', UpgradePlanView.as_view(), name='resource_upgrade'),
        path('limit-exceeded/<str:resource_type>/', ResourceLimitExceededView.as_view(), name='resource_limit_exceeded'),
        path('api/usage/', ResourceAPIView.as_view(), name='resource_usage_api'),
        path('api/quota/', ResourceQuotaAPIView.as_view(), name='resource_quota_api'),
        path('admin/', ResourceAdminView.as_view(), name='resource_admin'),
    ])),
]