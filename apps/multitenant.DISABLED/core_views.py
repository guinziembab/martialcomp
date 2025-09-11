from django.core.exceptions import PermissionDenied
"""
Views for multi-tenant functionality
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from .models import Tenant
from .forms import TenantOnboardingForm, TenantSettingsForm, TenantBillingForm
from .payments.service import TenantPaymentService
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


def tenant_info_view(request):
    """API endpoint to get current tenant information"""
    if hasattr(request, 'tenant') and request.tenant:
        return JsonResponse({
            'tenant': {
                'id': str(request.tenant.id),
                'name': request.tenant.name,
                'domain': request.tenant.domain,
                'plan': request.tenant.subscription_plan,
                'continent': request.tenant.continent,
                'is_active': request.tenant.is_active,
                'features': request.tenant.get_available_features(),
            }
        })
    else:
        return JsonResponse({
            'error': 'No tenant found',
            'domain': request.get_host()
        }, status=404)


@login_required
def tenant_dashboard_view(request):
    """Dashboard view for tenant management"""
    context = {
        'tenant': request.tenant if hasattr(request, 'tenant') else None,
    }
    return render(request, 'multitenant/dashboard.html', context)


def tenant_onboarding_view(request):
    """Onboarding flow for new tenants"""
    if request.method == 'POST':
        form = TenantOnboardingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create tenant and owner
                    tenant = form.save()
                    
                    # Log in the owner
                    user = authenticate(
                        username=form.cleaned_data['owner_email'],
                        password=form.cleaned_data['owner_password']
                    )
                    if user:
                        login(request, user)
                    
                    # Redirect to tenant domain
                    tenant_url = f"https://{tenant.domain}"
                    if settings.DEBUG:
                        # Use non-SSL for local development
                        tenant_url = f"http://{tenant.domain}:8000"
                    
                    messages.success(
                        request,
                        _("Votre organisation a été créée avec succès!")
                    )
                    
                    # Redirect to payment setup if not trial
                    if tenant.subscription_plan != 'trial':
                        return redirect(tenant_url + reverse('multitenant:payment_setup'))
                    
                    return redirect(tenant_url + reverse('multitenant:tenant_dashboard'))
                    
            except Exception as e:
                messages.error(
                    request,
                    _("Erreur lors de la création de votre organisation: ") + str(e)
                )
    else:
        form = TenantOnboardingForm()
    
    context = {
        'form': form,
        'pricing_matrix': Tenant.get_pricing_matrix(),
        'feature_matrix': {
            'essentials': {
                'max_members': 100,
                'max_disciplines': 2,
                'competitions': False,
                'advanced_reporting': False,
                'api_access': False,
                'mobile_app': False,
            },
            'masters': {
                'max_members': 300,
                'max_disciplines': 5,
                'competitions': True,
                'advanced_reporting': True,
                'api_access': False,
                'mobile_app': False,
            },
            'champion': {
                'max_members': None,
                'max_disciplines': None,
                'competitions': True,
                'advanced_reporting': True,
                'api_access': True,
                'mobile_app': True,
            },
        }
    }
    
    return render(request, 'multitenant/onboarding.html', context)


@login_required
def tenant_settings_view(request):
    """Tenant settings management"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return HttpResponse("No tenant found", status=404)
    
    tenant = request.tenant
    
    # Check if user is tenant owner
    if request.user != tenant.owner:
        messages.error(request, _("Vous n'Ãªtes pas autorisé Ã  modifier ces paramètres."))
        return redirect('multitenant:tenant_dashboard')
    
    if request.method == 'POST':
        form = TenantSettingsForm(request.POST, request.FILES, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, _("Paramètres mis Ã  jour avec succès."))
            return redirect('multitenant:tenant_settings')
    else:
        form = TenantSettingsForm(instance=tenant)
    
    context = {
        'form': form,
        'tenant': tenant,
    }
    
    return render(request, 'multitenant/settings.html', context)


@login_required
def tenant_billing_view(request):
    """Tenant billing management"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return HttpResponse("No tenant found", status=404)
    
    tenant = request.tenant
    payment_service = TenantPaymentService()
    
    # Check if user is tenant owner
    if request.user != tenant.owner:
        messages.error(request, _("Vous n'Ãªtes pas autorisé Ã  accéder Ã  cette page."))
        return redirect('multitenant:tenant_dashboard')
    
    if request.method == 'POST':
        form = TenantBillingForm(request.POST)
        if form.is_valid():
            # Update billing information in payment config
            billing_info = {
                'billing_name': form.cleaned_data['billing_name'],
                'billing_address': form.cleaned_data['billing_address'],
                'billing_city': form.cleaned_data['billing_city'],
                'billing_postal_code': form.cleaned_data['billing_postal_code'],
                'billing_country': form.cleaned_data['billing_country'],
                'billing_tax_id': form.cleaned_data.get('billing_tax_id', ''),
            }
            
            tenant.payment_config['billing_info'] = billing_info
            tenant.save()
            
            messages.success(request, _("Informations de facturation mises Ã  jour."))
            return redirect('multitenant:tenant_billing')
    else:
        # Pre-fill form with existing billing info
        initial_data = tenant.payment_config.get('billing_info', {})
        form = TenantBillingForm(initial=initial_data)
    
    # Get subscription details
    subscription_info = None
    portal_url = None
    
    try:
        if tenant.payment_config.get('subscription_id'):
            # Get customer portal URL
            portal_url = payment_service.get_customer_portal_url(tenant)
    except Exception as e:
        messages.warning(request, _("Impossible de récupérer les informations de facturation."))
    
    context = {
        'form': form,
        'tenant': tenant,
        'subscription_info': subscription_info,
        'portal_url': portal_url,
        'pricing': tenant.get_price_for_plan(),
    }
    
    return render(request, 'multitenant/billing.html', context)


@login_required
def payment_setup_view(request):
    """Setup payment for a tenant"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return HttpResponse("No tenant found", status=404)
    
    tenant = request.tenant
    payment_service = TenantPaymentService()
    
    # Check if user is tenant owner
    if request.user != tenant.owner:
        messages.error(request, _("Vous n'Ãªtes pas autorisé Ã  accéder Ã  cette page."))
        return redirect('multitenant:tenant_dashboard')
    
    try:
        # Create checkout session
        checkout_url = payment_service.create_checkout_url(
            tenant=tenant,
            plan=tenant.subscription_plan
        )
        
        return redirect(checkout_url)
        
    except Exception as e:
        messages.error(
            request,
            _("Erreur lors de la configuration du paiement: ") + str(e)
        )
        return redirect('multitenant:tenant_dashboard')


def payment_success_view(request):
    """Payment success callback"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return HttpResponse("No tenant found", status=404)
    
    messages.success(
        request,
        _("Paiement réussi! Votre abonnement est maintenant actif.")
    )
    
    return redirect('multitenant:tenant_dashboard')


def payment_cancel_view(request):
    """Payment cancelled callback"""
    messages.warning(
        request,
        _("Paiement annulé. Vous pouvez réessayer Ã  tout moment.")
    )
    
    return redirect('multitenant:tenant_billing')


@csrf_exempt
def webhook_view(request, provider):
    """Handle payment provider webhooks"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    payment_service = TenantPaymentService()
    
    try:
        # Get webhook signature
        if provider == 'stripe':
            signature = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        else:
            signature = request.META.get('HTTP_X_WEBHOOK_SIGNATURE', '')
        
        # Process webhook
        event = payment_service.handle_webhook(
            provider_name=provider,
            payload=request.body,
            signature=signature
        )
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
