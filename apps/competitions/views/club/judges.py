# competitions/views/club/judges.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from ...models import Club, Judge, JudgeCompetitionAssignment, CompetitionCategory, CompetitionRegistration
from apps.organizations.models import Organization
from ...utils.decorators import club_required

# Importations pour les permissions
# Correction: utiliser le nom correct du décorateur disponible dans le module
from apps.permissions_manager.decorators import permission_required
from apps.permissions_manager.auth import user_has_permission

# Import d'utilitaires pour le club
from .utils import get_user_club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def judges_list(request):
    """Liste des juges et arbitres du club."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
        
    # Vérification simplifiée: l'utilisateur doit Ãªtre le propriétaire du club ou un administrateur
    is_authorized = (club.owner == request.user) or \
                   (hasattr(request.user, 'is_staff') and request.user.is_staff)

    # Si l'utilisateur n'est pas autorisé, vérifier s'il est administrateur du club
    if not is_authorized and hasattr(request.user, 'club_admin_roles'):
        is_authorized = request.user.club_admin_roles.filter(club=club).exists()

    # Vérifier aussi via OrganizationMember (manager ou admin)
    if not is_authorized and club.organization:
        from apps.organizations.models import OrganizationMember
        is_authorized = OrganizationMember.objects.filter(
            user=request.user,
            organization=club.organization,
            role__in=['manager', 'admin', 'owner'],
            is_active=True
        ).exists()
        
    if not is_authorized:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour gérer les juges."))
        return redirect('competitions:dashboard:index')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        judges = Judge.objects.none()
    else:
        # Récupérer les pratiquants qui ont des qualifications de juge
        judges = Judge.objects.filter(
            practitioner__organization=club_organization
        ).select_related('practitioner').prefetch_related('practitioner__qualifications')
    
    context = {
        'club': club,
        'judges': judges,
        'current_section': 'judges',
    }
    
    return render(request, 'competitions/club/judges_list.html', context)

@login_required
def judge_assignments(request):
    """
    Affiche et gère les affectations des juges du club aux compétitions.
    Cette vue permet de voir toutes les affectations actuelles et futures.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
        
    # Vérification simplifiée: l'utilisateur doit Ãªtre le propriétaire du club ou un administrateur
    is_authorized = (club.owner == request.user) or \
                   (hasattr(request.user, 'is_staff') and request.user.is_staff)

    # Si l'utilisateur n'est pas autorisé, vérifier s'il est administrateur du club
    if not is_authorized and hasattr(request.user, 'club_admin_roles'):
        is_authorized = request.user.club_admin_roles.filter(club=club).exists()

    # Vérifier aussi via OrganizationMember (manager ou admin)
    if not is_authorized and club.organization:
        from apps.organizations.models import OrganizationMember
        is_authorized = OrganizationMember.objects.filter(
            user=request.user,
            organization=club.organization,
            role__in=['manager', 'admin', 'owner'],
            is_active=True
        ).exists()
        
    if not is_authorized:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour gérer les juges."))
        return redirect('competitions:dashboard:index')
    
    # Date actuelle
    now = timezone.now().date()
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        club_judges = Judge.objects.none()
        assignments = JudgeCompetitionAssignment.objects.none()
    else:
        # Récupérer les juges du club
        club_judges = Judge.objects.filter(
            practitioner__organization=club_organization
        ).select_related('practitioner')
        
        # Récupérer les affectations de juges
        assignments = JudgeCompetitionAssignment.objects.filter(
            registration__practitioner__organization=club_organization,
            category__competition__end_date__gte=now
        ).select_related(
            'registration', 
            'registration__practitioner',
            'category', 
            'category__competition'
        ).order_by(
            'category__competition__start_date',
            'category__name'
        )
    
    # Regrouper les affectations par compétition
    competitions_assignments = {}
    
    for assignment in assignments:
        competition = assignment.category.competition
        competition_id = competition.id
        
        if competition_id not in competitions_assignments:
            competitions_assignments[competition_id] = {
                'competition': competition,
                'judges': {},
                'total_assignments': 0
            }
        
        judge_id = assignment.registration.practitioner.id
        if judge_id not in competitions_assignments[competition_id]['judges']:
            competitions_assignments[competition_id]['judges'][judge_id] = {
                'judge': assignment.registration.practitioner,
                'assignments': []
            }
        
        competitions_assignments[competition_id]['judges'][judge_id]['assignments'].append(assignment)
        competitions_assignments[competition_id]['total_assignments'] += 1
    
    context = {
        'club': club,
        'club_judges': club_judges,
        'competitions_assignments': competitions_assignments,
        'current_section': 'judges',
    }
    
    return render(request, 'competitions/club/judge_assignments.html', context)

@login_required
def judge_add(request):
    """
    Ajoute un juge ou arbitre (vue simplifiée pour démonstration).
    Dans une implémentation réelle, cette vue utiliserait un formulaire.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
        
    # Vérification simplifiée: l'utilisateur doit Ãªtre le propriétaire du club ou un administrateur
    is_authorized = (club.owner == request.user) or \
                   (hasattr(request.user, 'is_staff') and request.user.is_staff)

    # Si l'utilisateur n'est pas autorisé, vérifier s'il est administrateur du club
    if not is_authorized and hasattr(request.user, 'club_admin_roles'):
        is_authorized = request.user.club_admin_roles.filter(club=club).exists()

    # Vérifier aussi via OrganizationMember (manager ou admin)
    if not is_authorized and club.organization:
        from apps.organizations.models import OrganizationMember
        is_authorized = OrganizationMember.objects.filter(
            user=request.user,
            organization=club.organization,
            role__in=['manager', 'admin', 'owner'],
            is_active=True
        ).exists()
        
    if not is_authorized:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour gérer les juges."))
        return redirect('competitions:dashboard:index')
    
    # Placeholder - Ã  remplacer par la vraie logique d'ajout
    messages.info(request, _("Fonctionnalité d'ajout de juge Ã  implémenter."))
    return redirect('competitions:club:judges_list')

