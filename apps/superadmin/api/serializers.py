# -*- coding: utf-8 -*-
"""
Serializers pour l'API REST Super Admin.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import timedelta

from apps.superadmin.models import (
    MembershipProfile,
    EventPass,
    MembershipTransformation,
    SystemMetric,
    ServiceStatus,
    AdminAction,
    PlatformAlert,
)


class MembershipProfileSerializer(serializers.ModelSerializer):
    """Serializer pour les profils d'adhésion."""

    subscription_count = serializers.SerializerMethodField()
    active_count = serializers.SerializerMethodField()
    revenue_mtd = serializers.SerializerMethodField()

    class Meta:
        model = MembershipProfile
        fields = [
            'id', 'name', 'slug', 'description', 'profile_type',
            'validity_type', 'validity_duration', 'is_global',
            'base_tier', 'feature_overrides', 'pricing_model',
            'price', 'currency', 'max_participants',
            'requires_approval', 'is_active',
            'subscription_count', 'active_count', 'revenue_mtd',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_subscription_count(self, obj):
        """Nombre total de souscriptions."""
        # TODO: Implémenter quand le modèle Subscription sera lié
        return 0

    def get_active_count(self, obj):
        """Nombre de souscriptions actives."""
        return 0

    def get_revenue_mtd(self, obj):
        """Revenus du mois en cours."""
        return 0.0


class MembershipProfileListSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes."""

    class Meta:
        model = MembershipProfile
        fields = ['id', 'name', 'slug', 'profile_type', 'price', 'currency', 'is_active']


class EventPassSerializer(serializers.ModelSerializer):
    """Serializer pour les passes événement."""

    profile_name = serializers.CharField(source='profile.name', read_only=True)
    event_name = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = EventPass
        fields = [
            'id', 'profile', 'profile_name', 'event', 'event_name',
            'organization', 'organization_name', 'participant_count',
            'external_participants', 'status', 'valid_from', 'valid_until',
            'is_expired', 'created_at',
        ]

    def get_event_name(self, obj):
        return obj.event.name if obj.event else None

    def get_organization_name(self, obj):
        return obj.organization.name if obj.organization else None

    def get_is_expired(self, obj):
        if obj.valid_until:
            return timezone.now() > obj.valid_until
        return False


class MembershipTransformationSerializer(serializers.ModelSerializer):
    """Serializer pour les transformations."""

    from_profile_name = serializers.CharField(source='from_profile.name', read_only=True)
    to_profile_name = serializers.CharField(source='to_profile.name', read_only=True)
    organization_name = serializers.SerializerMethodField()
    triggered_by_name = serializers.SerializerMethodField()

    class Meta:
        model = MembershipTransformation
        fields = [
            'id', 'transformation_type', 'from_profile', 'from_profile_name',
            'to_profile', 'to_profile_name', 'organization', 'organization_name',
            'event_pass', 'reason', 'triggered_by', 'triggered_by_name',
            'was_automatic', 'metadata', 'created_at',
        ]

    def get_organization_name(self, obj):
        return obj.organization.name if obj.organization else None

    def get_triggered_by_name(self, obj):
        if obj.triggered_by:
            return obj.triggered_by.get_full_name() or obj.triggered_by.username
        return None


class SystemMetricSerializer(serializers.ModelSerializer):
    """Serializer pour les métriques système."""

    class Meta:
        model = SystemMetric
        fields = ['id', 'metric_name', 'value', 'unit', 'collected_at', 'metadata']


class ServiceStatusSerializer(serializers.ModelSerializer):
    """Serializer pour le statut des services."""

    display_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = ServiceStatus
        fields = [
            'id', 'service_name', 'display_name', 'status', 'status_display',
            'response_time_ms', 'pid', 'cpu_percent', 'memory_mb',
            'error_message', 'last_check',
        ]

    def get_display_name(self, obj):
        names = {
            'web': 'Serveur Web',
            'database': 'Base de données',
            'redis': 'Cache Redis',
            'celery': 'Celery Worker',
            'celery_beat': 'Celery Beat',
            'nginx': 'Nginx',
        }
        return names.get(obj.service_name, obj.service_name)

    def get_status_display(self, obj):
        displays = {
            'ok': 'En ligne',
            'warning': 'Avertissement',
            'error': 'Erreur',
            'unknown': 'Inconnu',
        }
        return displays.get(obj.status, obj.status)


class AdminActionSerializer(serializers.ModelSerializer):
    """Serializer pour les actions d'administration."""

    user_name = serializers.SerializerMethodField()
    action_display = serializers.SerializerMethodField()

    class Meta:
        model = AdminAction
        fields = [
            'id', 'user', 'user_name', 'action_type', 'action_display',
            'target_service', 'target_id', 'description', 'ip_address',
            'user_agent', 'success', 'error_message', 'duration_ms',
            'created_at', 'completed_at',
        ]

    def get_user_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return 'Système'

    def get_action_display(self, obj):
        displays = {
            'restart_service': 'Redémarrage service',
            'maintenance_mode': 'Mode maintenance',
            'cache_clear': 'Vidage cache',
            'backup_trigger': 'Backup déclenché',
            'config_change': 'Modification config',
            'emergency_stop': 'Arrêt d\'urgence',
        }
        return displays.get(obj.action_type, obj.action_type)


class PlatformAlertSerializer(serializers.ModelSerializer):
    """Serializer pour les alertes plateforme."""

    acknowledged_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PlatformAlert
        fields = [
            'id', 'alert_type', 'severity', 'title', 'message',
            'source', 'is_active', 'acknowledged', 'acknowledged_by',
            'acknowledged_by_name', 'acknowledged_at', 'resolved',
            'resolved_at', 'auto_resolved', 'metadata',
            'created_at', 'updated_at',
        ]

    def get_acknowledged_by_name(self, obj):
        if obj.acknowledged_by:
            return obj.acknowledged_by.get_full_name() or obj.acknowledged_by.username
        return None


# Serializers pour les réponses API du dashboard

class DashboardKPIsSerializer(serializers.Serializer):
    """Serializer pour les KPIs du dashboard."""

    total_memberships = serializers.DictField()
    total_transformations = serializers.DictField()
    total_competitions = serializers.DictField()
    total_organizations = serializers.DictField()
    total_users = serializers.DictField()
    monthly_revenue = serializers.DictField()


class DashboardEvolutionSerializer(serializers.Serializer):
    """Serializer pour les données d'évolution."""

    dates = serializers.ListField(child=serializers.CharField())
    memberships = serializers.ListField(child=serializers.IntegerField())
    transformations = serializers.ListField(child=serializers.IntegerField())
    competitions = serializers.ListField(child=serializers.IntegerField())


class DatabaseStatsSerializer(serializers.Serializer):
    """Serializer pour les stats DB."""

    size_gb = serializers.FloatField()
    tables_count = serializers.IntegerField()
    connections_active = serializers.IntegerField()
    connections_max = serializers.IntegerField()
    connections_percent = serializers.FloatField()


class StorageStatsSerializer(serializers.Serializer):
    """Serializer pour les stats stockage."""

    used_gb = serializers.FloatField()
    total_gb = serializers.FloatField()
    percent_used = serializers.FloatField()
    breakdown = serializers.DictField()


class GeoCountrySerializer(serializers.Serializer):
    """Serializer pour les stats par pays."""

    country_code = serializers.CharField()
    country_name = serializers.CharField()
    count = serializers.IntegerField()
    delta_24h = serializers.IntegerField()
    percent = serializers.FloatField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class RecentSignupSerializer(serializers.Serializer):
    """Serializer pour les inscriptions récentes."""

    id = serializers.IntegerField()
    name = serializers.CharField()
    organization_type = serializers.CharField()
    country_code = serializers.CharField()
    country_name = serializers.CharField()
    city = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()
    lat = serializers.FloatField(allow_null=True)
    lng = serializers.FloatField(allow_null=True)


class SystemControlActionSerializer(serializers.Serializer):
    """Serializer pour les actions de contrôle système."""

    action = serializers.ChoiceField(
        choices=[
            ('restart_gunicorn', 'Redémarrer Gunicorn'),
            ('enable_maintenance', 'Activer maintenance'),
            ('disable_maintenance', 'Désactiver maintenance'),
            ('clear_cache', 'Vider le cache'),
            ('trigger_backup', 'Déclencher backup'),
            ('emergency_stop', 'Arrêt d\'urgence'),
        ]
    )
    reason = serializers.CharField(required=False, allow_blank=True)
    confirm = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        if data['action'] == 'emergency_stop':
            if not data.get('reason') or len(data.get('reason', '')) < 10:
                raise serializers.ValidationError({
                    'reason': 'Une raison détaillée est obligatoire pour l\'arrêt d\'urgence (min 10 caractères)'
                })
            if not data.get('confirm'):
                raise serializers.ValidationError({
                    'confirm': 'Confirmation obligatoire pour l\'arrêt d\'urgence'
                })
        return data
