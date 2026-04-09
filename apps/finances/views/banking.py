# -*- coding: utf-8 -*-
"""
Vues pour l'import bancaire et la réconciliation.
"""

import json
import logging
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q

from apps.finances.models import (
    FinancialAccount,
    BankImportBatch,
    BankTransaction,
    ReconciliationRule,
    TransactionCategory,
    Transaction,
)
from apps.finances.services.bank_import_service import (
    BankImportService,
    ReconciliationService,
)
from apps.finances.parsers import PARSER_REGISTRY
from apps.competitions.models import Practitioner

logger = logging.getLogger(__name__)


def _create_transaction_from_bank_tx(bank_tx, user, category=None, practitioner=None):
    """
    Crée une Transaction standard à partir d'une BankTransaction importée.

    Args:
        bank_tx: BankTransaction - la transaction bancaire source
        user: User - l'utilisateur effectuant l'action
        category: TransactionCategory - catégorie optionnelle
        practitioner: Practitioner - pratiquant optionnel

    Returns:
        Transaction: la nouvelle transaction créée
    """
    from django.contrib.contenttypes.models import ContentType

    # Déterminer le type de transaction
    tx_type = 'income' if bank_tx.transaction_type == 'INCOME' else 'expense'

    # Construire la description
    description_parts = []
    if bank_tx.counterparty_name:
        description_parts.append(bank_tx.counterparty_name)
    if bank_tx.communication:
        description_parts.append(bank_tx.communication)
    description = ' - '.join(description_parts) or f"Import bancaire {bank_tx.external_reference}"

    # Créer la transaction
    system_tx = Transaction.objects.create(
        type=tx_type,
        amount=abs(bank_tx.amount),
        currency=bank_tx.currency,
        date=bank_tx.transaction_date,
        status='validated',  # Les transactions bancaires sont déjà validées par la banque
        category=category or bank_tx.matched_category,
        description=description,
        created_by=user,
        validated_by=user,
        date_validated=timezone.now(),
        financial_account=bank_tx.import_batch.financial_account,
        metadata={
            'source': 'bank_import',
            'bank_transaction_id': str(bank_tx.id),
            'external_reference': bank_tx.external_reference,
            'counterparty_name': bank_tx.counterparty_name,
            'counterparty_iban': bank_tx.counterparty_iban,
            'payment_method': bank_tx.payment_method,
        }
    )

    # Si un pratiquant est spécifié, lier via source_content_type
    if practitioner:
        ct = ContentType.objects.get_for_model(Practitioner)
        system_tx.source_content_type = ct
        system_tx.source_object_id = str(practitioner.id)
        system_tx.save()

    return system_tx


@login_required
def bank_import_dashboard(request):
    """
    Dashboard principal pour l'import bancaire.
    Affiche les statistiques et les derniers imports.
    """
    # Récupérer les comptes financiers de l'utilisateur
    # Pour simplifier, on prend tous les comptes actifs pour l'instant
    accounts = FinancialAccount.objects.filter(is_active=True)

    # Statistiques des imports
    stats = {
        'total_batches': BankImportBatch.objects.count(),
        'pending_reconciliation': BankTransaction.objects.filter(
            reconciliation_status='pending'
        ).count(),
        'matched_count': BankTransaction.objects.filter(
            reconciliation_status='matched'
        ).count(),
        'total_imported': BankTransaction.objects.count(),
    }

    # Derniers imports
    recent_batches = BankImportBatch.objects.select_related(
        'financial_account', 'imported_by'
    ).order_by('-import_date')[:10]

    # Formats bancaires disponibles
    bank_formats = [
        {'code': code, 'name': parser_class.BANK_NAME}
        for code, parser_class in PARSER_REGISTRY.items()
    ]

    context = {
        'accounts': accounts,
        'stats': stats,
        'recent_batches': recent_batches,
        'bank_formats': bank_formats,
        'active_tab': 'import',
    }

    return render(request, 'finances/banking/import_dashboard.html', context)


@login_required
def bank_import_upload(request):
    """
    Vue pour uploader un fichier de relevé bancaire.
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        account_id = request.POST.get('account_id')
        bank_format = request.POST.get('bank_format', '')

        if not uploaded_file:
            messages.error(request, _("Veuillez sélectionner un fichier."))
            return redirect('finances:bank_import_dashboard')

        if not account_id:
            messages.error(request, _("Veuillez sélectionner un compte bancaire."))
            return redirect('finances:bank_import_dashboard')

        try:
            account = get_object_or_404(FinancialAccount, pk=account_id)
            file_content = uploaded_file.read()

            # Créer le service d'import
            import_service = BankImportService(user=request.user)

            # Prévisualisation d'abord
            preview_data, detected_format, errors = import_service.preview_import(
                file_content,
                bank_format=bank_format if bank_format else None
            )

            if errors:
                for error in errors:
                    messages.error(request, error)
                return redirect('finances:bank_import_dashboard')

            # Stocker en session pour confirmation
            request.session['bank_import_preview'] = {
                'file_name': uploaded_file.name,
                'account_id': str(account_id),
                'bank_format': detected_format,
                'transaction_count': len(preview_data),
                'total_income': str(sum(
                    t.amount for t in preview_data if t.transaction_type == 'INCOME'
                )),
                'total_expense': str(abs(sum(
                    t.amount for t in preview_data if t.transaction_type == 'EXPENSE'
                ))),
            }

            # Stocker le contenu du fichier temporairement
            # En production, utiliser un stockage temporaire approprié
            request.session['bank_import_file_content'] = file_content.decode('utf-8', errors='replace')

            # Rediriger vers la prévisualisation
            return redirect('finances:bank_import_preview')

        except Exception as e:
            logger.exception(f"Erreur lors de l'upload: {e}")
            messages.error(request, _("Erreur lors de l'analyse du fichier: {}").format(str(e)))
            return redirect('finances:bank_import_dashboard')

    # GET - Afficher le formulaire d'upload
    accounts = FinancialAccount.objects.filter(is_active=True)
    bank_formats = [
        {'code': code, 'name': parser_class.BANK_NAME}
        for code, parser_class in PARSER_REGISTRY.items()
    ]

    context = {
        'accounts': accounts,
        'bank_formats': bank_formats,
    }

    return render(request, 'finances/banking/import_upload.html', context)


@login_required
def bank_import_preview(request):
    """
    Prévisualisation de l'import avant confirmation.
    """
    preview_data = request.session.get('bank_import_preview')
    file_content_str = request.session.get('bank_import_file_content')

    if not preview_data or not file_content_str:
        messages.warning(request, _("Aucun import en attente de confirmation."))
        return redirect('finances:bank_import_dashboard')

    # Reparser pour afficher les transactions
    file_content = file_content_str.encode('utf-8')
    import_service = BankImportService(user=request.user)

    transactions, bank_format, errors = import_service.preview_import(
        file_content,
        bank_format=preview_data.get('bank_format')
    )

    account = get_object_or_404(
        FinancialAccount,
        pk=preview_data.get('account_id')
    )

    context = {
        'preview_data': preview_data,
        'transactions': transactions[:50],  # Limiter l'affichage
        'total_transactions': len(transactions),
        'account': account,
        'bank_format': bank_format,
        'bank_format_name': PARSER_REGISTRY.get(bank_format, type('', (), {'BANK_NAME': bank_format})).BANK_NAME,
    }

    return render(request, 'finances/banking/import_preview.html', context)


@login_required
@require_POST
def bank_import_confirm(request):
    """
    Confirme et exécute l'import.
    Avec option auto_validate pour créer automatiquement les Transaction.
    """
    preview_data = request.session.get('bank_import_preview')
    file_content_str = request.session.get('bank_import_file_content')

    if not preview_data or not file_content_str:
        messages.error(request, _("Session expirée. Veuillez recommencer l'import."))
        return redirect('finances:bank_import_dashboard')

    # Option de validation automatique (pour utilisateurs non-comptables)
    auto_validate = request.POST.get('auto_validate') == 'on'

    try:
        file_content = file_content_str.encode('utf-8')
        account = get_object_or_404(
            FinancialAccount,
            pk=preview_data.get('account_id')
        )

        # Exécuter l'import
        import_service = BankImportService(user=request.user)
        result = import_service.import_file(
            file_content=file_content,
            file_name=preview_data.get('file_name'),
            financial_account=account,
            bank_format=preview_data.get('bank_format')
        )

        # Nettoyer la session
        del request.session['bank_import_preview']
        del request.session['bank_import_file_content']

        if result.success:
            imported_count = result.imported_count

            # Si auto_validate est activé, créer automatiquement les Transaction
            if auto_validate and imported_count > 0:
                created_count = _auto_validate_imported_transactions(
                    result.batch_id, request.user
                )
                messages.success(
                    request,
                    _("Import réussi! {imported} transactions importées et validées automatiquement. "
                      "{duplicates} doublons ignorés.").format(
                        imported=created_count,
                        duplicates=result.duplicate_count
                    )
                )
                # Rediriger vers le dashboard finances (les transactions sont comptabilisées)
                return redirect('finances:dashboard')
            else:
                messages.success(
                    request,
                    _("Import réussi! {} transactions importées, {} doublons ignorés.").format(
                        result.imported_count,
                        result.duplicate_count
                    )
                )

            if result.error_count > 0:
                messages.warning(
                    request,
                    _("{} erreurs lors de l'import.").format(result.error_count)
                )

            # Rediriger vers les transactions à réconcilier
            return redirect('finances:bank_reconciliation_pending')

        else:
            for error in result.errors:
                messages.error(request, error)
            return redirect('finances:bank_import_dashboard')

    except Exception as e:
        logger.exception(f"Erreur lors de la confirmation d'import: {e}")
        messages.error(request, _("Erreur lors de l'import: {}").format(str(e)))
        return redirect('finances:bank_import_dashboard')


def _auto_validate_imported_transactions(batch_id, user):
    """
    Valide automatiquement toutes les BankTransaction d'un batch
    et crée les Transaction correspondantes.

    Args:
        batch_id: UUID du batch d'import
        user: Utilisateur effectuant l'action

    Returns:
        int: Nombre de transactions créées
    """
    from apps.finances.models import BankTransaction

    pending_transactions = BankTransaction.objects.filter(
        import_batch_id=batch_id,
        reconciliation_status='pending'
    )

    created_count = 0

    for bank_tx in pending_transactions:
        try:
            # Créer la Transaction standard
            system_tx = _create_transaction_from_bank_tx(bank_tx, user)

            # Marquer comme validé automatiquement
            bank_tx.matched_transaction = system_tx
            bank_tx.reconciliation_status = 'matched'
            bank_tx.reconciled_at = timezone.now()
            bank_tx.reconciled_by = user
            bank_tx.reconciliation_notes = "Validation automatique à l'import"
            bank_tx.save()

            created_count += 1
        except Exception as e:
            logger.error(f"Erreur auto-validation transaction {bank_tx.id}: {e}")

    # Mettre à jour le current_balance du compte financier
    if created_count > 0:
        try:
            from apps.finances.models import BankImportBatch
            from django.db.models import Sum
            from decimal import Decimal

            batch = BankImportBatch.objects.select_related('financial_account').get(pk=batch_id)
            account = batch.financial_account
            if account:
                # Recalculer le solde à partir des transactions validées
                income = Transaction.objects.filter(
                    financial_account=account,
                    type='income',
                    status='validated'
                ).aggregate(s=Sum('amount'))['s'] or Decimal(0)

                expense = Transaction.objects.filter(
                    financial_account=account,
                    type='expense',
                    status='validated'
                ).aggregate(s=Sum('amount'))['s'] or Decimal(0)

                account.current_balance = income - expense
                account.save(update_fields=['current_balance'])
                logger.info(f"Solde du compte {account.name} mis à jour: {account.current_balance}")
        except Exception as e:
            logger.error(f"Erreur mise à jour solde compte: {e}")

    return created_count


@login_required
def bank_import_history(request):
    """
    Historique des imports bancaires.
    """
    batches = BankImportBatch.objects.select_related(
        'financial_account', 'imported_by'
    ).order_by('-import_date')

    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        batches = batches.filter(status=status_filter)

    account_filter = request.GET.get('account')
    if account_filter:
        batches = batches.filter(financial_account_id=account_filter)

    # Pagination
    paginator = Paginator(batches, 20)
    page = request.GET.get('page')
    batches_page = paginator.get_page(page)

    context = {
        'batches': batches_page,
        'accounts': FinancialAccount.objects.filter(is_active=True),
        'status_filter': status_filter,
        'account_filter': account_filter,
        'active_tab': 'history',
    }

    return render(request, 'finances/banking/import_history.html', context)


@login_required
def bank_import_detail(request, batch_id):
    """
    Détail d'un lot d'import.
    """
    batch = get_object_or_404(
        BankImportBatch.objects.select_related('financial_account', 'imported_by'),
        pk=batch_id
    )

    transactions = batch.transactions.all().order_by('-transaction_date')

    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        transactions = transactions.filter(reconciliation_status=status_filter)

    type_filter = request.GET.get('type')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)

    # Pagination
    paginator = Paginator(transactions, 50)
    page = request.GET.get('page')
    transactions_page = paginator.get_page(page)

    context = {
        'batch': batch,
        'transactions': transactions_page,
        'status_filter': status_filter,
        'type_filter': type_filter,
    }

    return render(request, 'finances/banking/import_detail.html', context)


# === Vues de réconciliation ===

@login_required
def bank_reconciliation_pending(request):
    """
    Liste des transactions en attente de réconciliation.
    """
    transactions = BankTransaction.objects.filter(
        reconciliation_status='pending'
    ).select_related(
        'import_batch__financial_account'
    ).order_by('-transaction_date')

    # Filtres
    type_filter = request.GET.get('type')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)

    search = request.GET.get('search')
    if search:
        transactions = transactions.filter(
            Q(counterparty_name__icontains=search) |
            Q(communication__icontains=search)
        )

    # Statistiques
    stats = {
        'total_pending': transactions.count(),
        'total_income': transactions.filter(
            transaction_type='INCOME'
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'total_expense': transactions.filter(
            transaction_type='EXPENSE'
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }

    # Pagination
    paginator = Paginator(transactions, 30)
    page = request.GET.get('page')
    transactions_page = paginator.get_page(page)

    context = {
        'transactions': transactions_page,
        'stats': stats,
        'type_filter': type_filter,
        'search': search,
        'active_tab': 'reconciliation',
    }

    return render(request, 'finances/banking/reconciliation_pending.html', context)


@login_required
def bank_transaction_reconcile(request, transaction_id):
    """
    Réconciliation manuelle d'une transaction.
    Crée automatiquement une Transaction standard lors de la réconciliation.
    """
    from apps.finances.models import Transaction

    bank_tx = get_object_or_404(BankTransaction, pk=transaction_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'match_practitioner':
            practitioner_id = request.POST.get('practitioner_id')
            if practitioner_id:
                practitioner = get_object_or_404(Practitioner, pk=practitioner_id)

                # Créer une Transaction standard
                system_tx = _create_transaction_from_bank_tx(bank_tx, request.user)

                bank_tx.mark_as_matched(
                    transaction=system_tx,
                    practitioner=practitioner,
                    user=request.user,
                    score=100
                )
                messages.success(request, _("Transaction réconciliée et créée dans le système."))

        elif action == 'assign_category':
            category_id = request.POST.get('category_id')
            if category_id:
                category = get_object_or_404(TransactionCategory, pk=category_id)

                # Créer une Transaction standard avec la catégorie
                system_tx = _create_transaction_from_bank_tx(bank_tx, request.user, category=category)

                bank_tx.matched_transaction = system_tx
                bank_tx.matched_category = category
                bank_tx.reconciliation_status = 'matched'
                bank_tx.reconciled_at = timezone.now()
                bank_tx.reconciled_by = request.user
                bank_tx.save()
                messages.success(request, _("Transaction créée et catégorie assignée."))

        elif action == 'ignore':
            reason = request.POST.get('reason', '')
            bank_tx.mark_as_ignored(user=request.user, reason=reason)
            messages.success(request, _("Transaction ignorée."))

        return redirect('finances:bank_reconciliation_pending')

    # GET - Afficher les suggestions
    recon_service = ReconciliationService()
    suggestions = recon_service.get_suggestions(bank_tx)

    # Listes pour sélection manuelle
    practitioners = Practitioner.objects.all().order_by('last_name', 'first_name')[:100]
    categories = TransactionCategory.objects.filter(active=True).order_by('name')

    context = {
        'transaction': bank_tx,
        'suggestions': suggestions,
        'practitioners': practitioners,
        'categories': categories,
    }

    return render(request, 'finances/banking/transaction_reconcile.html', context)


@login_required
def bank_transaction_auto_reconcile(request):
    """
    Réconciliation automatique des transactions en attente.
    Accepte GET (affiche info) et POST (exécute).
    Crée également les Transaction standard pour chaque match.
    """
    if request.method == 'GET':
        # Rediriger vers la page de réconciliation avec un message
        messages.info(request, _("Utilisez le bouton 'Réconciliation auto' pour lancer le processus."))
        return redirect('finances:bank_reconciliation_pending')

    # POST - exécuter la réconciliation
    min_confidence = int(request.POST.get('min_confidence', 90))

    pending_transactions = BankTransaction.objects.filter(
        reconciliation_status='pending'
    )

    recon_service = ReconciliationService()

    matched_count = 0
    created_tx_count = 0

    for bank_tx in pending_transactions:
        if recon_service.auto_reconcile(bank_tx, min_confidence=min_confidence):
            matched_count += 1

            # Créer une Transaction standard si pas déjà créée
            if not bank_tx.matched_transaction:
                try:
                    system_tx = _create_transaction_from_bank_tx(
                        bank_tx,
                        request.user,
                        category=bank_tx.matched_category,
                        practitioner=bank_tx.matched_practitioner
                    )
                    bank_tx.matched_transaction = system_tx
                    bank_tx.save()
                    created_tx_count += 1
                except Exception as e:
                    logger.error(f"Erreur création transaction pour {bank_tx.id}: {e}")

    messages.success(
        request,
        _("{matched} transactions réconciliées, {created} transactions créées dans le système.").format(
            matched=matched_count,
            created=created_tx_count
        )
    )

    return redirect('finances:bank_reconciliation_pending')


@login_required
def bank_transaction_validate_all(request):
    """
    Valide toutes les transactions en attente et crée les Transaction standard.
    Utilisé pour importer toutes les transactions sans réconciliation manuelle.
    """
    if request.method != 'POST':
        return redirect('finances:bank_reconciliation_pending')

    pending_transactions = BankTransaction.objects.filter(
        reconciliation_status='pending'
    )

    created_count = 0
    error_count = 0

    for bank_tx in pending_transactions:
        try:
            # Créer la Transaction standard
            system_tx = _create_transaction_from_bank_tx(bank_tx, request.user)

            # Marquer comme validé
            bank_tx.matched_transaction = system_tx
            bank_tx.reconciliation_status = 'matched'
            bank_tx.reconciled_at = timezone.now()
            bank_tx.reconciled_by = request.user
            bank_tx.reconciliation_notes = "Validation en masse"
            bank_tx.save()

            created_count += 1
        except Exception as e:
            logger.error(f"Erreur création transaction pour {bank_tx.id}: {e}")
            error_count += 1

    if error_count > 0:
        messages.warning(
            request,
            _("{created} transactions créées, {errors} erreurs.").format(
                created=created_count,
                errors=error_count
            )
        )
    else:
        messages.success(
            request,
            _("{created} transactions créées dans le système.").format(created=created_count)
        )

    return redirect('finances:bank_reconciliation_pending')


# === API endpoints pour AJAX ===

@login_required
def api_search_practitioners(request):
    """
    API pour rechercher des pratiquants (AJAX).
    """
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'results': []})

    practitioners = Practitioner.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).order_by('last_name', 'first_name')[:20]

    results = [
        {
            'id': str(p.id),
            'text': p.full_name,
            'first_name': p.first_name,
            'last_name': p.last_name,
        }
        for p in practitioners
    ]

    return JsonResponse({'results': results})


@login_required
def api_transaction_suggestions(request, transaction_id):
    """
    API pour obtenir les suggestions de réconciliation.
    """
    bank_tx = get_object_or_404(BankTransaction, pk=transaction_id)

    recon_service = ReconciliationService()
    suggestions = recon_service.get_suggestions(bank_tx)

    results = [
        {
            'practitioner_id': str(s.suggested_practitioner.id) if s.suggested_practitioner else None,
            'practitioner_name': s.suggested_practitioner.full_name if s.suggested_practitioner else None,
            'category_id': str(s.suggested_category.id) if s.suggested_category else None,
            'category_name': str(s.suggested_category) if s.suggested_category else None,
            'confidence_score': s.confidence_score,
            'match_reason': s.match_reason,
        }
        for s in suggestions
    ]

    return JsonResponse({'suggestions': results})


# === Tableau de bord de rapprochement ===

@login_required
def bank_reconciliation_dashboard(request):
    """
    Tableau de bord complet du rapprochement bancaire.
    Affiche statistiques, taux de rapprochement, graphiques et analyses.
    """
    from datetime import timedelta
    from django.db.models.functions import TruncDate, TruncWeek, TruncMonth

    today = timezone.now().date()

    # Filtres
    period = request.GET.get('period', '30days')
    selected_account = request.GET.get('account', '')

    # Calculer les dates selon la période
    if period == '7days':
        start_date = today - timedelta(days=7)
    elif period == '30days':
        start_date = today - timedelta(days=30)
    elif period == '90days':
        start_date = today - timedelta(days=90)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:  # 'all'
        start_date = None

    # Base queryset
    transactions_qs = BankTransaction.objects.all()

    if start_date:
        transactions_qs = transactions_qs.filter(transaction_date__gte=start_date)

    if selected_account:
        transactions_qs = transactions_qs.filter(
            import_batch__financial_account_id=selected_account
        )

    # Statistiques principales
    total = transactions_qs.count()
    reconciled = transactions_qs.filter(reconciliation_status='matched').count()
    pending = transactions_qs.filter(reconciliation_status='pending').count()
    ignored = transactions_qs.filter(reconciliation_status='ignored').count()

    # Auto-matched vs manual
    auto_matched = transactions_qs.filter(
        reconciliation_status='matched',
        reconciliation_notes__icontains='auto'
    ).count()
    manual_matched = reconciled - auto_matched

    # Taux de rapprochement
    reconciliation_rate = (reconciled / total * 100) if total > 0 else 0

    # Montants par statut et type
    reconciled_income = transactions_qs.filter(
        reconciliation_status='matched',
        transaction_type='INCOME'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    reconciled_expense = transactions_qs.filter(
        reconciliation_status='matched',
        transaction_type='EXPENSE'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    pending_income = transactions_qs.filter(
        reconciliation_status='pending',
        transaction_type='INCOME'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    pending_expense = transactions_qs.filter(
        reconciliation_status='pending',
        transaction_type='EXPENSE'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Calculs de pourcentages pour les barres de progression
    max_amount = max(reconciled_income, reconciled_expense, Decimal('1'))
    income_percent = float(reconciled_income / max_amount * 100) if max_amount else 0
    expense_percent = float(reconciled_expense / max_amount * 100) if max_amount else 0

    stats = {
        'total': total,
        'reconciled': reconciled,
        'pending': pending,
        'unmatched': pending,  # alias
        'auto_matched': auto_matched,
        'manual_matched': manual_matched,
        'reconciliation_rate': reconciliation_rate,
        'reconciled_income': reconciled_income,
        'reconciled_expense': reconciled_expense,
        'reconciled_balance': reconciled_income - reconciled_expense,
        'pending_income': pending_income,
        'pending_expense': pending_expense,
        'pending_total': pending_income + pending_expense,
        'income_percent': income_percent,
        'expense_percent': expense_percent,
    }

    # Statistiques par méthode de paiement
    payment_methods = transactions_qs.values('payment_method').annotate(
        count=Count('id'),
        amount=Sum('amount'),
        reconciled_count=Count('id', filter=Q(reconciliation_status='matched'))
    ).order_by('-count')

    # Mapping icônes et couleurs pour les méthodes de paiement
    method_icons = {
        'virement': ('exchange-alt', 'primary'),
        'virement_instantane': ('bolt', 'warning'),
        'paiement_carte': ('credit-card', 'info'),
        'paiement_carte_credit': ('credit-card', 'danger'),
        'prelevement': ('file-invoice', 'secondary'),
        'cheque': ('money-check', 'success'),
        'especes': ('money-bill', 'success'),
        'mobile_money': ('mobile-alt', 'warning'),
        'autre': ('question-circle', 'secondary'),
    }

    stats_by_method = []
    for pm in payment_methods:
        method_code = pm['payment_method'] or 'autre'
        icon, color = method_icons.get(method_code, ('question-circle', 'secondary'))
        reconciled_percent = (pm['reconciled_count'] / pm['count'] * 100) if pm['count'] > 0 else 0
        stats_by_method.append({
            'code': method_code,
            'name': method_code.replace('_', ' ').title(),
            'icon': icon,
            'color': color,
            'count': pm['count'],
            'amount': pm['amount'] or Decimal('0.00'),
            'reconciled_percent': round(reconciled_percent, 1),
        })

    # Top contreparties non rapprochées
    top_unmatched_counterparties = transactions_qs.filter(
        reconciliation_status='pending'
    ).exclude(
        counterparty_name__isnull=True
    ).exclude(
        counterparty_name=''
    ).values('counterparty_name').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')[:10]

    top_unmatched_counterparties = [
        {'name': item['counterparty_name'], 'count': item['count'], 'total': item['total']}
        for item in top_unmatched_counterparties
    ]

    # Transactions récentes non rapprochées
    recent_unmatched = transactions_qs.filter(
        reconciliation_status='pending'
    ).order_by('-transaction_date')[:10]

    # Données pour le graphique temporel
    if period == '7days':
        trunc_func = TruncDate
        date_format = '%d/%m'
    elif period in ['30days', '90days']:
        trunc_func = TruncWeek
        date_format = 'S%W'
    else:
        trunc_func = TruncMonth
        date_format = '%m/%Y'

    chart_data = transactions_qs.annotate(
        period=trunc_func('transaction_date')
    ).values('period').annotate(
        imported=Count('id'),
        reconciled=Count('id', filter=Q(reconciliation_status='matched'))
    ).order_by('period')

    chart_labels = []
    chart_imported = []
    chart_reconciled = []

    for item in chart_data:
        if item['period']:
            chart_labels.append(item['period'].strftime(date_format))
            chart_imported.append(item['imported'])
            chart_reconciled.append(item['reconciled'])

    # Liste des comptes pour le filtre
    accounts = FinancialAccount.objects.filter(is_active=True)

    context = {
        'stats': stats,
        'stats_by_method': stats_by_method,
        'top_unmatched_counterparties': top_unmatched_counterparties,
        'recent_unmatched': recent_unmatched,
        'accounts': accounts,
        'period': period,
        'selected_account': selected_account,
        'currency': 'EUR',  # TODO: adapter selon le compte
        'chart_labels': json.dumps(chart_labels),
        'chart_imported': json.dumps(chart_imported),
        'chart_reconciled': json.dumps(chart_reconciled),
        'active_tab': 'dashboard',
    }

    return render(request, 'finances/banking/reconciliation_dashboard.html', context)


@login_required
def bank_reconciliation_export_pdf(request):
    """
    Exporte le rapport de rapprochement en PDF.
    """
    from datetime import timedelta
    from io import BytesIO

    # Essayer d'importer reportlab
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        messages.error(request, _("Le module reportlab n'est pas installé. Export PDF non disponible."))
        return redirect('finances:bank_reconciliation_dashboard')

    today = timezone.now().date()

    # Filtres (mêmes que le dashboard)
    period = request.GET.get('period', '30days')
    selected_account = request.GET.get('account', '')

    if period == '7days':
        start_date = today - timedelta(days=7)
        period_label = _("7 derniers jours")
    elif period == '30days':
        start_date = today - timedelta(days=30)
        period_label = _("30 derniers jours")
    elif period == '90days':
        start_date = today - timedelta(days=90)
        period_label = _("90 derniers jours")
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        period_label = _("Année en cours")
    else:
        start_date = None
        period_label = _("Toutes les données")

    # Requête des transactions
    transactions_qs = BankTransaction.objects.all()

    if start_date:
        transactions_qs = transactions_qs.filter(transaction_date__gte=start_date)

    if selected_account:
        transactions_qs = transactions_qs.filter(
            import_batch__financial_account_id=selected_account
        )

    # Statistiques
    total = transactions_qs.count()
    reconciled = transactions_qs.filter(reconciliation_status='matched').count()
    pending = transactions_qs.filter(reconciliation_status='pending').count()
    reconciliation_rate = (reconciled / total * 100) if total > 0 else 0

    reconciled_income = transactions_qs.filter(
        reconciliation_status='matched',
        transaction_type='INCOME'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    reconciled_expense = transactions_qs.filter(
        reconciliation_status='matched',
        transaction_type='EXPENSE'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    pending_income = transactions_qs.filter(
        reconciliation_status='pending',
        transaction_type='INCOME'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    pending_expense = transactions_qs.filter(
        reconciliation_status='pending',
        transaction_type='EXPENSE'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Créer le PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title-Custom',
        parent=styles['Heading1'],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    ))
    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=30
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10
    ))

    elements = []

    # Titre
    elements.append(Paragraph(
        str(_("Rapport de Rapprochement Bancaire")),
        styles['Title-Custom']
    ))
    elements.append(Paragraph(
        f"{str(period_label)} - {str(_('Généré le'))} {today.strftime('%d/%m/%Y')}",
        styles['Subtitle']
    ))

    # Résumé
    elements.append(Paragraph(str(_("Résumé")), styles['SectionTitle']))

    summary_data = [
        [str(_("Indicateur")), str(_("Valeur"))],
        [str(_("Total transactions")), str(total)],
        [str(_("Transactions rapprochées")), str(reconciled)],
        [str(_("Transactions en attente")), str(pending)],
        [str(_("Taux de rapprochement")), f"{reconciliation_rate:.1f}%"],
    ]

    summary_table = Table(summary_data, colWidths=[10*cm, 5*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Montants
    elements.append(Paragraph(str(_("Détail des Montants")), styles['SectionTitle']))

    amounts_data = [
        [str(_("Catégorie")), str(_("Entrées (EUR)")), str(_("Sorties (EUR)")), str(_("Solde (EUR)"))],
        [
            str(_("Rapprochées")),
            f"{reconciled_income:,.2f}".replace(',', ' '),
            f"{reconciled_expense:,.2f}".replace(',', ' '),
            f"{(reconciled_income - reconciled_expense):,.2f}".replace(',', ' ')
        ],
        [
            str(_("En attente")),
            f"{pending_income:,.2f}".replace(',', ' '),
            f"{pending_expense:,.2f}".replace(',', ' '),
            f"{(pending_income - pending_expense):,.2f}".replace(',', ' ')
        ],
    ]

    amounts_table = Table(amounts_data, colWidths=[5*cm, 4*cm, 4*cm, 4*cm])
    amounts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#198754')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    elements.append(amounts_table)
    elements.append(Spacer(1, 20))

    # Transactions non rapprochées (top 20)
    unmatched = transactions_qs.filter(
        reconciliation_status='pending'
    ).order_by('-amount')[:20]

    if unmatched:
        elements.append(Paragraph(
            str(_("Transactions non rapprochées (Top 20)")),
            styles['SectionTitle']
        ))

        unmatched_data = [
            [str(_("Date")), str(_("Description")), str(_("Contrepartie")), str(_("Montant"))]
        ]

        for tx in unmatched:
            unmatched_data.append([
                tx.transaction_date.strftime('%d/%m/%Y'),
                (tx.communication or '-')[:40],
                (tx.counterparty_name or '-')[:25],
                f"{'+' if tx.transaction_type == 'INCOME' else '-'}{tx.amount:,.2f} {tx.currency}".replace(',', ' ')
            ])

        unmatched_table = Table(unmatched_data, colWidths=[2.5*cm, 7*cm, 4*cm, 3.5*cm])
        unmatched_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff3cd')]),
        ]))
        elements.append(unmatched_table)

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        f"MartialComp - {str(_('Rapport généré automatiquement'))}",
        ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
    ))

    # Construire le PDF
    doc.build(elements)

    # Retourner le PDF
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_rapprochement_{today.strftime("%Y%m%d")}.pdf"'

    return response
