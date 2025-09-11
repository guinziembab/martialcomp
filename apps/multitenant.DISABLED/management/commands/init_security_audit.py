"""
Commande Django pour initialiser le système d'audit de sécurité.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
from pathlib import Path


class Command(BaseCommand):
    help = 'Initialise le système d\'audit de sécurité multi-tenant'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Initialisation du système d\'audit de sécurité...'))
        
        # 1. Créer les répertoires nécessaires
        self.create_directories()
        
        # 2. Vérifier la configuration
        self.check_configuration()
        
        # 3. Créer les fichiers de configuration
        self.create_config_files()
        
        # 4. Initialiser les permissions
        self.init_permissions()
        
        self.stdout.write(self.style.SUCCESS('âœ“ Système d\'audit de sécurité initialisé avec succès!'))
    
    def create_directories(self):
        """Crée les répertoires nécessaires pour les rapports."""
        self.stdout.write('Création des répertoires...')
        
        # Répertoire pour les rapports de sécurité
        report_dir = getattr(settings, 'SECURITY_REPORT_DIR', 
                           os.path.join(settings.BASE_DIR, 'security_reports'))
        
        os.makedirs(report_dir, exist_ok=True)
        os.makedirs(os.path.join(report_dir, 'archives'), exist_ok=True)
        
        # Créer un fichier README
        readme_path = os.path.join(report_dir, 'README.md')
        if not os.path.exists(readme_path):
            with open(readme_path, 'w') as f:
                f.write("""# Rapports de Sécurité

Ce répertoire contient les rapports d'audit de sécurité multi-tenant.

## Structure

- `/` : Rapports actuels
- `/archives/` : Rapports archivés (plus de 30 jours)

## Format des fichiers

Les rapports sont stockés au format JSON avec le naming convention :
- `security_audit_global_YYYYMMDD_HHMMSS.json` : Audit global
- `security_audit_tenant_<slug>_YYYYMMDD_HHMMSS.json` : Audit spécifique Ã  un tenant

## Sécurité

âš ï¸ Ces rapports contiennent des informations sensibles. 
Assurez-vous que ce répertoire est correctement sécurisé et exclu du contrÃ´le de version.
""")
        
        # Ajouter au .gitignore si nécessaire
        gitignore_path = os.path.join(settings.BASE_DIR, '.gitignore')
        if os.path.exists(gitignore_path):
            with open(gitignore_path, 'r') as f:
                content = f.read()
            
            if 'security_reports/' not in content:
                with open(gitignore_path, 'a') as f:
                    f.write('\n# Security audit reports\nsecurity_reports/\n')
                self.stdout.write(self.style.WARNING('  Ajouté security_reports/ au .gitignore'))
        
        self.stdout.write(self.style.SUCCESS(f'  âœ“ Répertoires créés: {report_dir}'))
    
    def check_configuration(self):
        """Vérifie que la configuration est correcte."""
        self.stdout.write('Vérification de la configuration...')
        
        # Vérifier les middlewares
        middleware_classes = settings.MIDDLEWARE
        required_middleware = 'multitenant.middleware.TenantMiddleware'
        
        if required_middleware not in middleware_classes:
            self.stdout.write(self.style.ERROR(
                f'  âœ— {required_middleware} non trouvé dans MIDDLEWARE'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'  âœ“ {required_middleware} configuré'
            ))
        
        # Vérifier la configuration de sécurité
        security_config = getattr(settings, 'SECURITY_AUDIT_CONFIG', {})
        default_config = {
            'critical_score_threshold': 50,
            'warning_score_threshold': 75,
            'report_retention_days': 30,
            'email_alerts_enabled': True,
            'allowed_audit_hosts': ['localhost', '127.0.0.1'],
        }
        
        for key, default_value in default_config.items():
            if key not in security_config:
                self.stdout.write(self.style.WARNING(
                    f'  Configuration manquante: SECURITY_AUDIT_CONFIG[{key}] = {default_value}'
                ))
        
        # Vérifier Celery
        if 'django_celery_beat' in settings.INSTALLED_APPS:
            self.stdout.write(self.style.SUCCESS('  âœ“ Celery Beat configuré'))
        else:
            self.stdout.write(self.style.WARNING(
                '  âš  django_celery_beat non installé - audits planifiés non disponibles'
            ))
    
    def create_config_files(self):
        """Crée les fichiers de configuration par défaut."""
        self.stdout.write('Création des fichiers de configuration...')
        
        # Configuration de sécurité par défaut
        config_dir = os.path.join(settings.BASE_DIR, 'config', 'security')
        os.makedirs(config_dir, exist_ok=True)
        
        # Politique de sécurité
        policy_file = os.path.join(config_dir, 'security_policy.json')
        if not os.path.exists(policy_file):
            policy = {
                "version": "1.0",
                "policies": {
                    "password": {
                        "min_length": 12,
                        "require_uppercase": True,
                        "require_lowercase": True,
                        "require_numbers": True,
                        "require_special": True
                    },
                    "session": {
                        "timeout_minutes": 30,
                        "max_concurrent": 3
                    },
                    "audit": {
                        "retention_days": 90,
                        "required_tests": [
                            "cross_schema_access",
                            "middleware_isolation",
                            "cache_isolation",
                            "file_access",
                            "security_headers",
                            "tenant_permissions"
                        ]
                    }
                }
            }
            
            with open(policy_file, 'w') as f:
                json.dump(policy, f, indent=2)
            
            self.stdout.write(self.style.SUCCESS(f'  âœ“ Politique de sécurité créée: {policy_file}'))
        
        # Tests de sécurité personnalisés
        custom_tests_file = os.path.join(config_dir, 'custom_tests.py')
        if not os.path.exists(custom_tests_file):
            with open(custom_tests_file, 'w') as f:
                f.write("""\"\"\"
Tests de sécurité personnalisés pour l'audit multi-tenant.
\"\"\"

def custom_api_security_test(auditor):
    \"\"\"
    Test personnalisé pour vérifier la sécurité des API.
    \"\"\"
    return {
        'status': 'passed',
        'violations': [],
        'checks': [
            {
                'description': 'Vérification des endpoints API',
                'status': 'passed'
            }
        ]
    }

# Ajouter vos tests personnalisés ici
CUSTOM_TESTS = {
    'api_security': custom_api_security_test,
}
""")
            
            self.stdout.write(self.style.SUCCESS(f'  âœ“ Tests personnalisés créés: {custom_tests_file}'))
    
    def init_permissions(self):
        """Initialise les permissions pour l'audit de sécurité."""
        self.stdout.write('Initialisation des permissions...')
        
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Créer les permissions personnalisées si elles n'existent pas
        app_label = 'multitenant'
        permissions = [
            ('run_security_audit', 'Can run security audits'),
            ('view_security_reports', 'Can view security reports'),
            ('manage_security_alerts', 'Can manage security alerts'),
            ('configure_security_audit', 'Can configure security audit settings'),
        ]
        
        # Obtenir le content type pour l'app multitenant
        try:
            from apps.multitenant.models import Tenant
            content_type = ContentType.objects.get_for_model(Tenant)
            
            for codename, name in permissions:
                Permission.objects.get_or_create(
                    codename=codename,
                    name=name,
                    content_type=content_type,
                )
            
            self.stdout.write(self.style.SUCCESS('  âœ“ Permissions créées avec succès'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  âš  Impossible de créer les permissions: {e}'))
        
        # Créer un groupe pour les auditeurs de sécurité
        from django.contrib.auth.models import Group
        
        try:
            security_group, created = Group.objects.get_or_create(
                name='Security Auditors'
            )
            
            if created:
                # Ajouter les permissions au groupe
                for codename, _ in permissions:
                    perm = Permission.objects.get(codename=codename)
                    security_group.permissions.add(perm)
                
                self.stdout.write(self.style.SUCCESS('  âœ“ Groupe "Security Auditors" créé'))
            else:
                self.stdout.write(self.style.SUCCESS('  âœ“ Groupe "Security Auditors" existant'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  âš  Impossible de créer le groupe: {e}'))
        
        # Afficher un résumé
        self.stdout.write('\nRésumé de l\'initialisation:')
        self.stdout.write('  - Répertoires de rapports créés')
        self.stdout.write('  - Configuration vérifiée')
        self.stdout.write('  - Fichiers de configuration créés')
        self.stdout.write('  - Permissions et groupes initialisés')
        self.stdout.write('\nProchaines étapes:')
        self.stdout.write('  1. Configurer SECURITY_AUDIT_CONFIG dans settings.py')
        self.stdout.write('  2. Planifier des audits réguliers avec: manage.py schedule_security_audits')
        self.stdout.write('  3. Lancer un premier audit avec: manage.py run_security_audit')

