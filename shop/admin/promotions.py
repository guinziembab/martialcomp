from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from shop.models import Coupon, Promotion


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'type', 'value_display', 'is_active', 'usage_count', 'is_valid_now', 'start_date', 'end_date')
    list_filter = ('type', 'is_active', 'is_for_first_order')
    search_fields = ('code', 'description')
    list_editable = ('is_active',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('code', 'description', 'is_active')
        }),
        (_("Réduction"), {
            'fields': ('type', 'value', 'min_purchase_amount', 'max_discount_amount')
        }),
        (_("Période de validité"), {
            'fields': ('start_date', 'end_date')
        }),
        (_("Limites d'utilisation"), {
            'fields': ('usage_limit', 'usage_count', 'is_for_first_order')
        }),
        (_("Restrictions"), {
            'fields': ('applicable_products', 'applicable_categories')
        }),
    )
    
    filter_horizontal = ('applicable_products', 'applicable_categories')
    readonly_fields = ('usage_count',)
    
    def value_display(self, obj):
        if obj.type == 'percentage':
            return f"{obj.value} %"
        else:
            return f"{obj.value} €"
    value_display.short_description = _("Valeur")
    
    def is_valid_now(self, obj):
        return obj.is_valid
    is_valid_now.boolean = True
    is_valid_now.short_description = _("Valide maintenant")


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_type', 'discount_value_display', 'is_active', 'status', 'start_date', 'end_date')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('name', 'description', 'is_active')
        }),
        (_("Réduction"), {
            'fields': ('discount_type', 'discount_value')
        }),
        (_("Période de validité"), {
            'fields': ('start_date', 'end_date')
        }),
        (_("Éléments concernés"), {
            'fields': ('products', 'categories', 'brands')
        }),
        (_("Affichage"), {
            'fields': ('banner_image', 'highlight_color', 'priority')
        }),
    )
    
    filter_horizontal = ('products', 'categories', 'brands')
    
    def discount_value_display(self, obj):
        if obj.discount_type == 'percentage':
            return f"{obj.discount_value} %"
        else:
            return f"{obj.discount_value} €"
    discount_value_display.short_description = _("Valeur de la remise")
    
    def status(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return _("Inactive")
        elif now < obj.start_date:
            return _("À venir")
        elif now > obj.end_date:
            return _("Terminée")
        else:
            return _("En cours")
    status.short_description = _("Statut")