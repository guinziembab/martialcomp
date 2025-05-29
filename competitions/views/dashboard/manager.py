from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from datetime import date, timedelta
from django.urls import reverse

from ...models import (
    UserProfile, Competition, CompetitionRegistration, 
    CompetitionCategory, Match, Practitioner, Club, CompetitionRole
)


@login_required
def manager_dashboard(request):
    """Dashboard pour les gestionnaires d'événements."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        
        # Vérifications des permissions
        if profile.role not in ['event_manager', 'club_manager', 'federation_admin', 'judge']:
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('dashboard:index')
        
        # Récupérer les compétitions selon le rôle de l'utilisateur
        if profile.role == 'club_manager':
            # Les compétitions organisées par le club de l'utilisateur
            club = Club.objects.filter(owner=request.user).first()
            if club:
                # Vérifier si le club a une organisation associée
                club_organization = club.organization or getattr(club, 'as_organization', None)
                
                if not club_organization:
                    messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
                    managed_competitions = Competition.objects.none()
                else:
                    managed_competitions = Competition.objects.filter(
                        organizing_organization=club_organization
                    ).select_related('discipline', 'organizing_organization').prefetch_related('categories', 'registrations')
            else:
                managed_competitions = Competition.objects.none()
        else:
            # Pour les autres rôles, récupérer toutes les compétitions ou une sélection
            managed_competitions = Competition.objects.all().select_related('discipline', 'organizing_organization').prefetch_related('categories', 'registrations')
        
        # Compétitions actives
        active_competitions = managed_competitions.filter(
            status__in=['published', 'ongoing']
        ).order_by('start_date')
        
        # Statistiques générales
        today = date.today()
        upcoming_competitions = managed_competitions.filter(
            start_date__gt=today
        ).count()
        
        completed_competitions = managed_competitions.filter(
            status='completed'
        ).count()
        
        # Inscriptions récentes (7 derniers jours)
        recent_registrations = CompetitionRegistration.objects.filter(
            competition__in=managed_competitions,
            registration_date__gte=today - timedelta(days=7)
        ).select_related('practitioner', 'competition').order_by('-registration_date')[:5]
        
        # Statistiques détaillées pour chaque compétition active
        active_competitions_stats = []
        for competition in active_competitions:
            stats = {
                'competition': competition,
                'total_registrations': competition.registrations.count(),
                'pending_registrations': competition.registrations.filter(status='pending').count(),
                'categories_count': competition.categories.count(),
                'days_until_start': (competition.start_date - today).days if competition.start_date > today else 0,
            }
            active_competitions_stats.append(stats)
        
        # Tâches urgentes pour le gestionnaire
        urgent_tasks = []
        
        # 1. Inscriptions en attente de validation
        pending_registrations = CompetitionRegistration.objects.filter(
            competition__in=managed_competitions,
            status='pending'
        ).select_related('competition')
        
        pending_registrations_count = pending_registrations.count()
        
        if pending_registrations_count > 0:
            # Obtenir la première compétition avec des inscriptions en attente
            first_pending = pending_registrations.first()
            if first_pending:
                competition_id = first_pending.competition.id
                urgent_tasks.append({
                    'task': f"{pending_registrations_count} inscriptions en attente de validation",
                    'url_complete': reverse('competitions:competitions:manage_registrations', args=[competition_id]),
                    'priority': 'high'
                })
        
        # 2. Compétitions sans catégories
        competitions_without_categories = managed_competitions.annotate(
            categories_count=Count('categories')
        ).filter(categories_count=0)
        
        competitions_without_categories_count = competitions_without_categories.count()
        
        if competitions_without_categories_count > 0:
            urgent_tasks.append({
                'task': f"{competitions_without_categories_count} compétitions sans catégories",
                'url_complete': reverse('competitions:competitions:list'),
                'priority': 'medium'
            })
        
        # 3. Compétitions démarrant dans les 7 prochains jours
        upcoming_soon_competitions = managed_competitions.filter(
            start_date__gte=today,
            start_date__lte=today + timedelta(days=7),
            status='published'
        )
        
        upcoming_soon_count = upcoming_soon_competitions.count()
        
        if upcoming_soon_count > 0:
            urgent_tasks.append({
                'task': f"{upcoming_soon_count} compétitions démarrent dans les 7 prochains jours",
                'url_complete': reverse('competitions:competitions:list'),
                'priority': 'high'
            })
        
        # Activités récentes
        recent_activities = []
        
        # Matches récemment créés (Note: Match n'a pas de created_at, donc on utilise date_match)
        recent_matches = Match.objects.filter(
            competition__in=managed_competitions,
            date_match__gte=today - timedelta(days=7)
        ).select_related('competition').order_by('-date_match', '-start_time')[:5]
        
        for match in recent_matches:
            recent_activities.append({
                'type': 'match_created',
                'description': f'Match programmé : {match.name} dans {match.competition.title}',
                'date': match.date_match,  # Utiliser date_match au lieu de created_at
                'url': reverse('competitions:competitions:detail', args=[match.competition.id])
            })
        
        # Nouvelles inscriptions
        for registration in recent_registrations:
            recent_activities.append({
                'type': 'registration',
                'description': f'Nouvelle inscription : {registration.practitioner.full_name} pour {registration.competition.title}',
                'date': registration.registration_date,
                'url': reverse('competitions:competitions:manage_registrations', args=[registration.competition.id])
            })
        
        # Trier les activités par date
        recent_activities.sort(key=lambda x: x['date'], reverse=True)
        recent_activities = recent_activities[:10]
        
        # Statuts de compétition pour le summary
        competition_statuses = {
            'draft': managed_competitions.filter(status='draft').count(),
            'published': managed_competitions.filter(status='published').count(),
            'ongoing': managed_competitions.filter(status='ongoing').count(),
            'completed': managed_competitions.filter(status='completed').count(),
            'cancelled': managed_competitions.filter(status='cancelled').count(),
        }
        
        # Get federation if applicable
        default_federation = None
        # Add debug logs
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"User role: {profile.role}")
        logger.info(f"Is federation admin: {profile.is_federation_admin}")
        
        # Temporarily force default_federation to None for testing
        default_federation = None
        logger.info("Forcing default_federation to None for testing")
        
        # Original code (commented out)
        # if profile.is_federation_admin:
        #     federations = request.user.get_administered_federations()
        #     logger.info(f"User administered federations: {federations.count() if federations else 'None'}")
        #     default_federation = federations.first() if federations.exists() else None
        #     logger.info(f"Default federation: {default_federation}")
        # else:
        #     logger.info("User is not a federation admin, default_federation will be None")
        
        context = {
            'profile': profile,
            'managed_competitions': managed_competitions,
            'active_competitions': active_competitions,
            'upcoming_competitions': upcoming_competitions,
            'completed_competitions': completed_competitions,
            'recent_registrations': recent_registrations,
            'active_competitions_stats': active_competitions_stats,
            'urgent_tasks': urgent_tasks,
            'recent_activities': recent_activities,
            'competition_statuses': competition_statuses,
            'total_managed_competitions': managed_competitions.count(),
            'default_federation': default_federation,
            'debug': True,  # Add debug flag to enable debug information in template
        }
        
        try:
            return render(request, 'competitions/dashboard/manager.html', context)
        except Exception as e:
            logger.error(f"Error rendering manager dashboard: {str(e)}")
            messages.error(request, _("Une erreur est survenue lors de l'affichage du tableau de bord. Veuillez contacter l'administrateur."))
            return redirect('welcome')
        
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')