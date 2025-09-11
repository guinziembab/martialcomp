from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import json
import logging

from .models import (
    OrganizationPaymentCapability, RegionalPaymentConfig, CountryPaymentConfig,
    PaymentGatewayConfig, Transaction, PaymentAttempt, ManualPaymentTracking,
    PaymentWebhook, PaymentRefund, PaymentError
)
from .services import (
    PaymentCapabilityService, PaymentGatewaySelector, 
    RegionalPricingService, PaymentProcessingService
)
from .forms import PaymentCapabilityForm, PaymentGatewayConfigForm, RefundForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)


@login_required
def payment_dashboard(request):
    """Tableau de bord des paiements pour une organisation"""
    organization = request.user.organization
    
    if not organization:
        messages.error(request, "Aucune organisation associée Ã  votre compte.")
        return redirect('home')
    
    # Récupérer les statistiques de paiement
    transactions = Transaction.objects.filter(organization=organization)
    recent_transactions = transactions.order_by('-created_at')[:10]
    
    # Statistiques
    total_transactions = transactions.count()
    completed_transactions = transactions.filter(status='COMPLETED').count()
    pending_transactions = transactions.filter(status='PENDING').count()
    total_amount = transactions.filter(status='COMPLETED').aggregate(
        total=models.Sum('amount')
    )['total'] or 0
    
    # Capacités de paiement
    try:
        capability = OrganizationPaymentCapability.objects.get(organization=organization)
    except OrganizationPaymentCapability.DoesNotExist:
        capability = None
    
    # Passerelles configurées
    gateways = PaymentGatewayConfig.objects.filter(
        organization=organization,
        is_active=True
    )
    
    context = {
        'organization': organization,
        'capability': capability,
        'gateways': gateways,
        'recent_transactions': recent_transactions,
        'stats': {
            'total_transactions': total_transactions,
            'completed_transactions': completed_transactions,
            'pending_transactions': pending_transactions,
            'total_amount': total_amount,
        }
    }
    
    return render(request, 'competitions/payment/dashboard.html', context)


@login_required
def payment_capability_setup(request):
    """Configuration des capacités de paiement d'une organisation"""
    organization = request.user.organization
    
    if not organization:
        messages.error(request, "Aucune organisation associée Ã  votre compte.")
        return redirect('home')
    
    if request.method == 'POST':
        form = PaymentCapabilityForm(request.POST)
        if form.is_valid():
            answers = form.cleaned_data
            
            # Ã‰valuer les capacités de l'organisation
            capability = PaymentCapabilityService.evaluate_organization_capabilities(
                organization, answers
            )
            
            # Configurer les solutions de paiement
            setup_result = PaymentCapabilityService.setup_payment_solution(organization)
            
            if setup_result['setup_status'] == 'SUCCESS':
                messages.success(request, "Configuration des paiements mise Ã  jour avec succès.")
                return redirect('payment_dashboard')
            else:
                messages.error(request, f"Erreur lors de la configuration: {setup_result.get('error_message', 'Erreur inconnue')}")
    else:
        form = PaymentCapabilityForm()
    
    context = {
        'organization': organization,
        'form': form,
    }
    
    return render(request, 'competitions/payment/capability_setup.html', context)


@login_required
def payment_gateway_config(request, gateway_id=None):
    """Configuration d'une passerelle de paiement"""
    organization = request.user.organization
    
    if not organization:
        messages.error(request, "Aucune organisation associée Ã  votre compte.")
        return redirect('home')
    
    if gateway_id:
        gateway = get_object_or_404(PaymentGatewayConfig, id=gateway_id, organization=organization)
    else:
        gateway = None
    
    if request.method == 'POST':
        form = PaymentGatewayConfigForm(request.POST, instance=gateway)
        if form.is_valid():
            gateway = form.save(commit=False)
            gateway.organization = organization
            gateway.save()
            
            messages.success(request, "Configuration de la passerelle mise Ã  jour.")
            return redirect('payment_dashboard')
    else:
        form = PaymentGatewayConfigForm(instance=gateway)
    
    context = {
        'organization': organization,
        'gateway': gateway,
        'form': form,
    }
    
    return render(request, 'competitions/payment/gateway_config.html', context)


@login_required
def create_payment(request):
    """Création d'un nouveau paiement"""
    organization = request.user.organization
    
    if not organization:
        messages.error(request, "Aucune organisation associée Ã  votre compte.")
        return redirect('home')
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        currency = request.POST.get('currency', 'EUR')
        payment_method = request.POST.get('payment_method')
        description = request.POST.get('description', '')
        
        if not amount or not payment_method:
            messages.error(request, "Montant et méthode de paiement requis.")
            return redirect('payment_dashboard')
        
        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, "Montant invalide.")
            return redirect('payment_dashboard')
        
        # Traiter le paiement
        user_data = {
            'user': request.user,
            'user_id': request.user.id,
            'email': request.user.email,
            'country': organization.country
        }
        
        result = PaymentProcessingService.process_payment(
            organization=organization,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            user_data=user_data,
            metadata={'description': description}
        )
        
        if result['success']:
            messages.success(request, "Paiement initié avec succès.")
            return redirect('payment_detail', payment_id=result['payment_attempt_id'])
        else:
            messages.error(request, f"Erreur lors du traitement du paiement: {result.get('error', 'Erreur inconnue')}")
            return redirect('payment_dashboard')
    
    # Récupérer les méthodes de paiement disponibles
    gateways = PaymentGatewayConfig.objects.filter(
        organization=organization,
        is_active=True
    )
    
    context = {
        'organization': organization,
        'gateways': gateways,
    }
    
    return render(request, 'competitions/payment/create_payment.html', context)


@login_required
def payment_detail(request, payment_id):
    """Détails d'une tentative de paiement"""
    payment_attempt = get_object_or_404(PaymentAttempt, id=payment_id)
    organization = request.user.organization
    
    if payment_attempt.organization != organization:
        raise PermissionDenied("Vous n'avez pas accès Ã  ce paiement.")
    
    context = {
        'payment_attempt': payment_attempt,
        'organization': organization,
    }
    
    return render(request, 'competitions/payment/payment_detail.html', context)


@login_required
def payment_list(request):
    """Liste des paiements d'une organisation"""
    organization = request.user.organization
    
    if not organization:
        messages.error(request, "Aucune organisation associée Ã  votre compte.")
        return redirect('home')
    
    payments = PaymentAttempt.objects.filter(organization=organization).order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    method_filter = request.GET.get('method')
    if method_filter:
        payments = payments.filter(payment_method=method_filter)
    
    context = {
        'payments': payments,
        'organization': organization,
    }
    
    return render(request, 'competitions/payment/payment_list.html', context)


@login_required
def payment_success(request, payment_id):
    """Page de succès de paiement"""
    payment_attempt = get_object_or_404(PaymentAttempt, id=payment_id)
    organization = request.user.organization
    
    if payment_attempt.organization != organization:
        raise PermissionDenied("Vous n'avez pas accès Ã  ce paiement.")
    
    # Mettre Ã  jour le statut si nécessaire
    if payment_attempt.status == 'PROCESSING':
        payment_attempt.status = 'SUCCESS'
        payment_attempt.save()
        
        # Mettre Ã  jour la transaction
        transaction = payment_attempt.transaction
        transaction.status = 'COMPLETED'
        transaction.save()
    
    context = {
        'payment_attempt': payment_attempt,
        'organization': organization,
    }
    
    return render(request, 'competitions/payment/payment_success.html', context)


@login_required
def payment_cancel(request, payment_id):
    """Page d'annulation de paiement"""
    payment_attempt = get_object_or_404(PaymentAttempt, id=payment_id)
    organization = request.user.organization
    
    if payment_attempt.organization != organization:
        raise PermissionDenied("Vous n'avez pas accès Ã  ce paiement.")
    
    # Mettre Ã  jour le statut
    payment_attempt.status = 'CANCELLED'
    payment_attempt.save()
    
    context = {
        'payment_attempt': payment_attempt,
        'organization': organization,
    }
    
    return render(request, 'competitions/payment/payment_cancel.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def payment_webhook(request, provider):
    """Webhook pour les notifications de paiement"""
    try:
        # Récupérer les données du webhook
        payload = json.loads(request.body)
        headers = dict(request.headers)
        
        # Déterminer le type d'événement
        event_type = payload.get('type', 'unknown')
        
        # Traiter le webhook
        result = PaymentProcessingService.handle_webhook(
            provider=provider,
            event_type=event_type,
            payload=payload,
            headers=headers
        )
        
        if result['status'] == 'SUCCESS':
            return HttpResponse(status=200)
        else:
            logger.error(f"Webhook processing failed: {result}")
            return HttpResponse(status=400)
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return HttpResponse(status=500)


@login_required
def refund_payment(request, payment_id):
    """Demande de remboursement"""
    payment_attempt = get_object_or_404(PaymentAttempt, id=payment_id)
    organization = request.user.organization
    
    if payment_attempt.organization != organization:
        raise PermissionDenied("Vous n'avez pas accès Ã  ce paiement.")
    
    if payment_attempt.status != 'SUCCESS':
        messages.error(request, "Seuls les paiements réussis peuvent Ãªtre remboursés.")
        return redirect('payment_detail', payment_id=payment_id)
    
    if request.method == 'POST':
        form = RefundForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            reason = form.cleaned_data['reason']
            
            # Créer le remboursement
            refund = PaymentRefund.objects.create(
                transaction=payment_attempt.transaction,
                payment_attempt=payment_attempt,
                amount=amount,
                currency=payment_attempt.currency,
                reason=reason
            )
            
            # Traiter le remboursement (Ã  implémenter selon la passerelle)
            # Pour l'instant, on simule un succès
            refund.status = 'COMPLETED'
            refund.save()
            
            messages.success(request, "Remboursement initié avec succès.")
            return redirect('payment_detail', payment_id=payment_id)
    else:
        form = RefundForm(initial={'amount': payment_attempt.amount})
    
    context = {
        'payment_attempt': payment_attempt,
        'form': form,
        'organization': organization,
    }
    
    return render(request, 'competitions/payment/refund_payment.html', context)


@login_required
def manual_payment_verification(request, payment_id):
    """Vérification manuelle d'un paiement"""
    payment_attempt = get_object_or_404(PaymentAttempt, id=payment_id)
    organization = request.user.organization
    
    if payment_attempt.organization != organization:
        raise PermissionDenied("Vous n'avez pas accès Ã  ce paiement.")
    
    if request.method == 'POST':
        verification_status = request.POST.get('verification_status')
        payment_reference = request.POST.get('payment_reference', '')
        proof_notes = request.POST.get('proof_notes', '')
        
        # Créer ou mettre Ã  jour le suivi manuel
        manual_tracking, created = ManualPaymentTracking.objects.get_or_create(
            organization=organization,
            transaction=payment_attempt.transaction,
            defaults={
                'payment_method': payment_attempt.payment_method,
                'payment_reference': payment_reference,
                'proof_notes': proof_notes,
                'claimed_payment_date': timezone.now(),
            }
        )
        
        if not created:
            manual_tracking.payment_reference = payment_reference
            manual_tracking.proof_notes = proof_notes
        
        manual_tracking.verification_status = verification_status
        manual_tracking.verified_by = request.user
        manual_tracking.verification_date = timezone.now()
        manual_tracking.save()
        
        # Mettre Ã  jour le statut de la tentative de paiement
        if verification_status == 'VERIFIED':
            payment_attempt.status = 'SUCCESS'
            payment_attempt.transaction.status = 'COMPLETED'
        elif verification_status == 'REJECTED':
            payment_attempt.status = 'FAILED'
            payment_attempt.transaction.status = 'FAILED'
        
        payment_attempt.save()
        payment_attempt.transaction.save()
        
        messages.success(request, "Statut de vérification mis Ã  jour.")
        return redirect('payment_detail', payment_id=payment_id)
    
    # Récupérer le suivi manuel existant
    try:
        manual_tracking = ManualPaymentTracking.objects.get(
            organization=organization,
            transaction=payment_attempt.transaction
        )
    except ManualPaymentTracking.DoesNotExist:
        manual_tracking = None
    
    context = {
        'payment_attempt': payment_attempt,
        'manual_tracking': manual_tracking,
        'organization': organization,
    }
    
    return render(request, 'competitions/payment/manual_verification.html', context)


@login_required
def regional_pricing(request):
    """Affichage des tarifs régionaux"""
    # Récupérer toutes les configurations régionales
    regional_configs = get_organization_queryset(RegionalPaymentConfig, self.request.user).order_by('region')
    
    # Calculer les tarifs pour chaque région
    pricing_data = []
    for config in regional_configs:
        club_price, currency = RegionalPricingService.get_price_for_region('subscription', config.region, 'club')
        pro_price, _ = RegionalPricingService.get_price_for_region('subscription', config.region, 'pro')
        fed_price, _ = RegionalPricingService.get_price_for_region('subscription', config.region, 'fed')
        
        pricing_data.append({
            'region': config,
            'club_price': club_price,
            'pro_price': pro_price,
            'fed_price': fed_price,
            'currency': currency,
        })
    
    context = {
        'pricing_data': pricing_data,
    }
    
    return render(request, 'competitions/payment/regional_pricing.html', context)


# Vues API pour AJAX
@login_required
def api_payment_methods(request):
    """API pour récupérer les méthodes de paiement disponibles"""
    organization = request.user.organization
    
    if not organization:
        return JsonResponse({'error': 'Aucune organisation associée'}, status=400)
    
    gateways = PaymentGatewayConfig.objects.filter(
        organization=organization,
        is_active=True
    )
    
    methods = []
    for gateway in gateways:
        methods.append({
            'id': gateway.id,
            'provider': gateway.provider,
            'display_name': gateway.display_name or gateway.provider,
            'is_default': gateway.is_default,
        })
    
    return JsonResponse({'methods': methods})


@login_required
def api_payment_status(request, payment_id):
    """API pour vérifier le statut d'un paiement"""
    payment_attempt = get_object_or_404(PaymentAttempt, id=payment_id)
    organization = request.user.organization
    
    if payment_attempt.organization != organization:
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    
    return JsonResponse({
        'status': payment_attempt.status,
        'amount': str(payment_attempt.amount),
        'currency': payment_attempt.currency,
        'created_at': payment_attempt.created_at.isoformat(),
    }) 
