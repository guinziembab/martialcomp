"""
Script de migration progressive avec monitoring en temps réel.
"""
import time
import threading
import queue
from dataclasses import dataclass
from typing import List, Optional
from django.db import connection, transaction
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from multitenant.models import Tenant
from competitions.models import Club
from .migrate_existing_clubs import ClubMigrator


@dataclass
class MigrationTask:
    """Représente une tâche de migration."""
    club: Club
    priority: int = 0
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        # Calculer la priorité basée sur la taille du club
        self.priority = self.club.practitioners.count()


class MigrationMonitor:
    """Moniteur en temps réel de la migration."""
    
    def __init__(self):
        self.start_time = None
        self.clubs_migrated = 0
        self.clubs_failed = 0
        self.current_club = None
        self.total_clubs = 0
        self.errors = []
    
    def start(self, total_clubs: int):
        """Démarre le monitoring."""
        self.start_time = timezone.now()
        self.total_clubs = total_clubs
    
    def update_current(self, club_name: str):
        """Met à jour le club en cours de migration."""
        self.current_club = club_name
    
    def record_success(self):
        """Enregistre un succès."""
        self.clubs_migrated += 1
    
    def record_failure(self, error: str):
        """Enregistre un échec."""
        self.clubs_failed += 1
        self.errors.append(error)
    
    def get_stats(self) -> dict:
        """Retourne les statistiques actuelles."""
        elapsed = (timezone.now() - self.start_time).total_seconds() if self.start_time else 0
        progress = (self.clubs_migrated + self.clubs_failed) / self.total_clubs * 100 if self.total_clubs > 0 else 0
        
        return {
            'elapsed_time': elapsed,
            'progress': progress,
            'clubs_migrated': self.clubs_migrated,
            'clubs_failed': self.clubs_failed,
            'current_club': self.current_club,
            'remaining': self.total_clubs - self.clubs_migrated - self.clubs_failed,
            'avg_time_per_club': elapsed / (self.clubs_migrated + self.clubs_failed) if (self.clubs_migrated + self.clubs_failed) > 0 else 0,
            'estimated_remaining': self._estimate_remaining_time(),
            'errors': self.errors[-5:],  # Dernières 5 erreurs
        }
    
    def _estimate_remaining_time(self) -> float:
        """Estime le temps restant."""
        if self.clubs_migrated == 0:
            return 0
        
        elapsed = (timezone.now() - self.start_time).total_seconds()
        avg_time = elapsed / (self.clubs_migrated + self.clubs_failed)
        remaining_clubs = self.total_clubs - self.clubs_migrated - self.clubs_failed
        
        return avg_time * remaining_clubs


class ProgressiveMigrator:
    """Gestionnaire de migration progressive avec parallélisation."""
    
    def __init__(self, max_workers: int = 5, batch_size: int = 10):
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.task_queue = queue.PriorityQueue()
        self.monitor = MigrationMonitor()
        self.migrator = ClubMigrator()
        self.stop_event = threading.Event()
    
    def prepare_migration(self, club_ids: Optional[List[int]] = None):
        """Prépare la migration en créant les tâches."""
        if club_ids:
            clubs = Club.objects.filter(id__in=club_ids)
        else:
            clubs = Club.objects.filter(is_migrated=False)
        
        clubs = clubs.select_related('owner').prefetch_related(
            'federations', 'practitioners'
        )
        
        # Créer les tâches avec priorité
        tasks = []
        for club in clubs:
            task = MigrationTask(club=club)
            tasks.append(task)
        
        # Trier par priorité (clubs plus grands en premier)
        tasks.sort(key=lambda t: t.priority, reverse=True)
        
        # Ajouter à la queue
        for task in tasks:
            self.task_queue.put((-task.priority, task))  # Priorité négative pour max-heap
        
        return len(tasks)
    
    def migrate_progressive(self):
        """Lance la migration progressive."""
        total_tasks = self.task_queue.qsize()
        self.monitor.start(total_tasks)
        
        # Démarrer le thread de monitoring
        monitor_thread = threading.Thread(target=self._monitor_progress)
        monitor_thread.start()
        
        # Pool de workers pour migration parallèle
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            # Traiter les tâches par batch
            while not self.task_queue.empty() and not self.stop_event.is_set():
                batch_futures = []
                
                # Créer un batch de tâches
                for _ in range(min(self.batch_size, self.task_queue.qsize())):
                    if self.task_queue.empty():
                        break
                    
                    _, task = self.task_queue.get()
                    future = executor.submit(self._migrate_club_safe, task)
                    batch_futures.append((future, task))
                
                # Attendre que le batch se termine
                for future, task in batch_futures:
                    try:
                        future.result(timeout=300)  # Timeout de 5 minutes par club
                    except Exception as e:
                        self._handle_migration_error(task, e)
            
            # Attendre que tous les workers se terminent
            executor.shutdown(wait=True)
        
        # Arrêter le monitoring
        self.stop_event.set()
        monitor_thread.join()
        
        return self.monitor.get_stats()
    
    def _migrate_club_safe(self, task: MigrationTask):
        """Migre un club avec gestion d'erreurs et retry."""
        club = task.club
        self.monitor.update_current(club.name)
        
        try:
            # Tenter la migration
            with transaction.atomic():
                self.migrator.migrate_club(club)
            
            self.monitor.record_success()
            return True
            
        except Exception as e:
            error_msg = f"Échec migration {club.name}: {str(e)}"
            
            if task.retry_count < task.max_retries:
                # Réessayer après un délai
                task.retry_count += 1
                time.sleep(2 ** task.retry_count)  # Backoff exponentiel
                self.task_queue.put((-task.priority, task))
                return False
            else:
                # Échec définitif
                self.monitor.record_failure(error_msg)
                raise
    
    def _handle_migration_error(self, task: MigrationTask, error: Exception):
        """Gère les erreurs de migration."""
        error_msg = f"Échec définitif pour {task.club.name}: {str(error)}"
        self.monitor.record_failure(error_msg)
        
        # Logger l'erreur
        import logging
        logger = logging.getLogger('multitenant.migration')
        logger.error(error_msg, exc_info=True)
        
        # Optionnel: envoyer une notification
        self._send_error_notification(task.club, error)
    
    def _monitor_progress(self):
        """Thread de monitoring en temps réel."""
        while not self.stop_event.is_set():
            stats = self.monitor.get_stats()
            self._display_progress(stats)
            
            # Vérifier si on doit arrêter (trop d'erreurs)
            if self.monitor.clubs_failed > 10:
                print("\n⚠️  Trop d'erreurs, arrêt de la migration")
                self.stop_event.set()
            
            time.sleep(1)  # Mise à jour toutes les secondes
    
    def _display_progress(self, stats: dict):
        """Affiche la progression en temps réel."""
        print(f"\r[{stats['progress']:.1f}%] "
              f"Migré: {stats['clubs_migrated']} | "
              f"Échoué: {stats['clubs_failed']} | "
              f"En cours: {stats['current_club'] or 'Aucun'} | "
              f"Temps restant: {stats['estimated_remaining']:.0f}s", 
              end='', flush=True)
    
    def _send_error_notification(self, club: Club, error: Exception):
        """Envoie une notification d'erreur."""
        # Implémenter selon vos besoins (email, Slack, etc.)
        pass


class MigrationOrchestrator:
    """Orchestrateur principal de la migration."""
    
    def __init__(self):
        self.migrator = ProgressiveMigrator()
    
    def run_migration(self, dry_run: bool = False, club_ids: Optional[List[int]] = None):
        """Lance le processus de migration complet."""
        print("🚀 Démarrage de la migration progressive...")
        
        # Phase 1: Préparation
        print("\n📋 Phase 1: Préparation")
        total_clubs = self.migrator.prepare_migration(club_ids)
        print(f"✓ {total_clubs} clubs à migrer")
        
        if dry_run:
            print("\n[MODE DRY RUN] Simulation uniquement")
            return
        
        # Phase 2: Backup
        print("\n💾 Phase 2: Backup")
        backup_file = self._create_backup()
        print(f"✓ Backup créé: {backup_file}")
        
        # Phase 3: Migration
        print("\n⚙️  Phase 3: Migration")
        try:
            stats = self.migrator.migrate_progressive()
            
            # Phase 4: Validation
            print("\n✅ Phase 4: Validation")
            self._validate_migration(stats)
            
            # Phase 5: Finalisation
            print("\n🎉 Phase 5: Finalisation")
            self._finalize_migration(stats)
            
        except Exception as e:
            print(f"\n❌ Erreur fatale: {e}")
            print(f"Restauration depuis: {backup_file}")
            self._restore_backup(backup_file)
            raise
    
    def _create_backup(self) -> str:
        """Crée un backup de la base de données."""
        import subprocess
        from django.conf import settings
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_pre_migration_{timestamp}.sql'
        
        db_config = settings.DATABASES['default']
        
        command = [
            'pg_dump',
            '-h', db_config['HOST'],
            '-U', db_config['USER'],
            '-d', db_config['NAME'],
            '-f', backup_file,
            '--verbose'
        ]
        
        subprocess.run(command, check=True)
        return backup_file
    
    def _validate_migration(self, stats: dict):
        """Valide la migration globale."""
        success_rate = stats['clubs_migrated'] / (stats['clubs_migrated'] + stats['clubs_failed']) * 100
        
        print(f"Taux de réussite: {success_rate:.1f}%")
        
        if success_rate < 95:
            raise Exception(f"Taux de réussite trop faible: {success_rate:.1f}%")
    
    def _finalize_migration(self, stats: dict):
        """Finalise la migration."""
        print(f"Migration terminée!")
        print(f"  - Clubs migrés: {stats['clubs_migrated']}")
        print(f"  - Clubs échoués: {stats['clubs_failed']}")
        print(f"  - Durée totale: {stats['elapsed_time']:.0f}s")
    
    def _restore_backup(self, backup_file: str):
        """Restaure la base de données depuis un backup."""
        # Implémenter la restauration
        pass


# Point d'entrée pour les scripts
if __name__ == '__main__':
    orchestrator = MigrationOrchestrator()
    orchestrator.run_migration(dry_run=False)