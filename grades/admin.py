# grades/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django import forms
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# Import depuis la nouvelle application grades
from .models import (
    Grade, 
    GradeCategory, 
    PractitionerGrade, 
    GradeRequirement,
    GradeExam,
    GradeExamRegistration
)
from competitions.models import Discipline, Practitioner

class GradeRequirementInline(admin.TabularInline):
    model = GradeRequirement
    extra = 1
    fields = ('name', 'description', 'is_mandatory', 'order')

class GradeAdminForm(forms.ModelForm):
    # Champ pour filtrer dynamiquement les catégories par discipline
    class Meta:
        model = Grade
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si on édite un grade existant, filtrer les catégories par discipline
        if self.instance and self.instance.pk and self.instance.discipline:
            self.fields['category'].queryset = GradeCategory.objects.filter(
                discipline=self.instance.discipline
            )
        else:
            # Pour un nouveau grade, on peut sélectionner toutes les catégories
            # La sélection sera filtrée dynamiquement par JavaScript
            pass

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    form = GradeAdminForm
    list_display = ('name', 'discipline', 'category', 'level', 'color_display', 'is_dan_grade', 'is_active')
    list_filter = ('discipline', 'category', 'is_dan_grade', 'is_active')
    search_fields = ('name', 'discipline__name', 'category__name')
    ordering = ('discipline', 'level', 'name')
    inlines = [GradeRequirementInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'discipline', 'category')
        }),
        (_("Détails du grade"), {
            'fields': ('color', 'color_code', 'level', 'order', 'is_dan_grade')
        }),
        (_("Critères d'accès"), {
            'fields': ('min_age', 'min_time_in_previous_grade', 'requirements_text')  # Modification ici de requirements à requirements_text
        }),
        (_("Options"), {
            'fields': ('is_active',)
        }),
    )
    
    # Script JavaScript pour le filtrage dynamique des catégories
    class Media:
        js = ('admin/js/grade_category_filter.js',)
    
    def color_display(self, obj):
        if obj.color_code:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ddd; display: inline-block;"></div> {}',
                obj.color_code, obj.color
            )
        return obj.color
    color_display.short_description = _("Couleur")

@admin.register(GradeCategory)
class GradeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'discipline', 'order', 'is_active')
    list_filter = ('discipline', 'is_active')
    search_fields = ('name', 'discipline__name')
    ordering = ('discipline', 'order', 'name')

@admin.register(PractitionerGrade)
class PractitionerGradeAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'grade', 'discipline', 'date_obtained', 'is_current')
    list_filter = ('is_current', 'discipline', 'grade', 'date_obtained')
    search_fields = ('practitioner__first_name', 'practitioner__last_name', 'grade__name')
    date_hierarchy = 'date_obtained'
    raw_id_fields = ('practitioner', 'grade')
    
    fieldsets = (
        (None, {
            'fields': ('practitioner', 'grade', 'discipline')
        }),
        (_("Détails d'obtention"), {
            'fields': ('date_obtained', 'date_expiry', 'awarded_by', 'location')
        }),
        (_("Documentation"), {
            'fields': ('certificate_number', 'certificate_file', 'notes')
        }),
        (_("Statut"), {
            'fields': ('is_current',)
        }),
    )

@admin.register(GradeRequirement)
class GradeRequirementAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'is_mandatory', 'order')
    list_filter = ('grade__discipline', 'is_mandatory')
    search_fields = ('name', 'grade__name')
    ordering = ('grade', 'order')

@admin.register(GradeExam)
class GradeExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'discipline', 'date', 'location', 'status', 'registered_count')
    list_filter = ('discipline', 'status', 'date')
    search_fields = ('title', 'location', 'discipline__name')
    date_hierarchy = 'date'
    filter_horizontal = ('available_grades',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'discipline', 'description')
        }),
        (_("Programmation"), {
            'fields': ('date', 'location', 'registration_deadline', 'max_participants')
        }),
        (_("Configuration"), {
            'fields': ('available_grades', 'examiners', 'fee')
        }),
        (_("Statut"), {
            'fields': ('status', 'notes')
        }),
    )
    
    def registered_count(self, obj):
        return obj.registrations.count()
    registered_count.short_description = _("Inscrits")

@admin.register(GradeExamRegistration)
class GradeExamRegistrationAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'exam', 'target_grade', 'status', 'registration_date', 'payment_confirmed')
    list_filter = ('status', 'payment_confirmed', 'exam')
    search_fields = ('practitioner__first_name', 'practitioner__last_name', 'exam__title')
    date_hierarchy = 'registration_date'
    raw_id_fields = ('practitioner', 'exam', 'target_grade')
    
    fieldsets = (
        (None, {
            'fields': ('exam', 'practitioner', 'target_grade')
        }),
        (_("Statut"), {
            'fields': ('status', 'payment_confirmed', 'score')
        }),
        (_("Résultats"), {
            'fields': ('examiner_notes', 'certificate_issued', 'certificate_number')
        }),
    )

# Vue API pour le filtrage des catégories par discipline
@require_GET
def categories_by_discipline(request):
    """Vue API pour récupérer les catégories d'une discipline."""
    discipline_id = request.GET.get('discipline_id')
    
    if not discipline_id:
        return JsonResponse({'categories': []})
    
    categories = GradeCategory.objects.filter(
        discipline_id=discipline_id,
        is_active=True
    ).order_by('order', 'name')
    
    data = [{'id': cat.id, 'name': cat.name} for cat in categories]
    
    return JsonResponse({'categories': data})