from django.contrib import admin

# Import des modèles explicites au lieu d'utiliser *
from finances.models.transactions import Transaction, TransactionCategory, TransactionAttachment
from finances.models.payments import PaymentMethod, PaymentAttempt
from finances.models.invoices import Invoice, InvoiceItem
from finances.models.accounts import AccountingCategory, FinancialAccount, MembershipFee

from finances.admin.transaction import TransactionAdmin
from finances.admin.payment import PaymentMethodAdmin, PaymentAttemptAdmin
from finances.admin.invoice import InvoiceAdmin, InvoiceItemAdmin
from finances.admin.account import AccountingCategoryAdmin, FinancialAccountAdmin, MembershipFeeAdmin

# Enregistrer les modèles avec leurs classes d'administration
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(TransactionCategory)
admin.site.register(TransactionAttachment)
admin.site.register(PaymentMethod, PaymentMethodAdmin)
admin.site.register(PaymentAttempt, PaymentAttemptAdmin)
admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(InvoiceItem, InvoiceItemAdmin)
admin.site.register(AccountingCategory, AccountingCategoryAdmin)
admin.site.register(FinancialAccount, FinancialAccountAdmin)
admin.site.register(MembershipFee, MembershipFeeAdmin)