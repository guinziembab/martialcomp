from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from ...utils.decorators import federation_admin_required
from ...models import Federation

import logging
logger = logging.getLogger('django')

@login_required
@federation_admin_required
def federation_finance_dashboard(request, federation_id):
    """
    Vue du tableau de bord financier pour une fédération.
    """
    federation = get_object_or_404(Federation, pk=federation_id)
    
    # Vérification que l'utilisateur a les droits sur cette fédération
    has_access = False
    
    # Vérifier via le rôle administrateur
    if hasattr(request.user, 'federation_admin_roles'):
        is_admin = federation.administrators.filter(user=request.user).exists()
        if is_admin:
            has_access = True
    
    # Vérifier via la relation owner
    if request.user == federation.owner:
        has_access = True
    
    if not has_access:
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Préparer les données pour le résumé financier
    try:
        # Obtenir le type de contenu pour la fédération
        federation_content_type = ContentType.objects.get_for_model(Federation)
        
        # Importer les modèles du module finances
        from finances.models.transactions import Transaction
        from finances.models.invoices import Invoice
        
        # Récupérer les données financières liées à cette fédération
        transactions = Transaction.objects.filter(
            entity_content_type=federation_content_type,
            entity_object_id=federation.id
        )
        
        invoices = Invoice.objects.filter(
            issuer_content_type=federation_content_type,
            issuer_object_id=federation.id
        )
        
        # Préparer les statistiques
        from django.db.models import Sum
        
        # Statistiques des transactions
        income = transactions.filter(type='income').aggregate(Sum('amount'))['amount__sum'] or 0
        expenses = transactions.filter(type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
        balance = income - expenses
        
        # Statistiques des factures
        invoice_total = invoices.aggregate(Sum('total'))['total__sum'] or 0
        unpaid_invoices = invoices.filter(status='unpaid').count()
        unpaid_amount = invoices.filter(status='unpaid').aggregate(Sum('total'))['total__sum'] or 0
        
        # Récupérer les transactions récentes
        recent_transactions = transactions.order_by('-date')[:5]
        
        # Récupérer les factures récentes
        recent_invoices = invoices.order_by('-date')[:5]
        
        financial_data = {
            'income': income,
            'expenses': expenses,
            'balance': balance,
            'invoice_total': invoice_total,
            'unpaid_invoices': unpaid_invoices,
            'unpaid_amount': unpaid_amount,
            'recent_transactions': recent_transactions,
            'recent_invoices': recent_invoices,
            'has_finance_data': transactions.exists() or invoices.exists()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données financières: {str(e)}")
        financial_data = {
            'income': 0,
            'expenses': 0,
            'balance': 0,
            'invoice_total': 0,
            'unpaid_invoices': 0,
            'unpaid_amount': 0,
            'recent_transactions': [],
            'recent_invoices': [],
            'has_finance_data': False,
            'error': _("Une erreur est survenue lors de la récupération des données financières.")
        }
    
    context = {
        'federation': federation,
        'finance': financial_data,
        'title': _("Finances de la fédération")
    }
    
    return render(request, 'competitions/dashboard/finance/index.html', context)