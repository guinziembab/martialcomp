"""
Management command to monitor tenant health
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tabulate import tabulate
import json

from ...monitoring import TenantHealthMonitor, TenantMetricsCollector
from ...models import Tenant


class Command(BaseCommand):
    help = 'Monitor tenant health and collect metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Run health check on all tenants'
        )
        parser.add_argument(
            '--metrics',
            action='store_true',
            help='Collect metrics for all tenants'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Check specific tenant (ID, slug, or domain)'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON'
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Continuously monitor (refresh every 30 seconds)'
        )
    
    def handle(self, *args, **options):
        if options['watch']:
            self._continuous_monitoring(options)
        else:
            self._single_check(options)
    
    def _single_check(self, options):
        """Perform a single health check"""
        monitor = TenantHealthMonitor()
        
        if options['tenant']:
            # Check specific tenant
            tenant = self._get_tenant(options['tenant'])
            results = monitor.check_tenant_health(tenant)
            
            if options['json']:
                self.stdout.write(json.dumps(results, indent=2))
            else:
                self._display_tenant_health(results)
        
        elif options['check']:
            # Check all tenants
            results = monitor.check_all_tenants()
            
            if options['json']:
                self.stdout.write(json.dumps(results, indent=2))
            else:
                self._display_all_health(results)
        
        elif options['metrics']:
            # Collect metrics
            collector = TenantMetricsCollector()
            
            if options['tenant']:
                tenant = self._get_tenant(options['tenant'])
                metrics = collector.collect_metrics(tenant)
                
                if options['json']:
                    self.stdout.write(json.dumps(metrics, indent=2))
                else:
                    self._display_metrics(metrics)
            else:
                # Collect for all tenants
                all_metrics = {}
                for tenant in Tenant.objects.filter(is_active=True):
                    all_metrics[str(tenant.id)] = collector.collect_metrics(tenant)
                
                if options['json']:
                    self.stdout.write(json.dumps(all_metrics, indent=2))
                else:
                    self._display_all_metrics(all_metrics)
        
        else:
            self.stdout.write(self.style.WARNING('No action specified. Use --check or --metrics'))
            self.stdout.write('Use --help for usage information')
    
    def _continuous_monitoring(self, options):
        """Continuously monitor tenant health"""
        import time
        import os
        
        self.stdout.write(self.style.SUCCESS('Starting continuous monitoring...'))
        self.stdout.write('Press Ctrl+C to stop')
        
        try:
            while True:
                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')
                
                # Display timestamp
                self.stdout.write(f"Last update: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.stdout.write("-" * 50)
                
                # Run health check
                monitor = TenantHealthMonitor()
                results = monitor.check_all_tenants()
                self._display_all_health(results)
                
                # Wait for next update
                time.sleep(30)
        
        except KeyboardInterrupt:
            self.stdout.write('\n' + self.style.WARNING('Monitoring stopped'))
    
    def _display_tenant_health(self, health):
        """Display health status for a single tenant"""
        self.stdout.write(f"\nTenant: {health['tenant_name']}")
        self.stdout.write(f"Status: {self._colored_status(health['status'])}")
        self.stdout.write(f"Last check: {health['last_check']}")
        
        # Display checks
        self.stdout.write("\nHealth Checks:")
        table_data = []
        for check, result in health['checks'].items():
            status = self._colored_status(result['status'])
            table_data.append([check.title(), status, result['message']])
        
        self.stdout.write(
            tabulate(table_data, headers=['Check', 'Status', 'Message'], tablefmt='simple')
        )
        
        # Display warnings and errors
        if health['warnings']:
            self.stdout.write("\n" + self.style.WARNING("Warnings:"))
            for warning in health['warnings']:
                self.stdout.write(f"  - {warning}")
        
        if health['errors']:
            self.stdout.write("\n" + self.style.ERROR("Errors:"))
            for error in health['errors']:
                self.stdout.write(f"  - {error}")
    
    def _display_all_health(self, results):
        """Display health status for all tenants"""
        # Summary
        self.stdout.write("\nSystem Health Summary:")
        summary_data = [
            ['Total Tenants', results['total_tenants']],
            ['Healthy', self.style.SUCCESS(str(results['healthy_tenants']))],
            ['Unhealthy', self.style.ERROR(str(results['unhealthy_tenants']))],
            ['Warnings', self.style.WARNING(str(results['warnings']))],
            ['Overall Status', self._colored_status(results['overall_health'])],
        ]
        
        self.stdout.write(
            tabulate(summary_data, tablefmt='simple')
        )
        
        # Tenant details
        self.stdout.write("\nTenant Status:")
        table_data = []
        
        for slug, status in results['tenant_status'].items():
            health_status = self._colored_status(status['status'])
            warning_count = len(status.get('warnings', []))
            error_count = len(status.get('errors', []))
            
            table_data.append([
                status['tenant_name'],
                slug,
                health_status,
                warning_count,
                error_count,
            ])
        
        self.stdout.write(
            tabulate(
                table_data,
                headers=['Tenant', 'Slug', 'Status', 'Warnings', 'Errors'],
                tablefmt='grid'
            )
        )
        
        # Check duration
        self.stdout.write(f"\nCheck completed in {results['check_duration']:.2f} seconds")
    
    def _display_metrics(self, metrics):
        """Display metrics for a tenant"""
        self.stdout.write(f"\nMetrics for Tenant: {metrics['tenant_id']}")
        self.stdout.write(f"Timestamp: {metrics['timestamp']}")
        
        # Performance metrics
        if 'performance' in metrics:
            self.stdout.write("\nPerformance Metrics:")
            perf_data = []
            for key, value in metrics['performance'].items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        perf_data.append([f"{key}.{subkey}", subvalue])
                else:
                    perf_data.append([key, value])
            
            self.stdout.write(
                tabulate(perf_data, headers=['Metric', 'Value'], tablefmt='simple')
            )
        
        # Usage metrics
        if 'usage' in metrics:
            self.stdout.write("\nUsage Metrics:")
            usage_data = []
            for key, value in metrics['usage'].items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        usage_data.append([f"{key}.{subkey}", subvalue])
                else:
                    usage_data.append([key, value])
            
            self.stdout.write(
                tabulate(usage_data, headers=['Metric', 'Value'], tablefmt='simple')
            )
    
    def _display_all_metrics(self, all_metrics):
        """Display metrics for all tenants"""
        for tenant_id, metrics in all_metrics.items():
            self.stdout.write(f"\n{'=' * 50}")
            self._display_metrics(metrics)
    
    def _colored_status(self, status):
        """Return colored status text"""
        if status == 'healthy' or status == 'ok':
            return self.style.SUCCESS(status.upper())
        elif status == 'warning':
            return self.style.WARNING(status.upper())
        elif status == 'unhealthy' or status == 'error':
            return self.style.ERROR(status.upper())
        else:
            return status
    
    def _get_tenant(self, identifier):
        """Get tenant by ID, slug, or domain"""
        try:
            # Try UUID first
            return Tenant.objects.get(id=identifier)
        except (Tenant.DoesNotExist, ValueError):
            pass
        
        try:
            # Try slug
            return Tenant.objects.get(slug=identifier)
        except Tenant.DoesNotExist:
            pass
        
        try:
            # Try domain
            return Tenant.objects.get(domain=identifier)
        except Tenant.DoesNotExist:
            pass
        
        raise CommandError(f"Tenant not found: {identifier}")