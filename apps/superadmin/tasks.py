# -*- coding: utf-8 -*-
"""
Tâches Celery pour l'application Super Admin.
"""

import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    name='superadmin.collect_metrics',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=50,
    time_limit=60
)
def collect_metrics_task(self):
    """
    Collecte les métriques légères (KPIs, services).
    Fréquence recommandée: toutes les 60 secondes.
    """
    try:
        from apps.superadmin.services.metrics import MetricsCollector

        collector = MetricsCollector()
        results = collector.collect_all()

        logger.info(f"Métriques collectées: {results}")
        return {'status': 'success', 'results': results}

    except Exception as e:
        logger.error(f"Erreur collecte métriques: {e}")
        raise self.retry(exc=e)


@shared_task(
    name='superadmin.collect_heavy_metrics',
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    soft_time_limit=280,
    time_limit=300
)
def collect_heavy_metrics_task(self):
    """
    Collecte les métriques lourdes (DB stats, storage).
    Fréquence recommandée: toutes les 5 minutes.
    """
    try:
        from apps.superadmin.services.metrics import MetricsService

        service = MetricsService()

        # Stats DB
        db_stats = service.get_database_stats()
        logger.info(f"Stats DB: {db_stats['size_gb']} GB, {db_stats['tables_count']} tables")

        # Stats stockage
        storage_stats = service.get_storage_stats()
        logger.info(f"Stockage: {storage_stats['used_gb']}/{storage_stats['total_gb']} GB")

        return {
            'status': 'success',
            'db_size_gb': db_stats['size_gb'],
            'storage_used_gb': storage_stats['used_gb']
        }

    except Exception as e:
        logger.error(f"Erreur collecte métriques lourdes: {e}")
        raise self.retry(exc=e)


@shared_task(
    name='superadmin.cleanup_metrics',
    soft_time_limit=550,
    time_limit=600
)
def cleanup_metrics_task(days=30):
    """
    Nettoie les anciennes métriques.
    Fréquence recommandée: quotidien à 3h du matin.

    Args:
        days: Nombre de jours à conserver
    """
    try:
        from apps.superadmin.services.metrics import MetricsCollector

        collector = MetricsCollector()
        deleted = collector.cleanup_old_metrics(days=days)

        logger.info(f"Nettoyage métriques: {deleted} entrées supprimées (> {days} jours)")
        return {'status': 'success', 'deleted': deleted}

    except Exception as e:
        logger.error(f"Erreur nettoyage métriques: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task(
    name='superadmin.check_alerts',
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=110,
    time_limit=120
)
def check_alerts_task(self):
    """
    Vérifie les seuils d'alerte et crée des alertes si nécessaire.
    Fréquence recommandée: toutes les 2 minutes.
    """
    try:
        from apps.superadmin.models import PlatformAlert, ServiceStatus
        from apps.superadmin.services.metrics import MetricsService

        service = MetricsService()
        alerts_created = []

        # Vérifier l'espace disque
        storage = service.get_storage_stats()
        if storage['percent_used'] > 90:
            alert = PlatformAlert.create_if_threshold(
                alert_type='disk_space',
                severity='critical',
                title='Espace disque critique',
                message=f"L'espace disque est utilisé à {storage['percent_used']}%",
                threshold_check=True
            )
            if alert:
                alerts_created.append('disk_space_critical')

        elif storage['percent_used'] > 80:
            alert = PlatformAlert.create_if_threshold(
                alert_type='disk_space',
                severity='warning',
                title='Espace disque faible',
                message=f"L'espace disque est utilisé à {storage['percent_used']}%",
                threshold_check=True
            )
            if alert:
                alerts_created.append('disk_space_warning')

        # Vérifier les connexions DB
        db_stats = service.get_database_stats()
        if db_stats['connections_percent'] > 80:
            alert = PlatformAlert.create_if_threshold(
                alert_type='db_connections',
                severity='warning',
                title='Connexions DB élevées',
                message=f"{db_stats['connections_active']}/{db_stats['connections_max']} connexions actives",
                threshold_check=True
            )
            if alert:
                alerts_created.append('db_connections')

        # Vérifier les services
        services = ServiceStatus.objects.filter(status='error')
        for svc in services:
            alert = PlatformAlert.create_if_threshold(
                alert_type='service_down',
                severity='critical',
                title=f"Service {svc.get_service_name_display()} hors ligne",
                message=svc.error_message or 'Le service ne répond pas',
                threshold_check=True
            )
            if alert:
                alerts_created.append(f'service_{svc.service_name}')

        # Auto-résoudre les alertes si les conditions sont revenues à la normale
        if storage['percent_used'] < 75:
            PlatformAlert.objects.filter(
                alert_type='disk_space',
                is_resolved=False
            ).update(
                is_resolved=True,
                auto_resolved=True,
                resolved_at=timezone.now()
            )

        if db_stats['connections_percent'] < 70:
            PlatformAlert.objects.filter(
                alert_type='db_connections',
                is_resolved=False
            ).update(
                is_resolved=True,
                auto_resolved=True,
                resolved_at=timezone.now()
            )

        logger.info(f"Vérification alertes: {len(alerts_created)} nouvelles alertes")
        return {'status': 'success', 'alerts_created': alerts_created}

    except Exception as e:
        logger.error(f"Erreur vérification alertes: {e}")
        raise self.retry(exc=e)


@shared_task(
    name='superadmin.check_services',
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=55,
    time_limit=60
)
def check_services_task(self):
    """
    Vérifie le statut de tous les services.
    Fréquence recommandée: toutes les 30 secondes.
    """
    try:
        from apps.superadmin.services.system_control import SystemControlService

        service = SystemControlService()
        results = service.check_all_services()

        # Compter les services OK
        ok_count = sum(1 for r in results.values() if r.get('status') == 'ok')
        total = len(results)

        logger.info(f"Services vérifiés: {ok_count}/{total} OK")
        return {'status': 'success', 'services_ok': ok_count, 'total': total}

    except Exception as e:
        logger.error(f"Erreur vérification services: {e}")
        raise self.retry(exc=e)


@shared_task(name='superadmin.broadcast_metrics')
def broadcast_metrics_task():
    """
    Diffuse les métriques via WebSocket aux admins connectés.
    Fréquence recommandée: toutes les 30 secondes.
    """
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from apps.superadmin.services.metrics import MetricsService

        service = MetricsService()

        # Récupérer les données à diffuser
        data = {
            'type': 'metrics_update',
            'platform_status': service.get_platform_status(),
            'kpis': service.get_kpis(),
            'services': service.get_services_status(),
            'timestamp': timezone.now().isoformat()
        }

        # Envoyer au groupe WebSocket
        try:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'superadmin_metrics',
                    {
                        'type': 'metrics.update',
                        'data': data
                    }
                )
                logger.debug("Métriques diffusées via WebSocket")
        except Exception as ws_error:
            # WebSocket non configuré, ignorer silencieusement
            logger.debug(f"WebSocket non disponible: {ws_error}")

        return {'status': 'success', 'broadcast': True}

    except Exception as e:
        logger.error(f"Erreur broadcast métriques: {e}")
        return {'status': 'error', 'message': str(e)}


# Configuration Celery Beat (à ajouter dans config/celery.py)
CELERY_BEAT_SCHEDULE_SUPERADMIN = {
    'superadmin-collect-metrics': {
        'task': 'superadmin.collect_metrics',
        'schedule': 60.0,  # Toutes les 60 secondes
    },
    'superadmin-collect-heavy-metrics': {
        'task': 'superadmin.collect_heavy_metrics',
        'schedule': 300.0,  # Toutes les 5 minutes
    },
    'superadmin-check-services': {
        'task': 'superadmin.check_services',
        'schedule': 30.0,  # Toutes les 30 secondes
    },
    'superadmin-check-alerts': {
        'task': 'superadmin.check_alerts',
        'schedule': 120.0,  # Toutes les 2 minutes
    },
    'superadmin-broadcast-metrics': {
        'task': 'superadmin.broadcast_metrics',
        'schedule': 30.0,  # Toutes les 30 secondes
    },
    'superadmin-cleanup-metrics': {
        'task': 'superadmin.cleanup_metrics',
        'schedule': {
            'hour': 3,
            'minute': 0,
        },  # Tous les jours à 3h du matin
        'kwargs': {'days': 30}
    },
}
