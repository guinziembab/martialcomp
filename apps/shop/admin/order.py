from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from apps.shop.models import Order, OrderItem, Address


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'product_sku', 'variation_description', 'price', 'quantity', 'discount', 'tax_rate', 'subtotal', 'total')
    readonly_fields = ('subtotal', 'total')
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def subtotal(self, obj):
        return f"{obj.subtotal} â‚¬"
    subtotal.short_description = _("Sous-total")
    
    def total(self, obj):
        return f"{obj.total} â‚¬"
    total.short_description = _("Total")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user_link', 'status', 'total_display', 'payment_method', 'is_paid', 'created_at')
    list_filter = ('status', 'payment_method', 'shipping_method', 'is_paid')
    search_fields = ('order_number', 'user__username', 'user__email', 'shipping_address__first_name', 'shipping_address__last_name')
    readonly_fields = ('order_number', 'created_at', 'id')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_("Informations de commande"), {
            'fields': ('order_number', 'id', 'user', 'club', 'status', 'created_at')
        }),
        (_("Montants"), {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'discount_amount', 'total')
        }),
        (_("Paiement"), {
            'fields': ('payment_method', 'payment_id', 'is_paid', 'paid_at')
        }),
        (_("Livraison"), {
            'fields': ('shipping_method', 'tracking_number', 'estimated_delivery_date', 'shipped_at', 'delivered_at')
        }),
        (_("Adresses"), {
            'fields': ('billing_address', 'shipping_address')
        }),
        (_("Notes"), {
            'fields': ('customer_notes', 'admin_notes')
        }),
        (_("Facturation"), {
            'fields': ('invoice_number', 'invoice_date', 'invoice_pdf'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [OrderItemInline]
    
    def total_display(self, obj):
        return f"{obj.total} â‚¬"
    total_display.short_description = _("Total")
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return _("Utilisateur inconnu")
    user_link.short_description = _("Client")
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'club', 'billing_address', 'shipping_address')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'city', 'country', 'is_default_shipping', 'is_default_billing')
    list_filter = ('country', 'is_default_shipping', 'is_default_billing')
    search_fields = ('first_name', 'last_name', 'address_line1', 'city', 'postal_code')
    
    fieldsets = (
        (_("Utilisateur"), {
            'fields': ('user', 'is_default_shipping', 'is_default_billing')
        }),
        (_("Contact"), {
            'fields': ('first_name', 'last_name', 'company', 'email', 'phone')
        }),
        (_("Adresse"), {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country')
        }),
        (_("Livraison"), {
            'fields': ('delivery_instructions',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

