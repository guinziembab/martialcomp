from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'fee_fixed', 'fee_percentage', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('name', 'type', 'description', 'is_active')
        }),
        (_('Frais'), {
            'fields': ('fee_fixed', 'fee_percentage')
        }),
        (_('Organisation'), {
            'fields': ('organization_content_type', 'organization_id')
        }),
        (_('Configuration API'), {
            'fields': ('api_key', 'api_secret', 'config'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    

class PaymentAttemptAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'payment_method', 'amount', 'currency', 'status', 'initiated_at')
    list_filter = ('status', 'initiated_at')
    search_fields = ('transaction__reference', 'provider_reference', 'error_code')
    readonly_fields = ('id', 'initiated_at', 'updated_at', 'completed_at')
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('transaction', 'payment_method', 'amount', 'fee_amount', 'currency')
        }),
        (_('Statut et dates'), {
            'fields': ('status', 'initiated_at', 'updated_at', 'completed_at')
        }),
        (_('Résultats'), {
            'fields': ('error_code', 'error_message', 'provider_reference')
        }),
        (_('Données techniques'), {
            'fields': ('ip_address', 'user_agent', 'provider_response'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_succeeded', 'mark_as_failed']
    
    def mark_as_succeeded(self, request, queryset):
        updated = 0
        for attempt in queryset.filter(status__in=['initiated', 'processing']):
            attempt.mark_as_succeeded()
            updated += 1
        self.message_user(request, _("{} tentatives de paiement ont été marquées comme réussies.").format(updated))
    mark_as_succeeded.short_description = _("Marquer comme réussies")
    
    def mark_as_failed(self, request, queryset):
        updated = 0
        for attempt in queryset.filter(status__in=['initiated', 'processing']):
            attempt.mark_as_failed(error_code='manual', error_message='Marked as failed by admin')
            updated += 1
        self.message_user(request, _("{} tentatives de paiement ont été marquées comme échouées.").format(updated))
    mark_as_failed.short_description = _("Marquer comme échouées")