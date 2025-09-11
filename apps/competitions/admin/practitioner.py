from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.core.isolation import OrganizationSecureAdminMixin
from ..models import Practitioner

@admin.register(Practitioner)
class PractitionerAdmin(OrganizationSecureAdminMixin, admin.ModelAdmin):
    list_display = (
        'full_name', 
        'get_organization',  # Remplacé 'club' par une méthode
        'birth_date', 
        'age', 
        'grade', 
        'get_disciplines',
        'license_number', 
        'medical_certificate_date'
    )
    list_filter = (
        'organization',  # Remplacé 'club' par 'organization'
        'grade',
        'disciplines',
        'gender',
        'status'
    )
    search_fields = (
        'first_name', 
        'last_name', 
        'license_number',
        'email',
        'disciplines__name',
        'organization__name'  # Ajouté pour la recherche par nom d'organisation
    )
    
    # Configuration des champs pour l'édition
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('user', 'first_name', 'last_name', 'birth_date', 'gender')
        }),
        ('Informations sportives', {
            'fields': ('organization', 'disciplines', 'grade', 'license_number', 'medical_certificate_date'),  # Remplacé 'club' par 'organization'
            'description': 'Gérez les disciplines pratiquées et le grade du pratiquant.'
        }),
        ('Documents', {
            'fields': ('medical_certificate', 'parental_authorization'),
            'classes': ('collapse',)  # Section repliable
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'address', 'city', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Contact d\'urgence', {
            'fields': ('emergency_contact_name', 'emergency_contact_relation', 
                      'emergency_contact_phone', 'emergency_contact_email'),
            'classes': ('collapse',)
        }),
        ('Informations médicales', {
            'fields': ('blood_group', 'weight', 'height', 'allergies', 'medical_conditions'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('age',)
    
    # Interface améliorée pour les disciplines
    filter_horizontal = ('disciplines',)  # Widget pour sélection multiple
    
    # Méthode pour afficher l'organisation dans la liste
    def get_organization(self, obj):
        """Affiche l'organisation associée au pratiquant."""
        if hasattr(obj, 'organization') and obj.organization:
            return obj.organization.name
        return '-'
    get_organization.short_description = 'Organisation'
    get_organization.admin_order_field = 'organization'
    
    # Méthode pour afficher les disciplines dans la liste
    def get_disciplines(self, obj):
        """Affiche la liste des disciplines pratiquées"""
        disciplines = obj.disciplines.all()
        if disciplines:
            return ', '.join([d.name for d in disciplines])
        return '-'
    get_disciplines.short_description = 'Disciplines'
    get_disciplines.admin_order_field = 'disciplines'
    
    # Améliorer l'affichage du nom complet
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Nom complet'
    full_name.admin_order_field = 'last_name'
    
    # Configuration des requÃªtes optimisées
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('organization', 'user')  # Remplacé 'club' par 'organization'
        queryset = queryset.prefetch_related('disciplines')
        return queryset
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Personnalise les formulaires pour les clés étrangères."""
        if db_field.name == "organization":
            from apps.organizations.models import Organization
            kwargs["queryset"] = Organization.objects.filter(
                organization_type__in=['club', 'academy']
            ).order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    # Actions personnalisées (optionnel)
    actions = ['export_as_csv']
    
    def export_as_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="practitioners.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Nom', 'Prénom', 'Organisation', 'Disciplines', 'Grade', 'Licence', 'Date naissance'])  # Remplacé 'Club' par 'Organisation'
        
        for practitioner in queryset:
            disciplines = ', '.join([d.name for d in practitioner.disciplines.all()])
            writer.writerow([
                practitioner.last_name,
                practitioner.first_name,
                practitioner.organization.name if practitioner.organization else '',  # Remplacé club par organization
                disciplines,
                practitioner.grade or '',
                practitioner.license_number or '',
                practitioner.birth_date
            ])
        
        return response
    export_as_csv.short_description = "Exporter les pratiquants sélectionnés vers CSV"

