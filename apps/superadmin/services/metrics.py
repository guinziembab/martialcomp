# -*- coding: utf-8 -*-
"""
Service de collecte et d'agrégation des métriques pour Super Admin.
"""

import logging
import os
import psutil
from decimal import Decimal
from datetime import timedelta
from typing import Dict, List, Optional, Any

from django.conf import settings
from django.db import connection
from django.db.models import Count, Sum, Avg, F, Q
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from django.core.cache import cache

from apps.superadmin.models import (
    MembershipProfile,
    EventPass,
    MembershipTransformation,
    SystemMetric,
    ServiceStatus,
)

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Service principal pour la collecte et l'agrégation des métriques.
    Fournit les données pour le dashboard Super Admin.
    """

    CACHE_TTL_SHORT = 30  # 30 secondes pour les KPIs
    CACHE_TTL_MEDIUM = 300  # 5 minutes pour les stats lourdes
    CACHE_TTL_LONG = 3600  # 1 heure pour les données historiques

    def get_platform_status(self) -> Dict[str, Any]:
        """
        Retourne le statut global de la plateforme.

        Returns:
            dict: {
                'status': 'operational' | 'degraded' | 'down',
                'uptime': str,
                'timestamp': datetime,
                'services_ok': int,
                'services_total': int
            }
        """
        cache_key = 'superadmin:platform_status'
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Vérifier les services essentiels en temps réel
            self._update_essential_services_status()

            services = ServiceStatus.objects.all()

            # En mode développement, ne considérer que les services essentiels
            is_debug = getattr(settings, 'DEBUG', False)
            if is_debug:
                essential_services = ['web', 'database']
                services = services.filter(service_name__in=essential_services)

            services_ok = services.filter(status='ok').count()
            services_total = services.count()

            # Déterminer le statut global
            if services_total == 0:
                status = 'unknown'
            elif services_ok == services_total:
                status = 'operational'
            elif services_ok >= services_total / 2:
                status = 'degraded'
            else:
                status = 'down'

            # Calculer l'uptime (depuis le dernier redémarrage)
            uptime = self._get_uptime()

            result = {
                'status': status,
                'status_display': self._get_status_display(status),
                'uptime': uptime,
                'uptime_display': self._format_uptime(uptime),
                'timestamp': timezone.now().isoformat(),
                'services_ok': services_ok,
                'services_total': services_total,
            }

            cache.set(cache_key, result, self.CACHE_TTL_SHORT)
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut plateforme: {e}")
            return {
                'status': 'unknown',
                'status_display': 'Inconnu',
                'uptime': 0,
                'uptime_display': 'N/A',
                'timestamp': timezone.now().isoformat(),
                'services_ok': 0,
                'services_total': 0,
            }

    def get_kpis(self) -> Dict[str, Any]:
        """
        Retourne les KPIs principaux avec deltas.

        Returns:
            dict: {
                'total_memberships': {'value': int, 'delta_24h': int, 'delta_7d': int},
                'total_transformations': {...},
                'total_competitions': {...},
                'total_organizations': {...},
                'total_users': {...},
                'monthly_revenue': {...}
            }
        """
        cache_key = 'superadmin:kpis'
        cached = cache.get(cache_key)
        if cached:
            return cached

        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        try:
            # Import des modèles nécessaires
            from apps.competitions.models import Competition
            from apps.organizations.models import Organization
            from django.contrib.auth import get_user_model
            User = get_user_model()

            result = {
                'total_memberships': self._get_kpi_with_deltas(
                    EventPass.objects.filter(status='active'),
                    day_ago, week_ago
                ),
                'total_transformations': self._get_kpi_with_deltas(
                    MembershipTransformation.objects.all(),
                    day_ago, week_ago
                ),
                'total_competitions': self._get_kpi_with_deltas(
                    Competition.objects.all(),
                    day_ago, week_ago
                ),
                'total_organizations': self._get_kpi_with_deltas(
                    Organization.objects.filter(is_active=True),
                    day_ago, week_ago,
                    date_field='created_at'
                ),
                'total_users': self._get_kpi_with_deltas(
                    User.objects.filter(is_active=True),
                    day_ago, week_ago,
                    date_field='date_joined'
                ),
                'monthly_revenue': self._get_revenue_kpi(month_start, day_ago),
            }

            cache.set(cache_key, result, self.CACHE_TTL_SHORT)
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des KPIs: {e}")
            return self._get_empty_kpis()

    def _get_kpi_with_deltas(
        self,
        queryset,
        day_ago,
        week_ago,
        date_field='created_at'
    ) -> Dict[str, int]:
        """Calcule un KPI avec ses deltas 24h et 7j."""
        try:
            total = queryset.count()
            delta_24h = queryset.filter(**{f'{date_field}__gte': day_ago}).count()
            delta_7d = queryset.filter(**{f'{date_field}__gte': week_ago}).count()

            return {
                'value': total,
                'delta_24h': delta_24h,
                'delta_7d': delta_7d,
            }
        except Exception:
            return {'value': 0, 'delta_24h': 0, 'delta_7d': 0}

    def _get_revenue_kpi(self, month_start, day_ago) -> Dict[str, Any]:
        """Calcule le KPI de revenus mensuel."""
        try:
            from apps.finances.models import Transaction

            monthly = Transaction.objects.filter(
                created_at__gte=month_start,
                status='completed',
                transaction_type='CREDIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            daily = Transaction.objects.filter(
                created_at__gte=day_ago,
                status='completed',
                transaction_type='CREDIT'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            return {
                'value': float(monthly),
                'delta_24h': float(daily),
                'currency': 'EUR',
            }
        except Exception:
            return {'value': 0, 'delta_24h': 0, 'currency': 'EUR'}

    def _get_empty_kpis(self) -> Dict[str, Dict]:
        """Retourne des KPIs vides en cas d'erreur."""
        empty = {'value': 0, 'delta_24h': 0, 'delta_7d': 0}
        return {
            'total_memberships': empty.copy(),
            'total_transformations': empty.copy(),
            'total_competitions': empty.copy(),
            'total_organizations': empty.copy(),
            'total_users': empty.copy(),
            'monthly_revenue': {'value': 0, 'delta_24h': 0, 'currency': 'EUR'},
        }

    def get_memberships_by_profile(self) -> List[Dict[str, Any]]:
        """
        Retourne les statistiques d'adhésions par profil.

        Returns:
            list: [{
                'name': str,
                'slug': str,
                'profile_type': str,
                'total': int,
                'delta_24h': int,
                'delta_7d': int,
                'transformation_rate': float
            }]
        """
        cache_key = 'superadmin:memberships_by_profile'
        cached = cache.get(cache_key)
        if cached:
            return cached

        now = timezone.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        try:
            profiles = MembershipProfile.objects.filter(is_active=True)
            result = []

            for profile in profiles:
                passes = EventPass.objects.filter(membership_profile=profile)
                total = passes.count()
                delta_24h = passes.filter(created_at__gte=day_ago).count()
                delta_7d = passes.filter(created_at__gte=week_ago).count()

                # Taux de transformation
                transformations = MembershipTransformation.objects.filter(
                    to_profile=profile
                ).count()
                transformation_rate = (transformations / total * 100) if total > 0 else 0

                result.append({
                    'id': profile.id,
                    'name': profile.name,
                    'slug': profile.slug,
                    'profile_type': profile.profile_type,
                    'is_global': profile.is_global,
                    'total': total,
                    'delta_24h': delta_24h,
                    'delta_7d': delta_7d,
                    'transformation_rate': round(transformation_rate, 1),
                })

            # Trier par total décroissant
            result.sort(key=lambda x: (-x['is_global'], -x['total']))

            cache.set(cache_key, result, self.CACHE_TTL_SHORT)
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats par profil: {e}")
            return []

    def get_evolution_data(self, days: int = 7) -> Dict[str, Any]:
        """
        Retourne les données d'évolution pour les graphiques.

        Args:
            days: Nombre de jours à inclure

        Returns:
            dict: {
                'dates': ['2025-01-01', ...],
                'memberships': [10, 15, ...],
                'transformations': [2, 5, ...],
                'competitions': [1, 3, ...]
            }
        """
        cache_key = f'superadmin:evolution_data:{days}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        now = timezone.now()
        start_date = now - timedelta(days=days)

        try:
            from apps.competitions.models import Competition

            # Générer les dates
            dates = []
            current = start_date.date()
            while current <= now.date():
                dates.append(current.isoformat())
                current += timedelta(days=1)

            # Adhésions par jour
            memberships_data = EventPass.objects.filter(
                created_at__gte=start_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            # Transformations par jour
            transformations_data = MembershipTransformation.objects.filter(
                created_at__gte=start_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            # Compétitions par jour
            competitions_data = Competition.objects.filter(
                created_at__gte=start_date
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')

            # Convertir en dictionnaires pour un accès facile
            memberships_dict = {
                item['date'].isoformat(): item['count']
                for item in memberships_data
            }
            transformations_dict = {
                item['date'].isoformat(): item['count']
                for item in transformations_data
            }
            competitions_dict = {
                item['date'].isoformat(): item['count']
                for item in competitions_data
            }

            result = {
                'dates': dates,
                'memberships': [memberships_dict.get(d, 0) for d in dates],
                'transformations': [transformations_dict.get(d, 0) for d in dates],
                'competitions': [competitions_dict.get(d, 0) for d in dates],
            }

            cache.set(cache_key, result, self.CACHE_TTL_MEDIUM)
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données d'évolution: {e}")
            return {'dates': [], 'memberships': [], 'transformations': [], 'competitions': []}

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de la base de données.

        Returns:
            dict: {
                'size_gb': float,
                'tables_count': int,
                'connections_active': int,
                'connections_max': int,
                'top_tables': [{'name': str, 'size_gb': float, 'rows_count': int}]
            }
        """
        cache_key = 'superadmin:database_stats'
        cached = cache.get(cache_key)
        if cached:
            return cached

        size_gb = 0
        tables_count = 0
        connections_active = 0
        connections_max = 100
        top_tables = []

        try:
            with connection.cursor() as cursor:
                # Taille de la base - méthode principale
                try:
                    cursor.execute("""
                        SELECT pg_database_size(current_database()) / 1024.0 / 1024.0 / 1024.0
                    """)
                    result = cursor.fetchone()
                    if result and result[0]:
                        size_gb = float(result[0])
                except Exception as e:
                    logger.warning(f"pg_database_size non accessible: {e}")
                    # Méthode alternative: calculer depuis pg_stat_user_tables
                    try:
                        cursor.execute("""
                            SELECT COALESCE(SUM(pg_total_relation_size(quote_ident(tablename))), 0) / 1024.0 / 1024.0 / 1024.0
                            FROM pg_stat_user_tables
                        """)
                        result = cursor.fetchone()
                        if result and result[0]:
                            size_gb = float(result[0])
                    except Exception as e2:
                        logger.warning(f"Méthode alternative taille DB aussi en erreur: {e2}")

                # Nombre de tables
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    """)
                    result = cursor.fetchone()
                    if result:
                        tables_count = result[0]
                except Exception as e:
                    logger.warning(f"Comptage tables en erreur: {e}")

                # Connexions actives - plusieurs méthodes selon les permissions
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM pg_stat_activity
                        WHERE datname = current_database()
                    """)
                    result = cursor.fetchone()
                    if result:
                        connections_active = result[0]
                except Exception as e:
                    logger.warning(f"pg_stat_activity non accessible: {e}")
                    # Méthode alternative: compter depuis numbackends
                    try:
                        cursor.execute("""
                            SELECT numbackends FROM pg_stat_database
                            WHERE datname = current_database()
                        """)
                        result = cursor.fetchone()
                        if result and result[0]:
                            connections_active = result[0]
                    except Exception as e2:
                        logger.warning(f"pg_stat_database aussi en erreur: {e2}")
                        # Dernier recours: au moins 1 connexion (celle en cours)
                        connections_active = 1

                # Max connexions
                try:
                    cursor.execute("SHOW max_connections")
                    result = cursor.fetchone()
                    if result:
                        connections_max = int(result[0])
                except Exception as e:
                    logger.warning(f"SHOW max_connections en erreur: {e}")

                # Top tables par taille
                try:
                    cursor.execute("""
                        SELECT
                            schemaname || '.' || tablename as full_name,
                            pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)) / 1024.0 / 1024.0 / 1024.0 as size_gb,
                            COALESCE(n_live_tup, 0) as rows_count
                        FROM pg_stat_user_tables
                        WHERE schemaname = 'public'
                        ORDER BY pg_total_relation_size(quote_ident(schemaname) || '.' || quote_ident(tablename)) DESC
                        LIMIT 10
                    """)
                    top_tables = [
                        {
                            'name': row[0].replace('public.', ''),
                            'size_gb': round(float(row[1]) if row[1] else 0, 3),
                            'rows_count': row[2] or 0
                        }
                        for row in cursor.fetchall()
                    ]
                except Exception as e:
                    logger.warning(f"Top tables en erreur: {e}")
                    # Méthode alternative depuis information_schema
                    try:
                        cursor.execute("""
                            SELECT table_name, 0 as size_gb, 0 as rows_count
                            FROM information_schema.tables
                            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                            ORDER BY table_name
                            LIMIT 10
                        """)
                        top_tables = [
                            {'name': row[0], 'size_gb': 0, 'rows_count': 0}
                            for row in cursor.fetchall()
                        ]
                    except Exception as e2:
                        logger.warning(f"Information schema tables aussi en erreur: {e2}")

            result = {
                'size_gb': round(size_gb, 2),
                'tables_count': tables_count,
                'connections_active': connections_active,
                'connections_max': connections_max,
                'connections_percent': round(connections_active / connections_max * 100, 1) if connections_max > 0 else 0,
                'top_tables': top_tables,
            }

            cache.set(cache_key, result, self.CACHE_TTL_MEDIUM)
            return result

        except Exception as e:
            logger.error(f"Erreur globale lors de la récupération des stats DB: {e}")
            return {
                'size_gb': 0,
                'tables_count': 0,
                'connections_active': 0,
                'connections_max': 100,
                'connections_percent': 0,
                'top_tables': [],
            }

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques de stockage.

        Returns:
            dict: {
                'total_gb': float,
                'used_gb': float,
                'free_gb': float,
                'percent_used': float,
                'breakdown': {'media': float, 'static': float, 'backups': float, 'logs': float}
            }
        """
        cache_key = 'superadmin:storage_stats'
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            # Stats du disque principal
            disk = psutil.disk_usage('/')
            total_gb = disk.total / (1024 ** 3)
            used_gb = disk.used / (1024 ** 3)
            free_gb = disk.free / (1024 ** 3)
            percent_used = disk.percent

            # Breakdown par dossier
            breakdown = {}
            base_path = getattr(settings, 'BASE_DIR', '/var/www')

            folders = {
                'media': getattr(settings, 'MEDIA_ROOT', os.path.join(base_path, 'media')),
                'static': getattr(settings, 'STATIC_ROOT', os.path.join(base_path, 'static')),
                'logs': os.path.join(base_path, 'logs'),
            }

            for name, path in folders.items():
                if os.path.exists(path):
                    size = self._get_folder_size(path)
                    breakdown[name] = round(size / (1024 ** 3), 2)
                else:
                    breakdown[name] = 0

            result = {
                'total_gb': round(total_gb, 1),
                'used_gb': round(used_gb, 1),
                'free_gb': round(free_gb, 1),
                'percent_used': round(percent_used, 1),
                'breakdown': breakdown,
            }

            cache.set(cache_key, result, self.CACHE_TTL_MEDIUM)
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats stockage: {e}")
            return {
                'total_gb': 0,
                'used_gb': 0,
                'free_gb': 0,
                'percent_used': 0,
                'breakdown': {},
            }

    def get_services_status(self) -> List[Dict[str, Any]]:
        """
        Retourne le statut de tous les services.

        Returns:
            list: [{
                'name': str,
                'display_name': str,
                'status': str,
                'status_display': str,
                'pid': int,
                'cpu': float,
                'memory_mb': float,
                'response_time_ms': int
            }]
        """
        try:
            services = ServiceStatus.objects.all()
            return [
                {
                    'name': s.service_name,
                    'display_name': s.get_service_name_display(),
                    'status': s.status,
                    'status_display': s.get_status_display(),
                    'pid': s.pid,
                    'cpu': float(s.cpu_percent) if s.cpu_percent else None,
                    'memory_mb': float(s.memory_mb) if s.memory_mb else None,
                    'response_time_ms': s.response_time_ms,
                    'last_check': s.last_check.isoformat() if s.last_check else None,
                    'error_message': s.error_message,
                }
                for s in services
            ]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statuts services: {e}")
            return []

    # Méthodes utilitaires privées

    def _get_uptime(self) -> int:
        """Retourne l'uptime du système en secondes."""
        try:
            return int(psutil.boot_time())
        except Exception:
            return 0

    def _format_uptime(self, boot_time: int) -> str:
        """Formate l'uptime pour l'affichage."""
        if not boot_time:
            return 'N/A'
        try:
            uptime_seconds = int(timezone.now().timestamp() - boot_time)
            days = uptime_seconds // 86400
            hours = (uptime_seconds % 86400) // 3600
            minutes = (uptime_seconds % 3600) // 60

            if days > 0:
                return f"{days}j {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except Exception:
            return 'N/A'

    def _get_status_display(self, status: str) -> str:
        """Retourne le libellé du statut."""
        displays = {
            'operational': '🟢 Opérationnel',
            'degraded': '🟡 Dégradé',
            'down': '🔴 Hors ligne',
            'unknown': '⚪ Inconnu',
        }
        return displays.get(status, 'Inconnu')

    def _get_folder_size(self, path: str) -> int:
        """Calcule la taille d'un dossier en bytes."""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except Exception:
            pass
        return total

    def _update_essential_services_status(self):
        """
        Met à jour le statut des services essentiels (web et database) en temps réel.
        Appelé avant de calculer le statut global de la plateforme.
        """
        import time as time_module

        # Vérifier le service web (si on arrive ici, c'est que Django fonctionne)
        try:
            ServiceStatus.objects.update_or_create(
                service_name='web',
                defaults={
                    'status': 'ok',
                    'error_message': None,
                    'last_check': timezone.now(),
                }
            )
        except Exception as e:
            logger.warning(f"Erreur mise à jour statut web: {e}")

        # Vérifier la base de données
        try:
            start = time_module.time()
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            response_time = int((time_module.time() - start) * 1000)

            ServiceStatus.objects.update_or_create(
                service_name='database',
                defaults={
                    'status': 'ok',
                    'response_time_ms': response_time,
                    'error_message': None,
                    'last_check': timezone.now(),
                }
            )
        except Exception as e:
            logger.warning(f"Erreur mise à jour statut database: {e}")
            ServiceStatus.objects.update_or_create(
                service_name='database',
                defaults={
                    'status': 'error',
                    'error_message': str(e),
                    'last_check': timezone.now(),
                }
            )


class MetricsCollector:
    """
    Collecteur de métriques pour les tâches Celery.
    """

    def collect_all(self) -> Dict[str, bool]:
        """
        Collecte toutes les métriques et les stocke.

        Returns:
            dict: {'metric_type': success_bool}
        """
        results = {}
        service = MetricsService()

        try:
            # Collecter les stats DB
            db_stats = service.get_database_stats()
            if db_stats['size_gb']:
                SystemMetric.objects.create(
                    metric_type='db_size',
                    value=Decimal(str(db_stats['size_gb'])),
                    unit='GB',
                    metadata={'tables_count': db_stats['tables_count']}
                )
                results['db_size'] = True

                SystemMetric.objects.create(
                    metric_type='db_connections',
                    value=Decimal(str(db_stats['connections_active'])),
                    unit='count',
                    metadata={'max': db_stats['connections_max']}
                )
                results['db_connections'] = True

            # Collecter les stats stockage
            storage_stats = service.get_storage_stats()
            if storage_stats['total_gb']:
                SystemMetric.objects.create(
                    metric_type='storage_total',
                    value=Decimal(str(storage_stats['total_gb'])),
                    unit='GB'
                )
                SystemMetric.objects.create(
                    metric_type='storage_used',
                    value=Decimal(str(storage_stats['used_gb'])),
                    unit='GB',
                    metadata={'percent': storage_stats['percent_used']}
                )
                results['storage'] = True

            # Collecter les stats CPU/mémoire
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()

                SystemMetric.objects.create(
                    metric_type='cpu_usage',
                    value=Decimal(str(cpu_percent)),
                    unit='%'
                )
                SystemMetric.objects.create(
                    metric_type='memory_usage',
                    value=Decimal(str(memory.percent)),
                    unit='%',
                    metadata={'total_gb': round(memory.total / (1024**3), 2)}
                )
                results['system'] = True
            except Exception as e:
                logger.warning(f"Erreur collecte CPU/mémoire: {e}")
                results['system'] = False

            # Collecter les utilisateurs actifs
            try:
                from django.contrib.sessions.models import Session
                from django.utils import timezone

                active_sessions = Session.objects.filter(
                    expire_date__gte=timezone.now()
                ).count()

                SystemMetric.objects.create(
                    metric_type='active_users',
                    value=Decimal(str(active_sessions)),
                    unit='count'
                )
                results['active_users'] = True
            except Exception as e:
                logger.warning(f"Erreur collecte utilisateurs actifs: {e}")
                results['active_users'] = False

        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques: {e}")

        return results

    def cleanup_old_metrics(self, days: int = 30) -> int:
        """
        Supprime les métriques plus anciennes que X jours.

        Args:
            days: Nombre de jours à conserver

        Returns:
            int: Nombre de métriques supprimées
        """
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = SystemMetric.objects.filter(recorded_at__lt=cutoff).delete()
        logger.info(f"Nettoyage métriques: {deleted} entrées supprimées")
        return deleted
