# grades/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django import forms
from django.http import JsonResponse
from django.views.decorators.http import require_GET
# from modeltranslation.admin import TranslationAdmin  # Temporairement commenté

# Import depuis la nouvelle application grades
from .models import (
    Grade, 
    GradeCategory, 
    PractitionerGrade, 
    GradeRequirement,
    GradeExam,
    GradeExamRegistration
)
from apps.competitions.models import Discipline, Practitioner

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
class GradeAdmin(admin.ModelAdmin):  # Temporairement changé de TranslationAdmin Ã  ModelAdmin
    form = GradeAdminForm
    list_display = ('name', 'discipline', 'category', 'level', 'color_display', 'image_preview_small', 'is_dan_grade', 'is_active')
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
        (_("Image du grade"), {
            'fields': ('image', 'image_preview', 'icon'),
            'description': _("Téléchargez une image pour représenter ce grade (PNG, JPG, SVG - max 500KB, recommandé 100x100px)")
        }),
        (_("Critères d'accès"), {
            'fields': ('min_age', 'min_time_in_previous_grade', 'requirements_text')
        }),
        (_("Options"), {
            'fields': ('is_active',)
        }),
    )
    readonly_fields = ('image_preview',)

    # Script JavaScript pour le filtrage dynamique des catégories
    class Media:
        js = ('admin/js/grade_category_filter.js',)

    def image_preview(self, obj):
        """Affiche une prévisualisation de l'image du grade dans le formulaire d'admin."""
        if obj.image:
            return format_html(
                '<div style="margin: 10px 0;">'
                '<img src="{}" style="max-width: 100px; max-height: 100px; border: 2px solid {}; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"/>'
                '<p style="margin-top: 5px; font-size: 12px; color: #666;">Taille recommandée: 100x100px</p>'
                '</div>',
                obj.image.url,
                obj.color_code or '#ddd'
            )
        color = obj.color_code or '#6c757d'
        initials = obj.initials if obj.pk else 'GR'
        return format_html(
            '<div style="width: 100px; height: 100px; background-color: {}; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 24px;">{}</div>'
            '<p style="margin-top: 5px; font-size: 12px; color: #666;">Aucune image - Affichage des initiales par défaut</p>',
            color, initials
        )
    image_preview.short_description = _("Prévisualisation")

    def image_preview_small(self, obj):
        """Affiche une petite prévisualisation dans la liste admin."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 4px; object-fit: cover; border: 1px solid {};"/>',
                obj.image.url,
                obj.color_code or '#ddd'
            )
        color = obj.color_code or '#6c757d'
        return format_html(
            '<div style="width: 30px; height: 30px; background-color: {}; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 10px;">{}</div>',
            color, obj.initials
        )
    image_preview_small.short_description = _("Image")

    def color_display(self, obj):
        if obj.color_code:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ddd; display: inline-block;"></div> {}',
                obj.color_code, obj.color
            )
        return obj.color
    color_display.short_description = _("Couleur")

@admin.register(GradeCategory)
class GradeCategoryAdmin(admin.ModelAdmin):  # Temporairement changé de TranslationAdmin Ã  ModelAdmin
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

