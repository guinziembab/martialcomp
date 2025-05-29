from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

from ...models import UserProfile, Competition, JudgeCompetitionAssignment, CompetitionRegistration

@login_required
def referee_dashboard(request):
    """Dashboard pour les juges/arbitres."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role not in ['referee', 'judge']:
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard')
        
        # Récupérer la date d'aujourd'hui
        today = timezone.now().date()
        
        # Récupérer les compétitions où le juge est impliqué
        # 1. Via les inscriptions directes
        registrations = CompetitionRegistration.objects.filter(
            practitioner__user=request.user
        ).filter(
            Q(is_technical_judge=True) | Q(is_combat_referee=True)
        ).select_related('competition')
        
        registered_competitions = [reg.competition for reg in registrations]
        
        # 2. Via les affectations spécifiques (si le modèle existe)
        judge_assignments = []
        assigned_competitions = []
        
        try:
            judge_assignments = JudgeCompetitionAssignment.objects.filter(
                registration__practitioner__user=request.user
            ).select_related('category__competition')
            
            assigned_competitions = [
                assignment.category.competition for assignment in judge_assignments
            ]
        except Exception as e:
            # Si le modèle n'existe pas encore ou autre erreur, ignorer cette partie
            print(f"Erreur lors de la récupération des affectations: {str(e)}")
            pass
        
        # 3. Ne plus essayer de récupérer les compétitions par la relation judges qui n'existe pas
        direct_competitions = Competition.objects.none()  # QuerySet vide
        
        # Fusionner toutes les compétitions
        all_competitions = list(set(registered_competitions + assigned_competitions + list(direct_competitions)))
        
        # Séparer en compétitions à venir et passées
        upcoming_competitions = [comp for comp in all_competitions if comp.end_date >= today]
        past_competitions = [comp for comp in all_competitions if comp.end_date < today]
        
        # Récupérer les compétitions disponibles pour inscription
        competition_ids = [comp.id for comp in all_competitions]
        available_competitions = Competition.objects.filter(
            start_date__gte=today,
            status__in=['published', 'open']
        ).exclude(
            id__in=competition_ids if competition_ids else [-1]  # Utiliser [-1] si la liste est vide
        ).order_by('start_date')[:5]  # Limiter à 5 compétitions pour l'affichage
        
        # Le reste du code reste inchangé...
        stats = {
            'upcoming_assignments': len(upcoming_competitions),
            'completed_assignments': len(past_competitions),
            'qualification_level': 'N/A',
            'experience_years': 0
        }
        
        # Récupérer le niveau de qualification si possible
        if hasattr(profile, 'qualification_level'):
            stats['qualification_level'] = profile.qualification_level
        
        # Récupérer les années d'expérience si possible
        if hasattr(profile, 'years_experience'):
            stats['experience_years'] = profile.years_experience
        
        # Vérifier si l'utilisateur a un pratiquant associé
        try:
            from ...models import Practitioner, Judge
            practitioner = Practitioner.objects.get(user=request.user)
            
            # Essayer de récupérer les informations du juge
            try:
                judge = Judge.objects.get(practitioner=practitioner)
                if judge.qualification_level:
                    stats['qualification_level'] = judge.get_qualification_level_display()
                if judge.years_experience:
                    stats['experience_years'] = judge.years_experience
            except (Judge.DoesNotExist, AttributeError):
                pass
                
        except (ImportError, Practitioner.DoesNotExist):
            # Si le pratiquant n'existe pas, continuer sans ces informations
            pass
        
        context = {
            'stats': stats,
            'upcoming_competitions': upcoming_competitions,
            'past_competitions': past_competitions,
            'available_competitions': available_competitions,
            'today': today
        }
        
        return render(request, 'competitions/dashboard/referee.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')