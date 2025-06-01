from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator

from ..models.transactions import Transaction
from ..models.invoices import Invoice
from ..models.accounts import FinancialAccount
from ..models.payments import PaymentMethod
from ..utils import get_financial_permissions

# Vue de diagnostic pour le dashboard financier
@method_decorator(login_required, name='dispatch')
class DebugDashboardView(TemplateView):
    """Vue de diagnostic pour le dashboard financier - Sans vérification de permission."""
    template_name = 'finances/dashboard/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Attribuer toutes les permissions pour le débogage
        permissions = {
            'can_view_dashboard': True,
            'can_view_transactions': True,
            'can_add_transactions': True,
            'can_validate_transactions': True,
            'can_view_all_transactions': True,
            'can_view_invoices': True,
            'can_create_invoices': True,
            'can_view_all_invoices': True,
            'can_process_payment': True,
            'can_view_reports': True,
            'can_view_accounts': True,
            'can_manage_accounts': True,
            'can_approve_all_transactions': True,
        }
        
        context['permissions'] = permissions
        
        # Ajouter des statistiques factices pour les fins de débogage
        context['total_income'] = 1000
        context['total_expense'] = 500
        context['net_result'] = 500
        context['invoice_count'] = 5
        context['recent_transactions'] = Transaction.objects.all()[:5]
        context['recent_invoices'] = Invoice.objects.all()[:5]
        
        return context

# Vue de diagnostic pour les méthodes de paiement
@method_decorator(login_required, name='dispatch')
class DebugPaymentMethodListView(ListView):
    """Vue de diagnostic pour lister les méthodes de paiement - Sans vérification de permission."""
    model = PaymentMethod
    template_name = 'finances/payment/methods/list.html'
    context_object_name = 'payment_methods'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Attribuer toutes les permissions pour le débogage
        permissions = {
            'can_view_paymentmethod': True,
            'can_add_paymentmethod': True,
            'can_change_paymentmethod': True,
            'can_delete_paymentmethod': True,
        }
        
        context['permissions'] = permissions
        return context