"""
Commande Django pour migrer les clubs existants vers l'architecture multi-tenant.
"""
import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.competitions.models import Club
from apps.multitenant.migrations.migrate_existing_clubs import ClubMigrator


class Command(BaseCommand):
    help = 'Migre les clubs existants vers l\'architecture multi-tenant'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--club-ids',
            nargs='+',
            type=int,
            help='IDs spécifiques des clubs Ã  migrer'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler la migration sans modifier les données'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Nombre de clubs Ã  migrer par batch (défaut: 10)'
        )
        parser.add_argument(
            '--start-from',
            type=int,
            default=0,
            help='Index du club Ã  partir duquel commencer'
        )
        parser.add_argument(
            '--report-dir',
            type=str,
            default='migration_reports',
            help='Répertoire pour sauvegarder les rapports'
        )
        parser.add_argument(
            '--interactive',
            action='store_true',
            help='Mode interactif avec confirmation pour chaque club'
        )
        parser.add_argument(
            '--rollback',
            type=int,
            help='Effectuer un rollback pour un club spécifique (ID)'
        )
    
    def handle(self, *args, **options):
        # Gérer le cas du rollback
        if options['rollback']:
            return self.handle_rollback(options['rollback'])
        
        # Configuration
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        start_from = options['start_from']
        report_dir = options['report_dir']
        interactive = options['interactive']
        
        # Créer le répertoire de rapports
        os.makedirs(report_dir, exist_ok=True)
        
        # Initialiser le migrator
        migrator = ClubMigrator(dry_run=dry_run)
        
        # Message de démarrage
        self.stdout.write(
            self.style.WARNING(
                f"{'[MODE DRY RUN] ' if dry_run else ''}"
                f"Début de la migration des clubs..."
            )
        )
        
        # Récupérer les clubs Ã  migrer
        if options['club_ids']:
            clubs = Club.objects.filter(
                id__in=options['club_ids']
            ).order_by('id')
        else:
            clubs = Club.objects.filter(
                is_migrated=False
            ).order_by('id')[start_from:]
        
        total_clubs = clubs.count()
        self.stdout.write(f"Nombre de clubs Ã  migrer : {total_clubs}")
        
        if total_clubs == 0:
            self.stdout.write(self.style.SUCCESS("Aucun club Ã  migrer."))
            return
        
        # Confirmation en mode interactif
        if interactive and not dry_run:
            if not self.confirm_migration(total_clubs):
                self.stdout.write(self.style.ERROR("Migration annulée."))
                return
        
        # Variables de suivi
        start_time = timezone.now()
        processed = 0
        errors = []
        
        try:
            # Migration par batch
            for i in range(0, total_clubs, batch_size):
                batch_clubs = clubs[i:i+batch_size]
                batch_start = timezone.now()
                
                self.stdout.write(
                    f"\nTraitement du batch {i//batch_size + 1} "
                    f"({i+1} Ã  {min(i+batch_size, total_clubs)} sur {total_clubs})"
                )
                
                for club in batch_clubs:
                    try:
                        # Confirmation interactive par club
                        if interactive:
                            if not self.confirm_club_migration(club):
                                self.stdout.write(f"Sauté: {club.name}")
                                continue
                        
                        # Afficher les infos du club
                        self.stdout.write(f"\nMigration de: {club.name}")
                        self.stdout.write(f"  ID: {club.id}")
                        self.stdout.write(f"  Pratiquants: {club.practitioners.count()}")
                        self.stdout.write(f"  Compétitions: {club.competitions.count()}")
                        
                        # Migration
                        migrator.migrate_club(club)
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"âœ“ {club.name} migré avec succès")
                        )
                        processed += 1
                        
                    except Exception as e:
                        error_msg = f"Ã‰chec pour {club.name} (ID: {club.id}): {str(e)}"
                        self.stdout.write(self.style.ERROR(f"âœ— {error_msg}"))
                        errors.append(error_msg)
                        
                        if not self.should_continue_after_error():
                            raise CommandError("Migration interrompue après erreur")
                
                # Statistiques du batch
                batch_duration = timezone.now() - batch_start
                self.stdout.write(
                    f"Batch terminé en {batch_duration.total_seconds():.2f}s"
                )
            
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nMigration interrompue par l'utilisateur"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nErreur fatale: {e}"))
            raise
        finally:
            # Générer et sauvegarder le rapport
            end_time = timezone.now()
            duration = end_time - start_time
            
            report = self.generate_final_report(
                migrator,
                start_time,
                end_time,
                duration,
                processed,
                errors
            )
            
            report_file = self.save_report(report, report_dir)
            self.stdout.write(
                self.style.SUCCESS(f"\nRapport sauvegardé: {report_file}")
            )
            
            # Afficher le résumé
            self.display_summary(report)
    
    def handle_rollback(self, club_id: int):
        """Effectue un rollback pour un club spécifique."""
        try:
            club = Club.objects.get(id=club_id)
            
            if not club.is_migrated or not hasattr(club, 'tenant'):
                self.stdout.write(
                    self.style.WARNING(f"Le club {club.name} n'est pas migré")
                )
                return
            
            self.stdout.write(f"Rollback du club: {club.name}")
            
            # Import de la classe de rollback
            from apps.multitenant.migrations.migrate_existing_clubs import MigrationRollback
            rollback = MigrationRollback(club.tenant)
            
            success, message = rollback.rollback()
            
            if success:
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(self.style.ERROR(message))
                
        except Club.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Club {club_id} non trouvé"))
    
    def confirm_migration(self, total_clubs: int) -> bool:
        """Demande confirmation avant de démarrer la migration."""
        self.stdout.write(
            self.style.WARNING(
                f"\nVous Ãªtes sur le point de migrer {total_clubs} clubs."
            )
        )
        response = input("Continuer ? (oui/non) : ").lower()
        return response in ['oui', 'yes', 'o', 'y']
    
    def confirm_club_migration(self, club: Club) -> bool:
        """Demande confirmation pour migrer un club spécifique."""
        self.stdout.write(f"\nMigrer {club.name} ? ")
        self.stdout.write(f"  Pratiquants: {club.practitioners.count()}")
        self.stdout.write(f"  Compétitions: {club.competitions.count()}")
        response = input("(oui/non/tous) : ").lower()
        
        if response == 'tous':
            self.interactive = False  # Désactiver pour les clubs suivants
            return True
        
        return response in ['oui', 'yes', 'o', 'y']
    
    def should_continue_after_error(self) -> bool:
        """Demande si la migration doit continuer après une erreur."""
        response = input("\nUne erreur s'est produite. Continuer ? (oui/non) : ").lower()
        return response in ['oui', 'yes', 'o', 'y']
    
    def generate_final_report(self, migrator, start_time, end_time, 
                            duration, processed, errors) -> dict:
        """Génère le rapport final de migration."""
        report = migrator.generate_report()
        
        report.update({
            'execution': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration': str(duration),
                'duration_seconds': duration.total_seconds(),
            },
            'summary': {
                'total_processed': processed,
                'successful': len(migrator.migrated_clubs),
                'failed': len(migrator.failed_clubs),
                'error_messages': errors,
            },
            'performance': {
                'avg_time_per_club': (
                    duration.total_seconds() / processed if processed > 0 else 0
                ),
            }
        })
        
        return report
    
    def save_report(self, report: dict, report_dir: str) -> str:
        """Sauvegarde le rapport dans un fichier JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'migration_report_{timestamp}.json'
        filepath = os.path.join(report_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def display_summary(self, report: dict):
        """Affiche un résumé du rapport de migration."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RÃ‰SUMÃ‰ DE LA MIGRATION")
        self.stdout.write("="*50)
        
        summary = report['summary']
        stats = report.get('migration_stats', {})
        
        self.stdout.write(f"Clubs traités: {summary['total_processed']}")
        self.stdout.write(
            self.style.SUCCESS(f"Réussis: {summary['successful']}")
        )
        self.stdout.write(
            self.style.ERROR(f"Ã‰choués: {summary['failed']}")
        )
        
        if stats:
            self.stdout.write(f"\nStatistiques détaillées:")
            self.stdout.write(f"  Pratiquants migrés: {stats.get('practitioners_migrated', 0)}")
            self.stdout.write(f"  Compétitions migrées: {stats.get('competitions_migrated', 0)}")
            self.stdout.write(f"  Inscriptions migrées: {stats.get('registrations_migrated', 0)}")
        
        self.stdout.write(f"\nDurée totale: {report['execution']['duration']}")
        self.stdout.write(
            f"Temps moyen par club: "
            f"{report['performance']['avg_time_per_club']:.2f}s"
        )
        
        if summary['failed'] > 0:
            self.stdout.write("\nClubs échoués:")
            for failed in report.get('failed_clubs', [])[:5]:  # Afficher max 5
                self.stdout.write(
                    self.style.ERROR(f"  - {failed['club_name']}: {failed['error']}")
                )
            
            if len(report.get('failed_clubs', [])) > 5:
                self.stdout.write(
                    f"  ... et {len(report['failed_clubs']) - 5} autres "
                    f"(voir le rapport complet)"
                )
        
        self.stdout.write("="*50)

