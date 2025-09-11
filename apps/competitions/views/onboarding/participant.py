from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from ...forms.onboarding import ParticipantProfileForm
from apps.grades.models import Grade
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def handle_participant_profile(request):
    """Gestion du profil participant"""
    # Vérifier si l'utilisateur a un profil et le rÃ´le approprié
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'participant':
        messages.error(request, _("Accès non autorisé. Vous devez Ãªtre participant."))
        return redirect('competitions:onboarding:role_selection')
    
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
                
                # Mise Ã  jour de l'étape d'onboarding
                request.user.profile.onboarding_step = 'final_setup'
                request.user.profile.save()
                request.session['onboarding_step'] = 'final_setup'
                
                messages.success(request, _("Profil de participant créé avec succès!"))
                return redirect('competitions:onboarding:final_setup')
            except Exception as e:
                messages.error(request, _(f"Erreur lors de la création du profil: {str(e)}"))
                logger.error(f"Erreur lors de la création du profil participant: {str(e)}")
    else:
        # Initialiser le formulaire avec les données utilisateur existantes
        initial_data = {
            'email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
        
        # Si l'utilisateur a déjÃ  un profil pratiquant, pré-remplir le formulaire
        try:
            practitioner = request.user.practitioners.first()
            if practitioner:
                initial_data.update({
                    'birth_date': practitioner.birth_date,
                    'gender': practitioner.gender,
                    'nationality': practitioner.nationality,
                    'weight': practitioner.weight,
                    'height': practitioner.height,
                    'license_number': practitioner.license_number,
                    'medical_certificate_date': practitioner.medical_certificate_date,
                    'notes': practitioner.notes,
                    'club': practitioner.organization,
                    'main_discipline': practitioner.primary_discipline,
                    'grade': practitioner.grade_text,
                })
                
                # Pré-sélectionner les disciplines
                if practitioner.disciplines.exists():
                    initial_data['disciplines'] = practitioner.disciplines.all()
        except:
            pass  # Si pas de profil existant, continuer avec les données de base
        
        form = ParticipantProfileForm(initial=initial_data)
    
    # Récupérer les disciplines pour le template
    from apps.competitions.models import Discipline
    disciplines = Discipline.objects.filter(is_active=True)
    
    # Récupérer les grades par discipline pour le JavaScript
    grades_by_discipline = {}
    try:
        for discipline in disciplines:
            discipline_grades = Grade.objects.filter(
                discipline=discipline,
                is_active=True
            ).order_by('level', 'name')
            
            grades_by_discipline[str(discipline.id)] = [
                {
                    'id': grade.id,
                    'name': grade.name,
                    'category': getattr(grade, 'category', 'Général'),
                    'level': getattr(grade, 'level', 0)
                }
                for grade in discipline_grades
            ]
    except ImportError:
        # Si l'application grades n'est pas disponible
        pass
    
    return render(request, 'competitions/onboarding/participant_profile.html', {
        'form': form,
        'step': 'participant_profile',
        'current_step': 'participant_profile',
        'disciplines': disciplines,
        'grades_by_discipline': grades_by_discipline,
    })

