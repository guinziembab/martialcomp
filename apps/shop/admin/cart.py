from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.shop.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ('product', 'variation', 'quantity', 'price_at_addition', 'unit_price', 'line_total')
    readonly_fields = ('unit_price', 'line_total')
    
    def unit_price(self, obj):
        return f"{obj.unit_price} â‚¬"
    unit_price.short_description = _("Prix unitaire")
    
    def line_total(self, obj):
        return f"{obj.line_total} â‚¬"
    line_total.short_description = _("Total ligne")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'item_count', 'subtotal_display', 'created_at', 'updated_at', 'converted_to_order')
    list_filter = ('converted_to_order', 'created_at')
    search_fields = ('user__username', 'user__email', 'session_id')
    readonly_fields = ('created_at', 'updated_at', 'subtotal_display', 'item_count')
    
    fieldsets = (
        (_("Informations de base"), {
            'fields': ('user', 'session_id', 'created_at', 'updated_at')
        }),
        (_("Résumé"), {
            'fields': ('item_count', 'subtotal_display')
        }),
        (_("Conversion"), {
            'fields': ('converted_to_order', 'order')
        }),
    )
    
    inlines = [CartItemInline]
    
    def subtotal_display(self, obj):
        return f"{obj.subtotal} â‚¬"
    subtotal_display.short_description = _("Sous-total")
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = _("Nombre d'articles")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'order').prefetch_related('items')


