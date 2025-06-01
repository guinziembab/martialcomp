"""
Commande Django pour exécuter un audit de sécurité multi-tenant.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
import os
import sys
import json
from datetime import datetime

from multitenant.models import Tenant
from multitenant.security import SecurityAuditor, run_security_audit


class Command(BaseCommand):
    help = "Exécute un audit de sécurité pour l'architecture multi-tenant"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant', 
            type=str,
            help='Slug du tenant à auditer (par défaut: tous les tenants)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Chemin de sortie pour le rapport JSON (par défaut: logs/security_reports/)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche les détails de chaque test'
        )
        parser.add_argument(
            '--only',
            type=str,
            help='Exécute uniquement les tests spécifiés, séparés par des virgules'
        )
        parser.add_argument(
            '--skip',
            type=str,
            help='Ignore les tests spécifiés, séparés par des virgules'
        )
    
    def handle(self, *args, **options):
        tenant_slug = options.get('tenant')
        output_path = options.get('output')
        verbose = options.get('verbose', False)
        only_tests = options.get('only')
        skip_tests = options.get('skip')
        
        # Initialiser le rapport
        report = {
            'timestamp': timezone.now().isoformat(),
            'tenants_audited': [],
            'summary': {
                'status': 'pending',
                'tests_run': 0,
                'violations_found': 0,
            },
            'results': {}
        }
        
        # Obtenir le tenant spécifié ou tous les tenants actifs
        if tenant_slug:
            try:
                tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
                tenants = [tenant]
                self.stdout.write(self.style.SUCCESS(
                    f"Audit de sécurité pour le tenant: {tenant.name}"
                ))
            except Tenant.DoesNotExist:
                raise CommandError(f"Tenant avec slug '{tenant_slug}' non trouvé ou inactif")
        else:
            tenants = Tenant.objects.filter(is_active=True)
            self.stdout.write(self.style.SUCCESS(
                f"Audit de sécurité pour tous les tenants ({tenants.count()} tenants)"
            ))
        
        # Traiter les filtres de tests
        available_tests = [
            'cross_schema_access',
            'middleware_isolation',
            'cache_isolation',
            'file_access',
            'security_headers',
            'tenant_permissions'
        ]
        
        tests_to_run = available_tests
        
        if only_tests:
            only_list = [test.strip() for test in only_tests.split(',')]
            tests_to_run = [test for test in only_list if test in available_tests]
            self.stdout.write(self.style.WARNING(
                f"Exécution limitée aux tests: {', '.join(tests_to_run)}"
            ))
        
        if skip_tests:
            skip_list = [test.strip() for test in skip_tests.split(',')]
            tests_to_run = [test for test in tests_to_run if test not in skip_list]
            self.stdout.write(self.style.WARNING(
                f"Tests ignorés: {', '.join(skip_list)}"
            ))
        
        if not tests_to_run:
            self.stdout.write(self.style.ERROR("Aucun test à exécuter après filtrage"))
            return
        
        # Exécuter l'audit pour chaque tenant
        total_violations = 0
        total_tests = 0
        all_passed = True
        
        for tenant in tenants:
            self.stdout.write(f"Auditing tenant: {tenant.name} ({tenant.schema_name})")
            
            # Créer un auditeur pour ce tenant
            auditor = SecurityAuditor(tenant)
            
            # Exécuter les tests sélectionnés
            for test in tests_to_run:
                self.stdout.write(f"  Exécution du test: {test}")
                
                # Exécuter le test
                test_method = getattr(auditor, f"audit_{test}")
                result = test_method()
                
                # Afficher les résultats si verbose
                if verbose:
                    self.stdout.write(f"    Résultat: {result['status']}")
                    
                    if result['status'] == 'passed':
                        self.stdout.write(self.style.SUCCESS(
                            f"    {len(result['checks'])} vérifications réussies"
                        ))
                    else:
                        self.stdout.write(self.style.ERROR(
                            f"    {len(result['violations'])} violations trouvées"
                        ))
                        
                        for i, violation in enumerate(result['violations'], 1):
                            self.stdout.write(self.style.ERROR(
                                f"    Violation {i}: {violation['description']} "
                                f"(Sévérité: {violation['severity']})"
                            ))
                
                # Mettre à jour les compteurs
                total_tests += 1
                total_violations += len(result['violations'])
                
                if result['status'] == 'failed':
                    all_passed = False
            
            # Enregistrer les résultats du tenant dans le rapport
            report['tenants_audited'].append(tenant.name)
            report['results'][tenant.name] = auditor.results
            
            # Enregistrer le rapport individuel
            auditor.save_audit_report()
        
        # Mettre à jour le résumé du rapport
        report['summary'] = {
            'status': 'passed' if all_passed else 'failed',
            'tests_run': total_tests,
            'violations_found': total_violations,
        }
        
        # Enregistrer le rapport global
        if output_path:
            # Utiliser le chemin spécifié
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            report_path = output_path
        else:
            # Utiliser le chemin par défaut
            now = datetime.now()
            report_name = f"security_audit_global_{now.strftime('%Y%m%d_%H%M%S')}.json"
            
            from multitenant.security import TENANT_SECURITY_REPORT_PATH
            os.makedirs(TENANT_SECURITY_REPORT_PATH, exist_ok=True)
            
            report_path = os.path.join(TENANT_SECURITY_REPORT_PATH, report_name)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f"Rapport d'audit enregistré: {report_path}"))
        
        # Afficher le résumé
        self.stdout.write("\nRésumé de l'audit de sécurité:")
        self.stdout.write(f"  Tenants audités: {len(report['tenants_audited'])}")
        self.stdout.write(f"  Tests exécutés: {report['summary']['tests_run']}")
        self.stdout.write(f"  Violations trouvées: {report['summary']['violations_found']}")
        
        if all_passed:
            self.stdout.write(self.style.SUCCESS("  Statut: SUCCÈS - Aucune violation trouvée"))
        else:
            self.stdout.write(self.style.ERROR(
                f"  Statut: ÉCHEC - {report['summary']['violations_found']} violations trouvées"
            ))
            sys.exit(1)  # Code de sortie non-zéro en cas d'échec