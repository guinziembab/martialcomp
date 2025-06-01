"""
Monitoring views and API endpoints
"""
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.utils import timezone
import json

from .models import Tenant
from .monitoring import TenantHealthMonitor, TenantMetricsCollector


def is_superuser(user):
    """Check if user is superuser"""
    return user.is_superuser


@require_http_methods(["GET"])
def health_check_view(request):
    """Basic health check endpoint"""
    return JsonResponse({
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'service': 'martialcomp',
        'version': '1.0.0',
    })


@require_http_methods(["GET"])
def tenant_health_check_view(request):
    """Tenant-specific health check"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return JsonResponse({
            'status': 'error',
            'message': 'No tenant found'
        }, status=404)
    
    monitor = TenantHealthMonitor()
    health_status = monitor.check_tenant_health(request.tenant)
    
    return JsonResponse(health_status)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def all_tenants_health_view(request):
    """Health check for all tenants (superuser only)"""
    # Check cache first
    cached_results = cache.get('tenant_health_check')
    if cached_results and not request.GET.get('force'):
        return JsonResponse(cached_results)
    
    # Run health checks
    monitor = TenantHealthMonitor()
    results = monitor.check_all_tenants()
    
    return JsonResponse(results)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def tenant_metrics_view(request, tenant_id=None):
    """Get metrics for a specific tenant or current tenant"""
    if tenant_id:
        # Superuser viewing specific tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return JsonResponse({
                'error': 'Tenant not found'
            }, status=404)
    else:
        # Current tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            return JsonResponse({
                'error': 'No tenant found'
            }, status=404)
        tenant = request.tenant
    
    # Check cache first
    cache_key = f'tenant_metrics_{tenant.id}'
    cached_metrics = cache.get(cache_key)
    
    if cached_metrics and not request.GET.get('force'):
        return JsonResponse(cached_metrics)
    
    # Collect fresh metrics
    collector = TenantMetricsCollector()
    metrics = collector.collect_metrics(tenant)
    
    return JsonResponse(metrics)


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def monitoring_dashboard_data(request):
    """Get data for monitoring dashboard"""
    data = {
        'timestamp': timezone.now().isoformat(),
        'summary': {},
        'recent_alerts': [],
        'performance': {},
    }
    
    # Get tenant summary
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()
    trial_tenants = Tenant.objects.filter(is_trial=True, is_active=True).count()
    
    data['summary'] = {
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'inactive_tenants': total_tenants - active_tenants,
        'trial_tenants': trial_tenants,
        'paid_tenants': active_tenants - trial_tenants,
    }
    
    # Get recent health check results
    health_check = cache.get('tenant_health_check')
    if health_check:
        data['health'] = {
            'overall_status': health_check.get('overall_health', 'unknown'),
            'healthy_tenants': health_check.get('healthy_tenants', 0),
            'unhealthy_tenants': health_check.get('unhealthy_tenants', 0),
            'warnings': health_check.get('warnings', 0),
            'last_check': health_check.get('timestamp'),
        }
    
    # Get performance metrics
    performance_keys = cache.get('performance_metrics_keys', [])
    for key in performance_keys:
        metric = cache.get(key)
        if metric:
            data['performance'][key] = metric
    
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def report_activity(request):
    """Report activity for the current tenant"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return JsonResponse({
            'error': 'No tenant found'
        }, status=404)
    
    # Update activity timestamp
    cache_key = f'tenant_activity_{request.tenant.id}'
    cache.set(cache_key, timezone.now().isoformat(), 86400)  # 24 hours
    
    # Update activity metrics
    metrics_key = f'tenant_metrics_activity_{request.tenant.id}'
    current_count = cache.get(metrics_key, 0)
    cache.set(metrics_key, current_count + 1, 3600)  # 1 hour
    
    return JsonResponse({
        'status': 'ok',
        'tenant': str(request.tenant.id),
        'timestamp': timezone.now().isoformat(),
    })


@login_required
@user_passes_test(is_superuser)
@require_http_methods(["GET"])
def system_status_view(request):
    """Get overall system status"""
    status = {
        'timestamp': timezone.now().isoformat(),
        'database': {},
        'cache': {},
        'tenants': {},
    }
    
    # Database status
    from django.db import connection
    with connection.cursor() as cursor:
        # Get database size
        cursor.execute("SELECT pg_database_size(current_database())")
        db_size = cursor.fetchone()[0]
        
        # Get connection count
        cursor.execute("""
            SELECT count(*) 
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """)
        connection_count = cursor.fetchone()[0]
        
        status['database'] = {
            'size_bytes': db_size,
            'size_human': f"{db_size / 1024 / 1024 / 1024:.2f} GB",
            'connections': connection_count,
            'status': 'healthy',
        }
    
    # Cache status
    try:
        cache.set('test_key', 'test_value', 1)
        if cache.get('test_key') == 'test_value':
            cache_status = 'healthy'
        else:
            cache_status = 'unhealthy'
    except Exception as e:
        cache_status = f'error: {str(e)}'
    
    status['cache'] = {
        'status': cache_status,
        'backend': settings.CACHES['default']['BACKEND'],
    }
    
    # Tenant summary
    status['tenants']['summary'] = {
        'total': Tenant.objects.count(),
        'active': Tenant.objects.filter(is_active=True).count(),
        'trial': Tenant.objects.filter(is_trial=True, is_active=True).count(),
    }
    
    return JsonResponse(status)