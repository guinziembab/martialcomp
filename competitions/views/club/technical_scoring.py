# competitions/views/club/technical_scoring.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from ...models import (
    Club, Competition, TechnicalPerformance, ScoringCriterion, 
    Score, Judge, Practitioner
)
from ...utils.decorators import club_required

@login_required
@club_required
def technical_scoring(request):
    """
    Vue principale pour la notation technique des compétitions.
    Affiche les compétitions disponibles pour la notation et les performances.
    """
    club = request.club
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Date actuelle
    now = timezone.now().date()
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        active_competitions = Competition.objects.none()
    else:
        # Récupérer les compétitions actives avec performances techniques
        active_competitions = Competition.objects.filter(
            Q(end_date__gte=now),
            Q(registrations__practitioner__organization=club_organization) | Q(organizing_organization=club_organization),
            status__in=['published', 'ongoing']
        ).distinct().order_by('start_date')
    
    # Récupérer les juges techniques du club
    judges = Judge.objects.filter(
        practitioner__club=club,
        is_technical_judge=True
    ).select_related('practitioner')
    
    # Récupérer les performances techniques récentes avec gestion d'erreur améliorée
    recent_performances = TechnicalPerformance.objects.none()
    
    try:
        # Méthode sûre : récupérer d'abord les IDs des pratiquants valides
        practitioner_ids = Practitioner.objects.filter(club=club).values_list('id', flat=True)
        
        # Construire la requête de performances de façon sécurisée
        recent_performances = TechnicalPerformance.objects.filter(
            practitioner_id__in=practitioner_ids,
            competition__end_date__gte=now - timezone.timedelta(days=30)
        ).select_related('practitioner', 'category', 'competition').order_by('-created_at')[:10]
        
        # Ajouter les performances liées à l'organisation si disponible
        if club_organization:
            try:
                org_performances = TechnicalPerformance.objects.filter(
                    competition__organizing_organization=club_organization,
                    competition__end_date__gte=now - timezone.timedelta(days=30)
                ).exclude(id__in=recent_performances.values_list('id', flat=True))
                
                # Combiner les résultats
                if org_performances.exists():
                    combined_ids = list(recent_performances.values_list('id', flat=True)) + list(org_performances.values_list('id', flat=True))
                    recent_performances = TechnicalPerformance.objects.filter(
                        id__in=combined_ids
                    ).select_related('practitioner', 'category', 'competition').order_by('-created_at')[:10]
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erreur lors de l'ajout des performances de l'organisation: {str(e)}")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la récupération des performances: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors de la récupération des performances."))
        recent_performances = TechnicalPerformance.objects.none()
    
    context = {
        'club': club,
        'active_competitions': active_competitions,
        'judges': judges,
        'recent_performances': recent_performances,
        'current_section': 'technical_scoring',
    }
    
    return render(request, 'competitions/club/technical_scoring.html', context)

@login_required
@club_required
def competition_scoring(request, competition_id):
    """
    Affiche les détails de notation pour une compétition spécifique.
    """
    club = request.club
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Récupérer la compétition
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Récupérer les catégories avec critères de notation
    categories = competition.categories.filter(
        scoring_criteria__isnull=False
    ).distinct().prefetch_related('scoring_criteria')
    
    # Récupérer les performances des pratiquants du club
    performances = TechnicalPerformance.objects.filter(
        competition=competition,
        practitioner__club=club
    ).select_related('practitioner', 'category')
    
    context = {
        'club': club,
        'competition': competition,
        'categories': categories,
        'performances': performances,
    }
    
    return render(request, 'competitions/club/competition_scoring.html', context)

@login_required
@club_required
def performance_detail(request, performance_id):
    """
    Affiche les détails d'une performance spécifique, y compris les notes.
    """
    club = request.club
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Récupérer la performance
    performance = get_object_or_404(TechnicalPerformance, id=performance_id)
    
    # Vérifier les permissions
    # S'assurer que club_organization est correctement obtenu
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    # Vérification de la club_organization avant de continuer
    if not club_organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:club:technical_scoring')
    
    # Vérification des droits avec l'objet club_organization au lieu d'une comparaison directe avec club
    if performance.practitioner.club != club and performance.competition.organizing_organization != club_organization:
        messages.error(request, _("Vous n'avez pas accès à cette performance."))
        return redirect('competitions:club:technical_scoring')
    
    # Récupérer les scores
    scores = Score.objects.filter(
        performance=performance
    ).select_related('judge', 'criterion')
    
    # Organiser les scores par juge et critère
    scores_by_judge = {}
    for score in scores:
        judge_id = score.judge.id
        if judge_id not in scores_by_judge:
            scores_by_judge[judge_id] = {
                'judge': score.judge,
                'scores': {}
            }
        scores_by_judge[judge_id]['scores'][score.criterion.id] = score
    
    context = {
        'club': club,
        'performance': performance,
        'scores_by_judge': scores_by_judge,
        'criteria': ScoringCriterion.objects.filter(category=performance.category).order_by('order'),
    }
    
    return render(request, 'competitions/club/performance_detail.html', context)