"""
Monitoring and health checks for multi-tenant system
"""
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .models import Tenant
from .utils import SchemaContext

logger = logging.getLogger('multitenant.monitoring')


class TenantHealthMonitor:
    """Monitor health and performance of tenants"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def check_all_tenants(self) -> Dict[str, any]:
        """Run health checks on all active tenants"""
        start_time = time.time()
        results = {
            'timestamp': timezone.now().isoformat(),
            'total_tenants': 0,
            'healthy_tenants': 0,
            'unhealthy_tenants': 0,
            'warnings': 0,
            'tenant_status': {},
            'overall_health': 'healthy',
            'check_duration': 0,
        }
        
        active_tenants = Tenant.objects.filter(is_active=True)
        results['total_tenants'] = active_tenants.count()
        
        for tenant in active_tenants:
            tenant_health = self.check_tenant_health(tenant)
            results['tenant_status'][tenant.slug] = tenant_health
            
            if tenant_health['status'] == 'healthy':
                results['healthy_tenants'] += 1
            elif tenant_health['status'] == 'unhealthy':
                results['unhealthy_tenants'] += 1
            
            if tenant_health['warnings']:
                results['warnings'] += len(tenant_health['warnings'])
        
        # Determine overall health
        if results['unhealthy_tenants'] > 0:
            results['overall_health'] = 'unhealthy'
        elif results['warnings'] > 5:
            results['overall_health'] = 'warning'
        
        results['check_duration'] = time.time() - start_time
        
        # Cache results
        cache.set('tenant_health_check', results, 300)  # Cache for 5 minutes
        
        return results
    
    def check_tenant_health(self, tenant: Tenant) -> Dict[str, any]:
        """Check health of a specific tenant"""
        health_status = {
            'tenant_id': str(tenant.id),
            'tenant_name': tenant.name,
            'status': 'healthy',
            'checks': {},
            'warnings': [],
            'errors': [],
            'last_check': timezone.now().isoformat(),
        }
        
        # Check schema exists
        health_status['checks']['schema'] = self._check_schema_exists(tenant)
        
        # Check database connectivity
        health_status['checks']['database'] = self._check_database_connection(tenant)
        
        # Check subscription status
        health_status['checks']['subscription'] = self._check_subscription_status(tenant)
        
        # Check resource usage
        health_status['checks']['resources'] = self._check_resource_usage(tenant)
        
        # Check recent activity
        health_status['checks']['activity'] = self._check_recent_activity(tenant)
        
        # Determine overall status
        for check, result in health_status['checks'].items():
            if result['status'] == 'error':
                health_status['status'] = 'unhealthy'
                health_status['errors'].append(f"{check}: {result['message']}")
            elif result['status'] == 'warning':
                health_status['warnings'].append(f"{check}: {result['message']}")
        
        return health_status
    
    def _check_schema_exists(self, tenant: Tenant) -> Dict[str, any]:
        """Check if tenant schema exists"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT 1 FROM information_schema.schemata 
                        WHERE schema_name = %s
                    )
                """, [tenant.schema_name])
                
                exists = cursor.fetchone()[0]
                
                if exists:
                    return {'status': 'ok', 'message': 'Schema exists'}
                else:
                    return {'status': 'error', 'message': 'Schema not found'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _check_database_connection(self, tenant: Tenant) -> Dict[str, any]:
        """Check database connectivity for tenant"""
        try:
            with SchemaContext(tenant.schema_name):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    
            return {'status': 'ok', 'message': 'Database connection successful'}
            
        except Exception as e:
            return {'status': 'error', 'message': f'Database connection failed: {str(e)}'}
    
    def _check_subscription_status(self, tenant: Tenant) -> Dict[str, any]:
        """Check tenant subscription status"""
        if tenant.is_trial:
            if tenant.trial_end_date:
                days_left = (tenant.trial_end_date - timezone.now()).days
                
                if days_left < 0:
                    return {
                        'status': 'error',
                        'message': 'Trial expired',
                        'trial_ended': tenant.trial_end_date.isoformat()
                    }
                elif days_left < 7:
                    return {
                        'status': 'warning',
                        'message': f'Trial expires in {days_left} days',
                        'trial_end_date': tenant.trial_end_date.isoformat()
                    }
                else:
                    return {
                        'status': 'ok',
                        'message': f'Trial active ({days_left} days left)',
                        'trial_end_date': tenant.trial_end_date.isoformat()
                    }
            else:
                return {'status': 'ok', 'message': 'Trial active (no expiry set)'}
        
        # Check paid subscription
        if tenant.subscription_status == 'active':
            return {'status': 'ok', 'message': 'Subscription active'}
        elif tenant.subscription_status == 'cancelling':
            return {
                'status': 'warning',
                'message': 'Subscription cancelling at period end'
            }
        else:
            return {
                'status': 'error',
                'message': f'Subscription status: {tenant.subscription_status}'
            }
    
    def _check_resource_usage(self, tenant: Tenant) -> Dict[str, any]:
        """Check resource usage for tenant"""
        try:
            with SchemaContext(tenant.schema_name):
                # Check table sizes
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                        FROM pg_tables
                        WHERE schemaname = %s
                        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                        LIMIT 5
                    """, [tenant.schema_name])
                    
                    tables = cursor.fetchall()
                    
                    # Check total schema size
                    cursor.execute("""
                        SELECT pg_size_pretty(
                            SUM(pg_total_relation_size(schemaname||'.'||tablename))
                        )
                        FROM pg_tables
                        WHERE schemaname = %s
                    """, [tenant.schema_name])
                    
                    total_size = cursor.fetchone()[0]
            
            return {
                'status': 'ok',
                'message': f'Schema size: {total_size}',
                'details': {
                    'total_size': total_size,
                    'largest_tables': [
                        {'table': t[1], 'size': t[2]} for t in tables
                    ]
                }
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to check resources: {str(e)}'}
    
    def _check_recent_activity(self, tenant: Tenant) -> Dict[str, any]:
        """Check recent activity for tenant"""
        # This is a placeholder - implement based on your activity tracking
        # For example, check last login, last data modification, etc.
        
        last_activity = cache.get(f'tenant_activity_{tenant.id}')
        
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            days_inactive = (timezone.now() - last_activity_time).days
            
            if days_inactive > 30:
                return {
                    'status': 'warning',
                    'message': f'No activity for {days_inactive} days'
                }
            else:
                return {
                    'status': 'ok',
                    'message': f'Last activity {days_inactive} days ago'
                }
        
        return {'status': 'ok', 'message': 'Activity tracking not available'}


class TenantMetricsCollector:
    """Collect performance metrics for tenants"""
    
    def collect_metrics(self, tenant: Tenant) -> Dict[str, any]:
        """Collect various metrics for a tenant"""
        metrics = {
            'tenant_id': str(tenant.id),
            'timestamp': timezone.now().isoformat(),
            'performance': {},
            'usage': {},
            'errors': {},
        }
        
        try:
            with SchemaContext(tenant.schema_name):
                # Collect performance metrics
                metrics['performance'] = self._collect_performance_metrics(tenant)
                
                # Collect usage metrics
                metrics['usage'] = self._collect_usage_metrics(tenant)
                
                # Collect error metrics
                metrics['errors'] = self._collect_error_metrics(tenant)
        
        except Exception as e:
            logger.error(f"Error collecting metrics for tenant {tenant.id}: {e}")
            metrics['error'] = str(e)
        
        # Store metrics
        self._store_metrics(tenant, metrics)
        
        return metrics
    
    def _collect_performance_metrics(self, tenant: Tenant) -> Dict[str, any]:
        """Collect performance-related metrics"""
        metrics = {}
        
        # Database query performance
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as query_count,
                    AVG(mean_time) as avg_query_time,
                    MAX(mean_time) as max_query_time
                FROM pg_stat_statements
                WHERE query LIKE %s
            """, [f'%{tenant.schema_name}%'])
            
            result = cursor.fetchone()
            if result:
                metrics['database'] = {
                    'query_count': result[0],
                    'avg_query_time': result[1],
                    'max_query_time': result[2],
                }
        
        # Cache performance
        cache_key = f'tenant_cache_hits_{tenant.id}'
        metrics['cache'] = {
            'hit_rate': cache.get(cache_key, 0),
        }
        
        return metrics
    
    def _collect_usage_metrics(self, tenant: Tenant) -> Dict[str, any]:
        """Collect usage-related metrics"""
        from django.contrib.auth.models import User
        
        metrics = {}
        
        # User counts
        metrics['users'] = {
            'total': User.objects.count(),
            'active': User.objects.filter(
                last_login__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }
        
        # Resource usage
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    pg_database_size(current_database()) as db_size,
                    (SELECT COUNT(*) FROM pg_tables WHERE schemaname = %s) as table_count
            """, [tenant.schema_name])
            
            result = cursor.fetchone()
            metrics['resources'] = {
                'database_size': result[0],
                'table_count': result[1],
            }
        
        return metrics
    
    def _collect_error_metrics(self, tenant: Tenant) -> Dict[str, any]:
        """Collect error-related metrics"""
        # This is a placeholder - implement based on your error tracking
        return {
            'error_count': 0,
            'error_rate': 0,
        }
    
    def _store_metrics(self, tenant: Tenant, metrics: Dict[str, any]):
        """Store metrics for later analysis"""
        cache_key = f'tenant_metrics_{tenant.id}'
        
        # Store in cache with timestamp
        cache.set(cache_key, metrics, 3600)  # Store for 1 hour
        
        # You could also store in a time-series database here
        # or send to monitoring service like Prometheus/Grafana