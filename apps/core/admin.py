"""
Administration pour le module core.
PHASE 3: Interface d'audit pour les logs d'acces par discipline.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Count
from .models import DisciplineAccessLog


@admin.register(DisciplineAccessLog)
class DisciplineAccessLogAdmin(admin.ModelAdmin):
    """Administration des logs d'acces par discipline."""

    list_display = [
        'timestamp',
        'user_link',
        'discipline_link',
        'action',
        'allowed_badge',
        'resource_info',
        'ip_address',
    ]
    list_filter = [
        'allowed',
        'action',
        ('timestamp', admin.DateFieldListFilter),
        'discipline',
        'organization',
    ]
    search_fields = [
        'user__username',
        'user__email',
        'discipline__name',
        'ip_address',
        'resource_type',
    ]
    readonly_fields = [
        'user',
        'discipline',
        'organization',
        'action',
        'allowed',
        'timestamp',
        'ip_address',
        'user_agent',
        'resource_type',
        'resource_id',
        'details',
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 50

    def has_add_permission(self, request):
        """Interdit la creation manuelle de logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Interdit la modification des logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Permet la suppression seulement aux superusers."""
        return request.user.is_superuser

    def user_link(self, obj):
        """Affiche un lien vers l'utilisateur."""
        if obj.user:
            return format_html(
                '<a href="/admin/auth/user/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = _('Utilisateur')
    user_link.admin_order_field = 'user__username'

    def discipline_link(self, obj):
        """Affiche un lien vers la discipline."""
        if obj.discipline:
            return format_html(
                '<a href="/admin/competitions/discipline/{}/change/">{}</a>',
                obj.discipline.id,
                obj.discipline.name
            )
        return '-'
    discipline_link.short_description = _('Discipline')
    discipline_link.admin_order_field = 'discipline__name'

    def allowed_badge(self, obj):
        """Affiche un badge colore selon le statut."""
        if obj.allowed:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 2px 8px; border-radius: 3px;">OK</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 2px 8px; border-radius: 3px;">REFUSE</span>'
        )
    allowed_badge.short_description = _('Statut')
    allowed_badge.admin_order_field = 'allowed'

    def resource_info(self, obj):
        """Affiche les informations sur la ressource accedee."""
        if obj.resource_type:
            if obj.resource_id:
                return f"{obj.resource_type} #{obj.resource_id}"
            return obj.resource_type
        return '-'
    resource_info.short_description = _('Ressource')

    def changelist_view(self, request, extra_context=None):
        """Ajoute des statistiques au contexte."""
        extra_context = extra_context or {}

        # Statistiques rapides
        from django.utils import timezone
        from datetime import timedelta

        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)

        qs = DisciplineAccessLog.objects.all()

        extra_context['stats'] = {
            'total': qs.count(),
            'denied_total': qs.filter(allowed=False).count(),
            'denied_24h': qs.filter(allowed=False, timestamp__gte=last_24h).count(),
            'denied_7d': qs.filter(allowed=False, timestamp__gte=last_7d).count(),
        }

        return super().changelist_view(request, extra_context=extra_context)
