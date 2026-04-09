# -*- coding: utf-8 -*-
"""
Configuration de l'admin Django pour Super Admin.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.superadmin.models import (
    MembershipProfile,
    EventPass,
    MembershipTransformation,
    SystemMetric,
    ServiceStatus,
    AdminAction,
    PlatformAlert,
)


@admin.register(MembershipProfile)
class MembershipProfileAdmin(admin.ModelAdmin):
    """Admin pour les profils de membership."""

    list_display = [
        'name', 'profile_type', 'validity_type', 'pricing_model',
        'price', 'is_global', 'is_active', 'created_at'
    ]
    list_filter = ['profile_type', 'validity_type', 'pricing_model', 'is_global', 'is_active']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-is_global', 'name']


@admin.register(EventPass)
class EventPassAdmin(admin.ModelAdmin):
    """Admin pour les passes événement."""

    list_display = [
        'user', 'membership_profile', 'competition', 'status',
        'payment_status', 'expires_at', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['user__email', 'user__username', 'competition__name']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    raw_id_fields = ['user', 'membership_profile', 'competition', 'organization', 'approved_by']


@admin.register(MembershipTransformation)
class MembershipTransformationAdmin(admin.ModelAdmin):
    """Admin pour les transformations de membership."""

    list_display = [
        'user', 'from_profile', 'to_profile', 'transformation_type',
        'discount_applied', 'created_at'
    ]
    list_filter = ['transformation_type', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at']
    raw_id_fields = ['user', 'from_profile', 'to_profile', 'source_event']


@admin.register(SystemMetric)
class SystemMetricAdmin(admin.ModelAdmin):
    """Admin pour les métriques système."""

    list_display = ['metric_type', 'value', 'unit', 'recorded_at']
    list_filter = ['metric_type', 'recorded_at']
    readonly_fields = ['recorded_at']
    ordering = ['-recorded_at']


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    """Admin pour le statut des services."""

    list_display = [
        'service_name', 'status', 'response_time_ms', 'pid',
        'cpu_percent', 'memory_mb', 'last_check'
    ]
    list_filter = ['service_name', 'status']
    readonly_fields = ['last_check']


@admin.register(AdminAction)
class AdminActionAdmin(admin.ModelAdmin):
    """Admin pour les actions d'administration."""

    list_display = [
        'admin_user', 'action_type', 'target_service', 'status',
        'ip_address', 'created_at', 'completed_at'
    ]
    list_filter = ['action_type', 'status', 'created_at']
    search_fields = ['admin_user__email', 'description']
    readonly_fields = ['created_at', 'completed_at', 'ip_address', 'user_agent']
    raw_id_fields = ['admin_user']


@admin.register(PlatformAlert)
class PlatformAlertAdmin(admin.ModelAdmin):
    """Admin pour les alertes plateforme."""

    list_display = [
        'title', 'alert_type', 'severity', 'is_resolved',
        'auto_resolved', 'created_at', 'resolved_at'
    ]
    list_filter = ['alert_type', 'severity', 'is_resolved', 'auto_resolved']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at', 'resolved_at']
    raw_id_fields = ['resolved_by']
