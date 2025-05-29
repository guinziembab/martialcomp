import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from ...models import UserProfile
from ...forms.onboarding import RoleSelectionForm

logger = logging.getLogger(__name__)

@login_required
def handle_role_selection(request):
    """Gestion de la sélection du rôle dans le processus d'onboarding."""
    try:
        # Récupérer ou créer le profil utilisateur
        profile = UserProfile.objects.get(user=request.user)
        if profile.onboarding_completed:
            messages.info(request, _("Votre compte est déjà configuré."))
            return redirect('dashboard:index')
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=request.user, 
            role='spectator',
            onboarding_step='role_selection'
        )
    
    if request.method == 'POST':
        form = RoleSelectionForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data['role']
            
            # Mettre à jour le rôle dans le profil
            profile.role = role
            
            # Définir l'étape suivante en fonction du rôle
            if role == 'federation_admin':
                profile.onboarding_step = 'federation'
                profile.save()
                request.session['onboarding_step'] = 'federation'
                return redirect('onboarding:federation')
            elif role == 'club_manager':
                profile.onboarding_step = 'club_creation'
                profile.save()
                request.session['onboarding_step'] = 'club_creation'
                return redirect('onboarding:club_creation')
            elif role == 'judge':
                profile.onboarding_step = 'judge_profile'
                profile.save()
                request.session['onboarding_step'] = 'judge_profile'
                return redirect('onboarding:judge_profile')
            elif role == 'coach':
                # Utiliser la version ultra-simplifiée qui contourne les problèmes de modèle
                profile.onboarding_step = 'coach_profile'
                profile.save()
                request.session['onboarding_step'] = 'coach_profile'
                return redirect('onboarding:coach_profile')
            elif role == 'participant':
                profile.onboarding_step = 'participant_profile'
                profile.save()
                request.session['onboarding_step'] = 'participant_profile'
                return redirect('onboarding:participant_profile')
            else:
                # Pour les autres rôles (spectateur, etc.), passer directement à l'étape finale
                profile.onboarding_step = 'final_setup'
                profile.save()
                request.session['onboarding_step'] = 'final_setup'
                return redirect('onboarding:final_setup')
    else:
        form = RoleSelectionForm()
    
    return render(request, 'competitions/onboarding/role_selection.html', {
        'form': form,
        'step': 'role_selection',
        'current_step': 'role_selection'
    })