"""
Signaux spécifiques pour django-allauth
Gestion de l'onboarding après inscription via allauth
"""
import logging
from django.dispatch import receiver
from django.contrib.auth import login
from django.shortcuts import redirect
from allauth.account.signals import user_signed_up, user_logged_in
from allauth.socialaccount.signals import social_account_added
from .models import UserProfile

logger = logging.getLogger(__name__)

@receiver(user_signed_up)
def create_user_profile_on_signup(sender, request, user, **kwargs):
    """
    Signal déclenché après l'inscription d'un utilisateur via django-allauth.
    Crée ou met Ã  jour le profil utilisateur et configure l'onboarding.
    """
    try:
        # S'assurer que l'utilisateur a le bon backend défini
        if not hasattr(user, 'backend'):
            user.backend = 'django.contrib.auth.backends.ModelBackend'
        
        # Vérifier si un profil existe déjÃ 
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'spectator',
                'onboarding_step': 'role_selection', 
                'onboarding_completed': False
            }
        )
        
        if not created:
            # Mettre Ã  jour le profil existant pour l'onboarding
            profile.role = 'spectator'
            profile.onboarding_step = 'role_selection'
            profile.onboarding_completed = False
            profile.save()
            logger.info(f"Profil utilisateur existant mis Ã  jour pour {user.username}")
        else:
            logger.info(f"Nouveau profil utilisateur créé pour {user.username}")
        
        # Forcer la connexion avec le bon backend si pas encore connecté
        if not request.user.is_authenticated or request.user != user:
            try:
                from django.contrib.auth import login
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                logger.info(f"Utilisateur {user.username} connecté automatiquement après inscription")
            except Exception as e:
                logger.error(f"Erreur lors de la connexion automatique: {str(e)}")
        
        # Loguer la redirection prévue
        logger.info(f"Redirection après inscription vers /competitions/onboarding/role/ pour {user.username}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la création/mise Ã  jour du profil pour {user.username}: {str(e)}")

@receiver(user_logged_in)
def handle_user_login_redirect(sender, request, user, **kwargs):
    """
    Signal déclenché après connexion d'un utilisateur.
    Gère la redirection vers l'onboarding si nécessaire.
    """
    try:
        # Vérifier si l'utilisateur a un profil
        if hasattr(user, 'profile'):
            profile = user.profile
            
            # Si l'onboarding n'est pas complété, ne rien faire ici
            # Le middleware s'occupera de la redirection
            if not profile.onboarding_completed:
                logger.info(f"Utilisateur {user.username} connecté - onboarding requis (étape: {profile.onboarding_step})")
            else:
                logger.info(f"Utilisateur {user.username} connecté - onboarding complété")
        else:
            # Créer un profil si nécessaire
            profile = UserProfile.objects.create(
                user=user,
                role='spectator',
                onboarding_step='role_selection',
                onboarding_completed=False
            )
            logger.info(f"Profil créé lors de la connexion pour {user.username}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la connexion pour {user.username}: {str(e)}")

@receiver(social_account_added)
def handle_social_account_added(sender, request, sociallogin, **kwargs):
    """
    Signal déclenché après ajout d'un compte social.
    Configure l'onboarding pour les utilisateurs connectés via réseaux sociaux.
    """
    try:
        user = sociallogin.user
        
        # Vérifier si un profil existe
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'spectator',
                'onboarding_step': 'role_selection',
                'onboarding_completed': False
            }
        )
        
        if not created and not profile.onboarding_completed:
            # S'assurer que l'onboarding est configuré correctement
            profile.onboarding_step = 'role_selection'
            profile.save()
        
        logger.info(f"Compte social ajouté pour {user.username} - onboarding configuré")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du compte social: {str(e)}")
