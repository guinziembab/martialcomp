from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from ..models import Club

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'get_disciplines', 'get_organization', 'owner', 'contact_email', 'is_active')
    list_filter = ('is_active', 'city', 'main_discipline')
    search_fields = ('name', 'address', 'city', 'postal_code', 'contact_email', 'owner__username')
    filter_horizontal = ('disciplines',)  # Pour les relations ManyToMany
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('name', 'description', 'logo', 'logo_preview', 'banner', 'banner_preview', 'is_active')
        }),
        (_('Adresse'), {
            'fields': ('address', 'city', 'postal_code')
        }),
        (_('Contact'), {
            'fields': ('contact_phone', 'contact_email', 'website')
        }),
        (_('Affiliations'), {
            'fields': ('disciplines', 'main_discipline', 'organization')
        }),
        (_('Équipements'), {
            'fields': ('has_equipment', 'has_changing_rooms', 'has_showers', 'has_parking'),
            'classes': ('collapse',),  # Pour rendre cette section repliable
        }),
        (_('Tranches d\'âge acceptées'), {
            'fields': ('accepts_children', 'accepts_teenagers', 'accepts_adults', 'accepts_seniors'),
            'classes': ('collapse',),  # Pour rendre cette section repliable
        }),
        (_('Horaires'), {
            'fields': ('training_hours',)
        }),
        (_('Propriétaire'), {
            'fields': ('owner',)
        }),
    )
    
    # Rendre les images clickables pour les voir en taille réelle
    readonly_fields = ('logo_preview', 'banner_preview')
    
    def logo_preview(self, obj):
        """Affiche une prévisualisation du logo"""
        if obj.logo:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="150" height="150" style="object-fit: contain;" /></a>', obj.logo.url)
        return _("Aucun logo")
    
    logo_preview.short_description = _("Aperçu du logo")
    
    def banner_preview(self, obj):
        """Affiche une prévisualisation de la bannière"""
        if obj.banner:
            return format_html('<a href="{0}" target="_blank"><img src="{0}" width="300" height="100" style="object-fit: contain;" /></a>', obj.banner.url)
        return _("Aucune bannière")
    
    banner_preview.short_description = _("Aperçu de la bannière")
    
    def get_disciplines(self, obj):
        """Retourne la liste des disciplines du club"""
        return ", ".join([d.name for d in obj.disciplines.all()])
    
    get_disciplines.short_description = _("Disciplines")
    
    def get_organization(self, obj):
        """Retourne l'organisation associée au club"""
        if hasattr(obj, 'organization') and obj.organization:
            return obj.organization.name
        return _("Aucune organisation")
    
    get_organization.short_description = _("Organisation")
    
    def get_queryset(self, request):
        """Optimisation des requêtes en préchargeant les relations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('owner', 'organization', 'main_discipline').prefetch_related('disciplines')
    
    # Vous pouvez également ajouter une action pour synchroniser les clubs vers Organization
    def sync_to_organization(self, request, queryset):
        """Synchronise les clubs sélectionnés vers le modèle Organization"""
        count = 0
        for club in queryset:
            # Utilise la méthode save qui contient la logique de synchronisation
            club.save()
            count += 1
        
        self.message_user(
            request, 
            _("%(count)d clubs ont été synchronisés avec le modèle Organization.") % {'count': count}
        )
    
    sync_to_organization.short_description = _("Synchroniser vers Organization")
    actions = ['sync_to_organization']