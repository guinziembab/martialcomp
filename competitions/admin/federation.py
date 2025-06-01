from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from ..models import Federation

@admin.register(Federation)
class FederationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'city', 'is_active', 'display_logo', 'contact_email', 'display_disciplines')
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'description', 'country', 'city')
    readonly_fields = ('created_at', 'updated_at', 'display_logo_large', 'organization_link')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('disciplines',)  # Interface améliorée pour sélectionner les disciplines
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('name', 'slug', 'description', 'logo', 'display_logo_large', 'is_active')
        }),
        (_('Disciplines'), {
            'fields': ('disciplines',)
        }),
        (_('Adresse et contact'), {
            'fields': ('country', 'address', 'city', 'postal_code', 'website', 'contact_email', 'contact_phone')
        }),
        (_('Propriétaire'), {
            'fields': ('owner',)
        }),
        (_('Informations supplémentaires'), {
            'fields': ('founding_date', 'created_at', 'updated_at')
        }),
        (_('Liaison avec Organization'), {
            'fields': ('organization_link',),
            'classes': ('collapse',),
        }),
    )
    
    def display_logo(self, obj):
        """Affiche une miniature du logo dans la liste d'admin."""
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.logo.url)
        return "-"
    display_logo.short_description = _("Logo")
    
    def display_logo_large(self, obj):
        """Affiche une version plus grande du logo dans le formulaire d'admin."""
        if obj.logo:
            return format_html('<img src="{}" width="200" style="max-height: 200px; object-fit: contain;" />', obj.logo.url)
        return _("Aucun logo")
    display_logo_large.short_description = _("Aperçu du logo")
    
    def display_disciplines(self, obj):
        """Affiche les disciplines associées à la fédération."""
        return ", ".join([discipline.name for discipline in obj.disciplines.all()])
    display_disciplines.short_description = _("Disciplines")
    
    def organization_link(self, obj):
        """Affiche un lien vers l'organisation correspondante."""
        from organizations.models import Organization
        try:
            organization = Organization.objects.get(old_federation_id=obj.id)
            return format_html(
                '<a href="{}">{}</a>',
                f"/admin/organizations/organization/{organization.id}/change/",
                f"Organization: {organization.name}"
            )
        except Organization.DoesNotExist:
            return _("Aucune organisation correspondante")
    organization_link.short_description = _("Organisation liée")
    
    def get_queryset(self, request):
        """Optimise les requêtes en préchargeant les relations."""
        queryset = super().get_queryset(request)
        return queryset.select_related('owner').prefetch_related('disciplines')
    
    # Actions administratives pour faciliter la migration
    def sync_to_organization(self, request, queryset):
        """Synchronise les fédérations sélectionnées vers le modèle Organization."""
        count = 0
        for federation in queryset:
            # Utilise la méthode save qui contient la logique de synchronisation
            federation.save()
            count += 1
        
        self.message_user(
            request, 
            _("%(count)d fédérations ont été synchronisées avec le modèle Organization.") % {'count': count}
        )
    
    sync_to_organization.short_description = _("Synchroniser vers Organization")
    
    def mark_as_national_federation(self, request, queryset):
        """Marque les organisations correspondantes comme fédérations nationales."""
        from organizations.models import Organization
        count = 0
        for federation in queryset:
            try:
                organization = Organization.objects.get(old_federation_id=federation.id)
                organization.organization_type = 'national_federation'
                organization.save()
                count += 1
            except Organization.DoesNotExist:
                continue
        
        self.message_user(
            request, 
            _("%(count)d organisations ont été marquées comme fédérations nationales.") % {'count': count}
        )
    
    mark_as_national_federation.short_description = _("Marquer comme fédération nationale")
    
    actions = ['sync_to_organization', 'mark_as_national_federation']