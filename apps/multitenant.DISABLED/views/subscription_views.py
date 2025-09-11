from django.core.exceptions import PermissionDenied
"""
Vues pour la gestion des abonnements et des paiements
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import (
    Tenant, SubscriptionTier, TenantSubscription, 
    PayPerUseFeature, FeatureUsage, PromotionCode
)
from ..payments.service_pricing import PaymentService
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def subscription_dashboard(request):
    """
    Affiche le tableau de bord des abonnements pour le tenant.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, _("Aucun tenant trouvé pour cet utilisateur."))
        return redirect('home')
    
    # Récupérer l'abonnement actif
    active_subscription = TenantSubscription.objects.filter(
        tenant=tenant,
        end_date__gt=timezone.now()
    ).order_by('-start_date').first()
    
    # Récupérer tous les niveaux d'abonnement disponibles
    subscription_tiers = SubscriptionTier.objects.filter(is_active=True).order_by('price_monthly')
    
    # Récupérer les fonctionnalités Ã  l'usage
    pay_per_use_features = PayPerUseFeature.objects.filter(is_active=True)
    
    # Récupérer l'historique d'utilisation récent
    recent_usage = FeatureUsage.objects.filter(tenant=tenant).order_by('-usage_date')[:10]
    
    # Calculer les coÃ»ts supplémentaires du mois en cours
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_usage = FeatureUsage.objects.filter(
        tenant=tenant,
        usage_date__gte=current_month_start
    )
    
    total_extra_cost = 0
    for usage in current_month_usage:
        total_extra_cost += usage.quantity * usage.feature.price_per_unit
    
    context = {
        'tenant': tenant,
        'active_subscription': active_subscription,
        'subscription_tiers': subscription_tiers,
        'pay_per_use_features': pay_per_use_features,
        'recent_usage': recent_usage,
        'total_extra_cost': total_extra_cost,
        'current_month': timezone.now().strftime('%B %Y'),
    }
    
    return render(request, 'multitenant/subscription/dashboard.html', context)


@login_required
def subscription_plans(request):
    """
    Affiche les plans d'abonnement disponibles.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, _("Aucun tenant trouvé pour cet utilisateur."))
        return redirect('home')
    
    # Récupérer l'abonnement actif
    active_subscription = TenantSubscription.objects.filter(
        tenant=tenant,
        end_date__gt=timezone.now()
    ).order_by('-start_date').first()
    
    # Récupérer tous les niveaux d'abonnement disponibles
    subscription_tiers = SubscriptionTier.objects.filter(is_active=True).order_by('price_monthly')
    
    # Récupérer le paramètre de fonctionnalité pour la mise en évidence
    highlighted_feature = request.GET.get('feature')
    
    context = {
        'tenant': tenant,
        'active_subscription': active_subscription,
        'subscription_tiers': subscription_tiers,
        'highlighted_feature': highlighted_feature,
        'billing_cycle': request.GET.get('billing_cycle', 'monthly')
    }
    
    return render(request, 'multitenant/subscription/plans.html', context)


@login_required
@require_POST
def subscribe(request):
    """
    Traite la souscription Ã  un nouveau plan.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, _("Aucun tenant trouvé pour cet utilisateur."))
        return redirect('home')
    
    tier_id = request.POST.get('tier_id')
    billing_cycle = request.POST.get('billing_cycle', 'monthly')
    promo_code = request.POST.get('promo_code')
    
    if not tier_id:
        messages.error(request, _("Niveau d'abonnement non spécifié."))
        return redirect('subscription_plans')
    
    try:
        tier = get_object_or_404(SubscriptionTier, id=tier_id, is_active=True)
        
        # Initialiser le service de paiement
        payment_service = PaymentService(tenant)
        
        # Appliquer le code promo si fourni
        if promo_code:
            promo_result = payment_service.apply_promotion_code(promo_code, tier_id, billing_cycle)
            if not promo_result.get('valid', False):
                messages.warning(request, promo_result.get('reason', _("Code promotionnel invalide.")))
        
        # Créer l'abonnement
        subscription = payment_service.create_subscription(tier_id, billing_cycle)
        
        messages.success(request, _("Votre abonnement a été créé avec succès."))
        return redirect('subscription_dashboard')
    
    except Exception as e:
        messages.error(request, str(e))
        return redirect('subscription_plans')


@login_required
@require_POST
def cancel_subscription(request):
    """
    Annule un abonnement existant.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, _("Aucun tenant trouvé pour cet utilisateur."))
        return redirect('home')
    
    subscription_id = request.POST.get('subscription_id')
    immediate = request.POST.get('immediate', 'false').lower() == 'true'
    
    if not subscription_id:
        messages.error(request, _("ID d'abonnement non spécifié."))
        return redirect('subscription_dashboard')
    
    try:
        subscription = get_object_or_404(TenantSubscription, id=subscription_id, tenant=tenant)
        
        # Initialiser le service de paiement
        payment_service = PaymentService(tenant)
        
        # Annuler l'abonnement
        result = payment_service.cancel_subscription(subscription_id, immediate=immediate)
        
        if result.get('success', False):
            if immediate:
                messages.success(request, _("Votre abonnement a été annulé immédiatement."))
            else:
                messages.success(request, _("Votre abonnement sera annulé Ã  la fin de la période de facturation."))
        else:
            messages.error(request, result.get('error', _("Une erreur s'est produite lors de l'annulation.")))
        
        return redirect('subscription_dashboard')
    
    except Exception as e:
        messages.error(request, str(e))
        return redirect('subscription_dashboard')


@login_required
def validate_promo_code(request):
    """
    Valide un code promotionnel et retourne les détails de la réduction.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return JsonResponse({'valid': False, 'reason': _("Aucun tenant trouvé.")})
    
    code = request.GET.get('code')
    tier_id = request.GET.get('tier_id')
    billing_cycle = request.GET.get('billing_cycle', 'monthly')
    
    if not code or not tier_id:
        return JsonResponse({'valid': False, 'reason': _("Paramètres manquants.")})
    
    try:
        # Initialiser le service de paiement
        payment_service = PaymentService(tenant)
        
        # Vérifier le code promo
        result = payment_service.apply_promotion_code(code, tier_id, billing_cycle)
        
        return JsonResponse(result)
    
    except Exception as e:
        return JsonResponse({'valid': False, 'reason': str(e)})


@login_required
def feature_usage_history(request):
    """
    Affiche l'historique d'utilisation des fonctionnalités Ã  l'usage.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, _("Aucun tenant trouvé pour cet utilisateur."))
        return redirect('home')
    
    # Paramètres de filtrage
    feature_id = request.GET.get('feature_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Base de la requÃªte
    usages = FeatureUsage.objects.filter(tenant=tenant).order_by('-usage_date')
    
    # Appliquer les filtres
    if feature_id:
        usages = usages.filter(feature_id=feature_id)
    
    if start_date:
        usages = usages.filter(usage_date__gte=start_date)
    
    if end_date:
        usages = usages.filter(usage_date__lte=end_date)
    
    # Récupérer les fonctionnalités Ã  l'usage pour le filtre
    features = PayPerUseFeature.objects.filter(is_active=True)
    
    context = {
        'tenant': tenant,
        'usages': usages,
        'features': features,
        'selected_feature': feature_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'multitenant/subscription/usage_history.html', context)


@login_required
def customer_portal(request):
    """
    Redirige vers le portail client du fournisseur de paiement.
    """
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, _("Aucun tenant trouvé pour cet utilisateur."))
        return redirect('home')
    
    try:
        # Initialiser le service de paiement
        payment_service = PaymentService(tenant)
        
        # Obtenir l'URL du portail client
        portal_url = payment_service.provider.get_customer_portal_url(
            customer_id=tenant.payment_config.get('customer_id'),
            return_url=request.build_absolute_uri('/subscriptions/dashboard/')
        )
        
        return redirect(portal_url)
    
    except Exception as e:
        messages.error(request, str(e))
        return redirect('subscription_dashboard')
