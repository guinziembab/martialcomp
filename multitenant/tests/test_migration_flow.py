"""
Tests pour le flux de migration multi-tenant
"""
from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.contrib.auth.models import User

from competitions.models import Club, Practitioner, Competition
from multitenant.models import Tenant, Domain
from multitenant.migrations.migrate_existing_clubs import ClubMigrator, MigrationValidator


class MigrationFlowTest(TransactionTestCase):
    """Test complet du flux de migration."""
    
    def setUp(self):
        """Configuration des tests."""
        # Créer un utilisateur admin
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Créer un club de test
        self.club = Club.objects.create(
            name="Test Martial Arts Club",
            description="Club de test pour migration",
            address="123 Test Street",
            city="Test City",
            postal_code="12345",
            country="FR",
            email="test@club.com",
            phone="+33123456789",
            owner=self.admin_user,
            is_active=True
        )
        
        # Ajouter des pratiquants
        for i in range(1, 6):
            Practitioner.objects.create(
                first_name=f"Test{i}",
                last_name=f"Practitioner{i}",
                email=f"test{i}@example.com",
                date_of_birth="1990-01-01",
                license_number=f"TEST{i:04d}",
                club=self.club,
                gender="M" if i % 2 == 0 else "F"
            )
        
        # Créer une compétition
        self.competition = Competition.objects.create(
            name="Test Competition 2024",
            date="2024-06-15",
            location="Test Location",
            description="Compétition de test",
            owner=self.club,
            status="planned"
        )
    
    def test_single_club_migration(self):
        """Test de migration d'un seul club."""
        migrator = ClubMigrator(dry_run=False)
        
        # Effectuer la migration
        migrator.migrate_club(self.club)
        
        # Vérifier que le tenant a été créé
        self.club.refresh_from_db()
        self.assertTrue(hasattr(self.club, 'tenant'))
        self.assertIsNotNone(self.club.tenant)
        
        tenant = self.club.tenant
        
        # Vérifications de base
        self.assertEqual(tenant.name, self.club.name)
        self.assertTrue(tenant.schema_name.startswith('test_martial_arts_club'))
        self.assertTrue(tenant.is_active)
        
        # Vérifier le domaine
        domain = Domain.objects.get(tenant=tenant, is_primary=True)
        self.assertEqual(domain.domain, f"{tenant.schema_name}.martialcomp.com")
        
        # Vérifier le plan
        self.assertEqual(tenant.subscription_plan, 'essentials')  # < 50 pratiquants
        
        # Vérifier les données migrées
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {tenant.schema_name}')
            
            # Vérifier les pratiquants
            cursor.execute("SELECT COUNT(*) FROM competitions_practitioner")
            practitioners_count = cursor.fetchone()[0]
            self.assertEqual(practitioners_count, 5)
            
            # Vérifier les compétitions
            cursor.execute("SELECT COUNT(*) FROM competitions_competition")
            competitions_count = cursor.fetchone()[0]
            self.assertEqual(competitions_count, 1)
    
    def test_migration_validation(self):
        """Test de la validation post-migration."""
        migrator = ClubMigrator(dry_run=False)
        migrator.migrate_club(self.club)
        
        tenant = self.club.tenant
        
        # Valider la migration
        validator = MigrationValidator(tenant, self.club)
        validation_result = validator.validate_all()
        
        # Vérifier qu'il n'y a pas d'erreurs
        self.assertFalse(validation_result['has_errors'])
        self.assertEqual(len(validation_result['errors']), 0)
    
    def test_dry_run_migration(self):
        """Test de migration en mode dry-run."""
        migrator = ClubMigrator(dry_run=True)
        
        # Effectuer la migration en dry-run
        migrator.migrate_club(self.club)
        
        # Vérifier que rien n'a été créé
        self.club.refresh_from_db()
        self.assertFalse(hasattr(self.club, 'tenant') and self.club.tenant)
        
        # Vérifier qu'aucun tenant n'a été créé
        tenant_count = Tenant.objects.filter(name=self.club.name).count()
        self.assertEqual(tenant_count, 0)
    
    def test_batch_migration(self):
        """Test de migration de plusieurs clubs."""
        # Créer des clubs supplémentaires
        clubs = [self.club]
        for i in range(1, 3):
            club = Club.objects.create(
                name=f"Club Test {i}",
                city=f"City{i}",
                country="FR",
                owner=self.admin_user
            )
            clubs.append(club)
        
        # Migrer tous les clubs
        migrator = ClubMigrator(dry_run=False)
        club_ids = [c.id for c in clubs]
        report = migrator.migrate_all_clubs(club_ids=club_ids)
        
        # Vérifier le rapport
        self.assertEqual(report['summary']['total_clubs'], 3)
        self.assertEqual(report['summary']['migrated'], 3)
        self.assertEqual(report['summary']['failed'], 0)
        
        # Vérifier que tous les clubs ont des tenants
        for club in clubs:
            club.refresh_from_db()
            self.assertTrue(hasattr(club, 'tenant'))
            self.assertIsNotNone(club.tenant)
    
    def test_migration_with_large_club(self):
        """Test avec un grand club pour vérifier le plan."""
        # Créer un grand club avec beaucoup de pratiquants
        large_club = Club.objects.create(
            name="Large Club",
            city="Big City",
            country="FR",
            owner=self.admin_user
        )
        
        # Ajouter 250 pratiquants
        for i in range(250):
            Practitioner.objects.create(
                first_name=f"Prat{i}",
                last_name="Large",
                email=f"prat{i}@large.com",
                club=large_club
            )
        
        # Migrer le club
        migrator = ClubMigrator(dry_run=False)
        migrator.migrate_club(large_club)
        
        # Vérifier le plan (devrait être 'champion' car > 200 pratiquants)
        large_club.refresh_from_db()
        self.assertEqual(large_club.tenant.subscription_plan, 'champion')
    
    def test_migration_error_handling(self):
        """Test de la gestion des erreurs."""
        # Créer un club avec des données invalides
        invalid_club = Club.objects.create(
            name="Invalid!@#$%^&*()Club",  # Nom avec caractères spéciaux
            city="Test",
            country="XX"  # Pays non reconnu
        )
        
        migrator = ClubMigrator(dry_run=False)
        
        try:
            migrator.migrate_club(invalid_club)
            # Le continent sera 'EUROPE' par défaut
            self.assertEqual(invalid_club.tenant.continent, 'EUROPE')
            
            # Le nom du schéma sera nettoyé
            self.assertTrue(invalid_club.tenant.schema_name.replace('_', '').isalnum())
        except Exception as e:
            self.fail(f"La migration a échoué avec l'erreur: {e}")
    
    def test_schema_uniqueness(self):
        """Test de l'unicité des noms de schéma."""
        # Créer deux clubs avec le même nom
        club1 = Club.objects.create(name="Duplicate Club", city="City1")
        club2 = Club.objects.create(name="Duplicate Club", city="City2")
        
        migrator = ClubMigrator(dry_run=False)
        
        # Migrer les deux clubs
        migrator.migrate_club(club1)
        migrator.migrate_club(club2)
        
        # Vérifier que les schémas sont différents
        self.assertNotEqual(club1.tenant.schema_name, club2.tenant.schema_name)
        
        # Le deuxième devrait avoir un suffixe
        self.assertTrue(club2.tenant.schema_name.endswith('_1'))
    
    def tearDown(self):
        """Nettoyage après les tests."""
        # Nettoyer les schémas créés
        tenants = Tenant.objects.all()
        for tenant in tenants:
            with connection.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS {tenant.schema_name} CASCADE')
        
        super().tearDown()


class MigrationUtilityTest(TestCase):
    """Tests des utilitaires de migration."""
    
    def test_schema_name_generation(self):
        """Test de la génération des noms de schéma."""
        migrator = ClubMigrator()
        
        test_cases = [
            ("Simple Club", "simple_club"),
            ("Club with Numbers 123", "club_with_numbers_123"),
            ("Spécial Çharacters!", "sp_cial_haracters"),
            ("Very Long Club Name That Exceeds The Maximum Length Allowed", "very_long_club_name_that_excee"),
        ]
        
        for club_name, expected_base in test_cases:
            club = Club(name=club_name)
            schema_name = migrator.generate_schema_name(club)
            self.assertTrue(schema_name.startswith(expected_base))
    
    def test_continent_determination(self):
        """Test de la détermination du continent."""
        migrator = ClubMigrator()
        
        test_cases = [
            ("FR", "EUROPE"),
            ("US", "NORTH_AMERICA"),
            ("BR", "SOUTH_AMERICA"),
            ("CN", "ASIA"),
            ("AU", "OCEANIA"),
            ("ZA", "AFRICA"),
            ("XX", "EUROPE"),  # Par défaut
        ]
        
        for country, expected_continent in test_cases:
            club = Club(country=country)
            continent = migrator.determine_continent(club)
            self.assertEqual(continent, expected_continent)
    
    def test_plan_determination(self):
        """Test de la détermination du plan d'abonnement."""
        migrator = ClubMigrator()
        
        # Club petit (< 50 pratiquants)
        small_club = Club.objects.create(name="Small Club")
        for i in range(30):
            Practitioner.objects.create(
                first_name=f"P{i}",
                last_name="Small",
                club=small_club
            )
        self.assertEqual(migrator.determine_subscription_plan(small_club), 'essentials')
        
        # Club moyen (50-200 pratiquants)
        medium_club = Club.objects.create(name="Medium Club")
        for i in range(100):
            Practitioner.objects.create(
                first_name=f"P{i}",
                last_name="Medium",
                club=medium_club
            )
        self.assertEqual(migrator.determine_subscription_plan(medium_club), 'masters')
        
        # Grand club (> 200 pratiquants)
        large_club = Club.objects.create(name="Large Club")
        for i in range(250):
            Practitioner.objects.create(
                first_name=f"P{i}",
                last_name="Large",
                club=large_club
            )
        self.assertEqual(migrator.determine_subscription_plan(large_club), 'champion')