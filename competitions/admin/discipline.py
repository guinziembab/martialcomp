from django.contrib import admin
from ..models import Discipline

@admin.register(Discipline)
class DisciplineAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_origin', 'is_active')
    list_filter = ('is_active', 'country_origin')
    search_fields = ('name', 'description')