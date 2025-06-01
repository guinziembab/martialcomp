import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings

from ..models.order import Order
from ..models.payment import PaymentMethod, Payment
from ..services.payment_service import PaymentService
from competitions.utils.decorators import club_required, federation_required

logger = logging.getLogger(__name__)


@login_required
def payment_methods(request, order_id):
    """
    Display available payment methods for an order
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order is already paid
    if order.status != 'pending':
        messages.warning(request, _("Cette commande n'est pas en attente de paiement."))
        return redirect('shop:order_confirmation', order.order_number)
    
    # Get available payment methods
    entity = None
    if order.club:
        entity = order.club
    elif order.federation:
        entity = order.federation
    
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    # Filter by entity type
    if entity:
        if hasattr(entity, 'club_type'):  # Club
            payment_methods = payment_methods.filter(available_for_clubs=True)
        elif hasattr(entity, 'website'):  # Federation
            payment_methods = payment_methods.filter(available_for_federations=True)
    
    # Filter by specific entity if needed
    available_methods = []
    for method in payment_methods:
        if not entity or method.is_available_for_entity(entity):
            available_methods.append(method)
    
    context = {
        'order': order,
        'payment_methods': available_methods,
    }
    
    return render(request, 'shop/checkout/payment_methods.html', context)


@login_required
@require_POST
def process_payment(request, order_id):
    """
    Process payment for an order
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order is already paid
    if order.status != 'pending':
        messages.warning(request, _("Cette commande n'est pas en attente de paiement."))
        return redirect('shop:order_confirmation', order.order_number)
    
    # Get payment method
    payment_method_id = request.POST.get('payment_method')
    if not payment_method_id:
        messages.error(request, _("Veuillez sélectionner une méthode de paiement."))
        return redirect('shop:payment_methods', order.id)
    
    try:
        payment_method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
    except PaymentMethod.DoesNotExist:
        messages.error(request, _("Méthode de paiement invalide."))
        return redirect('shop:payment_methods', order.id)
    
    # Process payment
    result = PaymentService.initialize_payment(order, payment_method, request)
    
    if not result.success:
        messages.error(request, result.error_message or _("Une erreur est survenue lors du traitement du paiement."))
        return redirect('shop:payment_methods', order.id)
    
    # Handle payment result
    if result.is_redirect:
        # External payment flow (e.g., PayPal)
        return redirect(result.redirect_url)
    else:
        # Direct payment (e.g., credit card processed on our side)
        if result.payment.status == 'completed':
            messages.success(request, _("Paiement effectué avec succès."))
            return redirect('shop:order_confirmation', order.order_number)
        elif result.payment.status == 'pending':
            # Bank transfer or other manual payment
            messages.info(request, _("Votre commande est en attente de paiement. Les instructions ont été envoyées par email."))
            return redirect('shop:order_confirmation', order.order_number)
        else:
            # Other status
            return redirect('shop:order_confirmation', order.order_number)


@login_required
def payment_callback(request, payment_id):
    """
    Callback endpoint for external payment processors
    """
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return HttpResponseBadRequest("Invalid payment ID")
    
    # Verify this is the user's payment
    if payment.order.user != request.user:
        return HttpResponseBadRequest("Unauthorized")
    
    # Get transaction data from request
    transaction_data = {}
    if request.method == 'POST':
        transaction_data = request.POST.dict()
    elif request.method == 'GET':
        transaction_data = request.GET.dict()
    
    # Complete the payment
    result = PaymentService.complete_payment(payment.id, transaction_data)
    
    if result.success:
        messages.success(request, _("Paiement effectué avec succès."))
        return redirect('shop:order_confirmation', payment.order.order_number)
    else:
        messages.error(request, result.error_message or _("Une erreur est survenue lors du traitement du paiement."))
        return redirect('shop:order_confirmation', payment.order.order_number)


@login_required
def payment_simulate_paypal(request, payment_id):
    """
    Simulate a PayPal payment flow for demonstration purposes
    """
    try:
        payment = Payment.objects.get(id=payment_id)
    except Payment.DoesNotExist:
        return HttpResponseBadRequest("Invalid payment ID")
    
    # Verify this is the user's payment
    if payment.order.user != request.user:
        return HttpResponseBadRequest("Unauthorized")
    
    if request.method == 'POST':
        # Complete the payment
        result = PaymentService.complete_payment(payment.id, {
            'type': 'paypal',
            'id': f"pp_{payment.id}",
            'status': 'COMPLETED',
            'payer': {
                'email': payment.payer_email,
                'name': payment.payer_name
            }
        })
        
        if result.success:
            messages.success(request, _("Paiement PayPal effectué avec succès."))
            return redirect('shop:order_confirmation', payment.order.order_number)
        else:
            messages.error(request, result.error_message or _("Une erreur est survenue lors du traitement du paiement."))
            return redirect('shop:order_confirmation', payment.order.order_number)
    
    # Display PayPal simulation page
    context = {
        'payment': payment,
        'order': payment.order,
    }
    
    return render(request, 'shop/checkout/simulate_paypal.html', context)


@login_required
@club_required
def club_refund_payment(request, payment_id):
    """
    Handle payment refund for club admins
    """
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order
    
    # Check if this is the club's order
    if not order.club or not hasattr(request, 'club') or order.club != request.club:
        messages.error(request, _("Vous n'êtes pas autorisé à rembourser ce paiement."))
        return redirect('shop:dashboard_orders')
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        
        try:
            amount = float(amount) if amount else None
        except ValueError:
            messages.error(request, _("Montant de remboursement invalide."))
            return redirect('shop:dashboard_order_detail', order.id)
        
        # Process refund
        result = PaymentService.refund_payment(payment, amount, reason)
        
        if result.success:
            messages.success(request, _("Remboursement effectué avec succès."))
        else:
            messages.error(request, result.error_message or _("Une erreur est survenue lors du remboursement."))
        
        return redirect('shop:dashboard_order_detail', order.id)
    
    # Display refund form
    context = {
        'payment': payment,
        'order': order,
    }
    
    return render(request, 'shop/dashboard/refund_payment.html', context)


@login_required
@federation_required
def federation_refund_payment(request, payment_id):
    """
    Handle payment refund for federation admins
    """
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order
    
    # Check if this is the federation's order
    if not hasattr(order, 'federation') or not hasattr(request, 'federation') or not order.federation or order.federation != request.federation:
        messages.error(request, _("Vous n'êtes pas autorisé à rembourser ce paiement."))
        return redirect('shop:dashboard_orders')
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')
        
        try:
            amount = float(amount) if amount else None
        except ValueError:
            messages.error(request, _("Montant de remboursement invalide."))
            return redirect('shop:dashboard_order_detail', order.id)
        
        # Process refund
        result = PaymentService.refund_payment(payment, amount, reason)
        
        if result.success:
            messages.success(request, _("Remboursement effectué avec succès."))
        else:
            messages.error(request, result.error_message or _("Une erreur est survenue lors du remboursement."))
        
        return redirect('shop:dashboard_order_detail', order.id)
    
    # Display refund form
    context = {
        'payment': payment,
        'order': order,
    }
    
    return render(request, 'shop/dashboard/refund_payment.html', context)