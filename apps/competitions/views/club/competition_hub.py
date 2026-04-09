"""
Hub de gestion de compétition - Vue centralisée
Interface organisée en cartes pour toutes les fonctionnalités de gestion
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q

from ...models import Competition, CompetitionRegistration, CompetitionCategory, Federation
from ...utils.permission_helpers import get_user_club
import logging

logger = logging.getLogger(__name__)


def get_user_federation(request):
    """Récupère la fédération associée à l'utilisateur courant."""
    try:
        # Chercher si l'utilisateur est owner d'une fédération
        federation = Federation.objects.filter(owner=request.user).first()
        if federation:
            return federation

        # Chercher si l'utilisateur est admin d'une fédération
        from ...models import FederationAdministrator
        admin = FederationAdministrator.objects.filter(user=request.user).first()
        if admin:
            return admin.federation
    except Exception as e:
        logger.warning(f"Erreur recherche fédération: {e}")

    return None


@login_required
def competition_management_hub(request, competition_id):
    """
    Hub centralisé de gestion d'une compétition
    Affiche toutes les fonctionnalités organisées en cartes par catégories
    Accessible aux responsables de club ET aux administrateurs de fédération
    """
    from django.db import connection
    from django.http import Http404

    # Récupérer la compétition d'abord
    competition = None
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, title, start_date, end_date, status, organizing_organization_id, discipline_id
            FROM competitions_competition
            WHERE id = %s
        """, [competition_id])
        row = cursor.fetchone()
        if row:
            try:
                competition = Competition.objects.raw(
                    'SELECT * FROM competitions_competition WHERE id = %s',
                    [competition_id]
                )[0]
            except:
                raise Http404("Competition not found")
        else:
            raise Http404("Competition not found")

    # Vérifier les permissions - plusieurs cas possibles
    has_permission = False
    redirect_url = 'competitions:dashboard:dashboard'
    club = None  # Initialiser à None pour éviter UnboundLocalError
    federation = None  # Initialiser aussi la fédération

    # Admin système a toujours accès
    if request.user.is_staff or request.user.is_superuser:
        has_permission = True

    # Vérifier via le club
    if not has_permission:
        club = get_user_club(request)
        if club:
            redirect_url = 'competitions:dashboard:club'
            organization = getattr(club, 'organization', None) or club
            if competition.organizing_organization and competition.organizing_organization == organization:
                has_permission = True

    # Vérifier via la fédération
    if not has_permission:
        federation = get_user_federation(request)
        if federation:
            redirect_url = 'competitions:dashboard:federation'
            # L'admin de fédération peut gérer les compétitions de son organisation
            if federation.organization and competition.organizing_organization == federation.organization:
                has_permission = True
            # Ou les compétitions de sa discipline
            elif competition.discipline:
                federation_disciplines = federation.disciplines.all()
                if federation_disciplines.filter(id=competition.discipline_id).exists():
                    has_permission = True

    if not has_permission:
        messages.error(request, _("Vous n'avez pas les permissions pour gérer cette compétition."))
        return redirect(redirect_url)
    
    # Statistiques de base - utiliser SQL brut
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM competitions_competitionregistration 
            WHERE competition_id = %s
        """, [competition.id])
        total_registrations = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM competitions_competitionregistration 
            WHERE competition_id = %s AND status = 'confirmed'
        """, [competition.id])
        confirmed_registrations = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM competitions_competitioncategory 
            WHERE competition_id = %s
        """, [competition.id])
        total_categories = cursor.fetchone()[0]
    
    # Statut de la compétition
    is_published = competition.status == 'published'
    is_ongoing = competition.status == 'ongoing'
    is_completed = competition.status == 'completed'
    
    # Récupérer les catégories
    categories = CompetitionCategory.objects.filter(competition=competition)
    
    # Statistiques de scoring par catégorie
    scoring_stats = {}
    try:
        from ...models.technical_scoring import TechnicalPerformance
        
        for category in categories:
            performances = TechnicalPerformance.objects.filter(category=category)
            total = performances.count()
            completed = performances.filter(status='completed').count()
            pending = performances.filter(status__in=['pending', 'in_progress']).count()
            
            scoring_stats[category.id] = {
                'total_performances': total,
                'completed_performances': completed,
                'pending_performances': pending,
                'progress_percent': int((completed / total * 100)) if total > 0 else 0
            }
    except Exception as e:
        logger.error(f"Erreur scoring stats: {str(e)}")
        scoring_stats = {}
    
    # Statistiques de combat pour cette compétition
    combat_stats = {
        'total_combats': 0,
        'en_cours': 0,
        'termines': 0,
        'planifies': 0,
    }
    active_combats = []
    taekwondo_combats = []
    poules = []
    
    try:
        from ...models.combat import Combat, Poule
        
        combats = Combat.objects.filter(competition=competition)
        
        active_combats = combats.filter(status='en_cours').select_related(
            'pratiquant_rouge', 'pratiquant_blanc', 'equipe_rouge', 'equipe_blanc', 'poule', 'configuration'
        ).order_by('-updated_at')[:10]
        
        taekwondo_combats = combats.filter(
            configuration__system='taekwondo',
            status='en_cours'
        ).select_related(
            'pratiquant_rouge', 'pratiquant_blanc', 'equipe_rouge', 'equipe_blanc', 'poule', 'configuration'
        ).order_by('-updated_at')[:5]
        
        # Récupérer les poules de la compétition
        poules = Poule.objects.filter(competition=competition).order_by('numero')
        
        combat_stats = {
            'total_combats': combats.count(),
            'en_cours': combats.filter(status='en_cours').count(),
            'termines': combats.filter(status='termine').count(),
            'planifies': combats.filter(status='planifie').count(),
        }
    except Exception as e:
        logger.error(f"Erreur combat stats: {str(e)}")
        active_combats = []
        taekwondo_combats = []
        poules = []
    
    # Enrichir stats existantes avec scoring et juges
    try:
        from ...models import JudgeAssignment
        
        stats = {
            'total_registrations': total_registrations,
            'confirmed_registrations': confirmed_registrations,
            'total_categories': total_categories,
            'scoring_total_performances': sum(s['total_performances'] for s in scoring_stats.values()),
            'judges_count': JudgeAssignment.objects.filter(
                category__competition=competition
            ).values('user').distinct().count(),
        }
    except Exception as e:
        logger.error(f"Erreur enrichissement stats: {str(e)}")
        stats = {
            'total_registrations': total_registrations,
            'confirmed_registrations': confirmed_registrations,
            'total_categories': total_categories,
            'scoring_total_performances': 0,
            'judges_count': 0,
        }
    
    context = {
        'competition': competition,
        'club': club,
        'stats': stats,
        'is_published': is_published,
        'is_ongoing': is_ongoing,
        'is_completed': is_completed,
        # Données pour les templates partiels
        'categories': categories,
        'scoring_stats': scoring_stats,
        'combat_stats': combat_stats,
        'active_combats': active_combats,
        'taekwondo_combats': taekwondo_combats,
        'poules': poules,
    }
    
    return render(request, 'competitions/club/competition_hub.html', context)
