from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.shop.models import Brand, Supplier


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_origin', 'is_premium', 'is_featured', 'created_at')
    list_filter = ('is_premium', 'is_featured', 'country_origin')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_premium', 'is_featured')
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('name', 'slug', 'description', 'logo')
        }),
        (_("Origine et historique"), {
            'fields': ('country_origin', 'year_established', 'website')
        }),
        (_("Statut et affichage"), {
            'fields': ('is_premium', 'is_featured')
        }),
    )


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_name', 'contact_email', 'is_active')
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'code', 'contact_name', 'contact_email')
    list_editable = ('is_active',)
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('name', 'code', 'is_active')
        }),
        (_("Contact"), {
            'fields': ('contact_name', 'contact_email', 'contact_phone', 'website')
        }),
        (_("Adresse"), {
            'fields': ('address', 'city', 'zip_code', 'country')
        }),
        (_("Termes commerciaux"), {
            'fields': ('payment_terms', 'delivery_terms', 'minimum_order', 'lead_time_days')
        }),
        (_("Notes"), {
            'fields': ('notes',)
        }),
    )

