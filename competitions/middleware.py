# middleware.py
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.conf import settings

class OnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ne s'applique qu'aux utilisateurs authentifiés
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Exclure les chemins d'onboarding et les chemins statiques/admin
        path = request.path_info
        excluded_paths = [
            '/static/', '/media/', '/admin/', '/logout/', 
            '/onboarding/', '/api/', '/favicon.ico'
        ]
        
        if any(path.startswith(excluded) for excluded in excluded_paths):
            return self.get_response(request)
        
        # Vérifier si l'utilisateur a un profil et s'il a complété l'onboarding
        try:
            profile = request.user.profile
            # Si l'onboarding n'est pas terminé, rediriger vers l'onboarding
            if not profile.onboarding_completed:
                onboarding_url = reverse('competitions:onboarding:onboarding_router')
                if path != onboarding_url:
                    return redirect(onboarding_url)
        except Exception:
            # Si pas de profil, laisser passer (sera géré ailleurs)
            pass
        
        return self.get_response(request)