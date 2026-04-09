# -*- coding: utf-8 -*-
"""
ViewSets pour l'API REST Super Admin.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging

from apps.superadmin.models import (
    MembershipProfile,
    EventPass,
    MembershipTransformation,
    SystemMetric,
    ServiceStatus,
    AdminAction,
    PlatformAlert,
)
from apps.superadmin.api.serializers import (
    MembershipProfileSerializer,
    MembershipProfileListSerializer,
    EventPassSerializer,
    MembershipTransformationSerializer,
    SystemMetricSerializer,
    ServiceStatusSerializer,
    AdminActionSerializer,
    PlatformAlertSerializer,
    DashboardKPIsSerializer,
    DashboardEvolutionSerializer,
    DatabaseStatsSerializer,
    StorageStatsSerializer,
    GeoCountrySerializer,
    RecentSignupSerializer,
    SystemControlActionSerializer,
)
from apps.superadmin.services.metrics import MetricsService
from apps.superadmin.services.geo_stats import GeoStatsService
from apps.superadmin.services.system_control import SystemControlService
from apps.superadmin.services.audit import AuditService
from apps.superadmin.decorators import SuperAdminRequiredMixin

logger = logging.getLogger(__name__)


class SuperAdminPermission(IsAuthenticated):
    """Permission pour vérifier l'accès superadmin."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_superuser


class MetricsViewSet(viewsets.ViewSet):
    """
    ViewSet pour les métriques du dashboard.

    Endpoints:
    - GET /api/superadmin/metrics/dashboard/ - KPIs complets
    - GET /api/superadmin/metrics/kpis/ - KPIs uniquement
    - GET /api/superadmin/metrics/evolution/ - Données d'évolution
    - GET /api/superadmin/metrics/services/ - Statut des services
    - GET /api/superadmin/metrics/database/ - Stats DB
    - GET /api/superadmin/metrics/storage/ - Stats stockage
    """

    permission_classes = [SuperAdminPermission]

    def list(self, request):
        """Liste toutes les métriques disponibles."""
        return Response({
            'endpoints': [
                {'url': '/dashboard/', 'description': 'Dashboard complet'},
                {'url': '/kpis/', 'description': 'KPIs uniquement'},
                {'url': '/evolution/', 'description': 'Données évolution'},
                {'url': '/services/', 'description': 'Statut services'},
                {'url': '/database/', 'description': 'Stats base de données'},
                {'url': '/storage/', 'description': 'Stats stockage'},
            ]
        })

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Retourne toutes les données du dashboard."""
        service = MetricsService()

        # Récupérer la période demandée
        period = request.query_params.get('period', '7')
        try:
            days = int(period)
        except ValueError:
            days = 7

        data = {
            'platform_status': service.get_platform_status(),
            'kpis': service.get_kpis(),
            'evolution_data': service.get_evolution_data(days=days),
            'services': service.get_services_status(),
            'db_stats': service.get_database_stats(),
            'storage_stats': service.get_storage_stats(),
            'memberships_by_profile': service.get_memberships_by_profile(),
            'timestamp': timezone.now().isoformat(),
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def kpis(self, request):
        """Retourne uniquement les KPIs."""
        service = MetricsService()
        data = service.get_kpis()
        serializer = DashboardKPIsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def evolution(self, request):
        """Retourne les données d'évolution."""
        service = MetricsService()

        period = request.query_params.get('period', '7')
        try:
            days = int(period)
        except ValueError:
            days = 7

        data = service.get_evolution_data(days=days)
        serializer = DashboardEvolutionSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def services(self, request):
        """Retourne le statut des services."""
        statuses = ServiceStatus.objects.all()
        serializer = ServiceStatusSerializer(statuses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def database(self, request):
        """Retourne les stats de la base de données."""
        service = MetricsService()
        data = service.get_database_stats()
        serializer = DatabaseStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def storage(self, request):
        """Retourne les stats de stockage."""
        service = MetricsService()
        data = service.get_storage_stats()
        serializer = StorageStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Retourne les alertes actives."""
        alerts = PlatformAlert.objects.filter(is_active=True, resolved=False)
        serializer = PlatformAlertSerializer(alerts, many=True)
        return Response(serializer.data)


class GeoViewSet(viewsets.ViewSet):
    """
    ViewSet pour les statistiques géographiques.

    Endpoints:
    - GET /api/superadmin/geo/countries/ - Stats par pays
    - GET /api/superadmin/geo/country/{code}/ - Détail d'un pays
    - GET /api/superadmin/geo/recent-signups/ - Inscriptions récentes
    - GET /api/superadmin/geo/heatmap/ - Données heatmap
    """

    permission_classes = [SuperAdminPermission]

    def list(self, request):
        """Liste des endpoints disponibles."""
        return Response({
            'endpoints': [
                {'url': '/countries/', 'description': 'Stats par pays'},
                {'url': '/country/{code}/', 'description': 'Détail pays'},
                {'url': '/recent-signups/', 'description': 'Inscriptions récentes'},
                {'url': '/heatmap/', 'description': 'Données heatmap'},
            ]
        })

    @action(detail=False, methods=['get'])
    def countries(self, request):
        """Retourne les statistiques par pays."""
        service = GeoStatsService()

        period = request.query_params.get('period', '24h')
        data = service.get_countries_stats(period=period)

        serializer = GeoCountrySerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='country/(?P<code>[A-Z]{2})')
    def country_detail(self, request, code=None):
        """Retourne le détail d'un pays."""
        service = GeoStatsService()
        data = service.get_country_detail(code)

        if not data:
            return Response(
                {'error': 'Pays non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(data)

    @action(detail=False, methods=['get'], url_path='recent-signups')
    def recent_signups(self, request):
        """Retourne les inscriptions récentes."""
        service = GeoStatsService()

        limit = request.query_params.get('limit', 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        country_code = request.query_params.get('country')
        data = service.get_recent_signups(limit=limit, country_code=country_code)

        serializer = RecentSignupSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def heatmap(self, request):
        """Retourne les données pour la heatmap."""
        service = GeoStatsService()

        period = request.query_params.get('period', '7d')
        data = service.get_heatmap_data(period=period)

        return Response(data)


class MembershipProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD pour les profils d'adhésion.
    """

    permission_classes = [SuperAdminPermission]
    queryset = MembershipProfile.objects.all()
    serializer_class = MembershipProfileSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return MembershipProfileListSerializer
        return MembershipProfileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtres
        profile_type = self.request.query_params.get('type')
        if profile_type:
            queryset = queryset.filter(profile_type=profile_type)

        is_active = self.request.query_params.get('active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        is_global = self.request.query_params.get('global')
        if is_global is not None:
            queryset = queryset.filter(is_global=is_global.lower() == 'true')

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save()
        AuditService.log_action(
            user=self.request.user,
            action_type='membership_create',
            request=self.request,
            description=f"Création profil: {serializer.instance.name}"
        )

    def perform_update(self, serializer):
        serializer.save()
        AuditService.log_action(
            user=self.request.user,
            action_type='membership_update',
            request=self.request,
            description=f"Modification profil: {serializer.instance.name}"
        )

    def perform_destroy(self, instance):
        name = instance.name
        instance.delete()
        AuditService.log_action(
            user=self.request.user,
            action_type='membership_delete',
            request=self.request,
            description=f"Suppression profil: {name}"
        )

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Active/désactive un profil."""
        profile = self.get_object()
        profile.is_active = not profile.is_active
        profile.save(update_fields=['is_active'])

        AuditService.log_action(
            user=request.user,
            action_type='membership_toggle',
            request=request,
            description=f"{'Activation' if profile.is_active else 'Désactivation'} profil: {profile.name}"
        )

        return Response({
            'success': True,
            'is_active': profile.is_active,
            'message': f"Profil {'activé' if profile.is_active else 'désactivé'}"
        })

    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplique un profil existant."""
        original = self.get_object()

        # Créer la copie
        copy = MembershipProfile.objects.create(
            name=f"{original.name} (copie)",
            slug=f"{original.slug}-copy",
            description=original.description,
            profile_type=original.profile_type,
            validity_type=original.validity_type,
            validity_duration=original.validity_duration,
            is_global=original.is_global,
            base_tier=original.base_tier,
            feature_overrides=original.feature_overrides.copy() if original.feature_overrides else {},
            pricing_model=original.pricing_model,
            price=original.price,
            currency=original.currency,
            max_participants=original.max_participants,
            requires_approval=original.requires_approval,
            is_active=False,  # Désactivé par défaut
        )

        AuditService.log_action(
            user=request.user,
            action_type='membership_duplicate',
            request=request,
            description=f"Duplication profil: {original.name} -> {copy.name}"
        )

        serializer = self.get_serializer(copy)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventPassViewSet(viewsets.ModelViewSet):
    """
    ViewSet CRUD pour les passes événement.
    """

    permission_classes = [SuperAdminPermission]
    queryset = EventPass.objects.all()
    serializer_class = EventPassSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtres
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        event_id = self.request.query_params.get('event')
        if event_id:
            queryset = queryset.filter(event_id=event_id)

        org_id = self.request.query_params.get('organization')
        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        return queryset.select_related('profile', 'event', 'organization').order_by('-created_at')


class TransformationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet en lecture seule pour les transformations.
    """

    permission_classes = [SuperAdminPermission]
    queryset = MembershipTransformation.objects.all()
    serializer_class = MembershipTransformationSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtres
        trans_type = self.request.query_params.get('type')
        if trans_type:
            queryset = queryset.filter(transformation_type=trans_type)

        from_date = self.request.query_params.get('from')
        if from_date:
            queryset = queryset.filter(created_at__gte=from_date)

        to_date = self.request.query_params.get('to')
        if to_date:
            queryset = queryset.filter(created_at__lte=to_date)

        return queryset.select_related(
            'from_profile', 'to_profile', 'organization', 'triggered_by'
        ).order_by('-created_at')

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des transformations."""
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        # Transformations par type
        by_type = list(
            MembershipTransformation.objects.values('transformation_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        # Transformations par jour (7 derniers jours)
        by_day = list(
            MembershipTransformation.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(days=7)
            )
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        return Response({
            'by_type': by_type,
            'by_day': [
                {'date': item['date'].isoformat(), 'count': item['count']}
                for item in by_day
            ],
        })


class SystemControlViewSet(viewsets.ViewSet):
    """
    ViewSet pour les actions de contrôle système.

    Endpoints:
    - POST /api/superadmin/system/restart-gunicorn/
    - POST /api/superadmin/system/maintenance/
    - POST /api/superadmin/system/clear-cache/
    - POST /api/superadmin/system/backup/
    - POST /api/superadmin/system/emergency-stop/
    - GET /api/superadmin/system/status/
    - GET /api/superadmin/system/actions/
    """

    permission_classes = [SuperAdminPermission]

    def list(self, request):
        """Liste les actions disponibles."""
        control = SystemControlService(user=request.user, request=request)

        return Response({
            'maintenance_mode': control.is_maintenance_mode(),
            'actions': [
                {
                    'id': 'restart_gunicorn',
                    'name': 'Redémarrer Gunicorn',
                    'description': 'Reload graceful des workers',
                    'dangerous': False,
                },
                {
                    'id': 'maintenance',
                    'name': 'Mode Maintenance',
                    'description': 'Active/désactive le mode maintenance',
                    'dangerous': False,
                },
                {
                    'id': 'clear_cache',
                    'name': 'Vider le cache',
                    'description': 'Vide le cache Redis',
                    'dangerous': False,
                },
                {
                    'id': 'backup',
                    'name': 'Backup DB',
                    'description': 'Déclenche un backup de la base',
                    'dangerous': False,
                },
                {
                    'id': 'emergency_stop',
                    'name': 'Arrêt d\'urgence',
                    'description': 'Arrête tous les services (DANGER!)',
                    'dangerous': True,
                },
            ],
        })

    @action(detail=False, methods=['post'], url_path='restart-gunicorn')
    def restart_gunicorn(self, request):
        """Redémarre Gunicorn."""
        control = SystemControlService(user=request.user, request=request)
        result = control.restart_gunicorn()

        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post', 'delete'])
    def maintenance(self, request):
        """Active/désactive le mode maintenance."""
        control = SystemControlService(user=request.user, request=request)

        if request.method == 'POST':
            result = control.enable_maintenance_mode()
        else:
            result = control.disable_maintenance_mode()

        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='clear-cache')
    def clear_cache(self, request):
        """Vide le cache."""
        control = SystemControlService(user=request.user, request=request)
        result = control.clear_cache()

        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def backup(self, request):
        """Déclenche un backup."""
        control = SystemControlService(user=request.user, request=request)
        result = control.trigger_backup()

        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='emergency-stop')
    def emergency_stop(self, request):
        """Arrêt d'urgence."""
        serializer = SystemControlActionSerializer(data={
            'action': 'emergency_stop',
            'reason': request.data.get('reason', ''),
            'confirm': request.data.get('confirm', False),
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        control = SystemControlService(user=request.user, request=request)
        result = control.emergency_stop(serializer.validated_data['reason'])

        return Response(result, status=status.HTTP_200_OK if result['success'] else status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Statut de tous les services."""
        control = SystemControlService(user=request.user, request=request)
        results = control.check_all_services()

        return Response({
            'services': results,
            'timestamp': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'])
    def actions(self, request):
        """Historique des actions."""
        limit = request.query_params.get('limit', 50)
        try:
            limit = int(limit)
        except ValueError:
            limit = 50

        actions = AdminAction.objects.order_by('-created_at')[:limit]
        serializer = AdminActionSerializer(actions, many=True)

        return Response(serializer.data)


class AlertsViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les alertes plateforme.
    """

    permission_classes = [SuperAdminPermission]
    queryset = PlatformAlert.objects.all()
    serializer_class = PlatformAlertSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtres
        is_active = self.request.query_params.get('active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)

        resolved = self.request.query_params.get('resolved')
        if resolved is not None:
            queryset = queryset.filter(resolved=resolved.lower() == 'true')

        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acquitte une alerte."""
        alert = self.get_object()

        if alert.acknowledged:
            return Response({
                'success': False,
                'message': 'Alerte déjà acquittée'
            })

        alert.acknowledged = True
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save(update_fields=['acknowledged', 'acknowledged_by', 'acknowledged_at'])

        return Response({
            'success': True,
            'message': 'Alerte acquittée'
        })

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Résout une alerte."""
        alert = self.get_object()

        if alert.resolved:
            return Response({
                'success': False,
                'message': 'Alerte déjà résolue'
            })

        alert.resolved = True
        alert.resolved_at = timezone.now()
        alert.is_active = False
        alert.save(update_fields=['resolved', 'resolved_at', 'is_active'])

        return Response({
            'success': True,
            'message': 'Alerte résolue'
        })
