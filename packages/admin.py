from django.contrib import admin
from .models import Feature, Package, OrganizationPackage

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('code', 'label', 'description')
    search_fields = ('code', 'label')

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'label', 'price', 'is_active')
    search_fields = ('name', 'label')
    filter_horizontal = ('features',)

@admin.register(OrganizationPackage)
class OrganizationPackageAdmin(admin.ModelAdmin):
    list_display = ('organization', 'package', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'package')
    search_fields = ('organization__name',) 