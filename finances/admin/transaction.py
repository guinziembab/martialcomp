from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('reference', 'type', 'amount', 'currency', 'date_created', 'status')
    list_filter = ('status', 'type', 'date_created')
    search_fields = ('reference', 'description')
    readonly_fields = ('id', 'reference', 'date_created', 'date_updated', 'date_validated')
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('reference', 'type', 'amount', 'currency', 'description')
        }),
        (_('Statut et dates'), {
            'fields': ('status', 'date_created', 'date_updated', 'date_validated')
        }),
        (_('Catégorisation'), {
            'fields': ('category',)
        }),
        (_('Relations'), {
            'fields': ('payment_method', 'financial_account', 'invoice', 'created_by', 'validated_by')
        }),
        (_('Entités liées'), {
            'fields': ('source_content_type', 'source_object_id', 'destination_content_type', 'destination_object_id')
        }),
        (_('Documents'), {
            'fields': ('receipt_file',)
        }),
        (_('Métadonnées'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    actions = ['validate_transactions', 'reject_transactions', 'cancel_transactions']
    
    def validate_transactions(self, request, queryset):
        updated = 0
        for transaction in queryset.filter(status='pending'):
            transaction.validate(request.user)
            updated += 1
        self.message_user(request, _("{} transactions ont été validées.").format(updated))
    validate_transactions.short_description = _("Valider les transactions sélectionnées")
    
    def reject_transactions(self, request, queryset):
        updated = 0
        for transaction in queryset.filter(status='pending'):
            transaction.reject(request.user)
            updated += 1
        self.message_user(request, _("{} transactions ont été rejetées.").format(updated))
    reject_transactions.short_description = _("Rejeter les transactions sélectionnées")
    
    def cancel_transactions(self, request, queryset):
        updated = 0
        for transaction in queryset.filter(status__in=['pending', 'validated']):
            transaction.cancel(request.user)
            updated += 1
        self.message_user(request, _("{} transactions ont été annulées.").format(updated))
    cancel_transactions.short_description = _("Annuler les transactions sélectionnées")