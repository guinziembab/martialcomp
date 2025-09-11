from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from apps.finances.models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'tax_rate', 'subtotal', 'tax_amount', 'total')
    readonly_fields = ('subtotal', 'tax_amount', 'total')


class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'issued_date', 'due_date', 'total', 'currency', 'status')
    list_filter = ('status', 'issued_date', 'due_date')
    search_fields = ('number', 'notes')
    readonly_fields = ('id', 'number', 'created_at', 'updated_at', 'subtotal', 'tax_amount', 'total')
    inlines = [InvoiceItemInline]
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('number', 'issued_date', 'due_date', 'paid_date')
        }),
        (_('Montants'), {
            'fields': ('subtotal', 'tax_amount', 'total', 'amount_paid', 'currency')
        }),
        (_('Statut'), {
            'fields': ('status', 'created_at', 'updated_at')
        }),
        (_('Ã‰metteur et destinataire'), {
            'fields': ('issuer_content_type', 'issuer_object_id', 'recipient_content_type', 'recipient_object_id')
        }),
        (_('Entité liée'), {
            'fields': ('related_content_type', 'related_object_id', 'created_by')
        }),
        (_('Informations supplémentaires'), {
            'fields': ('notes', 'terms', 'pdf_file')
        }),
    )
    actions = ['issue_invoices', 'cancel_invoices']
    
    def issue_invoices(self, request, queryset):
        updated = 0
        for invoice in queryset.filter(status='draft'):
            invoice.issue()
            updated += 1
        self.message_user(request, _("{} factures ont été émises.").format(updated))
    issue_invoices.short_description = _("Ã‰mettre les factures sélectionnées")
    
    def cancel_invoices(self, request, queryset):
        updated = 0
        for invoice in queryset.exclude(status='cancelled'):
            invoice.cancel()
            updated += 1
        self.message_user(request, _("{} factures ont été annulées.").format(updated))
    cancel_invoices.short_description = _("Annuler les factures sélectionnées")


class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'unit_price', 'tax_rate', 'total')
    list_filter = ('invoice__status',)
    search_fields = ('description', 'reference', 'invoice__number')
    readonly_fields = ('id', 'subtotal', 'tax_amount', 'total')
    fieldsets = (
        (_('Facture'), {
            'fields': ('invoice', 'order')
        }),
        (_('Informations de base'), {
            'fields': ('description', 'reference', 'quantity', 'unit_price', 'tax_rate')
        }),
        (_('Montants calculés'), {
            'fields': ('subtotal', 'tax_amount', 'total')
        }),
        (_('Catégorisation'), {
            'fields': ('category', 'item_content_type', 'item_object_id')
        }),
    )


