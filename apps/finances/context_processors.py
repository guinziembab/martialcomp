from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
from apps.finances.models import Transaction, Invoice, FinancialAccount
from apps.finances.currency_service import (
    get_preferred_currency_for_request,
    convert_amount,
)

def financial_stats(request):
    """
    Add financial statistics to the context for all templates.
    """
    if not request.user.is_authenticated:
        return {'financial_stats': {}}
    
    # Initialize stats dictionary
    stats = {
        'balance': 0,
        'income': 0,
        'expense': 0,
        'pending_invoices': 0,
        'pending_amount': 0,
        'transactions_count': 0,
        'accounts_count': 0,
        'currency': 'EUR',
    }
    
    # Get data for authenticated users only
    try:
        # Get user content type
        user_type = ContentType.objects.get_for_model(request.user)
        
        # Get total balance using content type and ID
        accounts_balance = FinancialAccount.objects.filter(
            owner_content_type=user_type,
            owner_id=str(request.user.id)
        ).aggregate(
            total=Sum('current_balance')
        )['total'] or 0
        
        stats['balance'] = accounts_balance
        
        # Count accounts
        stats['accounts_count'] = FinancialAccount.objects.filter(
            owner_content_type=user_type,
            owner_id=str(request.user.id)
        ).count()
        
        # Get income and expense totals
        transactions = Transaction.objects.filter(created_by=request.user)
        stats['transactions_count'] = transactions.count()
        
        income_total = transactions.filter(
            type='income'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        expense_total = transactions.filter(
            type='expense'
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        stats['income'] = income_total
        stats['expense'] = expense_total
        
        # Get pending invoices
        pending_invoices = Invoice.objects.filter(
            created_by=request.user,
            status__in=['draft', 'sent', 'unpaid']
        )
        
        stats['pending_invoices'] = pending_invoices.count()
        stats['pending_amount'] = pending_invoices.aggregate(
            total=Sum('total')
        )['total'] or 0
        
    except Exception as e:
        # In case of any error, just return empty stats
        print(f"Error calculating financial stats: {e}")
    
    # Attach preferred currency and convert display values
    try:
        currency, _source = get_preferred_currency_for_request(request)
        # Si on a une org avec un pays, on surclasse avec COUNTRY_TO_CURRENCY
        try:
            from .currency_service import COUNTRY_TO_CURRENCY, _get_request_organization  # type: ignore
            org = _get_request_organization(request)
            if org:
                org_country = getattr(org, 'country', '') or ''
                code = COUNTRY_TO_CURRENCY.get(org_country) or COUNTRY_TO_CURRENCY.get(str(org_country).upper())
                if code:
                    currency = code
        except Exception:
            pass
        stats['currency'] = currency
        # Convert for display (assumes EUR base for aggregates)
        for key in ['balance', 'income', 'expense', 'pending_amount']:
            try:
                value = float(stats.get(key, 0) or 0)
                converted, _ = convert_amount(value, 'EUR', currency)
                stats[key] = converted
            except Exception:
                pass
    except Exception:
        pass
    
    return {'financial_stats': stats}
