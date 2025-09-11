import logging
from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

class OnboardingRedirectMiddleware(MiddlewareMixin):
    """
    Middleware pour rediriger les utilisateurs vers le processus d'onboarding
    CORRIGÉ - Gestion des URLs sans préfixe de langue et logique améliorée
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        super().__init__(get_response)
        
    def process_request(self, request):
        """
        Traiter la requête pour rediriger vers l'onboarding si nécessaire
        """
        # Vérifier si l'utilisateur est authentifié
        if not request.user or isinstance(request.user, AnonymousUser) or not request.user.is_authenticated:
            return None
            
        current_path = request.path
        
        # URLs à exclure complètement du processus de redirection
        excluded_paths = [
            '/competitions/onboarding/',  # ✅ CORRIGÉ: URLs onboarding correctes
            '/onboarding/',               # Fallback pour compatibilité
            '/accounts/logout/',
            '/admin/',
            '/static/',
            '/media/',
            '/api/',
            '/__debug__/',
            '/accounts/logout/',
            '/favicon.ico',
            '/robots.txt',
            '/sitemap.xml',
        ]
        
        # Vérifier si le chemin actuel est exclu
        if any(current_path.startswith(path) for path in excluded_paths):
            return None
            
        try:
            # Vérifier si l'utilisateur a un profil
            profile = None
            
            # Méthode 1: Essayer userprofile
            if hasattr(request.user, 'userprofile'):
                profile = request.user.userprofile
            # Méthode 2: Essayer profile  
            elif hasattr(request.user, 'profile'):
                profile = request.user.profile
                
            if profile:
                # Vérifier si l'onboarding est complété
                onboarding_completed = getattr(profile, 'onboarding_completed', False)
                
                # ✅ CORRECTION: Vérifier si l'utilisateur a un pratiquant associé
                # Si c'est le cas, marquer automatiquement l'onboarding comme terminé
                if not onboarding_completed:
                    has_practitioner = False
                    try:
                        # Vérifier si l'utilisateur a un pratiquant associé
                        if hasattr(request.user, 'practitioners') and request.user.practitioners.exists():
                            has_practitioner = True
                        elif hasattr(request.user, 'practitioner'):
                            has_practitioner = True
                    except Exception:
                        pass
                    
                    if has_practitioner:
                        # Marquer automatiquement l'onboarding comme terminé pour les pratiquants convertis
                        profile.onboarding_completed = True
                        profile.onboarding_step = 'completed'
                        profile.role = 'participant'  # S'assurer que le rôle est correct
                        profile.save()
                        logger.info(f"Onboarding auto-complété pour pratiquant converti: {request.user.username}")
                        return None
                
                if not onboarding_completed:
                    # Déterminer l'étape d'onboarding
                    onboarding_step = getattr(profile, 'onboarding_step', 'role')
                    
                    # Nettoyer l'étape pour correspondre aux URLs
                    if onboarding_step == 'role_selection':
                        onboarding_step = 'role'
                    
                    # ✅ CORRIGÉ: URL correcte sans préfixe de langue
                    redirect_url = f'/competitions/onboarding/{onboarding_step}/'
                    
                    # Éviter les redirections en boucle
                    if current_path != redirect_url and not current_path.startswith('/competitions/onboarding/'):
                        logger.info(f"Redirection utilisateur {request.user.username} vers {redirect_url}")
                        return redirect(redirect_url)
            else:
                # Créer un profil par défaut si inexistant
                try:
                    from apps.competitions.models import UserProfile
                    UserProfile.objects.get_or_create(
                        user=request.user,
                        defaults={
                            'role': 'spectator',
                            'onboarding_step': 'role',
                            'onboarding_completed': False
                        }
                    )
                    logger.info(f"Profil créé pour utilisateur {request.user.username}")
                except Exception as create_error:
                    logger.error(f"Erreur création profil: {create_error}")
                
        except Exception as e:
            logger.error(f"Erreur middleware onboarding: {e}")
            
        return None
    
    def process_response(self, request, response):
        """
        Traiter la réponse (optionnel - pour debugging)
        """
        return response