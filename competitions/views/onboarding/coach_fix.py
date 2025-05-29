import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...models import UserProfile, Practitioner, CoachProfile, DisciplineExpertise, Discipline, Club
from ...forms.coach_forms_fix import CoachProfileForm, DisciplineExpertiseFormSetFixed

logger = logging.getLogger(__name__)

# Liste des champs problématiques
MISSING_FIELDS = ['years_experience', 'is_primary']

@login_required
def coach_profile_fix(request):
    """Version corrigée de la gestion du profil coach sans years_experience."""
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
            birth_date=request.user.date_joined.date()  # Date par défaut pour éviter les erreurs
        )
    
    # Vérifier si le profil coach existe
    try:
        coach_profile = CoachProfile.objects.get(practitioner=practitioner)
    except CoachProfile.DoesNotExist:
        coach_profile = None
    
    if request.method == 'POST':
        form = CoachProfileForm(request.POST, instance=coach_profile)
        formset = DisciplineExpertiseFormSetFixed(
            request.POST,
            instance=coach_profile,
            prefix='disciplines'
        )
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Sauvegarder le profil coach
                if not coach_profile:
                    coach_profile = form.save(commit=False)
                    coach_profile.practitioner = practitioner
                    coach_profile.save()
                else:
                    form.save()
                
                # Sauvegarder les expertises disciplinaires (sans years_experience)
                formset.instance = coach_profile
                formset.save()
                
                # Marquer le practitioner comme coach
                practitioner.is_coach = True
                practitioner.save()
                
                # Finaliser directement l'onboarding
                profile.role = 'coach'
                profile.onboarding_step = 'final_setup'
                profile.onboarding_completed = True
                profile.save()
                
                messages.success(request, _("Profil coach créé avec succès!"))
                return redirect('dashboard:index')
        else:
            logger.error(f"Erreurs de formulaire: {form.errors}, Formset errors: {formset.errors}")
            messages.error(request, _("Veuillez corriger les erreurs dans le formulaire."))
    else:
        form = CoachProfileForm(instance=coach_profile)
        formset = DisciplineExpertiseFormSetFixed(
            instance=coach_profile,
            prefix='disciplines'
        )
    
    context = {
        'form': form,
        'formset': formset,
        'step': 'coach_profile',
        'current_step': 'coach_profile',
        'disciplines': Discipline.objects.all(),
        'clubs': Club.objects.all()
    }
    
    return render(request, 'competitions/onboarding/coach_profile.html', context)