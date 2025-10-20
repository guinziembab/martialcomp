from django.core.exceptions import PermissionDenied
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import RefreshToken, AccessTokenLog, DeviceRegistration, PKCESession
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'issued_at', 'expires_at', 'revoked', 'tenant')
    list_filter = ('revoked', 'issued_at', 'expires_at', 'tenant')
    search_fields = ('user__username', 'user__email', 'device_id')
    readonly_fields = ('issued_at',)
    date_hierarchy = 'issued_at'
    fieldsets = (
        (None, {
            'fields': ('user', 'token', 'revoked')
        }),
        (_('Dates'), {
            'fields': ('issued_at', 'expires_at')
        }),
        (_('Appareil'), {
            'fields': ('device_id', 'user_agent', 'ip_address')
        }),
        (_('Multi-tenant'), {
            'fields': ('tenant',)
        }),
        (_('PKCE'), {
            'fields': ('code_challenge', 'code_challenge_method'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccessTokenLog)
class AccessTokenLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'jti', 'issued_at', 'expires_at', 'revoked')
    list_filter = ('revoked', 'issued_at', 'expires_at', 'tenant')
    search_fields = ('user__username', 'user__email', 'jti', 'device_id')
    readonly_fields = ('issued_at',)
    date_hierarchy = 'issued_at'
    fieldsets = (
        (None, {
            'fields': ('user', 'jti', 'revoked', 'revoked_at')
        }),
        (_('Dates'), {
            'fields': ('issued_at', 'expires_at')
        }),
        (_('Appareil'), {
            'fields': ('device_id', 'user_agent', 'ip_address')
        }),
        (_('Multi-tenant'), {
            'fields': ('tenant',)
        }),
    )


@admin.register(DeviceRegistration)
class DeviceRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'device_name', 'device_model', 'is_active', 'registered_at')
    list_filter = ('is_active', 'registered_at', 'last_used_at', 'tenant')
    search_fields = ('user__username', 'user__email', 'device_id', 'device_name')
    readonly_fields = ('registered_at', 'last_used_at')
    date_hierarchy = 'registered_at'
    fieldsets = (
        (None, {
            'fields': ('user', 'device_id', 'device_name', 'is_active')
        }),
        (_('Informations appareil'), {
            'fields': ('device_model', 'os_version', 'app_version')
        }),
        (_('Notifications'), {
            'fields': ('push_token',)
        }),
        (_('Dates'), {
            'fields': ('registered_at', 'last_used_at')
        }),
        (_('Multi-tenant'), {
            'fields': ('tenant',)
        }),
    )


@admin.register(PKCESession)
class PKCESessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'expires_at', 'used', 'client_id')
    list_filter = ('used', 'created_at', 'expires_at', 'code_challenge_method', 'tenant')
    search_fields = ('user__username', 'user__email', 'client_id', 'state')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {
            'fields': ('user', 'auth_code', 'used')
        }),
        (_('PKCE'), {
            'fields': ('code_challenge', 'code_challenge_method', 'code_verifier')
        }),
        (_('Détails'), {
            'fields': ('client_id', 'redirect_uri', 'scope', 'state')
        }),
        (_('Dates'), {
            'fields': ('created_at', 'expires_at')
        }),
        (_('Multi-tenant'), {
            'fields': ('tenant',)
        }),
    )