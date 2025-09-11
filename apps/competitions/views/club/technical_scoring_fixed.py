# competitions/views/club/technical_scoring_fixed.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
import logging

from ...models import (
    Club, Competition, TechnicalPerformance, ScoringCriterion, 
    Score, Judge, Practitioner
)
from ...utils.decorators import club_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
@club_required
def technical_scoring_fixed(request):
    """
    Vue principale pour la notation technique des compétitions (version corrigée).
    """
    club = request.club
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
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
        try:
            active_competitions = Competition.objects.filter(
                Q(end_date__gte=now),
                Q(registrations__practitioner__organization=club_organization) | Q(organizing_organization=club_organization),
                status__in=['published', 'ongoing']
            ).distinct().order_by('start_date')
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des compétitions: {str(e)}")
            active_competitions = Competition.objects.none()
    
    # Récupérer les juges techniques du club
    try:
        judges = Judge.objects.filter(
            practitioner__club=club,
            is_technical_judge=True
        ).select_related('practitioner')
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des juges: {str(e)}")
        judges = Judge.objects.none()
    
    # Récupérer les performances techniques récentes avec gestion d'erreur améliorée
    recent_performances = TechnicalPerformance.objects.none()
    
    try:
        # Méthode sÃ»re : récupérer d'abord les IDs des pratiquants valides
        practitioner_ids = Practitioner.objects.filter(club=club).values_list('id', flat=True)
        
        # Construire la requÃªte de performances en plusieurs étapes
        performance_query = TechnicalPerformance.objects.filter(
            practitioner_id__in=practitioner_ids
        )
        
        # Ajouter le filtre de date
        performance_query = performance_query.filter(
            competition__end_date__gte=now - timezone.timedelta(days=30)
        )
        
        # Ajouter les relations et l'ordre
        recent_performances = performance_query.select_related(
            'practitioner', 'category', 'competition'
        ).order_by('-created_at')[:10]
        
        # Vérifier chaque performance pour s'assurer qu'elle a un practitioner valide
        valid_performances = []
        for performance in recent_performances:
            try:
                if performance.practitioner and isinstance(performance.practitioner, Practitioner):
                    valid_performances.append(performance)
                else:
                    logger.warning(f"Performance {performance.id} a un practitioner invalide")
            except Exception as e:
                logger.error(f"Erreur avec la performance {performance.id}: {str(e)}")
        
        recent_performances = valid_performances
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des performances: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors de la récupération des performances."))
        recent_performances = []
    
    # Si on a toujours une erreur avec club_organization, essayer une approche alternative
    if club_organization and recent_performances.__class__.__name__ == 'QuerySet':
        try:
            # Ajouter les performances liées Ã  l'organisation du club
            org_performances = TechnicalPerformance.objects.filter(
                competition__organizing_organization=club_organization,
                competition__end_date__gte=now - timezone.timedelta(days=30)
            ).select_related('practitioner', 'category', 'competition').order_by('-created_at')[:10]
            
            # Combiner les résultats
            if org_performances.exists():
                combined_ids = set(p.id for p in recent_performances) | set(p.id for p in org_performances)
                recent_performances = TechnicalPerformance.objects.filter(
                    id__in=combined_ids
                ).select_related('practitioner', 'category', 'competition').order_by('-created_at')[:10]
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des performances de l'organisation: {str(e)}")
    
    context = {
        'club': club,
        'active_competitions': active_competitions,
        'judges': judges,
        'recent_performances': recent_performances if isinstance(recent_performances, list) else list(recent_performances),
        'current_section': 'technical_scoring',
    }
    
    return render(request, 'competitions/club/technical_scoring.html', context)
