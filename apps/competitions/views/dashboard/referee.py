from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q

from ...models import UserProfile, Competition, JudgeCompetitionAssignment, CompetitionRegistration
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# Import pour les juges ad-hoc
try:
    from ...models.adhoc_judges import AdHocJudge
except ImportError:
    AdHocJudge = None

@login_required
def referee_dashboard(request):
    """Dashboard pour les juges/arbitres."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Vérifier si l'utilisateur a accès au dashboard juge
        has_judge_access = False
        
        # 1. Vérifier si le rôle principal est judge/referee
        if profile.role in ['referee', 'judge']:
            has_judge_access = True
        
        # 2. Vérifier si c'est un pratiquant avec un profil juge
        elif profile.role == 'participant':
            from ...models import Practitioner, Judge

            # Vérifier d'abord s'il y a un profil Judge directement lié à l'utilisateur
            try:
                judge = Judge.objects.get(user=request.user)
                has_judge_access = True
            except Judge.DoesNotExist:
                # Sinon, vérifier via le profil pratiquant
                try:
                    practitioner = Practitioner.objects.get(user=request.user)
                    judge = Judge.objects.get(practitioner=practitioner)
                    has_judge_access = True
                except (Practitioner.DoesNotExist, Judge.DoesNotExist):
                    pass

        # 3. Vérifier si c'est un juge ad-hoc actif
        is_adhoc_judge = False
        adhoc_assignments = []
        if AdHocJudge is not None:
            try:
                from ...models import Practitioner
                practitioner = Practitioner.objects.get(user=request.user)
                adhoc_assignments = AdHocJudge.get_active_for_practitioner(practitioner)
                if adhoc_assignments.exists():
                    has_judge_access = True
                    is_adhoc_judge = True
            except (Practitioner.DoesNotExist, Exception):
                pass

        if not has_judge_access:
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
                
        except Practitioner.DoesNotExist:
            pass
        
        # Vérifier si l'utilisateur a un profil pratiquant
        has_practitioner_profile = False
        try:
            from ...models import Practitioner
            has_practitioner_profile = Practitioner.objects.filter(user=request.user).exists()
        except ImportError:
            pass
        
        # Ajouter les compétitions des assignations ad-hoc aux compétitions à venir
        adhoc_competitions = []
        if is_adhoc_judge and adhoc_assignments:
            for adhoc in adhoc_assignments:
                if adhoc.competition not in upcoming_competitions:
                    adhoc_competitions.append(adhoc.competition)

        context = {
            'upcoming_competitions': upcoming_competitions + adhoc_competitions,
            'past_competitions': past_competitions,
            'available_competitions': available_competitions,
            'stats': stats,
            'judge_assignments': judge_assignments,
            'has_practitioner_profile': has_practitioner_profile,
            # Informations sur les juges ad-hoc
            'is_adhoc_judge': is_adhoc_judge,
            'adhoc_assignments': adhoc_assignments if is_adhoc_judge else [],
        }

        return render(request, 'competitions/dashboard/referee.html', context)
        
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')
    except Exception as e:
        messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
        return redirect('welcome')
