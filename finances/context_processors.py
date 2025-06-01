from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
from finances.models import Transaction, Invoice, FinancialAccount

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
    
    return {'financial_stats': stats}