from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta
from decimal import Decimal
import csv
import json

from apps.competitions.models import Practitioner, Membership
from apps.finances.models import (
    FinancialAccount, 
    Transaction, 
    Invoice, 
    PaymentMethod,
    PaymentAttempt,
    MembershipFee
)
from apps.competitions.utils.finance_adapters import PaymentAdapter, AccountAdapter
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


def get_practitioner_account(practitioner):
    """Récupère ou crée le compte financier du pratiquant"""
    practitioner_ct = ContentType.objects.get_for_model(Practitioner)
    try:
        return FinancialAccount.objects.get(
            owner_content_type=practitioner_ct,
            owner_id=str(practitioner.id)
        )
    except FinancialAccount.DoesNotExist:
        return FinancialAccount.objects.create(
            owner_content_type=practitioner_ct,
            owner_id=str(practitioner.id),
            name=f"Compte de {practitioner.full_name}",
            type='cash',
            opening_balance=Decimal('0.00'),
            current_balance=Decimal('0.00')
        )


@login_required
def practitioner_finance_dashboard(request):
    """Vue principale du tableau de bord financier du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer le compte financier du pratiquant
    account = get_practitioner_account(practitioner)
    
    # Statistiques financières
    current_year = timezone.now().year
    transactions = Transaction.objects.filter(financial_account=account)
    
    stats = {
        'balance': account.balance,
        'total_paid_this_year': transactions.filter(
            transaction_type='debit',
            date__year=current_year
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'total_pending': Invoice.objects.filter(
            practitioner=practitioner,
            status='pending'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        'upcoming_payments': PaymentAttempt.objects.filter(
            transaction__created_by=request.user,
            status='initiated',
            transaction__date__gte=timezone.now().date()
        ).count()
    }
    
    # Dernières transactions
    recent_transactions = transactions.order_by('-date')[:10]
    
    # Factures en attente
    pending_invoices = Invoice.objects.filter(
        practitioner=practitioner,
        status='pending'
    ).order_by('due_date')
    
    # Prochains paiements programmés
    upcoming_payments = PaymentAttempt.objects.filter(
        transaction__created_by=request.user,
        status='initiated',
        transaction__date__gte=timezone.now().date()
    ).select_related('transaction').order_by('transaction__date')[:5]
    
    context = {
        'practitioner': practitioner,
        'account': account,
        'stats': stats,
        'recent_transactions': recent_transactions,
        'pending_invoices': pending_invoices,
        'upcoming_payments': upcoming_payments,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/dashboard.html', context)


@login_required
def practitioner_transactions(request):
    """Liste complète des transactions du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer le compte
    try:
        account = FinancialAccount.objects.get(
            owner_content_type=practitioner_ct,
            owner_id=str(practitioner.id)
        )
    except FinancialAccount.DoesNotExist:
        messages.error(request, _("Aucun compte financier trouvé."))
        return redirect('competitions:practitioner_finance_dashboard')
    
    # Filtres
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    transaction_type = request.GET.get('type')
    search = request.GET.get('search')
    
    transactions = Transaction.objects.filter(financial_account=account)
    
    # Appliquer les filtres
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    if search:
        transactions = transactions.filter(
            Q(description__icontains=search) |
            Q(reference__icontains=search)
        )
    
    # Tri
    sort_by = request.GET.get('sort', '-date')
    transactions = transactions.order_by(sort_by)
    
    # Export CSV si demandé
    if request.GET.get('export') == 'csv':
        return export_transactions_csv(transactions)
    
    context = {
        'practitioner': practitioner,
        'transactions': transactions,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/transactions.html', context)


@login_required
def practitioner_invoices(request):
    """Gestion des factures du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    year_filter = request.GET.get('year', timezone.now().year)
    
    invoices = Invoice.objects.filter(practitioner=practitioner)
    
    # Appliquer les filtres
    if status_filter != 'all':
        invoices = invoices.filter(status=status_filter)
    if year_filter:
        invoices = invoices.filter(date__year=year_filter)
    
    # Statistiques
    invoice_stats = {
        'total': invoices.count(),
        'pending': invoices.filter(status='pending').count(),
        'paid': invoices.filter(status='paid').count(),
        'overdue': invoices.filter(
            status='pending',
            due_date__lt=timezone.now().date()
        ).count(),
        'total_amount': invoices.aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_paid': invoices.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0,
        'total_pending': invoices.filter(status='pending').aggregate(total=Sum('total_amount'))['total'] or 0,
    }
    
    context = {
        'practitioner': practitioner,
        'invoices': invoices.order_by('-date'),
        'invoice_stats': invoice_stats,
        'status_filter': status_filter,
        'year_filter': year_filter,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/invoices.html', context)


@login_required
def practitioner_invoice_detail(request, invoice_id):
    """Détails d'une facture spécifique."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    invoice = get_object_or_404(Invoice, id=invoice_id, practitioner=practitioner)
    
    # Récupérer les paiements associés
    payments = PaymentAttempt.objects.filter(invoice=invoice)
    
    context = {
        'practitioner': practitioner,
        'invoice': invoice,
        'payments': payments,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/invoice_detail.html', context)


@login_required
def practitioner_payments(request):
    """Gestion des paiements du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer tous les paiements
    payments = PaymentAttempt.objects.filter(payer=request.user).order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    method_filter = request.GET.get('method', 'all')
    
    if status_filter != 'all':
        payments = payments.filter(status=status_filter)
    if method_filter != 'all':
        payments = payments.filter(payment_method=method_filter)
    
    # Statistiques
    payment_stats = {
        'total': payments.count(),
        'completed': payments.filter(status='completed').count(),
        'pending': payments.filter(status='pending').count(),
        'failed': payments.filter(status='failed').count(),
        'scheduled': payments.filter(status='scheduled').count(),
    }
    
    # Moyens de paiement sauvegardés (si disponibles)
    saved_payment_methods = []  # Ã€ implémenter avec un système de tokens
    
    context = {
        'practitioner': practitioner,
        'payments': payments,
        'payment_stats': payment_stats,
        'saved_payment_methods': saved_payment_methods,
        'status_filter': status_filter,
        'method_filter': method_filter,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/payments.html', context)


@login_required
def practitioner_make_payment(request, invoice_id=None):
    """Effectuer un paiement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    invoice = None
    if invoice_id:
        invoice = get_object_or_404(Invoice, id=invoice_id, practitioner=practitioner, status='pending')
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        amount = request.POST.get('amount')
        
        # Créer le paiement
        payment = PaymentAttempt.objects.create(
            payer=request.user,
            amount=Decimal(amount),
            payment_method=payment_method,
            status='pending',
            invoice=invoice if invoice else None,
            description=f"Paiement {invoice.number if invoice else 'manuel'}"
        )
        
        # Traiter le paiement selon la méthode
        if payment_method == 'card':
            # Rediriger vers la passerelle de paiement
            return redirect('shop:payment:process', payment_id=payment.id)
        elif payment_method == 'bank_transfer':
            # Fournir les instructions de virement
            messages.info(request, _("Instructions de virement envoyées par email."))
            return redirect('competitions:practitioner_payment_instructions', payment_id=payment.id)
        else:
            # Autres méthodes (espèces, chèque)
            messages.success(request, _("Paiement enregistré. En attente de confirmation."))
            return redirect('competitions:practitioner_payments')
    
    context = {
        'practitioner': practitioner,
        'invoice': invoice,
        'payment_methods': PaymentAttempt.PAYMENT_METHOD_CHOICES,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/make_payment.html', context)


@login_required  
def practitioner_membership_payment(request):
    """Paiement spécifique pour l'adhésion."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Récupérer les tarifs d'adhésion
    membership_fees = MembershipFee.objects.filter(
        organization=practitioner.organization,
        is_active=True
    )
    
    if request.method == 'POST':
        fee_id = request.POST.get('membership_fee')
        payment_method = request.POST.get('payment_method')
        
        fee = get_object_or_404(MembershipFee, id=fee_id)
        
        # Créer la facture
        invoice = Invoice.objects.create(
            practitioner=practitioner,
            organization=practitioner.organization,
            invoice_type='membership',
            total_amount=fee.amount,
            status='pending',
            due_date=timezone.now().date() + timedelta(days=30),
            description=f"Adhésion {fee.membership_type} - {fee.period}"
        )
        
        # Créer le paiement
        payment = PaymentAttempt.objects.create(
            payer=request.user,
            amount=fee.amount,
            payment_method=payment_method,
            status='pending',
            invoice=invoice,
            description=f"Adhésion {fee.membership_type}"
        )
        
        # Rediriger vers le traitement du paiement
        return redirect('shop:payment:process', payment_id=payment.id)
    
    context = {
        'practitioner': practitioner,
        'membership_fees': membership_fees,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/membership_payment.html', context)


@login_required
def practitioner_finance_reports(request):
    """Rapports financiers pour le pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('welcome')
    
    # Période sélectionnée
    year = int(request.GET.get('year', timezone.now().year))
    
    # Récupérer le compte
    try:
        account = FinancialAccount.objects.get(
            owner_content_type=practitioner_ct,
            owner_id=str(practitioner.id)
        )
    except FinancialAccount.DoesNotExist:
        messages.error(request, _("Aucun compte financier trouvé."))
        return redirect('competitions:practitioner_finance_dashboard')
    
    # Données pour les graphiques
    monthly_data = []
    for month in range(1, 13):
        month_transactions = Transaction.objects.filter(
            account=account,
            date__year=year,
            date__month=month
        )
        
        credits = month_transactions.filter(transaction_type='credit').aggregate(total=Sum('amount'))['total'] or 0
        debits = month_transactions.filter(transaction_type='debit').aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_data.append({
            'month': month,
            'credits': float(credits),
            'debits': float(debits),
            'balance': float(credits - debits)
        })
    
    # Répartition par catégorie
    category_data = Transaction.objects.filter(
        account=account,
        date__year=year,
        transaction_type='debit'
    ).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Totaux annuels
    yearly_stats = {
        'total_credits': Transaction.objects.filter(
            account=account,
            date__year=year,
            transaction_type='credit'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'total_debits': Transaction.objects.filter(
            account=account,
            date__year=year,
            transaction_type='debit'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    yearly_stats['balance'] = yearly_stats['total_credits'] - yearly_stats['total_debits']
    
    context = {
        'practitioner': practitioner,
        'year': year,
        'monthly_data': monthly_data,
        'category_data': category_data,
        'yearly_stats': yearly_stats,
        'active_page': 'finance'
    }
    
    return render(request, 'competitions/practitioner/finance/reports.html', context)


def export_transactions_csv(transactions):
    """Exporter les transactions en CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Type', 'Description', 'Référence', 'Débit', 'Crédit', 'Solde'])
    
    balance = 0
    for transaction in transactions:
        if transaction.transaction_type == 'credit':
            credit = transaction.amount
            debit = 0
            balance += transaction.amount
        else:
            credit = 0
            debit = transaction.amount
            balance -= transaction.amount
        
        writer.writerow([
            transaction.date.strftime('%d/%m/%Y'),
            transaction.get_transaction_type_display(),
            transaction.description,
            transaction.reference or '',
            debit if debit else '',
            credit if credit else '',
            balance
        ])
    
    return response

