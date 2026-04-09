from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from apps.competitions.models import Competition, CompetitionRegistration, Club
from apps.competitions.models import Performance, TechnicalPerformance, CompetitionRanking
from apps.competitions.utils.decorators import club_required

# Importation de notre helper de permission personnalisé
from apps.competitions.utils.permission_helpers import manual_permission_check, get_user_club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def competition_results(request):
    """Affiche les résultats des compétitions passées."""
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

    context = {
        'past_competitions': past_competitions,
        'selected_discipline': discipline_id,
        'selected_year': year,
        'years': range(today.year - 5, today.year + 1),
        'page_title': _("Résultats des compétitions")
    }

    return render(request, 'competitions/results/competition_results.html', context)


@login_required
def competition_result_detail(request, competition_id):
    """Affiche les résultats détaillés d'une compétition spécifique."""
    competition = get_object_or_404(Competition, id=competition_id)

    categories = competition.categories.all()

    has_rankings = False
    try:
        has_rankings = CompetitionRanking.objects.filter(
            category__competition=competition
        ).exists()
    except Exception:
        pass

    performances = []
    try:
        performances = TechnicalPerformance.objects.filter(
            competition=competition,
            is_completed=True
        ).select_related('practitioner', 'category')
    except Exception:
        try:
            performances = Performance.objects.filter(
                category__competition=competition,
                status='completed'
            ).select_related('practitioner', 'category')
        except Exception:
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
    from apps.competitions.models import Discipline, Practitioner

    # Récupérer le club de l'utilisateur
    club = get_user_club(request)

    if not club:
        return render(request, 'competitions/club/error.html', {
            'error_message': _("Vous n'êtes pas associé à un club.")
        })

    today = timezone.now().date()

    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)

    # Récupérer les pratiquants du club
    club_practitioners = []
    if club_organization:
        club_practitioners = Practitioner.objects.filter(
            organization=club_organization
        ).order_by('last_name', 'first_name')

    # Récupérer les inscriptions du club
    # Note: 'categories' est un ManyToMany, on utilise prefetch_related
    club_registrations_qs = CompetitionRegistration.objects.none()
    if club_organization:
        club_registrations_qs = CompetitionRegistration.objects.filter(
            practitioner__organization=club_organization
        ).select_related('competition', 'practitioner').prefetch_related('categories')

    # IDs des compétitions auxquelles le club a participé
    competition_ids = club_registrations_qs.values_list('competition_id', flat=True).distinct()

    # Compétitions passées
    past_competitions = Competition.objects.filter(
        id__in=competition_ids
    ).filter(
        Q(end_date__lt=today) | Q(status='completed')
    ).select_related('discipline').order_by('-end_date')

    # Appliquer les filtres
    discipline_id = request.GET.get('discipline')
    year = request.GET.get('year')
    practitioner_id = request.GET.get('practitioner')

    if discipline_id:
        past_competitions = past_competitions.filter(discipline_id=discipline_id)
    if year:
        past_competitions = past_competitions.filter(end_date__year=year)

    # Construire les résultats détaillés par compétition
    competition_results = []
    total_gold = 0
    total_silver = 0
    total_bronze = 0
    total_participants = set()

    for competition in past_competitions:
        # Inscriptions pour cette compétition
        comp_registrations = club_registrations_qs.filter(competition=competition)

        if practitioner_id:
            comp_registrations = comp_registrations.filter(practitioner_id=practitioner_id)

        participants_count = comp_registrations.count()

        # Récupérer les classements pour les pratiquants du club
        results = []
        try:
            rankings = CompetitionRanking.objects.filter(
                category__competition=competition,
                practitioner__organization=club_organization
            ).select_related('practitioner', 'category')

            if practitioner_id:
                rankings = rankings.filter(practitioner_id=practitioner_id)

            for ranking in rankings:
                medal_value = getattr(ranking, 'medal', '') or ''
                results.append({
                    'practitioner': ranking.practitioner,
                    'category': ranking.category.name if ranking.category else 'N/A',
                    'position': ranking.rank,
                    'score': ranking.final_score,
                    'medal': medal_value,
                })

                # Compter les médailles (normaliser en minuscules)
                medal_lower = medal_value.lower() if medal_value else ''
                if medal_lower in ('gold', 'or'):
                    total_gold += 1
                elif medal_lower in ('silver', 'argent'):
                    total_silver += 1
                elif medal_lower in ('bronze',):
                    total_bronze += 1

                total_participants.add(ranking.practitioner_id)
        except Exception:
            # Si pas de classements, utiliser les inscriptions comme fallback
            for reg in comp_registrations:
                # categories est un ManyToMany, prendre les premières
                cat_names = ', '.join([c.name for c in reg.categories.all()[:3]]) or 'N/A'
                results.append({
                    'practitioner': reg.practitioner,
                    'category': cat_names,
                    'position': None,
                    'score': None,
                    'medal': None,
                })
                total_participants.add(reg.practitioner_id)

        if participants_count > 0 or results:
            competition_results.append({
                'competition': competition,
                'participants_count': participants_count,
                'results': results,
            })

    # Statistiques
    stats = {
        'total_competitions': len(competition_results),
        'total_medals': total_gold + total_silver + total_bronze,
        'gold_medals': total_gold,
        'silver_medals': total_silver,
        'bronze_medals': total_bronze,
        'participants': len(total_participants),
    }

    # Liste des disciplines pour le filtre
    disciplines = Discipline.objects.filter(
        competitions__id__in=competition_ids
    ).distinct().order_by('name')

    # Années disponibles
    years_list = past_competitions.dates('end_date', 'year', order='DESC')
    years = [d.year for d in years_list]

    context = {
        'club': club,
        'competition_results': competition_results,
        'stats': stats,
        'disciplines': disciplines,
        'years': years,
        'practitioners': club_practitioners,
        'page_title': _("Résultats du club")
    }

    return render(request, 'competitions/results/club_results.html', context)
