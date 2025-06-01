"""
Commande Django pour effectuer un contrôle de sécurité rapide.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _
from multitenant.models import Tenant
from multitenant.security import SecurityAuditor


class Command(BaseCommand):
    help = 'Effectue un contrôle de sécurité rapide sur un ou tous les tenants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Nom ou ID du tenant à vérifier (laisser vide pour tous)',
        )
        parser.add_argument(
            '--test',
            choices=[
                'schema',
                'middleware',
                'cache',
                'files',
                'headers',
                'permissions'
            ],
            help='Test spécifique à exécuter',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher des informations détaillées',
        )

    def handle(self, *args, **options):
        tenant_identifier = options.get('tenant')
        test_name = options.get('test')
        verbose = options.get('verbose', False)
        
        auditor = SecurityAuditor()
        
        # Déterminer quel tenant vérifier
        if tenant_identifier:
            try:
                # Essayer d'abord par ID
                tenant = Tenant.objects.get(id=tenant_identifier)
            except (Tenant.DoesNotExist, ValueError):
                # Essayer par nom
                try:
                    tenant = Tenant.objects.get(name=tenant_identifier)
                except Tenant.DoesNotExist:
                    raise CommandError(f"Tenant non trouvé: {tenant_identifier}")
            
            tenants = [tenant]
            self.stdout.write(self.style.SUCCESS(f"Vérification du tenant: {tenant.name}"))
        else:
            tenants = Tenant.objects.filter(is_active=True)
            self.stdout.write(self.style.SUCCESS(f"Vérification de {tenants.count()} tenants actifs"))
        
        # Mapper les noms de tests aux méthodes
        test_methods = {
            'schema': ('audit_cross_schema_access', _('Isolation des schémas')),
            'middleware': ('audit_middleware_isolation', _('Isolation du middleware')),
            'cache': ('audit_cache_isolation', _('Isolation du cache')),
            'files': ('audit_file_access', _('Accès aux fichiers')),
            'headers': ('audit_security_headers', _('En-têtes de sécurité')),
            'permissions': ('audit_tenant_permissions', _('Permissions des tenants')),
        }
        
        violations_found = 0
        
        # Exécuter les tests
        if test_name:
            # Un seul test spécifique
            method_name, test_label = test_methods[test_name]
            method = getattr(auditor, method_name)
            
            self.stdout.write(f"\n{test_label}:")
            self.stdout.write("-" * 40)
            
            for tenant in tenants:
                result = method()
                violations = result.get('violations', [])
                violations_found += len(violations)
                
                if verbose or violations:
                    self.stdout.write(f"\n{tenant.name}:")
                    if violations:
                        for violation in violations:
                            self.stdout.write(
                                self.style.ERROR(f"  ❌ {violation['description']}")
                            )
                    else:
                        self.stdout.write(self.style.SUCCESS("  ✓ Aucune violation"))
        else:
            # Tous les tests
            for method_key, (method_name, test_label) in test_methods.items():
                method = getattr(auditor, method_name)
                
                self.stdout.write(f"\n{test_label}:")
                self.stdout.write("-" * 40)
                
                for tenant in tenants:
                    result = method()
                    violations = result.get('violations', [])
                    violations_found += len(violations)
                    
                    if verbose or violations:
                        self.stdout.write(f"\n{tenant.name}:")
                        if violations:
                            for violation in violations:
                                self.stdout.write(
                                    self.style.ERROR(f"  ❌ {violation['description']}")
                                )
                        else:
                            self.stdout.write(self.style.SUCCESS("  ✓ Aucune violation"))
        
        # Résumé
        self.stdout.write("\n" + "=" * 50)
        if violations_found > 0:
            self.stdout.write(
                self.style.ERROR(f"Total des violations trouvées: {violations_found}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("Aucune violation de sécurité trouvée! ✓")
            )
        
        # Retourner avec le code approprié
        if violations_found > 0:
            raise CommandError(f"{violations_found} violations trouvées")