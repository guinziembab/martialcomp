from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class AccountingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'code', 'parent', 'is_active', 'is_system')
    list_filter = ('type', 'is_active', 'is_system')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('name', 'type', 'description', 'code')
        }),
        (_('Hiérarchie'), {
            'fields': ('parent',)
        }),
        (_('Organisation'), {
            'fields': ('organization_content_type', 'organization_id')
        }),
        (_('Statut'), {
            'fields': ('is_active', 'is_system', 'created_at', 'updated_at')
        }),
    )
    

class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'current_balance', 'currency', 'is_active', 'is_default')
    list_filter = ('type', 'currency', 'is_active', 'is_default')
    search_fields = ('name', 'description', 'bank_name', 'account_number', 'iban')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_reconciled')
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('name', 'type', 'description', 'is_active', 'is_default')
        }),
        (_('Soldes'), {
            'fields': ('currency', 'opening_balance', 'current_balance', 'reconciled_balance', 'last_reconciled')
        }),
        (_('Propriétaire'), {
            'fields': ('owner_content_type', 'owner_id')
        }),
        (_('Informations bancaires'), {
            'fields': ('bank_name', 'account_number', 'iban', 'bic')
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['reconcile_accounts']
    
    def reconcile_accounts(self, request, queryset):
        updated = 0
        for account in queryset:
            account.reconcile()
            updated += 1
        self.message_user(request, _("{} comptes ont été rapprochés.").format(updated))
    reconcile_accounts.short_description = _("Rapprocher les comptes sélectionnés")


class MembershipFeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'amount', 'currency', 'period', 'start_date', 'end_date', 'is_active')
    list_filter = ('period', 'is_active', 'is_prorated')
    search_fields = ('name', 'description', 'member_type')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('name', 'description', 'is_active')
        }),
        (_('Organisation'), {
            'fields': ('organization_content_type', 'organization_id')
        }),
        (_('Configuration de la cotisation'), {
            'fields': ('amount', 'currency', 'period', 'is_prorated')
        }),
        (_('Période de validité'), {
            'fields': ('start_date', 'end_date', 'grace_period_days')
        }),
        (_('Critères d\'éligibilité'), {
            'fields': ('member_type', 'age_min', 'age_max')
        }),
        (_('Comptabilité'), {
            'fields': ('accounting_category',)
        }),
        (_('Métadonnées'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
