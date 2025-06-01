from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from ..models import CompetitionRegistration

class CompetitionRegistrationResource(resources.ModelResource):
    club = fields.Field(column_name='club', attribute='practitioner__club__name')
    first_name = fields.Field(column_name='prénom', attribute='practitioner__first_name')
    last_name = fields.Field(column_name='nom', attribute='practitioner__last_name')
    birth_date = fields.Field(column_name='date_naissance', attribute='practitioner__birth_date')
    grade = fields.Field(column_name='grade', attribute='practitioner__grade')
    age = fields.Field(column_name='age')
    
    def dehydrate_age(self, registration):
        return registration.practitioner.age
    
    class Meta:
        model = CompetitionRegistration
        fields = ('id', 'club', 'first_name', 'last_name', 'birth_date', 'grade', 'age',
                 'is_competitor', 'is_technical_judge', 'is_combat_referee', 'is_volunteer', 
                 'is_coach', 'status')
        export_order = fields

@admin.register(CompetitionRegistration)
class CompetitionRegistrationAdmin(ImportExportModelAdmin):
    resource_class = CompetitionRegistrationResource
    list_display = ('practitioner', 'competition', 'is_competitor', 'is_technical_judge', 
                   'is_combat_referee', 'status', 'registration_date')
    list_filter = ('competition', 'status', 'is_competitor', 'is_technical_judge', 'is_combat_referee')
    search_fields = ('practitioner__first_name', 'practitioner__last_name', 'competition__title')
    filter_horizontal = ('competition_types', 'categories', 'roles')
    fieldsets = (
        ('Informations générales', {
            'fields': ('practitioner', 'competition', 'status')
        }),
        ('Types et catégories', {
            'fields': ('competition_types', 'categories')
        }),
        ('Rôles', {
            'fields': ('roles', 'is_technical_judge', 'is_combat_referee')
        }),
    )
    readonly_fields = ('registration_date',)
    
    def get_export_queryset(self, request):
        # Filtrer par compétition si spécifié dans l'URL
        competition_id = request.GET.get('competition_id')
        queryset = super().get_export_queryset(request)
        
        if competition_id:
            queryset = queryset.filter(competition_id=competition_id)
            
        return queryset