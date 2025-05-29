import json
import logging
from django.utils import timezone
from django.urls import resolve
from django.conf import settings

logger = logging.getLogger('finances')

class FinancialAuditMiddleware:
    """
    Middleware pour enregistrer les actions financières.
    Cela permet d'avoir un journal d'audit des opérations financières.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Traitement de la requête avant la vue
        response = self.get_response(request)
        
        # Ne continuer que si l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return response
        
        # Vérifier si l'URL fait partie des URLs financières
        url_name = self._get_url_name(request)
        if not url_name.startswith('finances:'):
            return response
        
        # Vérifier si c'est une requête POST (création ou modification)
        if request.method == 'POST' and self._is_financial_action(url_name):
            self._log_financial_action(request, url_name)
        
        return response
    
    def _get_url_name(self, request):
        """Obtenir le nom de l'URL."""
        try:
            resolver_match = resolve(request.path)
            return f"{resolver_match.namespace}:{resolver_match.url_name}"
        except:
            return ""
    
    def _is_financial_action(self, url_name):
        """Vérifier si l'URL correspond à une action financière importante."""
        financial_actions = [
            'finances:transaction_create',
            'finances:transaction_update',
            'finances:transaction_delete',
            'finances:transaction_change_status',
            'finances:transaction_bulk_approval',
            'finances:invoice_create',
            'finances:invoice_update',
            'finances:invoice_delete',
            'finances:invoice_pay',
            'finances:invoice_cancel',
            'finances:process_payment',
            'finances:cancel_payment',
        ]
        
        return url_name in financial_actions
    
    def _log_financial_action(self, request, url_name):
        """Enregistrer l'action financière."""
        user = request.user
        
        # Préparer les données d'audit
        audit_data = {
            'user_id': user.id,
            'username': user.username,
            'timestamp': timezone.now().isoformat(),
            'url': request.path,
            'url_name': url_name,
            'method': request.method,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Ajouter les données POST (sanitizées)
        post_data = {}
        for key, value in request.POST.items():
            # Exclure les données sensibles
            if key not in ['password', 'csrfmiddlewaretoken']:
                # Limiter la taille des valeurs pour éviter des logs trop volumineux
                if isinstance(value, str) and len(value) > 200:
                    post_data[key] = value[:200] + '...'
                else:
                    post_data[key] = value
        
        audit_data['post_data'] = post_data
        
        # Log l'action
        logger.info(f"FINANCIAL_AUDIT: {json.dumps(audit_data)}")
    
    def _get_client_ip(self, request):
        """Obtenir l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip