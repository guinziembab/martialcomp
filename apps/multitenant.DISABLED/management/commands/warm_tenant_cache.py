"""
Management command to warm up tenant caches for better performance.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count
from datetime import datetime, timedelta
from apps.multitenant.models import Tenant
from apps.multitenant.cache import CacheManager, tenant_cache
from apps.competitions.models import Competition, Practitioner, Registration
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Warm up tenant caches for better performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Specific tenant schema to warm up (optional)'
        )
        parser.add_argument(
            '--skip-settings',
            action='store_true',
            help='Skip caching tenant settings'
        )
        parser.add_argument(
            '--skip-metadata',
            action='store_true',
            help='Skip caching club metadata'
        )
        parser.add_argument(
            '--skip-dashboard',
            action='store_true',
            help='Skip caching dashboard data'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=3600,
            help='Cache timeout in seconds (default: 3600)'
        )
    
    def handle(self, *args, **options):
        tenant_domain = options.get('tenant')
        timeout = options.get('timeout')
        
        if tenant_domain:
            tenants = Tenant.objects.filter(domain=tenant_domain)
            if not tenants.exists():
                self.stdout.write(self.style.ERROR(f'Tenant {tenant_domain} not found'))
                return
        else:
            tenants = Tenant.objects.filter(is_active=True)
        
        self.stdout.write(f'Warming cache for {tenants.count()} tenant(s)...')
        
        total_cached = 0
        
        for tenant in tenants:
            self.stdout.write(f'\nProcessing tenant: {tenant.name} ({tenant.domain})')
            
            try:
                # Set tenant context
                tenant_cache.set_tenant(tenant)
                connection.set_schema(tenant.schema_name)
                
                cached_items = 0
                
                if not options['skip_settings']:
                    self.cache_tenant_settings(tenant, timeout)
                    cached_items += 1
                
                if not options['skip_metadata']:
                    self.cache_club_metadata(tenant, timeout)
                    cached_items += 1
                
                if not options['skip_dashboard']:
                    self.cache_dashboard_data(tenant, timeout)
                    cached_items += 1
                
                total_cached += cached_items
                self.stdout.write(self.style.SUCCESS(f'  âœ“ Cached {cached_items} item groups'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing tenant {tenant.name}: {e}'))
                logger.error(f'Error warming cache for tenant {tenant.name}: {e}', exc_info=True)
            finally:
                # Reset context
                tenant_cache.set_tenant(None)
                connection.set_schema_to_public()
        
        self.stdout.write(self.style.SUCCESS(f'\nCache warming complete! Cached {total_cached} total items.'))
    
    def cache_tenant_settings(self, tenant, timeout):
        """Cache tenant settings and configuration."""
        self.stdout.write('  Caching tenant settings...')
        CacheManager.cache_tenant_settings(tenant, timeout)
        
        # Additional settings to cache
        settings_data = {
            'features': {f.feature_code: f.is_enabled for f in tenant.features.all()},
            'domain': tenant.domain,
            'subdomain': tenant.subdomain,
            'plan': tenant.subscription_plan,
            'continent': tenant.continent,
            'payment_provider': tenant.payment_provider or tenant.get_payment_provider(),
        }
        
        tenant_cache.set('settings', settings_data, timeout)
        self.stdout.write('    âœ“ Settings cached')
    
    def cache_club_metadata(self, tenant, timeout):
        """Cache club-specific metadata."""
        self.stdout.write('  Caching club metadata...')
        CacheManager.cache_club_metadata(tenant, timeout)
        
        # Additional metadata
        metadata = {
            'active_practitioners': Practitioner.objects.filter(
                club__federations__tenants=tenant,
                is_active=True
            ).count(),
            'competitions_this_month': Competition.objects.filter(
                tenants=tenant,
                date__month=datetime.now().month,
                date__year=datetime.now().year
            ).count(),
            'pending_registrations': Registration.objects.filter(
                competition__tenants=tenant,
                status='pending'
            ).count(),
        }
        
        tenant_cache.set('metadata', metadata, timeout)
        self.stdout.write('    âœ“ Metadata cached')
    
    def cache_dashboard_data(self, tenant, timeout):
        """Cache dashboard data."""
        self.stdout.write('  Caching dashboard data...')
        
        from datetime import datetime, timedelta
        
        # Recent competitions
        recent_competitions = list(
            Competition.objects.filter(
                tenants=tenant,
                date__gte=datetime.now() - timedelta(days=30)
            ).select_related('category', 'owner')
            .order_by('-date')[:10]
            .values('id', 'name', 'date', 'status', 'category__name')
        )
        tenant_cache.set('recent_competitions', recent_competitions, timeout)
        
        # Top practitioners
        top_practitioners = list(
            Practitioner.objects.filter(
                club__federations__tenants=tenant,
                is_active=True
            ).select_related('user', 'club')
            .annotate(
                competition_count=Count('registrations')
            ).order_by('-competition_count')[:10]
            .values('id', 'user__email', 'club__name', 'competition_count')
        )
        tenant_cache.set('top_practitioners', top_practitioners, timeout)
        
        # Registration trends
        registration_trends = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            count = Registration.objects.filter(
                competition__tenants=tenant,
                created_at__date=date.date()
            ).count()
            registration_trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        tenant_cache.set('registration_trends', registration_trends, timeout)
        
        self.stdout.write('    âœ“ Dashboard data cached')
