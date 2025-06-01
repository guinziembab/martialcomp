"""
Version simplifiée des vues financières pour éviter les problèmes de compatibilité
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from competitions.models import Practitioner


@login_required
def finance_dashboard(request):
    """Tableau de bord financier simplifié."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:dashboard')
    except:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:dashboard')
    
    # Données simulées pour le moment
    context = {
        'practitioner': practitioner,
        'stats': {
            'total_paid': 0,
            'total_pending': 0,
            'balance': 0,
            'upcoming_payments': 0
        },
        'recent_transactions': [],
        'pending_invoices': [],
        'upcoming_payments': [],
        'year': timezone.now().year,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/dashboard.html', context)


@login_required
def invoice_list(request):
    """Liste des factures."""
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    context = {
        'practitioner': practitioner,
        'invoices': [],
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/invoice_list.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """Détail d'une facture."""
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    context = {
        'practitioner': practitioner,
        'invoice': None,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/invoice_detail.html', context)


@login_required
def payment_list(request):
    """Liste des paiements."""
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    context = {
        'practitioner': practitioner,
        'payments': [],
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/payment_list.html', context)


@login_required
def payment_detail(request, payment_id):
    """Détail d'un paiement."""
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    context = {
        'practitioner': practitioner,
        'payment': None,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/payment_detail.html', context)


@login_required
def transaction_list(request):
    """Liste des transactions."""
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    context = {
        'practitioner': practitioner,
        'transactions': [],
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/transaction_list.html', context)


@login_required
def financial_report(request, year=None):
    """Rapport financier annuel."""
    practitioner = get_object_or_404(Practitioner, user=request.user)
    
    if not year:
        year = timezone.now().year
    
    context = {
        'practitioner': practitioner,
        'year': year,
        'stats': {
            'total_revenue': 0,
            'total_expenses': 0,
            'net_balance': 0,
            'monthly_data': []
        },
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/report.html', context)