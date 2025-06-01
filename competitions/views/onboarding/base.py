import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from ...models import UserProfile

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
            return redirect('dashboard:index')
    except UserProfile.DoesNotExist:
        # Créer un profil si nécessaire
        profile = UserProfile.objects.create(
            user=request.user, 
            role='spectator',  # Rôle par défaut
            onboarding_step='role_selection'
        )
    
    # Récupérer l'étape actuelle depuis le profil
    current_step = profile.onboarding_step or 'role_selection'
    
    # Mettre à jour la session
    request.session['onboarding_step'] = current_step
    
    # Rediriger vers l'étape appropriée
    if current_step == 'role_selection':
        return redirect('onboarding:role_selection')
    elif current_step == 'federation':
        return redirect('onboarding:federation')
    elif current_step == 'club_creation':
        return redirect('onboarding:club_creation')
    elif current_step == 'club_details':
        return redirect('onboarding:club_details')
    elif current_step == 'categories_setup':
        return redirect('onboarding:categories_setup')
    elif current_step == 'judge_profile':
        return redirect('onboarding:judge_profile')
    elif current_step == 'participant_profile':
        return redirect('onboarding:participant_profile')
    elif current_step == 'final_setup':
        return redirect('onboarding:final_setup')
    else:
        # Par défaut, commencer par la sélection du rôle
        profile.onboarding_step = 'role_selection'
        profile.save()
        request.session['onboarding_step'] = 'role_selection'
        return redirect('onboarding:role_selection')