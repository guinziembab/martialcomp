from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from .models import (
    SubscriptionPlan, OrganizationSubscription, Payment, 
    PaymentMethod, Refund
)
from .services import (
    SubscriptionService, PaymentService, TrialService, 
    NotificationService
)
from apps.organizations.models import Organization
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def subscription_dashboard(request):
    """Tableau de bord des abonnements"""
    try:
        # Récupérer l'organisation de l'utilisateur
        organization = request.user.organization if hasattr(request.user, 'organization') else None
        
        if not organization:
            messages.error(request, "Aucune organisation associée Ã  votre compte.")
            return redirect('competitions:dashboard')
        
        # Récupérer l'abonnement
        subscription = OrganizationSubscription.objects.filter(
            organization=organization
        ).first()
        
        # Récupérer les plans disponibles
        available_plans = SubscriptionPlan.objects.filter(is_active=True)
        
        # Récupérer l'historique des paiements
        payments = Payment.objects.filter(
            subscription=subscription
        ).order_by('-created_at')[:10] if subscription else []
        
        # Informations d'essai
        trial_info = TrialService.get_trial_info(organization) if organization else None
        
        context = {
            'organization': organization,
            'subscription': subscription,
            'available_plans': available_plans,
            'payments': payments,
            'trial_info': trial_info,
        }
        
        return render(request, 'payment/subscription_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans le tableau de bord des abonnements: {e}")
        messages.error(request, "Une erreur est survenue lors du chargement du tableau de bord.")
        return redirect('competitions:dashboard')

@login_required
def subscription_plans(request):
    """Page des plans d'abonnement"""
    try:
        plans = SubscriptionPlan.objects.filter(is_active=True)
        
        context = {
            'plans': plans,
        }
        
        return render(request, 'payment/subscription_plans.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans la page des plans: {e}")
        messages.error(request, "Une erreur est survenue lors du chargement des plans.")
        return redirect('payment:subscription_dashboard')

@login_required
def upgrade_subscription(request, plan_id):
    """Mise Ã  niveau d'un abonnement"""
    try:
        with transaction.atomic():
            organization = request.user.organization if hasattr(request.user, 'organization') else None
            
            if not organization:
                messages.error(request, "Aucune organisation associée Ã  votre compte.")
                return redirect('payment:subscription_dashboard')
            
            plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)
            subscription = OrganizationSubscription.objects.filter(
                organization=organization
            ).first()
            
            if not subscription:
                # Créer un nouvel abonnement
                subscription = SubscriptionService.create_trial_subscription(organization, plan.plan_type)
            
            # Mettre Ã  niveau l'abonnement
            SubscriptionService.upgrade_subscription(subscription, plan)
            
            messages.success(request, f"Votre abonnement a été mis Ã  niveau vers {plan.name}.")
            return redirect('payment:subscription_dashboard')
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise Ã  niveau: {e}")
        messages.error(request, "Une erreur est survenue lors de la mise Ã  niveau.")
        return redirect('payment:subscription_dashboard')

@login_required
def cancel_subscription(request):
    """Annulation d'un abonnement"""
    try:
        organization = request.user.organization if hasattr(request.user, 'organization') else None
        
        if not organization:
            messages.error(request, "Aucune organisation associée Ã  votre compte.")
            return redirect('payment:subscription_dashboard')
        
        subscription = OrganizationSubscription.objects.filter(
            organization=organization
        ).first()
        
        if subscription:
            SubscriptionService.cancel_subscription(subscription)
            messages.success(request, "Votre abonnement a été annulé avec succès.")
        else:
            messages.error(request, "Aucun abonnement trouvé.")
        
        return redirect('payment:subscription_dashboard')
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation: {e}")
        messages.error(request, "Une erreur est survenue lors de l'annulation.")
        return redirect('payment:subscription_dashboard')

@login_required
def payment_methods(request):
    """Gestion des méthodes de paiement"""
    try:
        organization = request.user.organization if hasattr(request.user, 'organization') else None
        
        if not organization:
            messages.error(request, "Aucune organisation associée Ã  votre compte.")
            return redirect('payment:subscription_dashboard')
        
        payment_methods = PaymentMethod.objects.filter(
            organization=organization,
            is_active=True
        )
        
        context = {
            'organization': organization,
            'payment_methods': payment_methods,
        }
        
        return render(request, 'payment/payment_methods.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans la gestion des méthodes de paiement: {e}")
        messages.error(request, "Une erreur est survenue lors du chargement des méthodes de paiement.")
        return redirect('payment:subscription_dashboard')

@login_required
def add_payment_method(request):
    """Ajout d'une méthode de paiement"""
    if request.method == 'POST':
        try:
            organization = request.user.organization if hasattr(request.user, 'organization') else None
            
            if not organization:
                messages.error(request, "Aucune organisation associée Ã  votre compte.")
                return redirect('payment:payment_methods')
            
            method_type = request.POST.get('method_type')
            payment_data = json.loads(request.POST.get('payment_data', '{}'))
            
            # Créer la méthode de paiement
            payment_method = PaymentMethod.objects.create(
                organization=organization,
                method_type=method_type,
                payment_data=payment_data,
                is_default=not PaymentMethod.objects.filter(organization=organization).exists()
            )
            
            messages.success(request, "Méthode de paiement ajoutée avec succès.")
            return redirect('payment:payment_methods')
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de la méthode de paiement: {e}")
            messages.error(request, "Une erreur est survenue lors de l'ajout de la méthode de paiement.")
            return redirect('payment:payment_methods')
    
    return render(request, 'payment/add_payment_method.html')

@login_required
def payment_history(request):
    """Historique des paiements"""
    try:
        organization = request.user.organization if hasattr(request.user, 'organization') else None
        
        if not organization:
            messages.error(request, "Aucune organisation associée Ã  votre compte.")
            return redirect('payment:subscription_dashboard')
        
        subscription = OrganizationSubscription.objects.filter(
            organization=organization
        ).first()
        
        payments = Payment.objects.filter(
            subscription=subscription
        ).order_by('-created_at') if subscription else []
        
        context = {
            'organization': organization,
            'payments': payments,
        }
        
        return render(request, 'payment/payment_history.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans l'historique des paiements: {e}")
        messages.error(request, "Une erreur est survenue lors du chargement de l'historique.")
        return redirect('payment:subscription_dashboard')

@login_required
def request_refund(request, payment_id):
    """Demande de remboursement"""
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Vérifier que l'utilisateur appartient Ã  l'organisation
        organization = request.user.organization if hasattr(request.user, 'organization') else None
        
        if not organization or payment.subscription.organization != organization:
            messages.error(request, "Vous n'Ãªtes pas autorisé Ã  effectuer cette action.")
            return redirect('payment:payment_history')
        
        if request.method == 'POST':
            amount = request.POST.get('amount')
            reason = request.POST.get('reason')
            
            if amount and reason:
                refund = PaymentService.create_refund(
                    payment=payment,
                    amount=amount,
                    reason=reason
                )
                
                messages.success(request, "Votre demande de remboursement a été soumise avec succès.")
                return redirect('payment:payment_history')
            else:
                messages.error(request, "Veuillez remplir tous les champs requis.")
        
        context = {
            'payment': payment,
        }
        
        return render(request, 'payment/request_refund.html', context)
        
    except Exception as e:
        logger.error(f"Erreur lors de la demande de remboursement: {e}")
        messages.error(request, "Une erreur est survenue lors de la demande de remboursement.")
        return redirect('payment:payment_history')

@csrf_exempt
def payment_webhook(request):
    """Webhook pour les notifications de paiement"""
    try:
        if request.method == 'POST':
            # Ici, vous traiteriez les webhooks de votre passerelle de paiement
            # Pour l'exemple, on simule un traitement basique
            
            data = json.loads(request.body)
            event_type = data.get('type')
            transaction_id = data.get('transaction_id')
            
            payment = Payment.objects.filter(transaction_id=transaction_id).first()
            
            if payment:
                if event_type == 'payment.succeeded':
                    PaymentService.process_payment(payment)
                    NotificationService.send_payment_success_notification(payment)
                elif event_type == 'payment.failed':
                    payment.status = 'failed'
                    payment.save()
                    NotificationService.send_payment_failure_notification(payment)
            
            return JsonResponse({'status': 'success'})
        
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
        
    except Exception as e:
        logger.error(f"Erreur dans le webhook de paiement: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# API Views pour AJAX
@login_required
def api_subscription_status(request):
    """API pour le statut de l'abonnement"""
    try:
        organization = request.user.organization if hasattr(request.user, 'organization') else None
        
        if not organization:
            return JsonResponse({'error': 'Aucune organisation associée'}, status=400)
        
        trial_info = TrialService.get_trial_info(organization)
        
        return JsonResponse({
            'status': 'success',
            'trial_info': trial_info
        })
        
    except Exception as e:
        logger.error(f"Erreur dans l'API de statut d'abonnement: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_extend_trial(request):
    """API pour prolonger l'essai"""
    try:
        organization = request.user.organization if hasattr(request.user, 'organization') else None
        
        if not organization:
            return JsonResponse({'error': 'Aucune organisation associée'}, status=400)
        
        subscription = OrganizationSubscription.objects.filter(
            organization=organization
        ).first()
        
        if subscription and subscription.status == 'trial':
            TrialService.extend_trial(subscription, additional_days=7)
            return JsonResponse({'status': 'success', 'message': 'Essai prolongé de 7 jours'})
        else:
            return JsonResponse({'error': 'Aucun essai actif trouvé'}, status=400)
        
    except Exception as e:
        logger.error(f"Erreur dans l'API de prolongation d'essai: {e}")
        return JsonResponse({'error': str(e)}, status=500)


