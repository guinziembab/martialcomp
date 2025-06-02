from django.conf import settings
from django.core.exceptions import DisallowedHost

class AllowedHostsOverrideMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Essayer de manipuler la vérification d'hôte ici
        try:
            return self.get_response(request)
        except DisallowedHost:
            # Si l'hôte est 'martialcomp.onrender.com', on autorise manuellement
            if 'HTTP_HOST' in request.META and (
                request.META['HTTP_HOST'] == 'martialcomp.onrender.com' or
                '.onrender.com' in request.META['HTTP_HOST']
            ):
                # Ajoutez-le temporairement aux hôtes autorisés
                settings.ALLOWED_HOSTS.append(request.META['HTTP_HOST'])
                # Essayez à nouveau
                return self.get_response(request)
            raise