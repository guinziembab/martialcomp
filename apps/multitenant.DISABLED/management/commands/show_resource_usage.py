"""
Commande pour afficher l'utilisation des ressources par tenant.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from tabulate import tabulate

from apps.multitenant.models import Tenant
from apps.multitenant.resource_limits import get_resource_summary_for_tenant


class Command(BaseCommand):
    help = "Affiche l'utilisation des ressources pour les tenants"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Slug du tenant spécifique'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['table', 'json', 'detailed'],
            default='table',
            help='Format de sortie'
        )
        parser.add_argument(
            '--alerts-only',
            action='store_true',
            help='Afficher uniquement les alertes'
        )
    
    def handle(self, *args, **options):
        tenant_slug = options.get('tenant')
        format_type = options.get('format')
        alerts_only = options.get('alerts_only')
        
        # Récupérer les tenants
        if tenant_slug:
            try:
                tenants = [Tenant.objects.get(slug=tenant_slug)]
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Tenant '{tenant_slug}' non trouvé"))
                return
        else:
            tenants = Tenant.objects.filter(is_active=True)
        
        # Collecter les données
        summaries = []
        for tenant in tenants:
            summary = get_resource_summary_for_tenant(tenant)
            summaries.append(summary)
        
        # Afficher selon le format
        if format_type == 'json':
            import json
            self.stdout.write(json.dumps(summaries, indent=2, default=str))
        elif format_type == 'detailed':
            self._display_detailed(summaries, alerts_only)
        else:
            self._display_table(summaries, alerts_only)
    
    def _display_table(self, summaries, alerts_only):
        """Affiche les résultats sous forme de tableau."""
        if alerts_only:
            self._display_alerts_table(summaries)
            return
        
        headers = ['Tenant', 'Plan', 'Storage', 'Users', 'Practitioners', 'Competitions', 'Alerts']
        rows = []
        
        for summary in summaries:
            usage = summary['usage']
            alerts = summary['alerts']
            
            def format_usage(key):
                count = usage.get(f"{key}_count", 0)
                percentage = usage.get(f"{key}_percentage", 0)
                unlimited = usage.get(f"{key}_unlimited", False)
                
                if unlimited:
                    return f"{count} (âˆž)"
                
                if percentage >= 95:
                    return self.style.ERROR(f"{count} ({percentage:.0f}%)")
                elif percentage >= 80:
                    return self.style.WARNING(f"{count} ({percentage:.0f}%)")
                else:
                    return f"{count} ({percentage:.0f}%)"
            
            alert_count = len(alerts)
            alert_display = ""
            if alert_count > 0:
                critical = len([a for a in alerts if a['level'] == 'critical'])
                warning = len([a for a in alerts if a['level'] == 'warning'])
                
                if critical > 0:
                    alert_display = self.style.ERROR(f"{critical} critical")
                if warning > 0:
                    if alert_display:
                        alert_display += ", "
                    alert_display += self.style.WARNING(f"{warning} warning")
            else:
                alert_display = self.style.SUCCESS("OK")
            
            rows.append([
                summary['tenant'],
                summary['plan'],
                format_usage('storage'),
                format_usage('user'),
                format_usage('practitioner'),
                format_usage('competition'),
                alert_display
            ])
        
        self.stdout.write(tabulate(rows, headers=headers, tablefmt='grid'))
    
    def _display_alerts_table(self, summaries):
        """Affiche uniquement les alertes."""
        headers = ['Tenant', 'Level', 'Metric', 'Usage', 'Message']
        rows = []
        
        for summary in summaries:
            for alert in summary['alerts']:
                level_display = (
                    self.style.ERROR(alert['level'].upper())
                    if alert['level'] == 'critical'
                    else self.style.WARNING(alert['level'].upper())
                )
                
                rows.append([
                    summary['tenant'],
                    level_display,
                    alert['metric'],
                    f"{alert['percentage']:.1f}%",
                    alert['message']
                ])
        
        if rows:
            self.stdout.write(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            self.stdout.write(self.style.SUCCESS("Aucune alerte"))
    
    def _display_detailed(self, summaries, alerts_only):
        """Affiche les détails complets."""
        for summary in summaries:
            self.stdout.write(f"\n{self.style.SUCCESS('=' * 50)}")
            self.stdout.write(f"Tenant: {summary['tenant']}")
            self.stdout.write(f"Plan: {summary['plan']}")
            self.stdout.write(f"Timestamp: {summary['timestamp']}")
            
            if not alerts_only:
                self.stdout.write(f"\n{self.style.SUCCESS('Utilisation des ressources:')}")
                usage = summary['usage']
                
                resources = [
                    ('Storage', 'storage'),
                    ('Users', 'user'),
                    ('Practitioners', 'practitioner'),
                    ('Competitions', 'competition'),
                    ('Categories', 'category'),
                    ('Clubs', 'club'),
                    ('Monthly Emails', 'monthly_emails'),
                    ('Backups', 'backup'),
                ]
                
                for display_name, key in resources:
                    count = usage.get(f"{key}_count", 0)
                    percentage = usage.get(f"{key}_percentage", 0)
                    unlimited = usage.get(f"{key}_unlimited", False)
                    limit = usage['limits'].get(f"max_{key}s", usage['limits'].get(f"max_{key}", 0))
                    
                    if unlimited:
                        status = f"{count} / âˆž"
                    else:
                        status = f"{count} / {limit} ({percentage:.1f}%)"
                        
                        if percentage >= 95:
                            status = self.style.ERROR(status)
                        elif percentage >= 80:
                            status = self.style.WARNING(status)
                    
                    self.stdout.write(f"  {display_name}: {status}")
                
                self.stdout.write(f"\n{self.style.SUCCESS('Quotas restants:')}")
                quotas = summary['quotas']
                for resource, remaining in quotas.items():
                    if remaining == float('inf'):
                        self.stdout.write(f"  {resource}: Illimité")
                    else:
                        self.stdout.write(f"  {resource}: {remaining}")
            
            if summary['alerts']:
                self.stdout.write(f"\n{self.style.SUCCESS('Alertes:')}")
                for alert in summary['alerts']:
                    if alert['level'] == 'critical':
                        self.stdout.write(self.style.ERROR(f"  [CRITICAL] {alert['message']}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  [WARNING] {alert['message']}"))
            elif not alerts_only:
                self.stdout.write(f"\n{self.style.SUCCESS('Aucune alerte')}")

