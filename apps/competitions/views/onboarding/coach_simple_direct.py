from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...models import UserProfile, Practitioner, CoachProfile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def coach_direct_registration(request):
    """
    Registration rapide et directe d'un coach sans utiliser le modèle DisciplineExpertise.
    Contourne tous les problèmes de champs manquants dans la base de données.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.onboarding_completed:
            messages.info(request, _("Votre profil coach est déjÃ  configuré."))
            return redirect('competitions:dashboard:index')
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur introuvable."))
        return redirect('competitions:onboarding:start')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Créer ou récupérer le practitioner
                try:
                    practitioner = Practitioner.objects.get(user=request.user)
                except Practitioner.DoesNotExist:
                    practitioner = Practitioner.objects.create(
                        user=request.user,
                        first_name=request.user.first_name or '',
                        last_name=request.user.last_name or '',
                        email=request.user.email,
                        is_coach=True,
                        birth_date=request.user.date_joined.date()  # Date par défaut
                    )
                
                # Mettre Ã  jour les informations si fournies
                if request.POST.get('first_name'):
                    practitioner.first_name = request.POST.get('first_name')
                if request.POST.get('last_name'):
                    practitioner.last_name = request.POST.get('last_name')
                if request.POST.get('email'):
                    practitioner.email = request.POST.get('email')
                
                # Marquer comme coach
                practitioner.is_coach = True
                practitioner.save()
                
                # 2. Créer ou récupérer le profil coach avec des paramètres minimaux
                try:
                    coach_profile = CoachProfile.objects.get(practitioner=practitioner)
                except CoachProfile.DoesNotExist:
                    coach_profile = CoachProfile.objects.create(
                        practitioner=practitioner,
                        profile_type=request.POST.get('profile_type', 'traditional'),
                        years_teaching=request.POST.get('years_teaching', 0),
                        teaching_philosophy=request.POST.get('teaching_philosophy', ''),
                        available_for_seminars=True,
                        available_for_private_lessons=True
                    )
                
                # 3. Marquer l'onboarding comme terminé
                profile.role = 'coach'
                profile.onboarding_step = 'final_setup'
                profile.onboarding_completed = True
                profile.save()
                
                messages.success(request, _("Félicitations ! Votre profil coach a été créé avec succès."))
                return redirect('competitions:dashboard:index')
        
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription coach directe: {str(e)}")
            messages.error(request, _("Une erreur est survenue. Veuillez réessayer ultérieurement."))
    
    # Afficher la page d'inscription simplifiée
    return render(request, 'competitions/onboarding/coach_direct_form.html', {
        'step': 'coach_direct',
        'current_step': 'coach_direct'
    })
