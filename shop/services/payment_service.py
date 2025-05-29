import logging
import uuid
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from ..models.payment import Payment, Transaction
from ..models.order import Order, OrderItem

logger = logging.getLogger(__name__)


class PaymentResult:
    """Class to represent payment processing result"""
    
    def __init__(self, success=False, payment=None, redirect_url=None, error_message=None):
        self.success = success
        self.payment = payment
        self.redirect_url = redirect_url
        self.error_message = error_message
    
    @property
    def is_redirect(self):
        return bool(self.redirect_url)


class PaymentService:
    """
    Service class for handling all payment-related operations
    """
    
    @classmethod
    def initialize_payment(cls, order, payment_method, request=None):
        """
        Initialize a payment for an order
        
        Args:
            order: The Order object
            payment_method: The PaymentMethod object
            request: The current request (optional)
            
        Returns:
            PaymentResult object
        """
        if order.status != 'pending':
            return PaymentResult(success=False, error_message=_("La commande n'est pas en attente de paiement"))
        
        # Calculate payment amount and fee
        amount = order.total
        fee = payment_method.get_fee_for_amount(amount)
        
        # Create the payment record
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=amount,
            fee=fee,
            currency='EUR',
            payer_email=order.user.email if order.user else '',
            payer_name=order.user.get_full_name() if order.user else ''
        )
        
        # Process payment based on payment type
        payment_type = payment_method.payment_type
        
        if payment_type == 'card':
            return cls._process_card_payment(payment, request)
        elif payment_type == 'paypal':
            return cls._process_paypal_payment(payment, request)
        elif payment_type == 'bank_transfer':
            return cls._process_bank_transfer(payment, request)
        elif payment_type == 'custom':
            return cls._process_custom_payment(payment, request)
        else:
            payment.status = 'failed'
            payment.admin_notes = f"Méthode de paiement non prise en charge: {payment_type}"
            payment.save()
            return PaymentResult(success=False, payment=payment, 
                                error_message=_("Méthode de paiement non prise en charge"))
    
    @classmethod
    def _process_card_payment(cls, payment, request):
        """Process a credit card payment"""
        # In a real implementation, this would integrate with a payment gateway
        # For now, we'll simulate a successful payment
        
        # Create transaction record
        transaction_data = {
            'payment': payment,
            'transaction_type': 'charge',
            'amount': payment.amount,
            'currency': payment.currency,
            'status': 'succeeded',
            'transaction_id': f"sim_{uuid.uuid4().hex[:10]}",
            'raw_response': {
                'status': 'succeeded',
                'id': f"sim_{uuid.uuid4().hex[:10]}",
                'amount': float(payment.amount),
                'currency': payment.currency,
                'card': {
                    'last4': '4242',
                    'brand': 'Visa',
                    'exp_month': 12,
                    'exp_year': 2025
                }
            }
        }
        
        transaction = Transaction.objects.create(**transaction_data)
        
        # Update payment record
        payment.status = 'completed'
        payment.transaction_id = transaction.transaction_id
        payment.provider_response = transaction.raw_response
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'processing'
        order.is_paid = True
        order.save()
        
        return PaymentResult(success=True, payment=payment)
    
    @classmethod
    def _process_paypal_payment(cls, payment, request):
        """Process a PayPal payment"""
        # In a real implementation, this would redirect to PayPal
        # For now, we'll simulate a PayPal redirect
        
        payment.status = 'processing'
        payment.save()
        
        # Generate a mock redirect URL
        redirect_url = f"{settings.SITE_URL}/shop/payment/simulate-paypal/{payment.id}/"
        
        return PaymentResult(success=True, payment=payment, redirect_url=redirect_url)
    
    @classmethod
    def _process_bank_transfer(cls, payment, request):
        """Process a bank transfer payment"""
        # Bank transfers are handled manually
        
        payment.status = 'pending'
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'on_hold'
        order.save()
        
        return PaymentResult(success=True, payment=payment)
    
    @classmethod
    def _process_custom_payment(cls, payment, request):
        """Process a custom payment method"""
        # Custom payments are handled based on the payment method's configuration
        
        payment.status = 'pending'
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'on_hold'
        order.save()
        
        return PaymentResult(success=True, payment=payment)
    
    @classmethod
    def complete_payment(cls, payment_id, transaction_data=None):
        """
        Complete a payment after external processing
        
        Args:
            payment_id: The payment ID
            transaction_data: Additional transaction data
            
        Returns:
            PaymentResult object
        """
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return PaymentResult(success=False, error_message=_("Paiement non trouvé"))
        
        if payment.status in ['completed', 'refunded', 'cancelled']:
            return PaymentResult(success=False, payment=payment, 
                                error_message=_("Ce paiement a déjà été traité"))
        
        # Create transaction record
        transaction_data = transaction_data or {}
        transaction = Transaction.objects.create(
            payment=payment,
            transaction_type=transaction_data.get('type', 'charge'),
            amount=payment.amount,
            currency=payment.currency,
            status='succeeded',
            transaction_id=transaction_data.get('id', f"ext_{uuid.uuid4().hex[:10]}"),
            raw_response=transaction_data
        )
        
        # Update payment record
        payment.status = 'completed'
        payment.transaction_id = transaction.transaction_id
        payment.provider_response = transaction_data
        payment.save()
        
        # Update order status
        with transaction.atomic():
            order = payment.order
            order.status = 'processing'
            order.is_paid = True
            order.save()
        
        return PaymentResult(success=True, payment=payment)
    
    @classmethod
    def refund_payment(cls, payment, amount=None, reason=None):
        """
        Process a refund for a payment
        
        Args:
            payment: The Payment object
            amount: Amount to refund (defaults to full amount)
            reason: Reason for the refund
            
        Returns:
            PaymentResult object
        """
        if payment.status != 'completed':
            return PaymentResult(success=False, payment=payment, 
                                error_message=_("Seuls les paiements complétés peuvent être remboursés"))
        
        refund_amount = amount or payment.amount
        
        if refund_amount > payment.amount:
            return PaymentResult(success=False, payment=payment, 
                                error_message=_("Le montant du remboursement ne peut pas dépasser le montant du paiement"))
        
        # In a real implementation, this would call the payment gateway's refund API
        # For now, we'll simulate a successful refund
        
        # Create transaction record for the refund
        transaction = Transaction.objects.create(
            payment=payment,
            transaction_type='refund',
            amount=refund_amount,
            currency=payment.currency,
            status='succeeded',
            transaction_id=f"ref_{uuid.uuid4().hex[:10]}",
            raw_response={
                'status': 'succeeded',
                'id': f"ref_{uuid.uuid4().hex[:10]}",
                'amount': float(refund_amount),
                'currency': payment.currency,
                'reason': reason
            }
        )
        
        # Update payment record
        if refund_amount == payment.amount:
            payment.status = 'refunded'
        else:
            payment.status = 'partially_refunded'
        
        payment.refund_reason = reason or ''
        payment.save()
        
        # Update order status if full refund
        if refund_amount == payment.amount:
            order = payment.order
            order.status = 'refunded'
            order.save()
        
        return PaymentResult(success=True, payment=payment)
    
    @classmethod
    def cancel_payment(cls, payment, reason=None):
        """
        Cancel a pending payment
        
        Args:
            payment: The Payment object
            reason: Reason for cancellation
            
        Returns:
            PaymentResult object
        """
        if payment.status not in ['pending', 'processing']:
            return PaymentResult(success=False, payment=payment, 
                                error_message=_("Seuls les paiements en attente peuvent être annulés"))
        
        # Create transaction record for the cancellation
        transaction = Transaction.objects.create(
            payment=payment,
            transaction_type='void',
            amount=payment.amount,
            currency=payment.currency,
            status='succeeded',
            transaction_id=f"void_{uuid.uuid4().hex[:10]}",
            raw_response={
                'status': 'succeeded',
                'id': f"void_{uuid.uuid4().hex[:10]}",
                'amount': float(payment.amount),
                'currency': payment.currency,
                'reason': reason
            }
        )
        
        # Update payment record
        payment.status = 'cancelled'
        payment.admin_notes = (payment.admin_notes or '') + f"\nAnnulé: {reason or 'Aucune raison fournie'}"
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'cancelled'
        order.save()
        
        return PaymentResult(success=True, payment=payment)