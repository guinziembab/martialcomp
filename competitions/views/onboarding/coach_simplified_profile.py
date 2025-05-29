import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...models import UserProfile, Practitioner, CoachProfile
from ...forms.onboarding import CoachProfileForm

logger = logging.getLogger(__name__)

@login_required
def coach_profile_simplified(request):
    """Version simplifiée de la gestion du profil coach sans disciplines."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.onboarding_completed:
            messages.info(request, _("Votre profil coach est déjà configuré."))
            return redirect('dashboard:index')
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur introuvable."))
        return redirect('onboarding:start')
    
    # Vérifier si le practitioner existe
    try:
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        # Créer un practitioner de base
        practitioner = Practitioner.objects.create(
            user=request.user,
            first_name=request.user.first_name or '',
            last_name=request.user.last_name or '',
            email=request.user.email,
            is_coach=True,
            birth_date=request.user.date_joined.date()  # Date par défaut pour éviter des erreurs
        )
    
    # Vérifier si le profil coach existe
    try:
        coach_profile = CoachProfile.objects.get(practitioner=practitioner)
    except CoachProfile.DoesNotExist:
        coach_profile = None
    
    if request.method == 'POST':
        form = CoachProfileForm(request.POST, instance=coach_profile)
        
        if form.is_valid():
            with transaction.atomic():
                # Sauvegarder le profil coach
                if not coach_profile:
                    coach_profile = form.save(commit=False)
                    coach_profile.practitioner = practitioner
                    coach_profile.save()
                else:
                    form.save()
                
                # Marquer le practitioner comme coach
                practitioner.is_coach = True
                practitioner.save()
                
                # Marquer l'onboarding comme terminé
                profile.role = 'coach'
                profile.onboarding_step = 'final_setup'
                profile.onboarding_completed = True
                profile.save()
                
                messages.success(request, _("Profil coach créé avec succès. Vous pouvez maintenant accéder à votre tableau de bord."))
                return redirect('dashboard:index')
    else:
        form = CoachProfileForm(instance=coach_profile)
    
    context = {
        'form': form,
        'step': 'coach_profile_simplified',
        'current_step': 'coach_profile_simplified'
    }
    
    return render(request, 'competitions/onboarding/coach_profile_simplified.html', context)