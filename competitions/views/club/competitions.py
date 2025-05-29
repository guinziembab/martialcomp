# competitions/views/club/competitions.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count

from ...models import Club, Competition, CompetitionRegistration
from ...utils.decorators import club_required
from competitions.utils.permission_helpers import manual_permission_check



@login_required
@manual_permission_check('club.manage_competitions')
def club_competitions(request):
    """
    Affiche les compétitions auxquelles le club est inscrit ou qu'il organise.
    Cette vue centralise toutes les compétitions liées au club.
    """
    club = request.club
    if not club:
        club = Club.objects.filter(owner=request.user).first()
        
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Obtenir la date actuelle
    now = timezone.now().date()
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        upcoming_competitions = Competition.objects.none()
        past_competitions = Competition.objects.none()
    else:
        # Compétitions futures (à venir)
        upcoming_competitions = Competition.objects.filter(
            Q(registrations__practitioner__organization=club_organization) | Q(organizing_organization=club_organization),
            end_date__gte=now
        ).distinct().order_by('start_date')
        
        # Compétitions passées
        past_competitions = Competition.objects.filter(
            Q(registrations__practitioner__organization=club_organization) | Q(organizing_organization=club_organization),
            end_date__lt=now
        ).distinct().order_by('-start_date')
    
    # Nombre de participants par compétition
    competition_stats = {}
    for comp in list(upcoming_competitions) + list(past_competitions):
        if not club_organization:
            participants_count = 0
        else:
            participants_count = CompetitionRegistration.objects.filter(
                competition=comp,
                practitioner__organization=club_organization,
                is_competitor=True
            ).count()
        
        competition_stats[comp.id] = {
            'participants_count': participants_count
        }
    
    context = {
        'club': club,
        'upcoming_competitions': upcoming_competitions,
        'past_competitions': past_competitions,
        'competition_stats': competition_stats,
        'current_section': 'competitions',  # Pour marquer l'élément actif dans le menu
    }
    
    return render(request, 'competitions/club/competitions.html', context)

@login_required
@manual_permission_check('club.manage_competitions')
def club_competition_detail(request, competition_id):
    """
    Affiche les détails d'une compétition spécifique pour le club,
    y compris les pratiquants inscrits et leurs catégories.
    """
    club = request.club
    if not club:
        club = Club.objects.filter(owner=request.user).first()
        
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Récupérer la compétition
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        registrations = CompetitionRegistration.objects.none()
    else:
        # Récupérer les inscriptions des membres du club
        registrations = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner__organization=club_organization
        ).select_related('practitioner')
    
    context = {
        'club': club,
        'competition': competition,
        'registrations': registrations,
        'current_section': 'competitions',
    }
    
    return render(request, 'competitions/club/competition_detail.html', context)