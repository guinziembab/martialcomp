from .discipline_filtering import get_user_access_context


class AccessContextMiddleware:
    """
    Middleware qui ajoute le contexte d'accès par discipline Ã  chaque requÃªte.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user_disciplines, request.discipline_federation_mapping = get_user_access_context(request.user)
        else:
            request.user_disciplines = []
            request.discipline_federation_mapping = {}
        
        response = self.get_response(request)
        return response 
