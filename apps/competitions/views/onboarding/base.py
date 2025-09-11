from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from ...models import UserProfile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def onboarding_start(request):
    """
    Point d'entrée pour le processus d'onboarding.
    Redirige vers l'étape appropriée en fonction de l'état d'avancement de l'utilisateur.
    """
    try:
        # Vérifier si le profil existe et si l'onboarding est complété
        profile = UserProfile.objects.get(user=request.user)
        if profile.onboarding_completed:
            messages.info(request, _("Votre compte est déjà configuré."))
            return redirect('competitions:dashboard:index')
    except UserProfile.DoesNotExist:
        # Créer un profil si nécessaire
        profile = UserProfile.objects.create(
            user=request.user, 
            role='spectator',  # Rôle par défaut
            onboarding_step='role_selection'
        )
        logger.info(f"Profil créé pour l'utilisateur {request.user.username}")
    
    # Récupérer l'étape actuelle depuis le profil
    current_step = profile.onboarding_step or 'role_selection'
    logger.debug(f"Étape d'onboarding actuelle pour {request.user.username}: {current_step}")
    
    # Mettre à jour la session
    request.session['onboarding_step'] = current_step
    
    # Rediriger vers l'étape appropriée
    routes = {
        'role_selection': 'competitions:onboarding:role_selection',
        'federation': 'competitions:onboarding:federation',
        'club_creation': 'competitions:onboarding:club_creation',
        'club_details': 'competitions:onboarding:club_details',
        'categories_setup': 'competitions:onboarding:categories_setup',
        'judge_profile': 'competitions:onboarding:judge_profile',
        'participant_profile': 'competitions:onboarding:participant_profile',
        'coach_profile_simplified': 'competitions:onboarding:coach_profile_simplified',
        'final_setup': 'competitions:onboarding:final_setup',
    }

    if current_step in routes:
        return redirect(routes[current_step])
    else:
        # Par défaut, commencer par la sélection du rôle
        profile.onboarding_step = 'role_selection'
        profile.save()
        request.session['onboarding_step'] = 'role_selection'
        logger.warning(f"Étape d'onboarding inconnue pour {request.user.username}: {current_step}. Réinitialisation à role_selection")
        return redirect('competitions:onboarding:role_selection')

@login_required
def onboarding_router(request):
    """
    Vue qui redirige l'utilisateur vers la bonne étape d'onboarding
    en fonction de son état actuel.
    Cette vue est utilisée par le middleware d'onboarding pour rediriger 
    les utilisateurs dont l'onboarding n'est pas terminé.
    """
    user = request.user

    try:
        # Vérifier si le profil existe
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        # Créer un profil par défaut si l'utilisateur n'en a pas
        profile = UserProfile.objects.create(
            user=user,
            role='spectator',
            onboarding_step='role_selection',
            onboarding_completed=False
        )
        logger.info(f"Profil créé pour {user.username} via le routeur d'onboarding")
    
    # Si l'onboarding est déjà terminé, rediriger vers le dashboard
    if profile.onboarding_completed:
        logger.info(f"Onboarding déjà terminé pour {user.username}, redirection vers le dashboard")
        return redirect('competitions:dashboard:index')
    
    onboarding_routes = {
        'role_selection': 'competitions:onboarding:role_selection',
        'federation': 'competitions:onboarding:federation',
        'club_creation': 'competitions:onboarding:club_creation',
        'club_details': 'competitions:onboarding:club_details',
        'categories_setup': 'competitions:onboarding:categories_setup',
        'judge_profile': 'competitions:onboarding:judge_profile',
        'participant_profile': 'competitions:onboarding:participant_profile',
        'coach_profile_simplified': 'competitions:onboarding:coach_profile_simplified',
        'final_setup': 'competitions:onboarding:final_setup',
    }

    # Déterminer l'étape d'onboarding actuelle
    onboarding_step = profile.onboarding_step or 'role_selection'
    logger.info(f"Étape d'onboarding pour {user.username}: {onboarding_step}")
    
    # Mettre à jour la session
    request.session['onboarding_step'] = onboarding_step
    
    # Rediriger vers l'étape correspondante
    if onboarding_step in onboarding_routes:
        return redirect(onboarding_routes[onboarding_step])
    else:
        logger.error(f"Étape d'onboarding inconnue pour {user.username}: {onboarding_step}")
        # Par défaut, rediriger vers la sélection de rôle
        profile.onboarding_step = 'role_selection'
        profile.save()
        request.session['onboarding_step'] = 'role_selection'
        return redirect('competitions:onboarding:role_selection')
