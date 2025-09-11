"""
Commande pour afficher le statut de la migration multi-tenant
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.competitions.models import Club, Practitioner, Competition
from apps.multitenant.models import Tenant, Domain
from tabulate import tabulate


class Command(BaseCommand):
    help = 'Affiche le statut actuel de la migration multi-tenant'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== STATUT MIGRATION MULTI-TENANT ===\n'))
        
        # 1. Statistiques générales
        self.display_general_stats()
        
        # 2. Clubs Ã  migrer
        self.display_pending_clubs()
        
        # 3. Tenants existants
        self.display_existing_tenants()
        
        # 4. Recommandations
        self.display_recommendations()
    
    def display_general_stats(self):
        """Affiche les statistiques générales."""
        self.stdout.write(self.style.WARNING('1. Statistiques générales'))
        
        # Stats clubs
        total_clubs = Club.objects.count()
        
        # Vérifier si le champ is_migrated existe
        migrated_clubs = 0
        try:
            migrated_clubs = Club.objects.filter(is_migrated=True).count()
        except Exception as e:
            self.stdout.write(self.style.WARNING('  âš ï¸  Le champ is_migrated n\'existe pas encore'))
        
        pending_clubs = total_clubs - migrated_clubs
        
        # Stats autres
        total_practitioners = Practitioner.objects.count()
        total_competitions = Competition.objects.count()
        
        # Vérifier si la table tenant existe
        total_tenants = 0
        try:
            total_tenants = Tenant.objects.count()
        except Exception as e:
            self.stdout.write(self.style.WARNING('  âš ï¸  Les tables multitenant n\'existent pas encore'))
        
        stats = [
            ['Total de clubs', total_clubs],
            ['Clubs migrés', migrated_clubs],
            ['Clubs Ã  migrer', pending_clubs],
            ['Total pratiquants', total_practitioners],
            ['Total compétitions', total_competitions],
            ['Tenants créés', total_tenants],
        ]
        
        self.stdout.write(tabulate(stats, headers=['Métrique', 'Valeur'], tablefmt='grid'))
        self.stdout.write('')
    
    def display_pending_clubs(self):
        """Affiche les clubs en attente de migration."""
        self.stdout.write(self.style.WARNING('2. Clubs Ã  migrer (10 premiers)'))
        
        try:
            pending_clubs = Club.objects.filter(is_migrated=False)[:10]
        except:
            pending_clubs = Club.objects.all()[:10]
        
        if not pending_clubs:
            self.stdout.write(self.style.SUCCESS('  Tous les clubs ont été migrés !'))
            return
        
        club_data = []
        for club in pending_clubs:
            club_data.append([
                club.id,
                club.name[:30],
                getattr(club, 'city', 'N/A'),
                getattr(club, 'country', 'N/A'),
                self.get_club_practitioners_count(club),
                self.get_club_competitions_count(club)
            ])
        
        headers = ['ID', 'Nom', 'Ville', 'Pays', 'Pratiquants', 'Compétitions']
        self.stdout.write(tabulate(club_data, headers=headers, tablefmt='grid'))
        
        total_pending = Club.objects.all().count()
        try:
            total_pending = Club.objects.filter(is_migrated=False).count()
        except:
            pass
        
        if total_pending > 10:
            self.stdout.write(f'\n  ... et {total_pending - 10} autres clubs')
        self.stdout.write('')
    
    def display_existing_tenants(self):
        """Affiche les tenants existants."""
        self.stdout.write(self.style.WARNING('3. Tenants existants'))
        
        try:
            tenants = Tenant.objects.all()[:10]
        except Exception as e:
            self.stdout.write(self.style.ERROR('  âŒ Les tables multitenant n\'existent pas'))
            self.stdout.write('     Exécutez: python manage.py migrate multitenant')
            return
        
        if not tenants:
            self.stdout.write('  Aucun tenant créé pour le moment')
            return
        
        tenant_data = []
        for tenant in tenants:
            # Compter les domaines
            domain_count = Domain.objects.filter(tenant=tenant).count()
            
            tenant_data.append([
                tenant.id,
                tenant.name[:30],
                tenant.schema_name,
                tenant.subscription_plan,
                domain_count,
                'âœ“' if tenant.is_active else 'âœ—'
            ])
        
        headers = ['ID', 'Nom', 'Schema', 'Plan', 'Domaines', 'Actif']
        self.stdout.write(tabulate(tenant_data, headers=headers, tablefmt='grid'))
        
        total_tenants = Tenant.objects.count()
        if total_tenants > 10:
            self.stdout.write(f'\n  ... et {total_tenants - 10} autres tenants')
        self.stdout.write('')
    
    def get_club_practitioners_count(self, club):
        """Obtient le nombre de pratiquants d'un club."""
        # Si le club a une organization liée
        if hasattr(club, 'organization') and club.organization:
            return Practitioner.objects.filter(organization=club.organization).count()
        
        # Sinon, essayer via le champ club (peut-Ãªtre legacy)
        try:
            return Practitioner.objects.filter(club=club).count()
        except:
            return 0
    
    def get_club_competitions_count(self, club):
        """Obtient le nombre de compétitions d'un club."""
        try:
            # Essayer différentes approches
            from apps.competitions.models import Competition
            
            # Si le club est propriétaire de compétitions
            count = Competition.objects.filter(owner=club).count()
            
            # Si le club a une organization
            if hasattr(club, 'organization') and club.organization:
                count += Competition.objects.filter(owner_organization=club.organization).count()
            
            return count
        except:
            return 0
    
    def display_recommendations(self):
        """Affiche les recommandations."""
        self.stdout.write(self.style.WARNING('4. Recommandations'))
        
        try:
            pending_count = Club.objects.filter(is_migrated=False).count()
        except:
            pending_count = Club.objects.count()
        
        if pending_count == 0:
            self.stdout.write(self.style.SUCCESS('  âœ“ Migration complète !'))
            return
        
        self.stdout.write('\n  Prochaines étapes:')
        
        if pending_count > 0:
            self.stdout.write(f'  1. {pending_count} clubs restent Ã  migrer')
            self.stdout.write('  2. Exécutez: python manage.py test_migration --mode=simple')
            self.stdout.write('  3. Pour migrer: python manage.py migrate_clubs_to_tenants')
        
        # Vérifier si les migrations sont appliquées
        self.stdout.write('\n  âš ï¸  Assurez-vous que toutes les migrations sont appliquées:')
        self.stdout.write('     python manage.py migrate')
        
        self.stdout.write('\n  Documentation:')
        self.stdout.write('  - Guide de migration: docs/migration_guide_orgs.md')
        self.stdout.write('  - Tests: run_migration_test.md')
        
        self.stdout.write('')

