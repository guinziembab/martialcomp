from django.core.exceptions import PermissionDenied
"""
Vues spécifiques Ã  l'intégration multi-tenant du module finances.
"""
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, 
    DeleteView, TemplateView, FormView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum, Count, F
from django.db import connection
from decimal import Decimal
from datetime import date, datetime, timedelta
import json

from apps.multitenant.mixins import TenantAwareViewMixin, TenantRequiredMixin
from apps.multitenant.models import Tenant
from apps.multitenant.performance_mixins import TenantCacheMixin, TenantDashboardMixin
from apps.finances.tenant_integration import tenant_finance_required
from apps.finances.models.accounts import Account, AccountType
from apps.finances.models.invoices import Invoice, InvoiceItem
from apps.finances.models.payments import Payment
from apps.finances.models.transactions import Transaction, TransactionType
from apps.finances.tenant_models import (
    TenantFinancialSetting, TenantBillingCycle, 
    TenantInvoiceTemplate
)
from apps.finances.forms.accounts_forms import AccountForm
from apps.finances.forms.invoice_forms import InvoiceForm, InvoiceItemFormSet
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class TenantFinanceDashboardView(LoginRequiredMixin, TenantRequiredMixin, 
                                TenantAwareViewMixin, TenantDashboardMixin, 
                                TemplateView):
    """
    Tableau de bord financier spécifique au tenant.
    """
    template_name = 'finances/tenant/dashboard.html'
    
    @tenant_finance_required
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques financières tenant-aware
        tenant = self.request.tenant
        
        # Statistiques globales
        revenue_accounts = Account.objects.filter(
            type=AccountType.REVENUE
        )
        
        expense_accounts = Account.objects.filter(
            type=AccountType.EXPENSE
        )
        
        # Calculer les totaux
        total_revenue = revenue_accounts.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0')
        
        total_expenses = expense_accounts.aggregate(
            total=Sum('balance')
        )['total'] or Decimal('0')
        
        context['summary'] = {
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': total_revenue - total_expenses,
            'account_count': Account.objects.count(),
            'invoice_count': Invoice.objects.count(),
            'payment_count': Payment.objects.count(),
        }
        
        # Factures récentes
        context['recent_invoices'] = Invoice.objects.order_by('-created_at')[:5]
        
        # Paiements récents
        context['recent_payments'] = Payment.objects.order_by('-payment_date')[:5]
        
        # Transactions récentes
        context['recent_transactions'] = Transaction.objects.order_by('-transaction_date')[:10]
        
        # Données pour graphiques
        context['revenue_data'] = self._get_revenue_data()
        context['expense_data'] = self._get_expense_data()
        
        # Cycle de facturation actuel
        today = date.today()
        current_cycle = TenantBillingCycle.objects.filter(
            tenant=tenant,
            start_date__lte=today,
            end_date__gte=today
        ).first()
        
        if current_cycle:
            context['current_cycle'] = current_cycle
        
        # Paramètres financiers du tenant
        try:
            settings = TenantFinancialSetting.objects.get(tenant=tenant)
            context['finance_settings'] = settings
        except TenantFinancialSetting.DoesNotExist:
            pass
        
        return context
    
    def _get_revenue_data(self):
        """
        Récupère les données de revenus pour le graphique.
        """
        # Récupérer les 6 derniers mois
        today = date.today()
        months = []
        for i in range(5, -1, -1):
            month = today.replace(day=1) - timedelta(days=i*30)
            months.append(month)
        
        data = []
        for month in months:
            month_name = month.strftime('%b %Y')
            month_start = month.replace(day=1)
            if month.month == 12:
                month_end = month.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month.replace(month=month.month + 1, day=1) - timedelta(days=1)
            
            total = Transaction.objects.filter(
                transaction_type=TransactionType.REVENUE,
                transaction_date__gte=month_start,
                transaction_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            data.append({
                'month': month_name,
                'revenue': float(total)
            })
        
        return data
    
    def _get_expense_data(self):
        """
        Récupère les données de dépenses pour le graphique.
        """
        # Récupérer les 6 derniers mois
        today = date.today()
        months = []
        for i in range(5, -1, -1):
            month = today.replace(day=1) - timedelta(days=i*30)
            months.append(month)
        
        data = []
        for month in months:
            month_name = month.strftime('%b %Y')
            month_start = month.replace(day=1)
            if month.month == 12:
                month_end = month.replace(year=month.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end = month.replace(month=month.month + 1, day=1) - timedelta(days=1)
            
            total = Transaction.objects.filter(
                transaction_type=TransactionType.EXPENSE,
                transaction_date__gte=month_start,
                transaction_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            data.append({
                'month': month_name,
                'expense': float(total)
            })
        
        return data


class TenantAccountListView(LoginRequiredMixin, TenantRequiredMixin,
                           TenantAwareViewMixin, ListView):
    """
    Liste des comptes du tenant.
    """
    model = Account
    template_name = 'finances/tenant/accounts/list.html'
    context_object_name = 'accounts'
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        queryset = super().get_queryset()
        
        # Filtre par type de compte
        account_type = self.request.GET.get('type')
        if account_type:
            queryset = queryset.filter(type=account_type)
        
        # Filtre de recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )
        
        return queryset.order_by('type', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Totaux par type de compte
        context['account_totals'] = {
            'asset': Account.objects.filter(type=AccountType.ASSET).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
            
            'liability': Account.objects.filter(type=AccountType.LIABILITY).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
            
            'equity': Account.objects.filter(type=AccountType.EQUITY).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
            
            'revenue': Account.objects.filter(type=AccountType.REVENUE).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
            
            'expense': Account.objects.filter(type=AccountType.EXPENSE).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
        }
        
        return context


class TenantSettingsUpdateView(LoginRequiredMixin, TenantRequiredMixin,
                              TenantAwareViewMixin, UpdateView):
    """
    Mise Ã  jour des paramètres financiers du tenant.
    """
    model = TenantFinancialSetting
    template_name = 'finances/tenant/settings.html'
    fields = [
        'vat_number', 'tax_id', 'tax_rate', 'invoice_prefix',
        'invoice_footer', 'payment_terms_days', 'revenue_account',
        'expense_account', 'transaction_daily_limit',
        'single_transaction_limit', 'auto_send_invoices',
        'auto_send_payment_reminders', 'auto_apply_platform_fees'
    ]
    success_url = reverse_lazy('finances:tenant_dashboard')
    
    def get_object(self, queryset=None):
        """
        Récupère les paramètres existants ou crée un nouvel objet.
        """
        tenant = self.request.tenant
        
        try:
            settings = TenantFinancialSetting.objects.get(tenant=tenant)
            return settings
        except TenantFinancialSetting.DoesNotExist:
            # Créer des paramètres par défaut
            settings = TenantFinancialSetting(tenant=tenant)
            settings.save()
            return settings
    
    def get_form(self, form_class=None):
        """
        Personnalise le formulaire.
        """
        form = super().get_form(form_class)
        
        # Limiter les choix de comptes Ã  ceux du tenant
        form.fields['revenue_account'].queryset = Account.objects.filter(
            type=AccountType.REVENUE
        )
        
        form.fields['expense_account'].queryset = Account.objects.filter(
            type=AccountType.EXPENSE
        )
        
        return form
    
    def form_valid(self, form):
        messages.success(self.request, _("Les paramètres financiers ont été mis Ã  jour."))
        return super().form_valid(form)


class TenantInvoiceListView(LoginRequiredMixin, TenantRequiredMixin,
                           TenantAwareViewMixin, ListView):
    """
    Liste des factures du tenant.
    """
    model = Invoice
    template_name = 'finances/tenant/invoices/list.html'
    context_object_name = 'invoices'
    paginate_by = 25
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        queryset = super().get_queryset()
        
        # Filtre par statut
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filtre par date
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(invoice_date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(invoice_date__lte=date_to)
        
        # Filtre de recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(reference__icontains=search) |
                Q(client_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-invoice_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques des factures
        stats = Invoice.objects.aggregate(
            total_count=Count('id'),
            total_amount=Sum('total_amount'),
            unpaid_count=Count('id', filter=Q(status='unpaid')),
            unpaid_amount=Sum('total_amount', filter=Q(status='unpaid')),
            paid_count=Count('id', filter=Q(status='paid')),
            paid_amount=Sum('total_amount', filter=Q(status='paid')),
        )
        
        # Remplacer les None par 0
        for key, value in stats.items():
            if value is None:
                stats[key] = Decimal('0')
        
        context['invoice_stats'] = stats
        
        return context

