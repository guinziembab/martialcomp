from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from competitions.models import Competition, CompetitionRegistration, Club
from competitions.models import Performance, TechnicalPerformance, CompetitionRanking
from competitions.utils.decorators import club_required

# Importation de notre helper de permission personnalisé
from competitions.utils.permission_helpers import manual_permission_check, get_user_club

@login_required
def competition_results(request):
    """Affiche les résultats des compétitions passées."""
    # Tous les utilisateurs connectés peuvent voir les résultats, pas besoin de vérification spéciale
    # Récupérer les compétitions terminées
    today = timezone.now().date()
    past_competitions = Competition.objects.filter(
        Q(end_date__lt=today) | Q(status='completed')
    ).order_by('-end_date')
    
    # Filtres optionnels
    discipline_id = request.GET.get('discipline')
    year = request.GET.get('year')
    
    if discipline_id:
        past_competitions = past_competitions.filter(discipline_id=discipline_id)
    
    if year:
        past_competitions = past_competitions.filter(end_date__year=year)
    
    # Contexte pour le template
    context = {
        'past_competitions': past_competitions,
        'selected_discipline': discipline_id,
        'selected_year': year,
        'years': range(today.year - 5, today.year + 1),  # 5 dernières années
        'page_title': _("Résultats des compétitions")
    }
    
    return render(request, 'competitions/results/competition_results.html', context)

@login_required
def competition_result_detail(request, competition_id):
    """Affiche les résultats détaillés d'une compétition spécifique."""
    # Tous les utilisateurs connectés peuvent voir les résultats détaillés
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Récupérer les différentes catégories de la compétition
    categories = competition.categories.all()
    
    # Si le modèle CompetitionRanking existe et est utilisé
    has_rankings = False
    try:
        # Vérifier s'il existe des classements pour cette compétition
        has_rankings = CompetitionRanking.objects.filter(competition=competition).exists()
    except:
        pass
    
    # Récupérer les performances techniques si disponibles
    performances = []
    try:
        performances = TechnicalPerformance.objects.filter(
            competition=competition,
            is_completed=True
        ).select_related('practitioner', 'category')
    except:
        # Si TechnicalPerformance n'existe pas ou n'est pas accessible
        try:
            performances = Performance.objects.filter(
                category__competition=competition,
                status='completed'
            ).select_related('practitioner', 'category')
        except:
            pass
    
    context = {
        'competition': competition,
        'categories': categories,
        'performances': performances,
        'has_rankings': has_rankings,
        'page_title': f"{_('Résultats')} - {competition.title}"
    }
    
    return render(request, 'competitions/results/result_detail.html', context)

@login_required
def club_competition_results(request):
    """Affiche les résultats des compétitions pour un club spécifique."""
    # Tous les utilisateurs associés à un club peuvent voir ses résultats
    # Récupérer le club de l'utilisateur en utilisant notre fonction helper
    club = get_user_club(request)
    
    if not club:
        return render(request, 'competitions/club/error.html', {
            'error_message': _("Vous n'êtes pas associé à un club.")
        })
    
    # Récupérer les compétitions terminées où le club a participé
    today = timezone.now().date()
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        club_registrations = []
    else:
        club_registrations = CompetitionRegistration.objects.filter(
            practitioner__organization=club_organization
        ).values_list('competition_id', flat=True).distinct()
    
    past_competitions = Competition.objects.filter(
        id__in=club_registrations,
        end_date__lt=today
    ).order_by('-end_date')
    
    context = {
        'club': club,
        'past_competitions': past_competitions,
        'page_title': _("Résultats du club")
    }
    
    return render(request, 'competitions/results/club_results.html', context)