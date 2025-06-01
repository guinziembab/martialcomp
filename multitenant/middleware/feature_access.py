"""
Middleware de contrôle d'accès aux fonctionnalités basé sur l'abonnement
"""
import re
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from ..payments.service_pricing import check_feature_availability, record_feature_usage


class FeatureAccessMiddleware:
    """
    Middleware qui contrôle l'accès aux fonctionnalités en fonction du niveau d'abonnement.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Définir les patterns d'URL qui nécessitent des fonctionnalités spécifiques
        # Format: (regex_url, feature_key)
        self.feature_patterns = [
            (r'^/api/v1/advanced-analytics/', 'advanced_analytics'),
            (r'^/api/v1/bulk-operations/', 'bulk_operations'),
            (r'^/api/v1/exports/', 'data_export'),
            (r'^/combats/realtime-scoring/', 'realtime_scoring'),
            (r'^/club/import/', 'bulk_import'),
            (r'^/dashboard/finance/advanced/', 'advanced_finance'),
            (r'^/judge/certification/manage/', 'certification_management'),
            # Ajouter d'autres modèles d'URL liés à des fonctionnalités spécifiques
        ]
    
    def __call__(self, request):
        # Ignorer le middleware pour l'authentification et les pages publiques
        if request.path.startswith('/api/v1/auth/') or request.path.startswith('/public/') or request.path.startswith('/static/'):
            return self.get_response(request)
        
        # Ignorer le middleware pour les pages de gestion des abonnements
        if request.path.startswith('/subscriptions/') or request.path.startswith('/tenant/payment/'):
            return self.get_response(request)
        
        # Récupérer le tenant depuis la requête (défini par un autre middleware)
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return self.get_response(request)
        
        # Vérifier si l'URL demandée nécessite une fonctionnalité spécifique
        for pattern, feature_key in self.feature_patterns:
            if re.match(pattern, request.path):
                is_available, reason = check_feature_availability(tenant, feature_key)
                
                if not is_available:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({
                            'error': _('Fonctionnalité non disponible'),
                            'reason': reason,
                            'upgrade_url': '/subscriptions/upgrade/'
                        }, status=403)
                    else:
                        # Rediriger vers la page de mise à niveau pour les requêtes navigateur
                        return redirect(f'/subscriptions/upgrade/?feature={feature_key}')
                
                # Si c'est une fonctionnalité à l'usage, enregistrer l'utilisation
                if reason == "pay_per_use":
                    record_feature_usage(tenant, feature_key)
                
                break
        
        return self.get_response(request)