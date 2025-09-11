"""
Adaptateurs pour faire le lien entre l'ancienne API finances et la nouvelle
"""
from django.db.models import Q
from finances.models import Transaction, PaymentMethod, PaymentAttempt, Invoice
from django.contrib.auth.models import User


class PaymentAdapter:
    """Adaptateur pour convertir l'ancienne API Payment vers la nouvelle"""
    
    @staticmethod
    def get_user_payments(user):
        """Obtenir tous les paiements d'un utilisateur"""
        return Transaction.objects.filter(
            Q(created_by=user) | 
            Q(invoice__practitioner__user=user)
        ).filter(type='expense')
    
    @staticmethod
    def get_scheduled_payments(user):
        """Obtenir les paiements planifiés d'un utilisateur"""
        return Transaction.objects.filter(
            Q(created_by=user) | 
            Q(invoice__practitioner__user=user),
            status='pending',
            date__gte=timezone.now().date()
        ).filter(type='expense')
    
    @staticmethod
    def create_payment(invoice, payer, amount, payment_method_type, **kwargs):
        """Créer un nouveau paiement"""
        try:
            payment_method = PaymentMethod.objects.get(type=payment_method_type)
        except PaymentMethod.DoesNotExist:
            payment_method = PaymentMethod.objects.first()
            
        transaction = Transaction.objects.create(
            type='expense',
            amount=amount,
            created_by=payer,
            invoice=invoice,
            payment_method=payment_method,
            description=kwargs.get('description', f'Paiement pour facture {invoice.number}'),
            status=kwargs.get('status', 'pending')
        )
        
        # Créer une tentative de paiement
        payment_attempt = PaymentAttempt.objects.create(
            transaction=transaction,
            payment_method=payment_method,
            amount=amount,
            status='succeeded' if kwargs.get('status') == 'validated' else 'initiated'
        )
        
        return transaction
    
    @staticmethod
    def get_payment_choices():
        """Obtenir les choix de méthodes de paiement"""
        return [(pm.type, pm.name) for pm in PaymentMethod.objects.filter(is_active=True)]


class AccountAdapter:
    """Adaptateur pour l'ancienne API Account"""
    
    @staticmethod
    def get_user_balance(user):
        """Obtenir le solde d'un utilisateur"""
        incomes = Transaction.objects.filter(
            Q(created_by=user) | Q(invoice__practitioner__user=user),
            type='income',
            status='validated'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        expenses = Transaction.objects.filter(
            Q(created_by=user) | Q(invoice__practitioner__user=user),
            type='expense',
            status='validated'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return incomes - expenses