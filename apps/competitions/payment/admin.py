from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Payment, PaymentConfig, PaymentWebhook, PaymentRefund


@admin.register(PaymentConfig)
class PaymentConfigAdmin(admin.ModelAdmin):
    list_display = ['organization', 'gateway', 'enabled', 'test_mode', 'created_at']
    list_filter = ['gateway', 'enabled', 'test_mode', 'created_at']
    search_fields = ['organization__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organisation', {
            'fields': ('organization',)
        }),
        ('Configuration générale', {
            'fields': ('gateway', 'enabled', 'test_mode')
        }),
        ('Stripe', {
            'fields': ('stripe_api_key', 'stripe_webhook_secret'),
            'classes': ('collapse',)
        }),
        ('PayPal', {
            'fields': ('paypal_client_id', 'paypal_client_secret', 'paypal_mode'),
            'classes': ('collapse',)
        }),
        ('Orange Money', {
            'fields': ('orange_money_merchant_id', 'orange_money_api_key'),
            'classes': ('collapse',)
        }),
        ('M-Pesa', {
            'fields': ('mpesa_consumer_key', 'mpesa_consumer_secret', 'mpesa_business_shortcode'),
            'classes': ('collapse',)
        }),
        ('Alipay', {
            'fields': ('alipay_app_id', 'alipay_private_key', 'alipay_public_key'),
            'classes': ('collapse',)
        }),
        ('WeChat Pay', {
            'fields': ('wechat_app_id', 'wechat_mch_id', 'wechat_api_key'),
            'classes': ('collapse',)
        }),
        ('Fawry', {
            'fields': ('fawry_merchant_code', 'fawry_security_key'),
            'classes': ('collapse',)
        }),
        ('STC Pay', {
            'fields': ('stc_merchant_id', 'stc_api_key'),
            'classes': ('collapse',)
        }),
        ('Paramètres', {
            'fields': ('supported_currencies', 'minimum_amount', 'maximum_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'organization', 'user', 'amount', 'currency', 
        'gateway', 'status', 'created_at', 'paid_at'
    ]
    list_filter = [
        'status', 'gateway', 'currency', 'created_at', 'paid_at',
        'organization'
    ]
    search_fields = [
        'id', 'gateway_payment_id', 'customer_email', 
        'customer_name', 'description'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'paid_at', 'organization_link'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'organization_link', 'user', 'gateway', 'gateway_payment_id')
        }),
        ('Paiement', {
            'fields': ('amount', 'currency', 'description', 'status')
        }),
        ('Client', {
            'fields': ('customer_email', 'customer_name', 'customer_phone')
        }),
        ('Métadonnées', {
            'fields': ('metadata', 'success_url', 'cancel_url'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )
    
    def organization_link(self, obj):
        if obj.organization:
            url = reverse('admin:organizations_organization_change', args=[obj.organization.id])
            return format_html('<a href="{}">{}</a>', url, obj.organization.name)
        return '-'
    organization_link.short_description = 'Organisation'
    organization_link.admin_order_field = 'organization__name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'user')
    
    actions = ['mark_as_succeeded', 'mark_as_failed', 'mark_as_cancelled']
    
    def mark_as_succeeded(self, request, queryset):
        updated = queryset.update(status='succeeded')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme réussi(s).')
    mark_as_succeeded.short_description = "Marquer comme réussi"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme échoué(s).')
    mark_as_failed.short_description = "Marquer comme échoué"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} paiement(s) marqué(s) comme annulé(s).')
    mark_as_cancelled.short_description = "Marquer comme annulé"


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    list_display = ['payment', 'gateway', 'event_type', 'processed', 'created_at']
    list_filter = ['gateway', 'event_type', 'processed', 'created_at']
    search_fields = ['payment__id', 'gateway', 'event_type']
    readonly_fields = ['created_at', 'processed_at']
    
    fieldsets = (
        ('Informations', {
            'fields': ('payment', 'gateway', 'event_type')
        }),
        ('Données', {
            'fields': ('event_data',),
            'classes': ('collapse',)
        }),
        ('Statut', {
            'fields': ('processed', 'processed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processed']
    
    def mark_as_processed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(processed=True, processed_at=timezone.now())
        self.message_user(request, f'{updated} webhook(s) marqué(s) comme traité(s).')
    mark_as_processed.short_description = "Marquer comme traité"


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    list_display = [
        'payment', 'amount', 'currency', 'status', 'created_at', 'processed_at'
    ]
    list_filter = ['status', 'currency', 'created_at', 'processed_at']
    search_fields = ['payment__id', 'gateway_refund_id', 'reason']
    readonly_fields = ['created_at', 'processed_at']
    
    fieldsets = (
        ('Informations', {
            'fields': ('payment', 'amount', 'currency', 'reason')
        }),
        ('Statut', {
            'fields': ('status', 'gateway_refund_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment') 
