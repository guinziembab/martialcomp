import time
import logging
from collections import defaultdict
try:
    from django.http import HttpResponseTooManyRequests
except ImportError:
    # Fallback pour Django < 4.1
    from django.http import HttpResponse
    class HttpResponseTooManyRequests(HttpResponse):
        status_code = 429
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('security')

class RateLimitingMiddleware(MiddlewareMixin):
    """
    Middleware pour limiter le nombre de requÃªtes par IP dans un intervalle de temps donné.
    Utilisé pour prévenir les attaques par force brute et les dénis de service.
    """
    
    # Structure pour stocker les requÃªtes par IP
    # Format: {ip_address: [(timestamp1, path1), (timestamp2, path2), ...]}
    request_history = defaultdict(list)
    
    # FenÃªtre de temps pour le rate limiting (en secondes)
    WINDOW_SIZE = getattr(settings, 'RATE_LIMIT_WINDOW_SIZE', 60)  # 1 minute par défaut
    
    # Nombre maximum de requÃªtes par fenÃªtre de temps
    MAX_REQUESTS = getattr(settings, 'RATE_LIMIT_MAX_REQUESTS', 100)  # 100 requÃªtes par minute par défaut
    
    # Nombre maximum de requÃªtes pour les endpoints sensibles
    SENSITIVE_MAX_REQUESTS = getattr(settings, 'RATE_LIMIT_SENSITIVE_MAX_REQUESTS', 10)  # 10 requÃªtes par minute pour les endpoints sensibles
    
    # Liste des endpoints sensibles qui nécessitent un rate limiting plus strict
    SENSITIVE_PATHS = getattr(settings, 'RATE_LIMIT_SENSITIVE_PATHS', [
        '/login/',
        '/admin/login/',
        '/api/token/',
        '/api/auth/',
        '/password-reset/',
    ])
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
    def process_request(self, request):
        """
        Traite la requÃªte entrante et vérifie les limites de taux.
        
        Args:
            request: L'objet HttpRequest Ã  vérifier
            
        Returns:
            HttpResponseTooManyRequests si la limite est dépassée, None sinon
        """
        # Récupération de l'adresse IP du client
        client_ip = self._get_client_ip(request)
        
        # Ignorer certains IPs (comme localhost) si configuré
        if self._is_exempt_ip(client_ip):
            return None
        
        # Nettoyage des anciennes entrées
        self._clean_old_requests(client_ip)
        
        # Ajout de la requÃªte actuelle Ã  l'historique
        current_time = time.time()
        self.request_history[client_ip].append((current_time, request.path))
        
        # Vérification si la requÃªte concerne un endpoint sensible
        is_sensitive = any(request.path.startswith(path) for path in self.SENSITIVE_PATHS)
        
        # Calcul du nombre de requÃªtes dans la fenÃªtre de temps
        requests_in_window = len(self.request_history[client_ip])
        
        # Limite Ã  appliquer selon le type d'endpoint
        limit = self.SENSITIVE_MAX_REQUESTS if is_sensitive else self.MAX_REQUESTS
        
        # Vérification si la limite est dépassée
        if requests_in_window > limit:
            logger.warning(
                f"Rate limit dépassé - IP: {client_ip}, RequÃªtes: {requests_in_window}, "
                f"Limite: {limit}, Endpoint: {request.path}, Sensible: {is_sensitive}"
            )
            return HttpResponseTooManyRequests("Trop de requÃªtes. Veuillez réessayer plus tard.")
        
        return None
    
    def _clean_old_requests(self, client_ip):
        """
        Nettoie les anciennes requÃªtes en dehors de la fenÃªtre de temps.
        
        Args:
            client_ip: L'adresse IP du client
        """
        if client_ip in self.request_history:
            current_time = time.time()
            cutoff_time = current_time - self.WINDOW_SIZE
            
            # Conserver uniquement les requÃªtes dans la fenÃªtre de temps
            self.request_history[client_ip] = [
                (timestamp, path) for timestamp, path in self.request_history[client_ip]
                if timestamp > cutoff_time
            ]
    
    def _get_client_ip(self, request):
        """
        Obtient l'adresse IP du client, en tenant compte des proxys.
        
        Args:
            request: L'objet HttpRequest
            
        Returns:
            L'adresse IP du client
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Prendre la première IP (la plus proche du client)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _is_exempt_ip(self, ip):
        """
        Vérifie si une adresse IP est exemptée des limites de taux.
        
        Args:
            ip: L'adresse IP Ã  vérifier
            
        Returns:
            True si l'IP est exemptée, False sinon
        """
        exempt_ips = getattr(settings, 'RATE_LIMIT_EXEMPT_IPS', ['127.0.0.1', '::1'])
        return ip in exempt_ips
