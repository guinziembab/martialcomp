from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...models import (
    UserProfile, 
    Practitioner, 
    CoachProfile, 
    DisciplineExpertise, 
    Discipline, 
    Club,
    Federation
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def handle_coach_simplified(request):
    """
    Vue simplifiée pour l'onboarding des coaches en une seule étape.
    Combine les informations essentielles des 3 étapes du processus standard.
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.onboarding_completed:
            messages.info(request, _("Votre profil coach est déjÃ  configuré."))
            return redirect('competitions:dashboard:index')
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur introuvable."))
        return redirect('competitions:onboarding:start')
    
    # Si la méthode est POST, traiter le formulaire
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 1. Créer ou récupérer le pratiquant
                practitioner, created = Practitioner.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'first_name': request.POST.get('first_name', request.user.first_name or ''),
                        'last_name': request.POST.get('last_name', request.user.last_name or ''),
                        'email': request.POST.get('email', request.user.email),
                        'phone': request.POST.get('phone', ''),
                        'is_coach': True
                    }
                )
                
                if not created:
                    # Mettre Ã  jour les infos si le pratiquant existe déjÃ 
                    practitioner.first_name = request.POST.get('first_name', request.user.first_name or '')
                    practitioner.last_name = request.POST.get('last_name', request.user.last_name or '')
                    practitioner.email = request.POST.get('email', request.user.email)
                    practitioner.phone = request.POST.get('phone', '')
                    practitioner.is_coach = True
                    practitioner.save()
                
                # 2. Créer ou mettre Ã  jour le profil coach
                coach_profile, created = CoachProfile.objects.get_or_create(
                    practitioner=practitioner,
                    defaults={
                        'profile_type': request.POST.get('profile_type', 'traditional'),
                        'years_teaching': request.POST.get('years_teaching', 0),
                        'teaching_place_name': request.POST.get('teaching_place_name', ''),
                        'available_for_seminars': 'available_for_seminars' in request.POST,
                        'available_for_private_lessons': 'available_for_private_lessons' in request.POST,
                        'available_for_online_coaching': 'available_for_online_coaching' in request.POST
                    }
                )
                
                if not created:
                    # Mettre Ã  jour le profil s'il existe déjÃ 
                    coach_profile.profile_type = request.POST.get('profile_type', 'traditional')
                    coach_profile.years_teaching = request.POST.get('years_teaching', 0)
                    coach_profile.teaching_place_name = request.POST.get('teaching_place_name', '')
                    coach_profile.available_for_seminars = 'available_for_seminars' in request.POST
                    coach_profile.available_for_private_lessons = 'available_for_private_lessons' in request.POST
                    coach_profile.available_for_online_coaching = 'available_for_online_coaching' in request.POST
                    coach_profile.save()
                
                # 3. Gérer les disciplines (principale et secondaires)
                primary_discipline_id = request.POST.get('primary_discipline')
                secondary_discipline_ids = request.POST.getlist('secondary_disciplines')
                
                # Supprimer l'ID de la discipline principale des disciplines secondaires si présent
                if primary_discipline_id in secondary_discipline_ids:
                    secondary_discipline_ids.remove(primary_discipline_id)
                
                if primary_discipline_id:
                    try:
                        # Récupérer la discipline principale
                        primary_discipline = get_object_or_404(Discipline, id=primary_discipline_id)
                        
                        # Définir la discipline principale du pratiquant
                        practitioner.primary_discipline = primary_discipline
                        practitioner.save()
                        
                        # Créer ou mettre Ã  jour l'expertise pour la discipline principale
                        expertise, created = DisciplineExpertise.objects.get_or_create(
                            coach_profile=coach_profile,
                            discipline=primary_discipline,
                            defaults={
                                'is_primary': True,
                                'level': 'advanced',
                                'years_experience': request.POST.get('years_teaching', 0),
                                'years_teaching': request.POST.get('years_teaching', 0),
                                'current_grade': request.POST.get('current_grade', ''),
                                'teaching_certification': request.POST.get('teaching_certification', '')
                            }
                        )
                        
                        if not created:
                            expertise.is_primary = True
                            expertise.years_experience = request.POST.get('years_teaching', 0)
                            expertise.years_teaching = request.POST.get('years_teaching', 0)
                            expertise.current_grade = request.POST.get('current_grade', '')
                            expertise.teaching_certification = request.POST.get('teaching_certification', '')
                            expertise.save()
                        
                        # Gérer les disciplines secondaires
                        if secondary_discipline_ids:
                            # Niveau d'expertise commun pour toutes les disciplines secondaires
                            for discipline_id in secondary_discipline_ids:
                                try:
                                    secondary_discipline = get_object_or_404(Discipline, id=discipline_id)
                                    
                                    # Vérifier si cette expertise existe déjÃ 
                                    sec_expertise, sec_created = DisciplineExpertise.objects.get_or_create(
                                        coach_profile=coach_profile,
                                        discipline=secondary_discipline,
                                        defaults={
                                            'is_primary': False,
                                            'level': 'intermediate',  # Niveau par défaut pour les disciplines secondaires
                                            'years_experience': request.POST.get('years_teaching', 0),
                                            'years_teaching': max(0, int(request.POST.get('years_teaching', 0)) - 1),  # Un peu moins d'expérience
                                        }
                                    )
                                    
                                    if not sec_created:
                                        sec_expertise.is_primary = False  # S'assurer que ce n'est pas marqué comme principal
                                        sec_expertise.save()
                                        
                                except (Discipline.DoesNotExist, ValueError):
                                    logger.warning(f"Discipline secondaire invalide: {discipline_id}")
                            
                            # Supprimer les expertises qui ne sont plus dans les disciplines secondaires
                            # (sauf la discipline principale)
                            DisciplineExpertise.objects.filter(
                                coach_profile=coach_profile,
                                is_primary=False
                            ).exclude(
                                discipline__id__in=secondary_discipline_ids
                            ).delete()
                    
                    except Discipline.DoesNotExist:
                        messages.warning(request, _("La discipline sélectionnée est invalide."))
                
                # 4. Marquer l'onboarding comme terminé
                profile.role = 'coach'
                profile.onboarding_step = 'final_setup'
                profile.onboarding_completed = True
                profile.save()
                
                messages.success(request, _("Votre profil coach a été créé avec succès !"))
                return redirect('competitions:dashboard:index')
        
        except Exception as e:
            logger.error(f"Erreur lors de la création du profil coach simplifié: {str(e)}")
            messages.error(request, _("Une erreur est survenue lors de la création de votre profil coach."))
    
    # Si la méthode est GET, afficher le formulaire
    context = {
        'disciplines': get_organization_queryset(Discipline, self.request.user).order_by('name'),
        'clubs': get_organization_queryset(Club, self.request.user).order_by('name'),
        'federations': get_organization_queryset(Federation, self.request.user).order_by('name'),
        'profile_types': CoachProfile.PROFILE_TYPES,
        'expertise_levels': DisciplineExpertise.EXPERTISE_LEVELS,
        'step': 'coach_simplified',
        'current_step': 'coach_simplified'
    }
    
    return render(request, 'competitions/onboarding/coach_simplified.html', context)
