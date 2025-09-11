import re
import logging
from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied

logger = logging.getLogger('security')
security_logger = logging.getLogger('security.organization_access')

class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware de sécurité personnalisé pour l'application MartialComp.
    Implémente diverses vérifications de sécurité sur les requÃªtes entrantes.
    """
    
    # Liste des caractères et motifs potentiellement malveillants dans les paramètres de requÃªte
    SUSPICIOUS_PATTERNS = [
        r'<script.*?>',             # Tags de script
        r'javascript:',             # Protocole javascript:
        r'eval\s*\(',               # Fonction eval()
        r'document\.cookie',        # Accès aux cookies
        r'onload=',                 # Ã‰vénements inline
        r'onerror=',
        r'onclick=',
        r'\.\./\.\.',               # Traversée de répertoire
        r'SELECT.*FROM',            # Motifs SQL simples
        r'INSERT.*INTO',
        r'DELETE.*FROM',
        r'DROP.*TABLE',
        r'UNION.*SELECT'
    ]
    
    # Compilation des expressions régulières pour optimiser les performances
    COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_PATTERNS]
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
    def process_request(self, request):
        """
        Traite la requÃªte entrante et effectue des vérifications de sécurité.
        
        Args:
            request: L'objet HttpRequest Ã  vérifier
            
        Returns:
            HttpResponseForbidden si une menace est détectée, None sinon
        """
        # Vérification des paramètres de requÃªte (GET et POST)
        if self._check_request_params(request):
            return HttpResponseForbidden("RequÃªte bloquée pour des raisons de sécurité.")
            
        # Vérification de l'entÃªte User-Agent
        if self._check_user_agent(request):
            return HttpResponseForbidden("RequÃªte bloquée pour des raisons de sécurité.")
        
        # Vérification de l'entÃªte Referer pour les attaques CSRF
        if self._check_referer(request):
            return HttpResponseForbidden("RequÃªte bloquée pour des raisons de sécurité.")
        
        # Vérification de l'isolation organisationnelle
        org_access_result = self._check_organization_access(request)
        if org_access_result:
            return org_access_result
        
        # Si toutes les vérifications sont passées, on continue
        return None
    
    def process_response(self, request, response):
        """
        Ajoute des entÃªtes de sécurité supplémentaires Ã  la réponse.
        
        Args:
            request: L'objet HttpRequest
            response: L'objet HttpResponse Ã  modifier
            
        Returns:
            HttpResponse modifié avec des entÃªtes de sécurité supplémentaires
        """
        # Ajout des entÃªtes de sécurité standards si pas déjÃ  présents
        if not response.has_header('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'
        
        if not response.has_header('X-XSS-Protection'):
            response['X-XSS-Protection'] = '1; mode=block'
        
        if not response.has_header('Referrer-Policy'):
            response['Referrer-Policy'] = 'same-origin'
        
        # Content-Security-Policy avec support des CDN Bootstrap et Font Awesome
        if settings.DEBUG:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' data: https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
        else:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' data: https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
        
        response['Content-Security-Policy'] = csp
        
        return response
    
    def _check_request_params(self, request):
        """
        Vérifie les paramètres de requÃªte pour détecter des motifs suspects.
        
        Args:
            request: L'objet HttpRequest Ã  vérifier
            
        Returns:
            True si un motif suspect est détecté, False sinon
        """
        # Vérification des paramètres GET
        for key, value in request.GET.items():
            if isinstance(value, str) and self._contains_suspicious_pattern(value):
                self._log_suspicious_activity(request, 'GET parameter', key, value)
                return True
        
        # Vérification des paramètres POST
        for key, value in request.POST.items():
            if isinstance(value, str) and self._contains_suspicious_pattern(value):
                self._log_suspicious_activity(request, 'POST parameter', key, value)
                return True
        
        return False
    
    def _check_user_agent(self, request):
        """
        Vérifie l'entÃªte User-Agent pour détecter des outils automatisés connus.
        
        Args:
            request: L'objet HttpRequest Ã  vérifier
            
        Returns:
            True si un outil automatisé est détecté, False sinon
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Liste d'outils automatisés connus (scanners, etc.)
        suspicious_agents = [
            'sqlmap', 'nikto', 'nessus', 'nmap', 'acunetix', 'burpsuite', 
            'w3af', 'metasploit', 'masscan', 'zgrab', 'dirbuster'
        ]
        
        if any(agent.lower() in user_agent.lower() for agent in suspicious_agents):
            self._log_suspicious_activity(request, 'User-Agent', 'HTTP_USER_AGENT', user_agent)
            return True
        
        return False
    
    def _check_referer(self, request):
        """
        Vérifie l'entÃªte Referer pour les requÃªtes POST.
        
        Args:
            request: L'objet HttpRequest Ã  vérifier
            
        Returns:
            True si le Referer est suspect, False sinon
        """
        if request.method == 'POST' and not settings.DEBUG:
            referer = request.META.get('HTTP_REFERER', '')
            host = request.META.get('HTTP_HOST', '')
            
            # Si la requÃªte POST a un Referer qui ne provient pas du site lui-mÃªme
            # et que ce n'est pas une exception connue (comme une API)
            if referer and host and not referer.startswith(f'http://{host}') and not referer.startswith(f'https://{host}'):
                # Exception pour les chemins d'API qui peuvent Ãªtre appelés par des services externes
                if not request.path.startswith('/api/'):
                    self._log_suspicious_activity(request, 'Referer', 'HTTP_REFERER', referer)
                    return True
        
        return False
    
    def _contains_suspicious_pattern(self, value):
        """
        Vérifie si une valeur contient un motif suspect.
        
        Args:
            value: La valeur Ã  vérifier
            
        Returns:
            True si un motif suspect est trouvé, False sinon
        """
        for pattern in self.COMPILED_PATTERNS:
            if pattern.search(value):
                return True
        return False
    
    def _log_suspicious_activity(self, request, param_type, param_name, param_value):
        """
        Enregistre l'activité suspecte dans les logs.
        
        Args:
            request: L'objet HttpRequest
            param_type: Le type de paramètre (GET, POST, etc.)
            param_name: Le nom du paramètre
            param_value: La valeur du paramètre
        """
        client_ip = self._get_client_ip(request)
        logger.warning(
            f"Activité suspecte détectée - IP: {client_ip}, Chemin: {request.path}, "
            f"Méthode: {request.method}, Type: {param_type}, Paramètre: {param_name}, "
            f"Valeur: {param_value[:100]}..."
        )
    
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
        
    def _check_organization_access(self, request):
        """
        Vérifie que l'utilisateur n'accède pas Ã  des ressources d'autres organisations.
        Cette vérification est complémentaire au middleware OrganizationIsolationMiddleware.
        
        Args:
            request: L'objet HttpRequest Ã  vérifier
            
        Returns:
            HttpResponseForbidden si une violation est détectée, None sinon
        """
        # Ignorer les requÃªtes non authentifiées
        if not request.user.is_authenticated:
            return None
            
        # Ignorer les admins et le staff qui ont des privilèges étendus
        if request.user.is_superuser or request.user.is_staff:
            return None
            
        # Vérifier que resolver_match existe
        if not hasattr(request, 'resolver_match') or request.resolver_match is None:
            return None
            
        # Si aucun objet n'est spécifié dans l'URL, on ne peut pas vérifier
        if 'pk' not in request.resolver_match.kwargs and 'id' not in request.resolver_match.kwargs:
            return None
            
        # Récupérer l'ID de l'objet
        object_id = request.resolver_match.kwargs.get('pk') or request.resolver_match.kwargs.get('id')
        if not object_id:
            return None
            
        # Vérifier si l'URL correspond Ã  un modèle connu avec isolation organisationnelle
        path = request.path.lower()
        
        # Liste des modèles sensibles et leurs préfixes d'URL
        sensitive_models = {
            'club': 'competitions.models.Club',
            'federation': 'competitions.models.Federation',
            'competition': 'competitions.models.Competition',
            'practitioner': 'competitions.models.Practitioner',
            'category': 'competitions.models.Category',
            'judge': 'competitions.models.Judge',
        }
        
        # Vérifier si l'URL correspond Ã  un modèle sensible
        detected_model = None
        for key, model_path in sensitive_models.items():
            if f'/{key}/' in path or f'/{key}s/' in path:
                detected_model = key
                break
                
        if not detected_model:
            return None
            
        # Loguer l'accès pour surveillance
        security_logger.info(
            f"Vérification d'accès - Utilisateur: {request.user.id}, "
            f"Modèle: {detected_model}, ID: {object_id}, "
            f"Organisation: {getattr(request.user, 'organization_id', None)}"
        )
        
        # Pour l'instant, on ne bloque pas, on surveille seulement
        # Ã€ l'avenir, on pourrait implémenter un blocage actif ici
        
        return None
