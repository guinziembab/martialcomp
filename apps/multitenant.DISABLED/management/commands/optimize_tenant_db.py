"""
Management command to optimize database for multi-tenant performance.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.multitenant.models import Tenant
from apps.multitenant.db_optimization import IndexManager, PerformanceMonitor
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize database for multi-tenant performance'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Specific tenant schema to optimize (optional)'
        )
        parser.add_argument(
            '--create-indexes',
            action='store_true',
            help='Create optimized indexes'
        )
        parser.add_argument(
            '--analyze-tables',
            action='store_true',
            help='Analyze tables for query planning'
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Show query performance statistics'
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Vacuum tables to reclaim space'
        )
    
    def handle(self, *args, **options):
        tenant_schema = options.get('tenant')
        
        if tenant_schema:
            tenants = Tenant.objects.filter(schema_name=tenant_schema)
            if not tenants.exists():
                self.stdout.write(self.style.ERROR(f'Tenant {tenant_schema} not found'))
                return
        else:
            tenants = Tenant.objects.filter(is_active=True)
        
        self.stdout.write(f'Optimizing {tenants.count()} tenant(s)...')
        
        for tenant in tenants:
            self.stdout.write(f'\nProcessing tenant: {tenant.name} (schema: {tenant.schema_name})')
            
            try:
                # Set schema context
                connection.set_schema(tenant.schema_name)
                
                if options['create_indexes']:
                    self.create_indexes(tenant)
                
                if options['analyze_tables']:
                    self.analyze_tables(tenant)
                
                if options['show_stats']:
                    self.show_stats(tenant)
                
                if options['vacuum']:
                    self.vacuum_tables(tenant)
                
                # Run all optimizations if no specific option
                if not any([options['create_indexes'], options['analyze_tables'], 
                           options['show_stats'], options['vacuum']]):
                    self.create_indexes(tenant)
                    self.analyze_tables(tenant)
                    self.vacuum_tables(tenant)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing tenant {tenant.name}: {e}'))
                logger.error(f'Error optimizing tenant {tenant.name}: {e}', exc_info=True)
            finally:
                # Reset to public schema
                connection.set_schema_to_public()
        
        self.stdout.write(self.style.SUCCESS('\nOptimization complete!'))
    
    def create_indexes(self, tenant):
        """Create optimized indexes for tenant schema."""
        self.stdout.write(f'  Creating indexes for {tenant.schema_name}...')
        IndexManager.create_tenant_indexes(tenant.schema_name)
        self.stdout.write(self.style.SUCCESS('  âœ“ Indexes created'))
    
    def analyze_tables(self, tenant):
        """Analyze tables for query optimization."""
        self.stdout.write(f'  Analyzing tables for {tenant.schema_name}...')
        IndexManager.analyze_tenant_tables(tenant.schema_name)
        self.stdout.write(self.style.SUCCESS('  âœ“ Tables analyzed'))
    
    def show_stats(self, tenant):
        """Show query performance statistics."""
        self.stdout.write(f'  Query statistics for {tenant.schema_name}:')
        stats = PerformanceMonitor.get_query_stats(tenant.schema_name)
        
        if stats.get('slow_queries'):
            self.stdout.write('  Slow queries:')
            for query in stats['slow_queries'][:5]:  # Show top 5
                self.stdout.write(f'    - {query[0][:100]}...')
                self.stdout.write(f'      Calls: {query[1]}, Avg time: {query[2]:.2f}ms')
        else:
            self.stdout.write('  No slow queries found')
    
    def vacuum_tables(self, tenant):
        """Vacuum tables to reclaim space."""
        self.stdout.write(f'  Vacuuming tables for {tenant.schema_name}...')
        
        with connection.cursor() as cursor:
            # Get all tables in schema
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = %s
            """, [tenant.schema_name])
            
            tables = cursor.fetchall()
            for table_name, in tables:
                try:
                    cursor.execute(f'VACUUM ANALYZE {tenant.schema_name}.{table_name}')
                    self.stdout.write(f'    âœ“ Vacuumed {table_name}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'    âš  Could not vacuum {table_name}: {e}'))
        
        self.stdout.write(self.style.SUCCESS('  âœ“ Vacuum complete'))
