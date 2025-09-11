# C:\martial_hub_django\martialcomp\competitions\middleware\__init__.py

from django.shortcuts import redirect
import logging
import re

logger = logging.getLogger(__name__)

class OnboardingRedirectMiddleware:
    """
    Middleware pour rediriger les utilisateurs vers le processus d'onboarding
    après une connexion réussie si nécessaire, et intercepter les anciennes URLs d'onboarding.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Intercepter les URLs d'onboarding sans préfixe /competitions/
        path = request.path
        
        # Si c'est une URL d'onboarding directe sans competitions
        onboarding_pattern = r'^/(?:(?P<lang>[a-z]{2})/)?onboarding/(?P<step>[\w-]*)/?$'
        match = re.match(onboarding_pattern, path)
        
        if match:
            lang = match.group('lang') or ''
            step = match.group('step') or ''
            if step == '':
                step = ''
            
            # Construire la nouvelle URL
            if lang:
                new_path = f'/{lang}/competitions/onboarding/{step}/'
            else:
                new_path = f'/competitions/onboarding/{step}/'
            
            logger.info(f"Redirection onboarding: {path} -> {new_path}")
            return redirect(new_path)
            
        # Obtenir la réponse normale
        response = self.get_response(request)
        
        # Vérifier si l'utilisateur est authentifié (avec protection contre les erreurs)
        try:
            user_authenticated = hasattr(request, 'user') and request.user.is_authenticated
        except AttributeError:
            user_authenticated = False
            
        if user_authenticated:
            # Exclure certaines URLs du processus de redirection
            excluded_paths = [
                '/competitions/onboarding/',
                '/competitions/dashboard/',
                '/onboarding/',
                '/dashboard/',
                '/accounts/',
                '/account/',
                '/admin/',
                '/static/',
                '/media/',
                '/api/',
                '/__debug__/',
            ]
            
            # Exclure les URLs d'onboarding avec préfixes de langue
            excluded_patterns = [
                r'^/[a-z]{2}/competitions/onboarding/',
                r'^/competitions/onboarding/',
            ]
            
            # Vérifier si le chemin actuel est exclu
            path_excluded = any(path.startswith(excl) for excl in excluded_paths)
            pattern_excluded = any(re.match(pattern, path) for pattern in excluded_patterns)
            
            if not (path_excluded or pattern_excluded):
                try:
                    # Vérifier si l'utilisateur a un profil et n'a pas complété l'onboarding
                    if hasattr(request.user, 'profile') and not request.user.profile.onboarding_completed:
                        # Récupérer l'étape d'onboarding de l'utilisateur
                        onboarding_step = request.user.profile.onboarding_step or 'role_selection'
                        
                        # Mapper l'étape vers l'URL correcte
                        step_url_mapping = {
                            'role_selection': 'role',
                            'federation': 'federations',
                            'club_creation': 'club/creation',
                            'club_details': 'club/details',
                            'categories_setup': 'categories/setup',
                            'judge_profile': 'judge',
                            'participant_profile': 'participant',
                            'coach_profile': 'coach/profile-simple',
                            'coach_profile_simplified': 'coach/profile-simple',
                            'final_setup': 'final'
                        }
                        
                        # Utiliser l'URL mappée ou l'étape par défaut
                        url_step = step_url_mapping.get(onboarding_step, 'role')
                        
                        # Déterminer si nous avons un préfixe de langue
                        lang_match = re.match(r'^/([a-z]{2})/', path)
                        lang_prefix = lang_match.group(1) + '/' if lang_match else ''
                        
                        # Construire l'URL de redirection
                        redirect_url = f'/{lang_prefix}competitions/onboarding/{url_step}/'
                        
                        # Log la redirection
                        logger.info(f"Redirection utilisateur {request.user.username} vers {redirect_url}")
                        
                        # Ne rediriger que si nous sommes sur une page différente
                        # et éviter les boucles infinies
                        current_is_onboarding = (path.startswith('/competitions/onboarding/') or 
                                                re.match(r'^/[a-z]{2}/competitions/onboarding/', path))
                        
                        if path != redirect_url and not current_is_onboarding:
                            return redirect(redirect_url)
                except Exception as e:
                    # Log l'erreur mais ne pas bloquer la navigation
                    logger.error(f"Erreur dans le middleware d'onboarding: {str(e)}")
        
        return response
