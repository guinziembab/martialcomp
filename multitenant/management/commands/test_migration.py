"""
Commande de test pour la migration multi-tenant
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

from competitions.models import Club, Practitioner, Competition
from multitenant.models import Tenant, Domain
from multitenant.migrations.migrate_existing_clubs import ClubMigrator, MigrationValidator


class Command(BaseCommand):
    help = 'Test la migration multi-tenant avec des données de test'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Nettoyer les données de test après'
        )
        parser.add_argument(
            '--mode',
            choices=['simple', 'batch', 'dry-run', 'all'],
            default='simple',
            help='Mode de test à exécuter'
        )
    
    def handle(self, *args, **options):
        mode = options['mode']
        cleanup = options['cleanup']
        
        self.stdout.write(self.style.SUCCESS('=== Test de migration multi-tenant ==='))
        
        if mode == 'simple' or mode == 'all':
            self.test_simple_migration()
        
        if mode == 'batch' or mode == 'all':
            self.test_batch_migration()
        
        if mode == 'dry-run' or mode == 'all':
            self.test_dry_run()
        
        if cleanup:
            self.cleanup_test_data()
    
    def create_test_club(self, name="Test Migration Club"):
        """Crée un club de test avec des données."""
        self.stdout.write(f"\nCréation du club de test: {name}")
        
        # Créer un admin
        admin, created = User.objects.get_or_create(
            username=f'admin_{name.lower().replace(" ", "_")}',
            defaults={
                'email': f'admin@{name.lower().replace(" ", "_")}.com',
                'is_staff': True
            }
        )
        if created:
            admin.set_password('testpass123')
            admin.save()
        
        # Créer le club
        club = Club.objects.create(
            name=name,
            description="Club de test pour migration",
            address="123 Test Street",
            city="Paris",
            postal_code="75001",
            country="FR",
            email=f"contact@{name.lower().replace(' ', '_')}.com",
            phone="+33123456789",
            owner=admin,
            is_active=True
        )
        
        # Ajouter des pratiquants
        for i in range(1, 6):
            Practitioner.objects.create(
                first_name=f"Test{i}",
                last_name=f"Pratiquant",
                email=f"test{i}@{name.lower().replace(' ', '_')}.com",
                date_of_birth="1990-01-01",
                license_number=f"{name[:3].upper()}{i:04d}",
                club=club,
                gender="M" if i % 2 == 0 else "F"
            )
        
        # Créer une compétition
        Competition.objects.create(
            name=f"{name} Championship 2024",
            date="2024-06-15",
            location="Paris",
            description="Compétition de test",
            owner=club,
            status="planned"
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Club créé: {club.name} (ID: {club.id})\n"
                f"  ✓ Pratiquants: {club.practitioners.count()}\n"
                f"  ✓ Compétitions: {club.competitions.count()}"
            )
        )
        
        return club
    
    def test_simple_migration(self):
        """Test de migration simple d'un club."""
        self.stdout.write(self.style.WARNING('\n--- Test de migration simple ---'))
        
        # Créer un club de test
        club = self.create_test_club("Simple Test Club")
        
        # Effectuer la migration
        self.stdout.write("\nDébut de la migration...")
        migrator = ClubMigrator(dry_run=False)
        
        try:
            migrator.migrate_club(club)
            
            # Vérifier le résultat
            club.refresh_from_db()
            if hasattr(club, 'tenant') and club.tenant:
                tenant = club.tenant
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✓ Migration réussie!\n"
                        f"  - Tenant: {tenant.name}\n"
                        f"  - Schema: {tenant.schema_name}\n"
                        f"  - Domaine: {tenant.domain}\n"
                        f"  - Plan: {tenant.subscription_plan}"
                    )
                )
                
                # Valider la migration
                validator = MigrationValidator(tenant, club)
                validation_result = validator.validate_all()
                
                if validation_result['has_errors']:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ Erreurs de validation: {validation_result['errors']}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS("✓ Validation réussie")
                    )
            else:
                self.stdout.write(
                    self.style.ERROR("✗ Échec: pas de tenant créé")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erreur de migration: {e}")
            )
    
    def test_batch_migration(self):
        """Test de migration de plusieurs clubs."""
        self.stdout.write(self.style.WARNING('\n--- Test de migration en batch ---'))
        
        # Créer plusieurs clubs
        clubs = []
        for i in range(1, 4):
            club = self.create_test_club(f"Batch Club {i}")
            clubs.append(club)
        
        # Migrer tous les clubs
        self.stdout.write("\nMigration de tous les clubs...")
        migrator = ClubMigrator(dry_run=False)
        
        club_ids = [c.id for c in clubs]
        report = migrator.migrate_all_clubs(club_ids=club_ids)
        
        # Afficher le rapport
        self.stdout.write(
            self.style.SUCCESS(
                f"\nRapport de migration:\n"
                f"  - Total: {report['summary']['total_clubs']}\n"
                f"  - Migrés: {report['summary']['migrated']}\n"
                f"  - Échecs: {report['summary']['failed']}\n"
                f"  - Pratiquants: {report['summary']['practitioners_migrated']}\n"
                f"  - Compétitions: {report['summary']['competitions_migrated']}"
            )
        )
        
        # Afficher les détails des clubs migrés
        for club_info in report['migrated_clubs']:
            self.stdout.write(
                f"  ✓ {club_info['club_name']} -> {club_info['domain']}"
            )
    
    def test_dry_run(self):
        """Test en mode dry-run."""
        self.stdout.write(self.style.WARNING('\n--- Test dry-run ---'))
        
        # Créer un club de test
        club = self.create_test_club("Dry Run Club")
        
        # Migration en dry-run
        self.stdout.write("\nMigration en mode dry-run...")
        migrator = ClubMigrator(dry_run=True)
        
        migrator.migrate_club(club)
        
        # Vérifier qu'aucun tenant n'a été créé
        club.refresh_from_db()
        
        if not hasattr(club, 'tenant') or not club.tenant:
            self.stdout.write(
                self.style.SUCCESS("✓ Dry-run réussi: aucun tenant créé")
            )
        else:
            self.stdout.write(
                self.style.ERROR("✗ Erreur: un tenant a été créé en dry-run")
            )
    
    def cleanup_test_data(self):
        """Nettoie les données de test."""
        self.stdout.write(self.style.WARNING('\n--- Nettoyage des données de test ---'))
        
        # Trouver tous les clubs de test
        test_clubs = Club.objects.filter(
            name__icontains="Test",
            name__iregex=r"(Simple|Batch|Dry Run|Migration)"
        )
        
        count = test_clubs.count()
        self.stdout.write(f"Clubs de test trouvés: {count}")
        
        for club in test_clubs:
            if hasattr(club, 'tenant') and club.tenant:
                tenant = club.tenant
                
                # Supprimer le schéma
                try:
                    from django.db import connection
                    with connection.cursor() as cursor:
                        cursor.execute(
                            f'DROP SCHEMA IF EXISTS {tenant.schema_name} CASCADE'
                        )
                    self.stdout.write(f"  - Schéma supprimé: {tenant.schema_name}")
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  - Erreur suppression schéma: {e}")
                    )
                
                # Supprimer le tenant
                tenant.delete()
                self.stdout.write(f"  - Tenant supprimé: {tenant.name}")
            
            # Supprimer le club
            club_name = club.name
            club.delete()
            self.stdout.write(f"  - Club supprimé: {club_name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Nettoyage terminé: {count} clubs supprimés")
        )