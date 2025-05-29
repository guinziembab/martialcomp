import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from ...forms.onboarding import ParticipantProfileForm

logger = logging.getLogger(__name__)

@login_required
def handle_participant_profile(request):
    """Gestion du profil participant"""
    # Vérifier si l'utilisateur a un profil et le rôle approprié
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'participant':
        messages.error(request, _("Accès non autorisé. Vous devez être participant."))
        return redirect('onboarding:role_selection')
    
    if request.method == 'POST':
        form = ParticipantProfileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                profile = form.save(commit=False)
                profile.user = request.user
                
                # S'assurer que l'email n'est pas vide, utiliser celui de l'utilisateur si nécessaire
                if not profile.email:
                    profile.email = request.user.email
                
                profile.save()
                
                # Si le formulaire a des champs ManyToMany
                form.save_m2m()
                
                # Mise à jour de l'étape d'onboarding
                request.user.profile.onboarding_step = 'final_setup'
                request.user.profile.save()
                request.session['onboarding_step'] = 'final_setup'
                
                messages.success(request, _("Profil de participant créé avec succès!"))
                return redirect('onboarding:final_setup')
            except Exception as e:
                messages.error(request, _(f"Erreur lors de la création du profil: {str(e)}"))
                logger.error(f"Erreur lors de la création du profil participant: {str(e)}")
    else:
        # Initialiser le formulaire avec l'email de l'utilisateur
        form = ParticipantProfileForm(initial={'email': request.user.email})
    
    return render(request, 'competitions/onboarding/participant_profile.html', {
        'form': form,
        'step': 'participant_profile',
        'current_step': 'participant_profile'
    })