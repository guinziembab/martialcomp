import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...models import UserProfile, Practitioner, CoachProfile, DisciplineExpertise, Discipline, Club
from ...forms.onboarding import CoachProfileForm, DisciplineExpertiseFormSet

logger = logging.getLogger(__name__)

@login_required
def coach_profile(request):
    """Gestion du profil coach dans le processus d'onboarding."""
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
            is_coach=True
        )
    
    # Vérifier si le profil coach existe
    try:
        coach_profile = CoachProfile.objects.get(practitioner=practitioner)
    except CoachProfile.DoesNotExist:
        coach_profile = None
    
    if request.method == 'POST':
        form = CoachProfileForm(request.POST, instance=coach_profile)
        formset = DisciplineExpertiseFormSet(
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
                
                # Sauvegarder les expertises disciplinaires
                formset.instance = coach_profile
                formset.save()
                
                # Marquer le practitioner comme coach
                practitioner.is_coach = True
                practitioner.save()
                
                # Mettre à jour le profil utilisateur
                profile.role = 'coach'
                profile.onboarding_step = 'coach_disciplines'
                profile.save()
                
                messages.success(request, _("Profil coach créé avec succès."))
                return redirect('onboarding:coach_disciplines')
    else:
        form = CoachProfileForm(instance=coach_profile)
        formset = DisciplineExpertiseFormSet(
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


@login_required
def coach_disciplines(request):
    """Gestion des disciplines du coach."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        practitioner = Practitioner.objects.get(user=request.user)
        coach_profile = CoachProfile.objects.get(practitioner=practitioner)
    except (UserProfile.DoesNotExist, Practitioner.DoesNotExist, CoachProfile.DoesNotExist):
        messages.error(request, _("Profil coach introuvable."))
        return redirect('onboarding:coach_profile')
    
    if request.method == 'POST':
        # Traiter les disciplines sélectionnées
        primary_discipline_id = request.POST.get('primary_discipline')
        secondary_discipline_ids = request.POST.getlist('secondary_disciplines')
        
        if primary_discipline_id:
            try:
                primary_discipline = Discipline.objects.get(id=primary_discipline_id)
                practitioner.primary_discipline = primary_discipline
                
                # Créer ou mettre à jour l'expertise principale
                expertise, created = DisciplineExpertise.objects.get_or_create(
                    coach_profile=coach_profile,
                    discipline=primary_discipline,
                    defaults={'is_primary': True}
                )
                if not created:
                    expertise.is_primary = True
                    expertise.save()
                
                # Ajouter les disciplines secondaires
                practitioner.secondary_disciplines.clear()
                for disc_id in secondary_discipline_ids:
                    if disc_id != primary_discipline_id:
                        discipline = Discipline.objects.get(id=disc_id)
                        practitioner.secondary_disciplines.add(discipline)
                        
                        # Créer l'expertise secondaire
                        DisciplineExpertise.objects.get_or_create(
                            coach_profile=coach_profile,
                            discipline=discipline,
                            defaults={'is_primary': False}
                        )
                
                practitioner.save()
                
                # Passer à l'étape suivante
                profile.onboarding_step = 'coach_availability'
                profile.save()
                
                messages.success(request, _("Disciplines configurées avec succès."))
                return redirect('onboarding:coach_availability')
                
            except Discipline.DoesNotExist:
                messages.error(request, _("Discipline invalide."))
    
    # Préparer les données pour le template
    disciplines = Discipline.objects.all()
    current_expertises = coach_profile.discipline_expertises.all()
    
    context = {
        'disciplines': disciplines,
        'current_expertises': current_expertises,
        'practitioner': practitioner,
        'step': 'coach_disciplines',
        'current_step': 'coach_disciplines'
    }
    
    return render(request, 'competitions/onboarding/coach_disciplines.html', context)


@login_required
def coach_availability(request):
    """Configuration des disponibilités du coach."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        practitioner = Practitioner.objects.get(user=request.user)
        coach_profile = CoachProfile.objects.get(practitioner=practitioner)
    except (UserProfile.DoesNotExist, Practitioner.DoesNotExist, CoachProfile.DoesNotExist):
        messages.error(request, _("Profil coach introuvable."))
        return redirect('onboarding:coach_profile')
    
    if request.method == 'POST':
        # Mettre à jour les disponibilités
        coach_profile.available_for_seminars = 'seminars' in request.POST
        coach_profile.available_for_private_lessons = 'private_lessons' in request.POST
        coach_profile.available_for_online_coaching = 'online_coaching' in request.POST
        coach_profile.hourly_rate_range = request.POST.get('hourly_rate_range', '')
        coach_profile.save()
        
        # Terminer l'onboarding
        profile.onboarding_step = 'final_setup'
        profile.onboarding_completed = True
        profile.save()
        
        messages.success(request, _("Configuration du profil coach terminée !"))
        return redirect('dashboard:index')
    
    context = {
        'coach_profile': coach_profile,
        'step': 'coach_availability',
        'current_step': 'coach_availability'
    }
    
    return render(request, 'competitions/onboarding/coach_availability.html', context)