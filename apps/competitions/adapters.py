"""
Adaptateurs Django-Allauth personnalisés pour MartialComp
Gestion de l'onboarding et redirection après inscription/connexion
"""
import logging
from django.urls import reverse
from django.shortcuts import resolve_url
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from apps.competitions.models import UserProfile

logger = logging.getLogger(__name__)

class MartialCompAccountAdapter(DefaultAccountAdapter):
    """
    Adaptateur personnalisé pour django-allauth.
    Gère l'onboarding après inscription et connexion.
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Sauvegarde l'utilisateur et configure l'onboarding.
        """
        user = super().save_user(request, user, form, commit=commit)
        
        if commit:
            try:
                # S'assurer que l'utilisateur a le bon backend défini
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                
                # Créer ou mettre à jour le profil utilisateur
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'spectator',
                        'onboarding_step': 'role_selection',
                        'onboarding_completed': False
                    }
                )
                
                if not created:
                    # Mettre à jour un profil existant pour l'onboarding
                    profile.role = 'spectator'
                    profile.onboarding_step = 'role_selection'
                    profile.onboarding_completed = False
                    profile.save()
                    logger.info(f"Profil utilisateur existant mis à jour pour {user.username}")
                else:
                    logger.info(f"Nouveau profil utilisateur créé pour {user.username}")
                    
            except Exception as e:
                logger.error(f"Erreur lors de la configuration du profil pour {user.username}: {str(e)}")
        
        return user
    
    def get_signup_redirect_url(self, request):
        """
        Redirection après inscription.
        """
        try:
            # Toujours rediriger vers l'onboarding après inscription
            # Le middleware se chargera de la gestion si l'utilisateur n'est pas connecté
            logger.info(f"Redirection après inscription vers l'onboarding")
            return reverse('competitions:onboarding:role_selection')
            
        except Exception as e:
            logger.error(f"Erreur lors de la redirection après inscription: {str(e)}")
            # En cas d'erreur, rediriger vers la page d'accueil
            return reverse('competitions:welcome')
    
    def get_login_redirect_url(self, request):
        """
        Redirection après connexion.
        """
        try:
            if request.user.is_authenticated:
                # Vérifier si l'utilisateur a un profil
                if hasattr(request.user, 'profile'):
                    profile = request.user.profile
                    # Si onboarding pas complété, rediriger vers l'onboarding
                    if not profile.onboarding_completed:
                        logger.info(f"Redirection après connexion vers l'onboarding pour {request.user.username}")
                        return reverse('competitions:onboarding:role_selection')
                    else:
                        # Onboarding complété, rediriger selon le rôle
                        role = profile.role
                        role_map = {
                            'coach': 'competitions:dashboard:coach',
                            'club_manager': 'competitions:dashboard:club',
                            'participant': 'competitions:dashboard:participant',
                            # federation_admin est géré séparément car il nécessite federation_id
                            'referee': 'competitions:dashboard:referee',
                            'judge': 'competitions:dashboard:judge_technical',
                            'pro': 'competitions:dashboard:pro',
                            'manager': 'competitions:dashboard:manager',
                            'spectator': 'competitions:dashboard:spectator',
                            'external_organizer': 'competitions:dashboard:external_organizer',
                        }
                        role_key = str(role).lower().strip()
                        if role_key == 'federation_admin':
                            # Import dynamique pour éviter les imports circulaires
                            try:
                                from apps.competitions.models import Federation
                                federation = Federation.objects.filter(owner=request.user).first()
                                if not federation:
                                    # Essayer via administrators
                                    federation = Federation.objects.filter(administrators__user=request.user).first()

                                if federation:
                                    # Utiliser le namespace dashboard (URL unifiée)
                                    return reverse('competitions:dashboard:federation', kwargs={'federation_id': federation.id})
                                else:
                                    # Rediriger vers la liste qui gère le cas sans fédération
                                    return reverse('competitions:dashboard:federations')
                            except Exception as fed_error:
                                logger.error(f"Erreur lors de l'accès à Federation: {str(fed_error)}")
                                return reverse('competitions:dashboard:federations')

                        if role_key in role_map:
                            return reverse(role_map[role_key])
                        # Fallback
                        return reverse('competitions:dashboard:spectator')
                else:
                    # Pas de profil, créer un profil et rediriger vers l'onboarding
                    UserProfile.objects.create(
                        user=request.user,
                        role='spectator',
                        onboarding_step='role_selection',
                        onboarding_completed=False
                    )
                    logger.info(f"Profil créé lors de la connexion pour {request.user.username}")
                    return reverse('competitions:onboarding:role_selection')
            # Fallback
            return reverse('competitions:welcome')
        except Exception as e:
            logger.error(f"Erreur lors de la redirection après connexion: {str(e)}")
            return reverse('competitions:welcome')
    
    def login(self, request, user):
        """
        Connexion de l'utilisateur avec backend spécifique pour éviter l'erreur.
        """
        try:
            from django.contrib.auth import login
            # Définir explicitement le backend sur l'utilisateur avant la connexion
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            # Connecter l'utilisateur
            login(request, user)
            logger.info(f"Utilisateur {user.username} connecté avec succès via adaptateur")
        except Exception as e:
            logger.error(f"Erreur lors de la connexion de {user.username}: {str(e)}")
            # Fallback: définir le backend et essayer la méthode parent
            try:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                super().login(request, user)
            except Exception as e2:
                logger.error(f"Erreur lors du fallback de connexion: {str(e2)}")
    
    def get_logout_redirect_url(self, request):
        """
        Redirection après déconnexion.
        Assure que l'utilisateur est redirigé vers la page d'accueil avec un paramètre
        pour éviter les redirections automatiques.
        """
        try:
            from django.utils.translation import get_language
            # Obtenir la langue courante
            current_language = get_language() or 'fr'
            
            # Toujours rediriger vers la page d'accueil avec un paramètre no_redirect
            # pour éviter que la vue welcome redirige automatiquement
            logger.info(f"Redirection après déconnexion vers la page d'accueil ({current_language})")
            
            # Construire l'URL avec le préfixe de langue correct
            return f'/{current_language}/?no_redirect=1'
        except Exception as e:
            logger.error(f"Erreur lors de la redirection après déconnexion: {str(e)}")
            # Fallback vers l'URL de base avec préfixe de langue
            return '/fr/?no_redirect=1'

class MartialCompSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adaptateur personnalisé pour les comptes sociaux.
    """

    def save_user(self, request, sociallogin, form=None):
        """
        Sauvegarde d'un utilisateur connecté via un compte social.
        """
        user = super().save_user(request, sociallogin, form)

        try:
            # Créer ou mettre à jour le profil utilisateur
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': 'spectator',
                    'onboarding_step': 'role_selection',
                    'onboarding_completed': False
                }
            )

            if not created and not profile.onboarding_completed:
                # S'assurer que l'onboarding est configuré
                profile.onboarding_step = 'role_selection'
                profile.save()

            logger.info(f"Compte social configuré pour {user.username}")

            # Envoyer un email de bienvenue si c'est une nouvelle inscription
            if created:
                try:
                    from apps.competitions.services.email_service import EmailService
                    provider = sociallogin.account.provider if sociallogin and sociallogin.account else None
                    EmailService.send_welcome_email(user, provider=provider)
                    logger.info(f"Email de bienvenue envoyé à {user.email} (provider: {provider})")
                except Exception as email_error:
                    logger.warning(f"Impossible d'envoyer l'email de bienvenue: {email_error}")

        except Exception as e:
            logger.error(f"Erreur lors de la configuration du compte social pour {user.username}: {str(e)}")

        return user
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        Redirection après connexion d'un compte social.
        """
        try:
            user = request.user
            if user.is_authenticated and hasattr(user, 'profile'):
                profile = user.profile
                if not profile.onboarding_completed:
                    return reverse('competitions:onboarding:role_selection')
            
            return reverse('competitions:dashboard:index')
            
        except Exception as e:
            logger.error(f"Erreur lors de la redirection après connexion sociale: {str(e)}")
            return reverse('competitions:welcome')

# Aliases pour compatibilité (si d'anciens noms sont utilisés quelque part)
CustomAccountAdapter = MartialCompAccountAdapter
CustomSocialAccountAdapter = MartialCompSocialAccountAdapter