from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import Organization, Affiliation, OrganizationMember, OrganizationType


class OrganizationMemberInline(admin.TabularInline):
    """Inline pour afficher les membres d'une organisation dans l'admin."""
    model = OrganizationMember
    extra = 0
    fields = ('user', 'role', 'title', 'is_active')  # Retirez 'join_date' ici
    raw_id_fields = ('user',)
    

class AffiliationParentInline(admin.TabularInline):
    """Inline pour afficher les affiliations parentes d'une organisation."""
    model = Affiliation
    extra = 0
    fk_name = 'child_organization'
    fields = ('parent_organization', 'affiliation_type', 'start_date', 'end_date', 'is_active')
    verbose_name = _("Affiliation à une organisation parente")
    verbose_name_plural = _("Affiliations aux organisations parentes")


class AffiliationChildInline(admin.TabularInline):
    """Inline pour afficher les affiliations enfants d'une organisation."""
    model = Affiliation
    extra = 0
    fk_name = 'parent_organization'
    fields = ('child_organization', 'affiliation_type', 'start_date', 'end_date', 'is_active')
    verbose_name = _("Organisation affiliée")
    verbose_name_plural = _("Organisations affiliées")


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Administration des organisations."""
    list_display = ('name', 'organization_type', 'display_disciplines', 'country', 'city', 'is_active')
    list_filter = ('organization_type', 'is_active', 'country', 'disciplines')
    search_fields = ('name', 'short_name', 'description', 'city')
    readonly_fields = ('created_at', 'updated_at', 'display_logo')
    filter_horizontal = ('disciplines',)
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': (
                'name', 'short_name', 'organization_type', 'description', 
                'disciplines', 'is_active'
            ),
        }),
        (_("Contact et localisation"), {
            'fields': (
                'email', 'phone', 'website', 'country', 'address',
                'city', 'postal_code'
            ),
            'classes': ('collapse',),
        }),
        (_("Médias"), {
            'fields': ('logo', 'display_logo'),
            'classes': ('collapse',),
        }),
        (_("Métadonnées"), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [
        OrganizationMemberInline,
        AffiliationParentInline,
        AffiliationChildInline,
    ]
    
    def display_disciplines(self, obj):
        """Affiche les disciplines sous forme de liste."""
        return ", ".join([discipline.name for discipline in obj.disciplines.all()[:3]]) + (
            " ..." if obj.disciplines.count() > 3 else ""
        )
    display_disciplines.short_description = _("Disciplines")
    
    def display_logo(self, obj):
        """Affiche le logo dans l'admin."""
        if obj.logo:
            return format_html('<img src="{}" height="100" />', obj.logo.url)
        return _("Aucun logo")
    display_logo.short_description = _("Aperçu du logo")


@admin.register(Affiliation)
class AffiliationAdmin(admin.ModelAdmin):
    """Administration des affiliations entre organisations."""
    list_display = (
        'id', 'child_organization', 'affiliation_type', 
        'parent_organization', 'start_date', 'is_active'
    )
    list_filter = ('affiliation_type', 'is_active')
    search_fields = (
        'child_organization__name', 'parent_organization__name',
        'certification_number', 'notes'
    )
    raw_id_fields = ('child_organization', 'parent_organization')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_("Information d'affiliation"), {
            'fields': (
                'child_organization', 'parent_organization', 'affiliation_type',
                'start_date', 'end_date', 'is_active'
            ),
        }),
        (_("Détails supplémentaires"), {
            'fields': ('certification_number', 'notes'),
            'classes': ('collapse',),
        }),
        (_("Métadonnées"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Administration des membres d'organisations."""
    list_display = (
        'user', 'organization', 'role', 'title', 
        'join_date', 'is_active'
    )
    list_filter = ('role', 'is_active', 'join_date')
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name',
        'organization__name', 'title', 'notes'
    )
    raw_id_fields = ('user', 'organization')
    readonly_fields = ('created_at', 'updated_at', 'join_date')  # Ajoutez 'join_date' ici
    
    fieldsets = (
        (_("Membre et Organisation"), {
            'fields': ('user', 'organization', 'role', 'title', 'is_active'),
        }),
        (_("Dates"), {
            'fields': ('join_date', 'end_date'),  # Gardez 'join_date' car il est maintenant en readonly_fields
            'classes': ('collapse',),
        }),
        (_("Permissions"), {
            'fields': ('can_manage_members', 'can_edit_organization', 'can_manage_competitions'),
            'classes': ('collapse',),
        }),
        (_("Notes"), {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
        (_("Métadonnées"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# Enregistrer le modèle OrganizationType si nécessaire
# @admin.register(OrganizationType)
# class OrganizationTypeAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description')
#     search_fields = ('name', 'description')