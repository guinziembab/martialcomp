from django.urls import path, include

from .views import (
    transactions, payments, invoices, accounts, dashboard, banking,
    stripe_views,
)

app_name = 'finances'

# URLs pour les transactions
transaction_patterns = [
    path('', transactions.TransactionListView.as_view(), name='transaction_list'),
    path('create/', transactions.TransactionCreateView.as_view(), name='transaction_create'),
    path('<str:pk>/', transactions.TransactionDetailView.as_view(), name='transaction_detail'),
    path('<str:pk>/edit/', transactions.TransactionUpdateView.as_view(), name='transaction_update'),
    path('<str:pk>/delete/', transactions.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('<str:pk>/status/<str:status>/', transactions.transaction_change_status, name='transaction_change_status'),
    path('<str:pk>/attachments/add/', transactions.transaction_add_attachment, name='transaction_add_attachment'),
    path('<str:transaction_pk>/attachments/<str:attachment_pk>/delete/', 
         transactions.transaction_delete_attachment, name='transaction_delete_attachment'),
    path('bulk-approval/', transactions.BulkTransactionApprovalView.as_view(), name='transaction_bulk_approval'),
    
    # Catégories de transactions
    path('categories/', transactions.TransactionCategoryListView.as_view(), name='transaction_category_list'),
    path('categories/create/', transactions.TransactionCategoryCreateView.as_view(), name='transaction_category_create'),
    path('categories/<str:pk>/', transactions.TransactionCategoryUpdateView.as_view(), name='transaction_category_update'),
    path('categories/<str:pk>/delete/', transactions.TransactionCategoryDeleteView.as_view(), name='transaction_category_delete'),
]

# URLs pour les paiements
payment_patterns = [
    # Méthodes de paiement
    path('methods/', payments.PaymentMethodListView.as_view(), name='payment_method_list'),
    path('methods/create/', payments.PaymentMethodCreateView.as_view(), name='payment_method_create'),
    path('methods/<str:pk>/', payments.PaymentMethodUpdateView.as_view(), name='payment_method_update'),
    path('methods/<str:pk>/delete/', payments.PaymentMethodDeleteView.as_view(), name='payment_method_delete'),
    
    # Tentatives de paiement
    path('attempts/', payments.PaymentAttemptListView.as_view(), name='payment_attempt_list'),
    path('attempts/create/', payments.PaymentAttemptCreateView.as_view(), name='payment_attempt_create'),
    path('attempts/<str:pk>/', payments.PaymentAttemptDetailView.as_view(), name='payment_attempt_detail'),
    path('process/<str:pk>/', payments.process_payment, name='process_payment'),
    path('cancel/<str:pk>/', payments.cancel_payment, name='cancel_payment'),
    
    # API pour les méthodes de paiement
    path('api/methods/', payments.payment_method_options, name='payment_method_options'),
]

# URLs pour les factures
invoice_patterns = [
    path('', invoices.InvoiceListView.as_view(), name='invoice_list'),
    path('create/', invoices.InvoiceCreateView.as_view(), name='invoice_create'),
    path('<str:pk>/', invoices.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('<str:pk>/edit/', invoices.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('<str:pk>/delete/', invoices.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('<str:pk>/pay/', invoices.invoice_pay, name='invoice_pay'),
    path('<str:pk>/pdf/', invoices.invoice_pdf, name='invoice_pdf'),
    path('<str:pk>/send/', invoices.invoice_send, name='invoice_send'),
    path('<str:pk>/send-email/', invoices.invoice_send_email, name='invoice_send_email'),
    path('<str:pk>/cancel/', invoices.invoice_cancel, name='invoice_cancel'),
    path('<str:pk>/recalculate/', invoices.recalculate_invoice, name='recalculate_invoice'),
]

# URLs pour les comptes
account_patterns = [
    # Catégories comptables
    path('categories/', accounts.AccountingCategoryListView.as_view(), name='accounting_category_list'),
    path('categories/create/', accounts.AccountingCategoryCreateView.as_view(), name='accounting_category_create'),
    path('categories/<str:pk>/', accounts.AccountingCategoryUpdateView.as_view(), name='accounting_category_update'),
    path('categories/<str:pk>/delete/', accounts.AccountingCategoryDeleteView.as_view(), name='accounting_category_delete'),
    
    # Comptes financiers
    path('financial/', accounts.FinancialAccountListView.as_view(), name='financial_account_list'),
    path('financial/create/', accounts.FinancialAccountCreateView.as_view(), name='financial_account_create'),
    path('financial/<str:pk>/', accounts.FinancialAccountDetailView.as_view(), name='financial_account_detail'),
    path('financial/<str:pk>/edit/', accounts.FinancialAccountUpdateView.as_view(), name='financial_account_update'),
    path('financial/<str:pk>/delete/', accounts.FinancialAccountDeleteView.as_view(), name='financial_account_delete'),
    
    # Cotisations
    path('membership/', accounts.MembershipFeeListView.as_view(), name='membership_fee_list'),
    path('membership/create/', accounts.MembershipFeeCreateView.as_view(), name='membership_fee_create'),
    path('membership/<str:pk>/', accounts.MembershipFeeUpdateView.as_view(), name='membership_fee_update'),
    path('membership/<str:pk>/delete/', accounts.MembershipFeeDeleteView.as_view(), name='membership_fee_delete'),
]

# URLs Stripe Checkout
stripe_patterns = [
    path('checkout/create/', stripe_views.create_checkout, name='stripe_checkout_create'),
    path('subscription/create/', stripe_views.create_subscription_checkout, name='subscription_checkout_create'),
    path('success/', stripe_views.checkout_success, name='stripe_checkout_success'),
    path('cancel/', stripe_views.checkout_cancel, name='stripe_checkout_cancel'),
]

# URLs principales de l'application
urlpatterns = [
    # Dashboard et rapports
    path('', dashboard.FinancialDashboardView.as_view(), name='dashboard'),
    path('reports/', dashboard.FinancialReportView.as_view(), name='reports'),
    
    # Sous-modules
    path('transactions/', include((transaction_patterns, 'transactions'))),
    path('payments/', include((payment_patterns, 'payments'))),
    path('invoices/', include((invoice_patterns, 'invoices'))),
    path('accounts/', include((account_patterns, 'accounts'))),
    # API utilitaire: options de catégorie parente
    path('accounts/categories/parent-options/', accounts.accounting_category_parent_options, name='accounting_category_parent_options'),
    
    # Aliases directs pour simplifier l'accès dans les templates
    path('transactions-list/', transactions.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<str:pk>/', transactions.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/<str:pk>/edit/', transactions.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<str:pk>/delete/', transactions.TransactionDeleteView.as_view(), name='transaction_delete'),
    path('transactions/create/', transactions.TransactionCreateView.as_view(), name='transaction_create'),
    
    path('invoices-list/', invoices.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<str:pk>/', invoices.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<str:pk>/edit/', invoices.InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<str:pk>/delete/', invoices.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/create/', invoices.InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<str:pk>/pdf/', invoices.invoice_pdf, name='invoice_pdf'),
    
    path('accounts-list/', accounts.FinancialAccountListView.as_view(), name='account_list'),
    path('accounts/categories/', accounts.AccountingCategoryListView.as_view(), name='accounting_category_list'),
    path('accounts/membership/', accounts.MembershipFeeListView.as_view(), name='membership_fee_list'),
    
    path('payments/methods/', payments.PaymentMethodListView.as_view(), name='payment_method_list'),

    # ===== Import bancaire et réconciliation =====
    # Dashboard import
    path('banking/', banking.bank_import_dashboard, name='bank_import_dashboard'),
    path('banking/upload/', banking.bank_import_upload, name='bank_import_upload'),
    path('banking/preview/', banking.bank_import_preview, name='bank_import_preview'),
    path('banking/confirm/', banking.bank_import_confirm, name='bank_import_confirm'),
    path('banking/history/', banking.bank_import_history, name='bank_import_history'),
    path('banking/batch/<str:batch_id>/', banking.bank_import_detail, name='bank_import_detail'),

    # Réconciliation - IMPORTANT: les routes fixes doivent être AVANT <uuid:transaction_id>/
    path('banking/reconciliation/', banking.bank_reconciliation_pending, name='bank_reconciliation_pending'),
    path('banking/reconciliation/dashboard/', banking.bank_reconciliation_dashboard, name='bank_reconciliation_dashboard'),
    path('banking/reconciliation/export-pdf/', banking.bank_reconciliation_export_pdf, name='bank_reconciliation_export_pdf'),
    path('banking/reconciliation/auto/', banking.bank_transaction_auto_reconcile, name='bank_transaction_auto_reconcile'),
    path('banking/reconciliation/validate-all/', banking.bank_transaction_validate_all, name='bank_transaction_validate_all'),
    path('banking/reconciliation/<uuid:transaction_id>/', banking.bank_transaction_reconcile, name='bank_transaction_reconcile'),

    # API endpoints pour AJAX
    path('banking/api/practitioners/', banking.api_search_practitioners, name='api_search_practitioners'),
    path('banking/api/suggestions/<str:transaction_id>/', banking.api_transaction_suggestions, name='api_transaction_suggestions'),

    # =============================================================================
    # API REST Multi-Devises
    # =============================================================================
    # Inclusion des endpoints API pour les devises et conversions
    # GET /finances/api/currencies/ - Liste des devises
    # GET /finances/api/rates/ - Taux de change actuels
    # GET/POST /finances/api/convert/ - Conversion de devises
    # GET/POST /finances/api/format/ - Formatage de montants
    # GET/POST /finances/api/user-currency/ - Préférence utilisateur
    # POST /finances/api/bulk-convert/ - Conversion en lot
    # Import urlpatterns directly from api.py to avoid conflict with api/ directory
    path('api/', include('apps.finances.rest_api')),

    # ===== Stripe Checkout =====
    path('stripe/', include((stripe_patterns, 'stripe'))),
]
