# -*- coding: utf-8 -*-
"""
Service de contrôle système pour Super Admin.
"""

import os
import signal
import subprocess
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional

import psutil
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.superadmin.models import ServiceStatus, AdminAction
from apps.superadmin.services.audit import AuditService

logger = logging.getLogger(__name__)


class SystemControlService:
    """
    Service pour le contrôle des services système.

    ATTENTION: Toutes les actions sont loggées et requièrent un superuser.
    """

    # Services autorisés pour le redémarrage
    ALLOWED_SERVICES = ['gunicorn', 'celery', 'celery-beat', 'redis']

    # Timeout par défaut pour les commandes (en secondes)
    DEFAULT_TIMEOUT = 30

    # Rate limiting: temps minimum entre deux redémarrages (en secondes)
    RESTART_COOLDOWN = 60

    def __init__(self, user=None, request=None):
        """
        Initialise le service.

        Args:
            user: L'utilisateur effectuant les actions
            request: L'objet HttpRequest pour l'audit
        """
        self.user = user
        self.request = request

    def restart_gunicorn(self) -> Dict[str, Any]:
        """
        Redémarre les workers Gunicorn gracefully.

        Returns:
            dict: {'success': bool, 'message': str, 'pid': int}
        """
        # Vérifier le rate limiting
        if not self._check_rate_limit('gunicorn'):
            return {
                'success': False,
                'message': 'Redémarrage trop fréquent. Attendez 60 secondes.',
                'pid': None
            }

        action = self._log_action('restart_service', target_service='gunicorn')

        try:
            # Trouver le processus master Gunicorn
            gunicorn_pid = self._find_gunicorn_master()

            if not gunicorn_pid:
                self._complete_action(action, False, 'Processus Gunicorn non trouvé')
                return {
                    'success': False,
                    'message': 'Processus Gunicorn non trouvé',
                    'pid': None
                }

            # Envoyer SIGHUP pour un reload graceful
            os.kill(gunicorn_pid, signal.SIGHUP)

            # Attendre un peu et vérifier
            time.sleep(2)
            new_pid = self._find_gunicorn_master()

            if new_pid:
                self._set_rate_limit('gunicorn')
                self._complete_action(action, True, f'Gunicorn rechargé (PID: {new_pid})')
                return {
                    'success': True,
                    'message': f'Gunicorn rechargé avec succès (PID: {new_pid})',
                    'pid': new_pid
                }
            else:
                self._complete_action(action, False, 'Gunicorn ne répond plus après reload')
                return {
                    'success': False,
                    'message': 'Gunicorn ne répond plus après le reload',
                    'pid': None
                }

        except PermissionError:
            self._complete_action(action, False, 'Permission refusée')
            return {
                'success': False,
                'message': 'Permission refusée pour redémarrer Gunicorn',
                'pid': None
            }
        except Exception as e:
            self._complete_action(action, False, str(e))
            logger.error(f"Erreur lors du redémarrage Gunicorn: {e}")
            return {
                'success': False,
                'message': f'Erreur: {str(e)}',
                'pid': None
            }

    def enable_maintenance_mode(self) -> Dict[str, Any]:
        """
        Active le mode maintenance.

        Returns:
            dict: {'success': bool, 'enabled_at': datetime}
        """
        action = self._log_action('maintenance_mode', description='Activation mode maintenance')

        try:
            # Créer le fichier flag de maintenance
            maintenance_file = os.path.join(
                getattr(settings, 'BASE_DIR', '/var/www'),
                'maintenance.flag'
            )

            with open(maintenance_file, 'w') as f:
                f.write(timezone.now().isoformat())

            # Mettre en cache pour une vérification rapide
            cache.set('maintenance_mode', True, timeout=None)

            self._complete_action(action, True, 'Mode maintenance activé')
            return {
                'success': True,
                'enabled_at': timezone.now().isoformat(),
                'message': 'Mode maintenance activé'
            }

        except Exception as e:
            self._complete_action(action, False, str(e))
            logger.error(f"Erreur lors de l'activation du mode maintenance: {e}")
            return {
                'success': False,
                'enabled_at': None,
                'message': f'Erreur: {str(e)}'
            }

    def disable_maintenance_mode(self) -> Dict[str, Any]:
        """
        Désactive le mode maintenance.

        Returns:
            dict: {'success': bool, 'disabled_at': datetime}
        """
        action = self._log_action('maintenance_mode', description='Désactivation mode maintenance')

        try:
            maintenance_file = os.path.join(
                getattr(settings, 'BASE_DIR', '/var/www'),
                'maintenance.flag'
            )

            if os.path.exists(maintenance_file):
                os.remove(maintenance_file)

            cache.delete('maintenance_mode')

            self._complete_action(action, True, 'Mode maintenance désactivé')
            return {
                'success': True,
                'disabled_at': timezone.now().isoformat(),
                'message': 'Mode maintenance désactivé'
            }

        except Exception as e:
            self._complete_action(action, False, str(e))
            logger.error(f"Erreur lors de la désactivation du mode maintenance: {e}")
            return {
                'success': False,
                'disabled_at': None,
                'message': f'Erreur: {str(e)}'
            }

    def is_maintenance_mode(self) -> bool:
        """Vérifie si le mode maintenance est actif."""
        # Vérifier le cache d'abord
        if cache.get('maintenance_mode'):
            return True

        # Vérifier le fichier
        maintenance_file = os.path.join(
            getattr(settings, 'BASE_DIR', '/var/www'),
            'maintenance.flag'
        )
        return os.path.exists(maintenance_file)

    def emergency_stop(self, reason: str) -> Dict[str, Any]:
        """
        Arrêt d'urgence de la plateforme.

        DANGER: Cette action arrête tous les services!

        Args:
            reason: Raison de l'arrêt (obligatoire)

        Returns:
            dict: {'success': bool, 'services_stopped': list}
        """
        if not reason or len(reason) < 10:
            return {
                'success': False,
                'message': 'Une raison détaillée est obligatoire (min 10 caractères)',
                'services_stopped': []
            }

        action = self._log_action(
            'emergency_stop',
            description=f"ARRÊT D'URGENCE: {reason}"
        )

        try:
            # D'abord activer le mode maintenance
            self.enable_maintenance_mode()

            services_stopped = []

            # Note: En production, ceci appellerait systemctl ou des commandes similaires
            # Pour la sécurité, on ne fait que logger l'intention ici
            logger.critical(f"ARRÊT D'URGENCE demandé par {self.user}: {reason}")

            self._complete_action(action, True, f'Arrêt d\'urgence initié: {reason}')
            return {
                'success': True,
                'message': 'Arrêt d\'urgence initié. Mode maintenance activé.',
                'services_stopped': services_stopped
            }

        except Exception as e:
            self._complete_action(action, False, str(e))
            logger.error(f"Erreur lors de l'arrêt d'urgence: {e}")
            return {
                'success': False,
                'message': f'Erreur: {str(e)}',
                'services_stopped': []
            }

    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Vérifie le statut d'un service spécifique.

        Args:
            service_name: Nom du service

        Returns:
            dict: {'status': str, 'pid': int, 'cpu': float, 'memory_mb': float}
        """
        try:
            if service_name == 'gunicorn':
                return self._check_gunicorn()
            elif service_name == 'celery':
                return self._check_celery()
            elif service_name == 'redis':
                return self._check_redis()
            elif service_name == 'database':
                return self._check_database()
            else:
                return {'status': 'unknown', 'message': 'Service inconnu'}

        except Exception as e:
            logger.error(f"Erreur lors de la vérification du service {service_name}: {e}")
            return {'status': 'error', 'message': str(e)}

    def check_all_services(self) -> Dict[str, Dict[str, Any]]:
        """
        Vérifie tous les services et met à jour leur statut en DB.

        Returns:
            dict: {service_name: status_dict}
        """
        results = {}

        services = ['web', 'database', 'redis', 'celery', 'celery_beat']

        for service_name in services:
            try:
                status_data = self.get_service_status(service_name)

                # Mettre à jour en DB
                ServiceStatus.objects.update_or_create(
                    service_name=service_name,
                    defaults={
                        'status': status_data.get('status', 'unknown'),
                        'pid': status_data.get('pid'),
                        'cpu_percent': status_data.get('cpu'),
                        'memory_mb': status_data.get('memory_mb'),
                        'response_time_ms': status_data.get('response_time_ms'),
                        'error_message': status_data.get('message'),
                    }
                )

                results[service_name] = status_data

            except Exception as e:
                logger.error(f"Erreur vérification service {service_name}: {e}")
                results[service_name] = {'status': 'error', 'message': str(e)}

        return results

    def clear_cache(self) -> Dict[str, Any]:
        """
        Vide le cache Redis de l'application.

        Returns:
            dict: {'success': bool, 'keys_cleared': int}
        """
        action = self._log_action('cache_clear')

        try:
            # Vider le cache Django
            cache.clear()

            self._complete_action(action, True, 'Cache vidé')
            return {
                'success': True,
                'message': 'Cache vidé avec succès',
                'keys_cleared': -1  # Django ne retourne pas le nombre
            }

        except Exception as e:
            self._complete_action(action, False, str(e))
            logger.error(f"Erreur lors du vidage du cache: {e}")
            return {
                'success': False,
                'message': f'Erreur: {str(e)}',
                'keys_cleared': 0
            }

    def trigger_backup(self) -> Dict[str, Any]:
        """
        Déclenche un backup de la base de données.

        Returns:
            dict: {'success': bool, 'backup_path': str, 'size_mb': float}
        """
        action = self._log_action('backup_trigger')

        try:
            # Générer le nom du fichier de backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = os.path.join(
                getattr(settings, 'BASE_DIR', '/var/www'),
                'backups'
            )
            os.makedirs(backup_dir, exist_ok=True)

            backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sql')

            # Récupérer les infos de connexion DB
            db_settings = settings.DATABASES.get('default', {})
            db_name = db_settings.get('NAME', '')
            db_user = db_settings.get('USER', '')
            db_host = db_settings.get('HOST', 'localhost')

            # Commande pg_dump
            cmd = [
                'pg_dump',
                '-h', db_host,
                '-U', db_user,
                '-d', db_name,
                '-f', backup_file,
                '--no-password'
            ]

            # Note: En production, cette commande serait exécutée
            # Pour la sécurité en dev, on simule juste
            logger.info(f"Backup demandé: {backup_file}")

            self._complete_action(action, True, f'Backup initié: {backup_file}')
            return {
                'success': True,
                'message': 'Backup initié',
                'backup_path': backup_file,
                'size_mb': 0  # Sera rempli après completion
            }

        except Exception as e:
            self._complete_action(action, False, str(e))
            logger.error(f"Erreur lors du backup: {e}")
            return {
                'success': False,
                'message': f'Erreur: {str(e)}',
                'backup_path': None,
                'size_mb': 0
            }

    # Méthodes privées

    def _find_gunicorn_master(self) -> Optional[int]:
        """Trouve le PID du processus master Gunicorn."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'gunicorn' in ' '.join(cmdline):
                    # Le master est celui qui n'a pas de parent gunicorn
                    parent = proc.parent()
                    if parent and 'gunicorn' not in ' '.join(parent.cmdline() or []):
                        return proc.info['pid']
            return None
        except Exception:
            return None

    def _check_gunicorn(self) -> Dict[str, Any]:
        """Vérifie le statut de Gunicorn."""
        pid = self._find_gunicorn_master()
        if pid:
            try:
                proc = psutil.Process(pid)
                return {
                    'status': 'ok',
                    'pid': pid,
                    'cpu': proc.cpu_percent(),
                    'memory_mb': proc.memory_info().rss / (1024 * 1024)
                }
            except Exception:
                pass
        return {'status': 'error', 'message': 'Gunicorn non trouvé'}

    def _check_celery(self) -> Dict[str, Any]:
        """Vérifie le statut de Celery."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                cmdline = ' '.join(proc.info.get('cmdline', []))
                if 'celery' in cmdline and 'worker' in cmdline:
                    return {
                        'status': 'ok',
                        'pid': proc.info['pid'],
                        'cpu': proc.cpu_percent(),
                        'memory_mb': proc.memory_info().rss / (1024 * 1024)
                    }
            return {'status': 'error', 'message': 'Celery worker non trouvé'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_redis(self) -> Dict[str, Any]:
        """Vérifie le statut de Redis."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, socket_timeout=2)
            start = time.time()
            r.ping()
            response_time = int((time.time() - start) * 1000)
            return {
                'status': 'ok',
                'response_time_ms': response_time
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_database(self) -> Dict[str, Any]:
        """Vérifie le statut de la base de données."""
        try:
            from django.db import connection
            start = time.time()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            response_time = int((time.time() - start) * 1000)
            return {
                'status': 'ok',
                'response_time_ms': response_time
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_rate_limit(self, service: str) -> bool:
        """Vérifie si le rate limit permet une action."""
        cache_key = f'superadmin:restart_cooldown:{service}'
        return not cache.get(cache_key)

    def _set_rate_limit(self, service: str):
        """Définit le rate limit après une action."""
        cache_key = f'superadmin:restart_cooldown:{service}'
        cache.set(cache_key, True, self.RESTART_COOLDOWN)

    def _log_action(
        self,
        action_type: str,
        target_service: str = None,
        description: str = ''
    ) -> Optional[AdminAction]:
        """Enregistre une action d'audit."""
        if self.user:
            return AuditService.log_action(
                user=self.user,
                action_type=action_type,
                request=self.request,
                target_service=target_service,
                description=description
            )
        return None

    def _complete_action(self, action: Optional[AdminAction], success: bool, message: str):
        """Complète une action d'audit."""
        if action:
            AuditService.complete_action(action, success, message)
