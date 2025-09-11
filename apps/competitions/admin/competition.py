from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.core.isolation import OrganizationSecureAdminMixin

try:
    from ..models import Competition, CompetitionType, CompetitionRole
except ImportError:
    # Importation directe depuis le fichier source
    from ..models.competitions import Competition, CompetitionType, CompetitionRole

from apps.competitions.models.permissions import ClubRole, UserClubRole


# Competition Admin avec sécurité par organisation
@admin.register(Competition)
class CompetitionAdmin(OrganizationSecureAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'discipline', 'start_date', 'end_date', 'city', 'status')
    list_filter = ('status', 'discipline', 'start_date')
    search_fields = ('title', 'description', 'city')
    filter_horizontal = ('competition_types',)
    date_hierarchy = 'start_date'
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Informations générales', {
            'fields': ('title', 'slug', 'description', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'registration_deadline')
        }),
        ('Lieu', {
            'fields': ('venue_name', 'address', 'city')
        }),
        ('Configuration', {
            'fields': ('discipline', 'competition_types', 'max_participants', 'logo')
        }),
    )


@admin.register(CompetitionType)
class CompetitionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline', 'team_based', 'weight_category', 'order')
    list_filter = ('discipline', 'team_based', 'weight_category')
    search_fields = ('name', 'description')


@admin.register(CompetitionRole)
class CompetitionRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'description')
    list_filter = ('competition',)
    search_fields = ('name', 'description')


@admin.register(ClubRole)
class ClubRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_organization', 'is_default', 'created_at')
    list_filter = ('is_default',)  # Supprimé 'club' du list_filter
    search_fields = ('name', 'organization__name')  # Modifié 'club__name' en 'organization__name'
    
    def get_organization(self, obj):
        """Retourne l'organisation associée au rÃ´le de club."""
        if hasattr(obj, 'organization') and obj.organization:
            return obj.organization.name
        return _("Aucune organisation")
    
    get_organization.short_description = _("Organisation")
    
    def get_queryset(self, request):
        """Optimise les requÃªtes en préchargeant les relations."""
        queryset = super().get_queryset(request)
        return queryset.select_related('organization')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnalise les formulaires pour les clés étrangères."""
        if db_field.name == "organization":
            from apps.organizations.models import Organization
            kwargs["queryset"] = Organization.objects.filter(
                organization_type__in=['club', 'academy']
            ).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(UserClubRole)
class UserClubRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_organization', 'role', 'assigned_at', 'is_active')
    list_filter = ('role', 'is_active')  # Supprimé 'club' du list_filter
    search_fields = ('user__username', 'user__email', 'organization__name', 'role__name')  # Modifié 'club__name' en 'organization__name'
    
    def get_organization(self, obj):
        """Retourne l'organisation associée au rÃ´le d'utilisateur de club."""
        if hasattr(obj, 'organization') and obj.organization:
            return obj.organization.name
        return _("Aucune organisation")
    
    get_organization.short_description = _("Organisation")
    
    def get_queryset(self, request):
        """Optimise les requÃªtes en préchargeant les relations."""
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'organization', 'role')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnalise les formulaires pour les clés étrangères."""
        if db_field.name == "organization":
            from apps.organizations.models import Organization
            kwargs["queryset"] = Organization.objects.filter(
                organization_type__in=['club', 'academy']
            ).order_by('name')
        elif db_field.name == "role":
            kwargs["queryset"] = ClubRole.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



