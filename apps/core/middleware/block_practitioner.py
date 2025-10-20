"""
Middleware d'urgence pour bloquer l'accès aux practitioners
"""
from django.http import HttpResponseRedirect
from django.contrib import messages

class BlockPractitionerMiddleware:
    """
    Middleware qui bloque complètement l'accès aux URLs practitioner
    et redirige vers le dashboard
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Vérifier si l'URL contient 'practitioner'
        if 'practitioner' in request.path.lower():
            # Logger l'accès bloqué
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Accès bloqué à practitioner: {request.path} par {request.user}")
            
            # Message à l'utilisateur
            if hasattr(request, 'user') and request.user.is_authenticated:
                messages.warning(
                    request, 
                    "La section Practitioners est temporairement désactivée pour maintenance."
                )
            
            # Rediriger vers l'admin
            return HttpResponseRedirect('/fr/admin/')
        
        response = self.get_response(request)
        return response
