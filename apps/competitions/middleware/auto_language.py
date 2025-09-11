"""
Middleware pour la détection automatique de langue et gestion des traductions manquantes
"""
from django.utils import translation
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class AutoDetectLanguageMiddleware:
    """Middleware pour détecter automatiquement la langue préférée de l'utilisateur."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Ne pas appliquer si la langue est déjÃ  spécifiée dans l'URL
        if any(request.path.startswith(f'/{lang}/') for lang, _ in settings.LANGUAGES):
            return self.get_response(request)
            
        # Si l'utilisateur a déjÃ  une préférence en session, ne rien faire
        if request.session.get('django_language') or translation.get_language():
            return self.get_response(request)
            
        # Détecter la langue préférée du navigateur
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for lang_code, lang_name in settings.LANGUAGES:
            if lang_code in accept_language:
                request.session['django_language'] = lang_code
                translation.activate(lang_code)
                logger.info(f"Auto-détection de langue: {lang_code} pour {request.META.get('REMOTE_ADDR')}")
                break
                
        response = self.get_response(request)
        return response


class MissingTranslationMiddleware:
    """Middleware pour détecter et journaliser les traductions manquantes."""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.missing_translations = set()
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Ne vérifier que si nous ne sommes pas en mode debug et pas dans l'admin
        if settings.DEBUG or request.path.startswith('/admin/') or request.path.startswith('/rosetta/'):
            return response
            
        # Vérifier si la réponse contient des marqueurs de traduction manquante
        if hasattr(response, 'content'):
            content = response.content.decode('utf-8', errors='ignore')
            if 'class="translation-missing"' in content:
                current_lang = translation.get_language()
                logger.warning(f"Traductions manquantes détectées sur {request.path} (langue: {current_lang})")
                
        return response
