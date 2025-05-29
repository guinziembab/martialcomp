"""
Vues pour le système de limites de ressources.
"""
from django.views.generic import TemplateView, FormView, RedirectView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse

from multitenant.mixins import TenantAwareViewMixin, TenantRequiredMixin, SuperAdminRequiredMixin
from multitenant.models import Tenant, TenantFeature
from multitenant.resource_limits import (
    ResourceUsageTracker, ResourceQuotaManager, ResourceMonitor,
    RESOURCE_LIMITS, get_resource_summary_for_tenant, QuotaExceededError
)


class ResourceUsageView(LoginRequiredMixin, TenantRequiredMixin, 
                       TenantAwareViewMixin, TemplateView):
    """
    Affiche l'utilisation des ressources du tenant.
    """
    template_name = 'multitenant/resource_usage.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Obtenir les limites pour ce plan
        limits = RESOURCE_LIMITS.get(
            tenant.subscription_plan,
            RESOURCE_LIMITS['essentials']
        )
        
        # Créer un tracker pour mesurer l'utilisation
        tracker = ResourceUsageTracker(tenant)
        usage = tracker.get_resource_usage()
        
        # Ajouter au contexte
        context['tenant'] = tenant
        context['limits'] = limits
        context['usage'] = usage
        context['last_updated'] = timezone.now()
        
        # Liste des fonctionnalités non disponibles
        all_features = set()
        for plan, plan_limits in RESOURCE_LIMITS.items():
            all_features.update(plan_limits['features'])
        
        context['unavailable_features'] = list(all_features - set(limits['features']))
        
        return context


class UpgradePlanView(LoginRequiredMixin, TenantRequiredMixin, 
                     TenantAwareViewMixin, TemplateView):
    """
    Page de mise à niveau du plan d'abonnement.
    """
    template_name = 'multitenant/upgrade_plan.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Informations sur les plans
        context['tenant'] = tenant
        context['current_plan'] = tenant.subscription_plan
        
        # Obtenir les détails de tous les plans
        context['plans'] = {
            plan: RESOURCE_LIMITS[plan]
            for plan in ['essentials', 'masters', 'champion']
        }
        
        # Informations sur les prix par région
        from multitenant.payments.pricing import get_regional_pricing
        context['pricing'] = get_regional_pricing(tenant.continent)
        
        # Tracker pour l'utilisation actuelle
        tracker = ResourceUsageTracker(tenant)
        context['usage'] = tracker.get_resource_usage()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """
        Traite la demande de mise à niveau.
        """
        tenant = request.tenant
        new_plan = request.POST.get('plan')
        
        # Vérifier que le plan est valide
        if new_plan not in RESOURCE_LIMITS:
            messages.error(request, _("Plan d'abonnement invalide."))
            return redirect('multitenant:resource_usage')
        
        # Vérifier que c'est une mise à niveau
        plan_levels = {
            'essentials': 1,
            'masters': 2,
            'champion': 3,
        }
        
        if plan_levels[new_plan] <= plan_levels[tenant.subscription_plan]:
            messages.error(request, _("Veuillez choisir un plan supérieur à votre plan actuel."))
            return redirect('multitenant:upgrade_plan')
        
        # Rediriger vers la page de paiement
        return redirect('multitenant:payment_setup', plan=new_plan)


class ResourceLimitExceededView(LoginRequiredMixin, TenantRequiredMixin, 
                              TenantAwareViewMixin, TemplateView):
    """
    Page affichée quand une limite est atteinte.
    """
    template_name = 'multitenant/limit_exceeded.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.tenant
        
        # Obtenir le type de ressource
        resource_type = self.kwargs.get('resource_type', 'generic')
        
        # Obtenir les limites pour ce plan
        limits = RESOURCE_LIMITS.get(
            tenant.subscription_plan,
            RESOURCE_LIMITS['essentials']
        )
        
        # Créer un tracker pour mesurer l'utilisation
        tracker = ResourceUsageTracker(tenant)
        usage = tracker.get_resource_usage()
        
        # Messages spécifiques par type de ressource
        resource_messages = {
            'storage': _("Vous avez atteint votre limite de stockage."),
            'users': _("Vous avez atteint votre limite d'utilisateurs."),
            'practitioners': _("Vous avez atteint votre limite de pratiquants."),
            'competitions': _("Vous avez atteint votre limite de compétitions."),
            'categories': _("Vous avez atteint votre limite de catégories."),
            'generic': _("Vous avez atteint une limite de ressources pour votre plan."),
        }
        
        context['resource_type'] = resource_type
        context['message'] = resource_messages.get(resource_type, resource_messages['generic'])
        context['tenant'] = tenant
        context['limits'] = limits
        context['usage'] = usage
        context['next_plan'] = self._get_next_plan(tenant.subscription_plan)
        
        return context
    
    def _get_next_plan(self, current_plan):
        """
        Détermine le plan suivant pour la mise à niveau.
        """
        plan_order = ['essentials', 'masters', 'champion']
        try:
            current_index = plan_order.index(current_plan)
            if current_index < len(plan_order) - 1:
                return plan_order[current_index + 1]
        except ValueError:
            pass
        
        return 'masters'  # Plan par défaut pour la mise à niveau


class ResourceAPIView(LoginRequiredMixin, TenantRequiredMixin, View):
    """
    API pour les données d'utilisation des ressources.
    """
    
    def get(self, request, *args, **kwargs):
        """
        Retourne les données d'utilisation actuelles au format JSON.
        """
        tenant = request.tenant
        
        # Créer un tracker pour mesurer l'utilisation
        tracker = ResourceUsageTracker(tenant)
        usage = tracker.get_resource_usage()
        
        # Obtenir les limites pour ce plan
        limits = RESOURCE_LIMITS.get(
            tenant.subscription_plan,
            RESOURCE_LIMITS['essentials']
        )
        
        # Vérifier quelles limites sont atteintes
        limits_reached = tracker.check_limits()
        
        # Construire la réponse
        data = {
            'tenant': {
                'id': str(tenant.id),
                'name': tenant.name,
                'plan': tenant.subscription_plan,
                'domain': tenant.domain,
            },
            'usage': usage,
            'limits': {
                'storage': limits['storage_limit'],
                'users': limits['max_users'],
                'practitioners': limits['max_practitioners'],
                'competitions': limits['max_competitions'],
                'categories': limits['max_categories'],
            },
            'limits_reached': limits_reached,
            'timestamp': timezone.now().isoformat(),
        }
        
        return JsonResponse(data)


class ResourceDashboardView(LoginRequiredMixin, TenantRequiredMixin, TemplateView):
    """Vue du tableau de bord des ressources pour un tenant."""
    template_name = 'multitenant/resources/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenir le résumé des ressources
        summary = get_resource_summary_for_tenant(self.request.tenant)
        
        # Préparer les données pour les graphiques
        usage_data = []
        for key, display_name in [
            ('storage', 'Storage'),
            ('user', 'Users'),
            ('practitioner', 'Practitioners'),
            ('competition', 'Competitions'),
            ('category', 'Categories'),
            ('club', 'Clubs'),
        ]:
            percentage = summary['usage'].get(f"{key}_percentage", 0)
            count = summary['usage'].get(f"{key}_count", 0)
            unlimited = summary['usage'].get(f"{key}_unlimited", False)
            
            usage_data.append({
                'name': display_name,
                'percentage': percentage,
                'count': count,
                'unlimited': unlimited,
                'critical': percentage >= 95,
                'warning': 80 <= percentage < 95
            })
        
        context.update({
            'tenant': self.request.tenant,
            'summary': summary,
            'usage_data': usage_data,
            'alerts': summary['alerts'],
            'quotas': summary['quotas'],
            'can_upgrade': self.request.tenant.subscription_plan != 'enterprise'
        })
        
        return context


class ResourceQuotaAPIView(LoginRequiredMixin, TenantRequiredMixin, View):
    """API pour vérifier et consommer des quotas."""
    
    def get(self, request):
        """Vérifie si un quota est disponible."""
        resource_type = request.GET.get('resource')
        amount = int(request.GET.get('amount', 1))
        
        if not resource_type:
            return JsonResponse({'error': 'Resource type required'}, status=400)
        
        quota_manager = ResourceQuotaManager(request.tenant)
        can_consume = quota_manager.can_consume(resource_type, amount)
        remaining = quota_manager.get_remaining_quota(resource_type)
        
        return JsonResponse({
            'resource': resource_type,
            'can_consume': can_consume,
            'remaining': remaining if remaining != float('inf') else None,
            'unlimited': remaining == float('inf')
        })
    
    def post(self, request):
        """Consomme un quota."""
        import json
        data = json.loads(request.body)
        resource_type = data.get('resource')
        amount = data.get('amount', 1)
        
        if not resource_type:
            return JsonResponse({'error': 'Resource type required'}, status=400)
        
        quota_manager = ResourceQuotaManager(request.tenant)
        
        try:
            quota_manager.consume_quota(resource_type, amount)
            return JsonResponse({
                'success': True,
                'remaining': quota_manager.get_remaining_quota(resource_type)
            })
        except QuotaExceededError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=429)


class ResourceAdminView(LoginRequiredMixin, SuperAdminRequiredMixin, TemplateView):
    """Vue d'administration globale des ressources."""
    template_name = 'multitenant/resources/admin.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenir les données de tous les tenants
        tenants_data = []
        for tenant in Tenant.objects.filter(is_active=True):
            summary = get_resource_summary_for_tenant(tenant)
            
            # Calculer le score d'utilisation global
            usage_scores = []
            for key in ['storage', 'user', 'practitioner', 'competition']:
                percentage = summary['usage'].get(f"{key}_percentage", 0)
                if not summary['usage'].get(f"{key}_unlimited", False):
                    usage_scores.append(percentage)
            
            avg_usage = sum(usage_scores) / len(usage_scores) if usage_scores else 0
            
            tenants_data.append({
                'tenant': tenant,
                'summary': summary,
                'avg_usage': avg_usage,
                'alert_count': len(summary['alerts']),
                'critical_alerts': len([a for a in summary['alerts'] if a['level'] == 'critical'])
            })
        
        # Trier par utilisation moyenne décroissante
        tenants_data.sort(key=lambda x: x['avg_usage'], reverse=True)
        
        context.update({
            'tenants_data': tenants_data,
            'total_tenants': len(tenants_data),
            'tenants_with_alerts': sum(1 for t in tenants_data if t['alert_count'] > 0),
            'critical_tenants': sum(1 for t in tenants_data if t['critical_alerts'] > 0)
        })
        
        return context