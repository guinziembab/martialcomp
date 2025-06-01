import re
import json
from django.utils import timezone
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken
from jwt import PyJWTError

from multitenant.models import Tenant
from .models import AccessTokenLog

class JWTTenantMiddleware(MiddlewareMixin):
    """
    Middleware pour extraire le contexte tenant des tokens JWT.
    Ce middleware s'intègre avec le système multi-tenant existant et permet
    d'extraire l'information de tenant depuis le token JWT au lieu du domaine.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Chemins d'API qui ne nécessitent pas de vérification de tenant
        self.exempt_paths = [
            r'^/api/v1/auth/login/?$',
            r'^/api/v1/auth/register/?$',
            r'^/api/v1/auth/refresh/?$',
            r'^/api/docs/?',
        ]
    
    def is_path_exempt(self, path):
        """Vérifie si le chemin est exempté de la vérification de tenant"""
        for exempt_path in self.exempt_paths:
            if re.match(exempt_path, path):
                return True
        return False
    
    def __call__(self, request):
        # Ne traiter que les requêtes d'API
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Ne pas traiter les chemins exemptés
        if self.is_path_exempt(request.path):
            return self.get_response(request)
        
        # Vérifier l'en-tête d'autorisation
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return self.get_response(request)
        
        # Extraire et valider le token
        token = auth_header.split(' ')[1]
        try:
            access_token = AccessToken(token)
            
            # Vérifier si le token contient une information de tenant
            tenant_id = access_token.get('tenant_id')
            if tenant_id:
                try:
                    # Récupérer le tenant
                    tenant = Tenant.objects.get(id=tenant_id)
                    
                    # Stocker le tenant dans la requête pour une utilisation ultérieure
                    request.tenant = tenant
                    
                    # Vérifier si le token est révoqué
                    jti = access_token.get('jti')
                    if jti:
                        try:
                            token_log = AccessTokenLog.objects.get(jti=jti)
                            if token_log.revoked:
                                return JsonResponse(
                                    {'error': 'Token révoqué.'},
                                    status=401
                                )
                        except AccessTokenLog.DoesNotExist:
                            # Token non trouvé dans les logs, c'est OK
                            pass
                except Tenant.DoesNotExist:
                    # Tenant non trouvé, mais on continue quand même
                    pass
        except (InvalidToken, PyJWTError):
            # Token invalide, on continue le traitement (d'autres middleware peuvent le rejeter)
            pass
        
        return self.get_response(request)


class APIErrorHandlingMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer les erreurs d'API de manière uniforme.
    Intercepte les exceptions et les formate en réponses JSON.
    """
    
    def process_exception(self, request, exception):
        # Ne traiter que les requêtes d'API
        if not request.path.startswith('/api/'):
            return None
        
        # Formater l'exception en réponse JSON
        error_data = {
            'error': str(exception),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Ajouter des détails supplémentaires en mode DEBUG
        if settings.DEBUG:
            import traceback
            error_data['traceback'] = traceback.format_exc()
        
        status_code = getattr(exception, 'status_code', 500)
        return JsonResponse(error_data, status=status_code)


class APILoggingMiddleware(MiddlewareMixin):
    """
    Middleware pour journaliser les requêtes et réponses API.
    Utile pour le débogage et l'audit.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = None
        
        # Initialiser le logger si nécessaire
        if 'api_auth' not in settings.LOGGING.get('loggers', {}):
            import logging
            self.logger = logging.getLogger('api_auth')
    
    def __call__(self, request):
        # Ne traiter que les requêtes d'API
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Enregistrer la requête
        self.log_request(request)
        
        # Obtenir la réponse
        response = self.get_response(request)
        
        # Enregistrer la réponse
        self.log_response(request, response)
        
        return response
    
    def log_request(self, request):
        """Journalise les détails de la requête"""
        if not self.logger:
            return
        
        # Extraire les informations de la requête
        request_data = {
            'method': request.method,
            'path': request.path,
            'user': str(request.user),
            'ip': self.get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Ne pas journaliser les données sensibles comme les mots de passe
        if request.method in ['POST', 'PUT', 'PATCH'] and request.content_type == 'application/json':
            try:
                body = json.loads(request.body)
                # Masquer les mots de passe et autres données sensibles
                for key in body:
                    if key.lower() in ['password', 'password_confirm', 'token', 'refresh', 'access']:
                        body[key] = '******'
                request_data['body'] = body
            except json.JSONDecodeError:
                pass
        
        self.logger.info(f"API Request: {json.dumps(request_data)}")
    
    def log_response(self, request, response):
        """Journalise les détails de la réponse"""
        if not self.logger:
            return
        
        # Extraire les informations de la réponse
        response_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'content_type': response.get('Content-Type', ''),
            'timestamp': timezone.now().isoformat(),
        }
        
        # Journaliser en fonction du niveau de verbosité
        if hasattr(response, 'data') and settings.DEBUG:
            # En développement, journaliser tout sauf les données sensibles
            data = response.data.copy() if isinstance(response.data, dict) else {}
            for key in data:
                if key.lower() in ['password', 'token', 'refresh', 'access']:
                    data[key] = '******'
            response_data['data'] = data
        
        self.logger.info(f"API Response: {json.dumps(response_data)}")
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip