"""
Commande pour valider la migration d'un tenant.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from multitenant.models import Tenant
from competitions.models import Club, Practitioner, Competition, Registration


class Command(BaseCommand):
    help = 'Valide la migration d\'un tenant spécifique'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'tenant_schema',
            type=str,
            help='Nom du schéma du tenant à valider'
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Effectuer une validation complète'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tenter de corriger les problèmes détectés'
        )
    
    def handle(self, *args, **options):
        schema_name = options['tenant_schema']
        full_validation = options['full']
        auto_fix = options['fix']
        
        try:
            tenant = Tenant.objects.get(schema_name=schema_name)
        except Tenant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Tenant avec schéma {schema_name} non trouvé')
            )
            return
        
        self.stdout.write(f"Validation du tenant: {tenant.name}")
        self.stdout.write(f"Schéma: {tenant.schema_name}")
        self.stdout.write(f"Domaine: {tenant.domain}")
        self.stdout.write("="*50)
        
        # Validation basique
        self.validate_schema_exists(tenant)
        self.validate_domain_exists(tenant)
        self.validate_tables(tenant)
        
        if full_validation:
            # Validation approfondie
            self.validate_data_integrity(tenant)
            self.validate_relationships(tenant)
            self.validate_permissions(tenant)
            self.validate_performance(tenant)
        
        if auto_fix and self.errors_found:
            self.fix_issues(tenant)
    
    def validate_schema_exists(self, tenant):
        """Vérifie que le schéma PostgreSQL existe."""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.schemata 
                WHERE schema_name = %s
            """, [tenant.schema_name])
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Schéma {tenant.schema_name} existe")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"✗ Schéma {tenant.schema_name} n'existe pas")
                )
                self.errors_found = True
    
    def validate_domain_exists(self, tenant):
        """Vérifie que les domaines sont configurés."""
        domains = tenant.domains.all()
        
        if domains.exists():
            self.stdout.write(
                self.style.SUCCESS(f"✓ {domains.count()} domaine(s) configuré(s)")
            )
            for domain in domains:
                self.stdout.write(f"  - {domain.domain} {'(principal)' if domain.is_primary else ''}")
        else:
            self.stdout.write(
                self.style.ERROR("✗ Aucun domaine configuré")
            )
            self.errors_found = True
    
    def validate_tables(self, tenant):
        """Vérifie que les tables nécessaires existent."""
        required_tables = [
            'competitions_practitioner',
            'competitions_competition',
            'competitions_registration',
            'grades_grade',
            'finances_invoice',
        ]
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s
            """, [tenant.schema_name])
            
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            missing_tables = []
            for table in required_tables:
                if table in existing_tables:
                    self.stdout.write(self.style.SUCCESS(f"✓ Table {table} existe"))
                else:
                    self.stdout.write(self.style.ERROR(f"✗ Table {table} manquante"))
                    missing_tables.append(table)
                    self.errors_found = True
            
            self.stdout.write(f"\nTotal: {len(existing_tables)} tables dans le schéma")
    
    def validate_data_integrity(self, tenant):
        """Valide l'intégrité des données migrées."""
        self.stdout.write("\nValidation de l'intégrité des données...")
        
        if hasattr(tenant, 'original_club_id'):
            try:
                original_club = Club.objects.get(id=tenant.original_club_id)
                
                with connection.cursor() as cursor:
                    # Basculer vers le schéma du tenant
                    cursor.execute(f'SET search_path TO {tenant.schema_name}')
                    
                    # Comparer le nombre de pratiquants
                    cursor.execute("SELECT COUNT(*) FROM competitions_practitioner")
                    tenant_practitioners = cursor.fetchone()[0]
                    
                    original_practitioners = original_club.practitioners.count()
                    
                    if tenant_practitioners == original_practitioners:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Nombre de pratiquants cohérent: {tenant_practitioners}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"✗ Incohérence pratiquants: {tenant_practitioners} "
                                f"vs {original_practitioners} (original)"
                            )
                        )
                        self.errors_found = True
                    
                    # Comparer les compétitions
                    cursor.execute("SELECT COUNT(*) FROM competitions_competition")
                    tenant_competitions = cursor.fetchone()[0]
                    
                    self.stdout.write(f"  Compétitions dans le tenant: {tenant_competitions}")
                    
            except Club.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING("Club original non trouvé pour comparaison")
                )
    
    def validate_relationships(self, tenant):
        """Valide les relations entre entités."""
        self.stdout.write("\nValidation des relations...")
        
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {tenant.schema_name}')
            
            # Vérifier les inscriptions orphelines
            cursor.execute("""
                SELECT COUNT(*) 
                FROM competitions_registration r
                LEFT JOIN competitions_practitioner p ON r.practitioner_id = p.id
                WHERE p.id IS NULL
            """)
            
            orphan_registrations = cursor.fetchone()[0]
            
            if orphan_registrations == 0:
                self.stdout.write(
                    self.style.SUCCESS("✓ Aucune inscription orpheline")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ {orphan_registrations} inscription(s) orpheline(s)"
                    )
                )
                self.errors_found = True
    
    def validate_permissions(self, tenant):
        """Valide les permissions et accès."""
        self.stdout.write("\nValidation des permissions...")
        
        # Vérifier les admins
        from django.contrib.auth.models import User
        
        admin_emails = [
            f"admin@{tenant.domain}",
            f"admin@{tenant.subdomain}.martialcomp.com"
        ]
        
        admins = User.objects.filter(
            email__in=admin_emails,
            is_staff=True
        )
        
        if admins.exists():
            self.stdout.write(
                self.style.SUCCESS(f"✓ {admins.count()} administrateur(s) trouvé(s)")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✗ Aucun administrateur configuré")
            )
            self.errors_found = True
    
    def validate_performance(self, tenant):
        """Teste les performances du schéma."""
        self.stdout.write("\nTests de performance...")
        
        import time
        
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {tenant.schema_name}')
            
            # Test de requête simple
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM competitions_practitioner")
            duration = time.time() - start_time
            
            if duration < 0.1:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Performance requête simple: {duration:.3f}s")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Performance requête simple: {duration:.3f}s")
                )
            
            # Test de jointure
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) 
                FROM competitions_registration r
                JOIN competitions_practitioner p ON r.practitioner_id = p.id
                JOIN competitions_competition c ON r.competition_id = c.id
            """)
            duration = time.time() - start_time
            
            if duration < 0.5:
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Performance jointure: {duration:.3f}s")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"⚠ Performance jointure: {duration:.3f}s")
                )
    
    def fix_issues(self, tenant):
        """Tente de corriger les problèmes détectés."""
        self.stdout.write("\nTentative de correction des problèmes...")
        
        # Ici, implémenter les corrections automatiques possibles
        # Par exemple, recréer les indexes manquants, etc.
        
        from multitenant.db_optimization import IndexManager
        
        self.stdout.write("Création des indexes manquants...")
        IndexManager.create_tenant_indexes(tenant.schema_name)
        
        self.stdout.write("Analyse des tables...")
        IndexManager.analyze_tenant_tables(tenant.schema_name)
        
        self.stdout.write(self.style.SUCCESS("Corrections appliquées"))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors_found = False