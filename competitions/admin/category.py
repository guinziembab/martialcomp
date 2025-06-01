from django.contrib import admin
from competitions.models.categories import CompetitionCategory

@admin.register(CompetitionCategory)
class CompetitionCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'competition', 'competition_type', 'gender', 'min_age', 'max_age', 'min_weight', 'max_weight')
    list_filter = ('competition', 'competition_type', 'gender')
    search_fields = ('name',)
    fieldsets = (
        ('Informations générales', {
            'fields': ('competition', 'competition_type', 'name')
        }),
        ('Catégorie d\'âge', {
            'fields': ('min_age', 'max_age')
        }),
        ('Catégorie de grade', {
            'fields': ('min_grade', 'max_grade')
        }),
        ('Catégorie de poids', {
            'fields': ('min_weight', 'max_weight')
        }),
        ('Genre', {
            'fields': ('gender',)
        }),
    )