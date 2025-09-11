from django.core.exceptions import PermissionDenied
# competitions/views/club/technical_scoring_hotfix.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import connection
import logging

from ...models import Competition
from ...utils.decorators import club_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
@club_required
def technical_scoring_hotfix(request):
    """
    Version hotfix qui évite complètement le problème BACH HAC
    """
    club = request.club
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard')
    
    # Date actuelle
    now = timezone.now().date()
    
    # Compétitions actives - requÃªte simple
    active_competitions = Competition.objects.filter(
        end_date__gte=now,
        status__in=['published', 'ongoing']
    ).order_by('start_date')[:10]
    
    # Utiliser des requÃªtes SQL brutes pour éviter les problèmes de type
    judges = []
    recent_performances = []
    
    try:
        with connection.cursor() as cursor:
            # Récupérer les juges
            cursor.execute("""
                SELECT 
                    j.id,
                    p.full_name,
                    p.id as practitioner_id
                FROM competitions_judge j
                INNER JOIN competitions_practitioner p ON j.practitioner_id = p.id
                WHERE p.club_id = %s 
                AND j.is_technical_judge = true
                ORDER BY p.full_name
            """, [club.id])
            
            judges_data = cursor.fetchall()
            
            # Récupérer les performances récentes
            cursor.execute("""
                SELECT 
                    tp.id,
                    p.full_name as practitioner_name,
                    cat.name as category_name,
                    comp.name as competition_name,
                    tp.created_at
                FROM competitions_technicalperformance tp
                INNER JOIN competitions_practitioner p ON tp.practitioner_id = p.id
                INNER JOIN competitions_competitioncategory cat ON tp.category_id = cat.id
                INNER JOIN competitions_competition comp ON tp.competition_id = comp.id
                WHERE p.club_id = %s
                AND comp.end_date >= %s
                ORDER BY tp.created_at DESC
                LIMIT 10
            """, [club.id, now - timezone.timedelta(days=30)])
            
            performances_data = cursor.fetchall()
            
            # Convertir les données en dictionnaires pour le template
            judges = [
                {
                    'id': row[0],
                    'practitioner_name': row[1],
                    'practitioner_id': row[2]
                }
                for row in judges_data
            ]
            
            recent_performances = [
                {
                    'id': row[0],
                    'practitioner_name': row[1],
                    'category_name': row[2],
                    'competition_name': row[3],
                    'created_at': row[4]
                }
                for row in performances_data
            ]
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données: {e}")
        messages.warning(request, _("Impossible de charger toutes les données."))
    
    context = {
        'club': club,
        'active_competitions': active_competitions,
        'judges': judges,
        'recent_performances': recent_performances,
        'current_section': 'technical_scoring',
        'is_hotfix': True,  # Indicateur pour le template
    }
    
    return render(request, 'competitions/club/technical_scoring_hotfix.html', context)
