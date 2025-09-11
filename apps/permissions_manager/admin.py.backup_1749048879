# permissions_manager/admin.py

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from .models import Permission, Role, UserRoleAssignment

class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'created_at')
    search_fields = ('code', 'name', 'description')
    list_filter = ('category',)
    ordering = ('category', 'code')
    fieldsets = (
        (None, {
            'fields': ('code', 'name', 'category')
        }),
        (_('Description'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'context_type', 'is_system_role', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('context_type', 'is_system_role')
    ordering = ('context_type', 'name')
    filter_horizontal = ('permissions',)
    fieldsets = (
        (None, {
            'fields': ('name', 'context_type', 'is_system_role')
        }),
        (_('Description'), {
            'fields': ('description',),
        }),
        (_('Permissions'), {
            'fields': ('permissions',),
            'classes': ('collapse',)
        }),
    )

class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'get_context_display', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'role__context_type', 'role')
    search_fields = ('user__username', 'user__email', 'role__name')
    autocomplete_fields = ('user', 'role', 'assigned_by')
    raw_id_fields = ('content_type',)
    fieldsets = (
        (None, {
            'fields': ('user', 'role')
        }),
        (_('Contexte'), {
            'fields': ('content_type', 'object_id'),
            'description': _("Laissez vide pour un rôle global")
        }),
        (_('Statut'), {
            'fields': ('is_active', 'start_date', 'end_date')
        }),
        (_('Métadonnées'), {
            'fields': ('assigned_by',),
            'classes': ('collapse',)
        }),
    )
    
    def get_context_display(self, obj):
        if obj.context:
            return f"{obj.content_type.name}: {obj.context}"
        return _("Global")
    get_context_display.short_description = _("Contexte")

admin.site.register(Permission, PermissionAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(UserRoleAssignment, UserRoleAssignmentAdmin)