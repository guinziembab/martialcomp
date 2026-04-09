# -*- coding: utf-8 -*-
"""
WebSocket consumers pour Super Admin.

Fournit des mises à jour en temps réel pour:
- Métriques système (CPU, RAM, disque)
- Statut des services
- Alertes
- Logs en direct
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from asgiref.sync import sync_to_async


class SuperAdminConsumer(AsyncWebsocketConsumer):
    """
    Consumer principal pour le dashboard Super Admin.
    Gère les connexions WebSocket et diffuse les mises à jour.
    """

    async def connect(self):
        """Connexion WebSocket."""
        # Vérifier que l'utilisateur est superuser
        user = self.scope.get('user')
        if not user or not user.is_authenticated or not user.is_superuser:
            await self.close(code=4003)
            return

        self.room_group_name = 'superadmin_dashboard'

        # Rejoindre le groupe
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Envoyer les données initiales
        await self.send_initial_data()

    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Réception de message du client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'request_metrics':
                await self.send_metrics()
            elif message_type == 'request_services':
                await self.send_services_status()
            elif message_type == 'request_alerts':
                await self.send_alerts()
            elif message_type == 'subscribe':
                # Gérer les abonnements spécifiques
                channel = data.get('channel')
                await self.handle_subscribe(channel)

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def send_initial_data(self):
        """Envoyer les données initiales à la connexion."""
        await self.send_metrics()
        await self.send_services_status()
        await self.send_alerts()

    async def send_metrics(self):
        """Envoyer les métriques système."""
        metrics = await self.get_system_metrics()
        await self.send(text_data=json.dumps({
            'type': 'metrics',
            'data': metrics,
            'timestamp': timezone.now().isoformat()
        }))

    async def send_services_status(self):
        """Envoyer le statut des services."""
        services = await self.get_services_status()
        await self.send(text_data=json.dumps({
            'type': 'services',
            'data': services,
            'timestamp': timezone.now().isoformat()
        }))

    async def send_alerts(self):
        """Envoyer les alertes actives."""
        alerts = await self.get_active_alerts()
        await self.send(text_data=json.dumps({
            'type': 'alerts',
            'data': alerts,
            'timestamp': timezone.now().isoformat()
        }))

    async def handle_subscribe(self, channel):
        """Gérer l'abonnement à un canal spécifique."""
        if channel == 'logs':
            await self.channel_layer.group_add(
                'superadmin_logs',
                self.channel_name
            )
        elif channel == 'alerts':
            await self.channel_layer.group_add(
                'superadmin_alerts',
                self.channel_name
            )

    # Handlers pour les messages de groupe
    async def metrics_update(self, event):
        """Recevoir et transmettre les mises à jour de métriques."""
        await self.send(text_data=json.dumps({
            'type': 'metrics',
            'data': event['data'],
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))

    async def service_update(self, event):
        """Recevoir et transmettre les mises à jour de services."""
        await self.send(text_data=json.dumps({
            'type': 'service_update',
            'data': event['data'],
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))

    async def alert_update(self, event):
        """Recevoir et transmettre les nouvelles alertes."""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': event['data'],
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))

    async def log_entry(self, event):
        """Recevoir et transmettre les nouvelles entrées de log."""
        await self.send(text_data=json.dumps({
            'type': 'log',
            'data': event['data'],
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))

    async def notification(self, event):
        """Recevoir et transmettre les notifications."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data'],
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))

    # Méthodes asynchrones pour récupérer les données
    @database_sync_to_async
    def get_system_metrics(self):
        """Récupérer les métriques système."""
        try:
            import psutil

            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count(),
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': disk.percent,
                },
            }
        except ImportError:
            return {
                'cpu': {'percent': 0, 'count': 0},
                'memory': {'total': 0, 'available': 0, 'percent': 0, 'used': 0},
                'disk': {'total': 0, 'used': 0, 'free': 0, 'percent': 0},
            }

    @database_sync_to_async
    def get_services_status(self):
        """Récupérer le statut des services."""
        from apps.superadmin.models import ServiceStatus

        services = ServiceStatus.objects.all()
        return [
            {
                'name': s.name,
                'status': s.status,
                'response_time': s.response_time,
                'last_check': s.last_check.isoformat() if s.last_check else None,
                'message': s.message,
            }
            for s in services
        ]

    @database_sync_to_async
    def get_active_alerts(self):
        """Récupérer les alertes actives."""
        from apps.superadmin.models import PlatformAlert

        alerts = PlatformAlert.objects.filter(
            is_active=True,
            resolved=False
        ).order_by('-created_at')[:10]

        return [
            {
                'id': a.id,
                'title': a.title,
                'message': a.message,
                'severity': a.severity,
                'alert_type': a.alert_type,
                'created_at': a.created_at.isoformat(),
                'acknowledged': a.acknowledged,
            }
            for a in alerts
        ]


class LogsStreamConsumer(AsyncWebsocketConsumer):
    """
    Consumer pour le streaming des logs en temps réel.
    """

    async def connect(self):
        """Connexion WebSocket pour les logs."""
        user = self.scope.get('user')
        if not user or not user.is_authenticated or not user.is_superuser:
            await self.close(code=4003)
            return

        self.room_group_name = 'superadmin_logs'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        """Déconnexion."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def log_entry(self, event):
        """Recevoir et transmettre les nouvelles entrées de log."""
        await self.send(text_data=json.dumps({
            'type': 'log',
            'data': event['data'],
            'timestamp': event.get('timestamp', timezone.now().isoformat())
        }))


# Fonctions utilitaires pour envoyer des messages depuis d'autres parties du code
async def broadcast_metrics(channel_layer, metrics_data):
    """Diffuser les métriques à tous les clients connectés."""
    await channel_layer.group_send(
        'superadmin_dashboard',
        {
            'type': 'metrics_update',
            'data': metrics_data,
            'timestamp': timezone.now().isoformat()
        }
    )


async def broadcast_alert(channel_layer, alert_data):
    """Diffuser une alerte à tous les clients connectés."""
    await channel_layer.group_send(
        'superadmin_dashboard',
        {
            'type': 'alert_update',
            'data': alert_data,
            'timestamp': timezone.now().isoformat()
        }
    )


async def broadcast_log(channel_layer, log_data):
    """Diffuser une entrée de log aux clients abonnés."""
    await channel_layer.group_send(
        'superadmin_logs',
        {
            'type': 'log_entry',
            'data': log_data,
            'timestamp': timezone.now().isoformat()
        }
    )


async def broadcast_service_update(channel_layer, service_data):
    """Diffuser une mise à jour de service."""
    await channel_layer.group_send(
        'superadmin_dashboard',
        {
            'type': 'service_update',
            'data': service_data,
            'timestamp': timezone.now().isoformat()
        }
    )
