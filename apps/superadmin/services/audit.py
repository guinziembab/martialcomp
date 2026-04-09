# -*- coding: utf-8 -*-
"""
Service d'audit pour Super Admin.
"""

import logging
from typing import Optional, Any

from django.utils import timezone

from apps.superadmin.models import AdminAction

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service pour logger les actions d'administration.
    """

    @classmethod
    def log_action(
        cls,
        user,
        action_type: str,
        request=None,
        description: str = '',
        target_service: str = None,
        target_object: Any = None,
        status: str = 'initiated'
    ) -> Optional[AdminAction]:
        """
        Enregistre une action d'administration.

        Args:
            user: L'utilisateur qui effectue l'action
            action_type: Type d'action (voir AdminAction.ACTION_TYPE_CHOICES)
            request: L'objet HttpRequest (pour IP et User-Agent)
            description: Description de l'action
            target_service: Service cible (optionnel)
            target_object: Objet Django cible (optionnel)
            status: Statut initial

        Returns:
            AdminAction ou None en cas d'erreur
        """
        try:
            # Extraire IP et User-Agent de la requête
            ip_address = '127.0.0.1'
            user_agent = ''

            if request:
                ip_address = cls._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            # Extraire les infos de l'objet cible
            target_object_type = None
            target_object_id = None

            if target_object:
                target_object_type = f"{target_object._meta.app_label}.{target_object._meta.model_name}"
                target_object_id = getattr(target_object, 'pk', None)

            # Créer l'entrée d'audit
            action = AdminAction.objects.create(
                admin_user=user,
                action_type=action_type,
                target_service=target_service,
                target_object_type=target_object_type,
                target_object_id=target_object_id,
                description=description or cls._get_default_description(action_type),
                ip_address=ip_address,
                user_agent=user_agent,
                status=status,
            )

            logger.info(
                f"Action admin: {action_type} par {user} "
                f"(IP: {ip_address}, cible: {target_service or target_object_type})"
            )

            return action

        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'action d'audit: {e}")
            return None

    @classmethod
    def complete_action(
        cls,
        action: AdminAction,
        success: bool = True,
        message: str = ''
    ):
        """
        Marque une action comme terminée.

        Args:
            action: L'action à compléter
            success: Si l'action a réussi
            message: Message de résultat
        """
        try:
            action.status = 'completed' if success else 'failed'
            action.result_message = message
            action.completed_at = timezone.now()
            action.save(update_fields=['status', 'result_message', 'completed_at'])

            logger.info(
                f"Action {action.id} terminée: "
                f"{'succès' if success else 'échec'} - {message[:100]}"
            )

        except Exception as e:
            logger.error(f"Erreur lors de la complétion de l'action {action.id}: {e}")

    @classmethod
    def _get_client_ip(cls, request) -> str:
        """Extrait l'IP client de la requête."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip

    @classmethod
    def _get_default_description(cls, action_type: str) -> str:
        """Retourne une description par défaut pour un type d'action."""
        descriptions = {
            'restart_service': 'Redémarrage de service',
            'maintenance_mode': 'Changement du mode maintenance',
            'emergency_stop': "Arrêt d'urgence de la plateforme",
            'config_change': 'Modification de la configuration',
            'profile_create': 'Création de profil de membership',
            'profile_modify': 'Modification de profil de membership',
            'profile_delete': 'Suppression de profil de membership',
            'user_action': 'Action sur un utilisateur',
            'backup_trigger': 'Déclenchement de backup',
            'cache_clear': 'Vidage du cache',
        }
        return descriptions.get(action_type, 'Action administrative')

    @classmethod
    def get_recent_actions(cls, limit: int = 20, action_type: str = None):
        """
        Récupère les actions récentes.

        Args:
            limit: Nombre maximum d'actions
            action_type: Filtrer par type (optionnel)

        Returns:
            QuerySet d'AdminAction
        """
        qs = AdminAction.objects.select_related('admin_user').order_by('-created_at')

        if action_type:
            qs = qs.filter(action_type=action_type)

        return qs[:limit]

    @classmethod
    def get_actions_for_user(cls, user, limit: int = 50):
        """
        Récupère les actions d'un utilisateur.

        Args:
            user: L'utilisateur
            limit: Nombre maximum d'actions

        Returns:
            QuerySet d'AdminAction
        """
        return AdminAction.objects.filter(
            admin_user=user
        ).order_by('-created_at')[:limit]
