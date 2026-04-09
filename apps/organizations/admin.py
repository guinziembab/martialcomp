from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import (
    Organization, Affiliation, OrganizationMember, OrganizationType,
    OrganizationNews, OrganizationGalleryImage, OrganizationVideoLink
)


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
    verbose_name = _("Affiliation Ã  une organisation parente")
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


@admin.register(OrganizationNews)
class OrganizationNewsAdmin(admin.ModelAdmin):
    """Administration des actualités/news des organisations."""
    list_display = (
        'title', 'organization', 'is_published', 'is_featured',
        'published_at', 'author', 'created_at'
    )
    list_filter = ('is_published', 'is_featured', 'organization', 'created_at')
    search_fields = ('title', 'content', 'excerpt', 'organization__name')
    raw_id_fields = ('organization', 'author')
    readonly_fields = ('created_at', 'updated_at', 'slug', 'display_image')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (_("Contenu"), {
            'fields': (
                'organization', 'title', 'slug', 'excerpt', 'content'
            ),
        }),
        (_("Image"), {
            'fields': ('image', 'display_image'),
            'classes': ('collapse',),
        }),
        (_("Publication"), {
            'fields': ('is_published', 'is_featured', 'published_at', 'author'),
        }),
        (_("Metadonnees"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def display_image(self, obj):
        """Affiche l'image dans l'admin."""
        if obj.image:
            return format_html('<img src="{}" height="100" />', obj.image.url)
        return _("Aucune image")
    display_image.short_description = _("Apercu de l'image")

    def save_model(self, request, obj, form, change):
        """Definit l'auteur automatiquement si non defini."""
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(OrganizationGalleryImage)
class OrganizationGalleryImageAdmin(admin.ModelAdmin):
    """Administration de la galerie d'images des organisations."""
    list_display = ('organization', 'description', 'order', 'created_at')
    list_filter = ('organization',)
    search_fields = ('description', 'alt_text', 'organization__name')
    raw_id_fields = ('organization',)
    readonly_fields = ('created_at', 'updated_at', 'display_image')
    ordering = ('organization', 'order')

    fieldsets = (
        (_("Image"), {
            'fields': ('organization', 'image', 'display_image', 'description', 'alt_text'),
        }),
        (_("Affichage"), {
            'fields': ('order',),
        }),
        (_("Metadonnees"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="100" />', obj.image.url)
        return _("Aucune image")
    display_image.short_description = _("Apercu")


@admin.register(OrganizationVideoLink)
class OrganizationVideoLinkAdmin(admin.ModelAdmin):
    """Administration des liens videos des organisations."""
    list_display = ('organization', 'title', 'video_id', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'organization')
    search_fields = ('title', 'description', 'organization__name', 'youtube_url')
    raw_id_fields = ('organization',)
    readonly_fields = ('created_at', 'updated_at', 'video_id', 'thumbnail_url', 'display_thumbnail')
    ordering = ('organization', 'order')

    fieldsets = (
        (_("Video"), {
            'fields': ('organization', 'youtube_url', 'title', 'description'),
        }),
        (_("Informations YouTube (auto)"), {
            'fields': ('video_id', 'thumbnail_url', 'display_thumbnail'),
            'classes': ('collapse',),
        }),
        (_("Affichage"), {
            'fields': ('order', 'is_active'),
        }),
        (_("Metadonnees"), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def display_thumbnail(self, obj):
        if obj.thumbnail_url:
            return format_html('<img src="{}" height="100" />', obj.thumbnail_url)
        return _("Aucune miniature")
    display_thumbnail.short_description = _("Apercu")


# Enregistrer le modele OrganizationType si necessaire
# @admin.register(OrganizationType)
# class OrganizationTypeAdmin(admin.ModelAdmin):
#     list_display = ('name', 'description')
#     search_fields = ('name', 'description')
