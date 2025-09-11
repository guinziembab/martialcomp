import time
import logging
from collections import defaultdict
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger('security')

class RateLimitingMiddleware(MiddlewareMixin):
    """
    Middleware pour limiter le nombre de requêtes par IP dans un intervalle de temps donné.
    Utilisé pour prévenir les attaques par force brute et les dénis de service.
    """

    # Structure pour stocker les requêtes par IP
    request_history = defaultdict(list)

    # Configuration par défaut
    WINDOW_SIZE = getattr(settings, 'RATE_LIMIT_WINDOW_SIZE', 60)
    MAX_REQUESTS = getattr(settings, 'RATE_LIMIT_MAX_REQUESTS', 100)
    SENSITIVE_MAX_REQUESTS = getattr(settings, 'RATE_LIMIT_SENSITIVE_MAX_REQUESTS', 10)
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
        Traite la requête entrante et vérifie les limites de taux.
        """
        client_ip = self._get_client_ip(request)
        
        if self._is_exempt_ip(client_ip):
            return None

        self._clean_old_requests(client_ip)
        current_time = time.time()
        self.request_history[client_ip].append((current_time, request.path))

        is_sensitive = any(request.path.startswith(path) for path in self.SENSITIVE_PATHS)
        requests_in_window = len(self.request_history[client_ip])
        limit = self.SENSITIVE_MAX_REQUESTS if is_sensitive else self.MAX_REQUESTS

        if requests_in_window > limit:
            logger.warning(f"Rate limit dépassé - IP: {client_ip}, Requêtes: {requests_in_window}")
            return HttpResponse("Trop de requêtes. Veuillez réessayer plus tard.", status=429)

        return None

    def _clean_old_requests(self, client_ip):
        """
        Nettoie les anciennes requêtes en dehors de la fenêtre de temps.
        """
        if client_ip in self.request_history:
            current_time = time.time()
            cutoff_time = current_time - self.WINDOW_SIZE
            self.request_history[client_ip] = [
                (timestamp, path) for timestamp, path in self.request_history[client_ip]
                if timestamp > cutoff_time
            ]

    def _get_client_ip(self, request):
        """
        Obtient l'adresse IP du client, en tenant compte des proxys.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def _is_exempt_ip(self, ip):
        """
        Vérifie si une adresse IP est exemptée des limites de taux.
        """
        exempt_ips = getattr(settings, 'RATE_LIMIT_EXEMPT_IPS', ['127.0.0.1', '::1'])
        return ip in exempt_ips