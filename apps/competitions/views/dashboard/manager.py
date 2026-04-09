from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import logging

logger = logging.getLogger(__name__)

@login_required
def manager_dashboard(request):
    """Vue pour le dashboard manager - Gestionnaire d'événements"""

    # Imports des modèles nécessaires
    from ...models import (
        Competition, CompetitionRegistration, Federation, Club,
        UserProfile
    )

    user = request.user
    profile = None

    # Récupérer le profil utilisateur
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        pass

    # Récupérer les compétitions gérées par l'utilisateur
    # Un manager gère les compétitions via son organisation
    managed_competitions = Competition.objects.none()

    # Méthode 1: Via OrganizationMember
    try:
        from apps.organizations.models import OrganizationMember
        user_orgs = OrganizationMember.objects.filter(user=user).values_list('organization_id', flat=True)
        if user_orgs:
            managed_competitions = Competition.objects.filter(
                organizing_organization_id__in=user_orgs
            )
    except Exception as e:
        logger.debug(f"Erreur OrganizationMember: {e}")

    # Méthode 2: Via Club owner ou Federation
    if not managed_competitions.exists():
        try:
            user_clubs = Club.objects.filter(owner=user).values_list('organization_id', flat=True)
            if user_clubs:
                managed_competitions = Competition.objects.filter(
                    organizing_organization_id__in=user_clubs
                )
        except Exception as e:
            logger.debug(f"Erreur Club: {e}")

    # Méthode 3: Via FederationAdministrator
    if not managed_competitions.exists():
        try:
            from ...models import FederationAdministrator
            fed_orgs = FederationAdministrator.objects.filter(user=user).values_list('federation__organization_id', flat=True)
            if fed_orgs:
                managed_competitions = Competition.objects.filter(
                    organizing_organization_id__in=fed_orgs
                )
        except Exception as e:
            logger.debug(f"Erreur FederationAdministrator: {e}")

    # Méthode 4: Si le manager est event_manager, récupérer toutes les compétitions accessibles
    if not managed_competitions.exists() and profile and profile.role == 'event_manager':
        # Récupérer toutes les compétitions (pour un event_manager sans organisation spécifique)
        managed_competitions = Competition.objects.all()

    total_managed_competitions = managed_competitions.count() if hasattr(managed_competitions, 'count') else len(managed_competitions)

    # Statistiques par statut des compétitions
    competition_statuses = {
        'draft': managed_competitions.filter(status='draft').count(),
        'published': managed_competitions.filter(status='published').count(),
        'ongoing': managed_competitions.filter(status='ongoing').count(),
        'completed': managed_competitions.filter(status='completed').count(),
        'cancelled': managed_competitions.filter(status='cancelled').count(),
    }

    # Compétitions actives (publiées ou en cours, avec date future ou en cours)
    today = timezone.now().date()
    active_competitions = managed_competitions.filter(
        Q(status='published') | Q(status='ongoing'),
        end_date__gte=today
    ).order_by('start_date')[:10]

    # Construire les statistiques pour les compétitions actives
    active_competitions_stats = []
    for comp in active_competitions:
        registrations = CompetitionRegistration.objects.filter(competition=comp)
        total_registrations = registrations.count()
        pending_registrations = registrations.filter(status='pending').count()

        days_until_start = (comp.start_date - today).days if comp.start_date else 0

        active_competitions_stats.append({
            'competition': comp,
            'total_registrations': total_registrations,
            'pending_registrations': pending_registrations,
            'days_until_start': days_until_start,
        })

    # Inscriptions récentes (toutes compétitions gérées)
    recent_registrations = CompetitionRegistration.objects.filter(
        competition__in=managed_competitions
    ).select_related('practitioner', 'competition').order_by('-registration_date')[:10]

    # Tâches urgentes - inscriptions en attente sur compétitions proches
    urgent_tasks = []
    upcoming_comps = managed_competitions.filter(
        status__in=['published', 'ongoing'],
        start_date__lte=today + timedelta(days=14),
        start_date__gte=today
    )

    for comp in upcoming_comps:
        pending = CompetitionRegistration.objects.filter(
            competition=comp,
            status='pending'
        ).count()
        if pending > 0:
            urgent_tasks.append({
                'task': f"{pending} inscription(s) en attente pour {comp.title}",
                'priority': 'warning' if pending < 5 else 'danger',
                'url_complete': f"/fr/competitions/management/{comp.id}/registrations/",
            })

    # Fédération par défaut (si le manager est lié à une fédération)
    default_federation = None
    try:
        from ...models import FederationAdministrator
        fed_admin = FederationAdministrator.objects.filter(user=user).first()
        if fed_admin:
            default_federation = fed_admin.federation
    except Exception as e:
        logger.debug(f"Pas de fédération pour le manager: {e}")

    # Club associé (si le manager est aussi lié à un club)
    club = None
    try:
        club = Club.objects.filter(owner=user).first()
        if not club and profile and hasattr(profile, 'club'):
            club = profile.club
        # Fallback: via OrganizationMember
        if not club:
            from apps.organizations.models import OrganizationMember
            member = OrganizationMember.objects.filter(
                user=user, is_active=True
            ).first()
            if member:
                club = Club.objects.filter(organization=member.organization).first()
    except Exception as e:
        logger.debug(f"Pas de club pour le manager: {e}")

    # Statistiques détaillées du club
    club_stats = {}
    if club and club.organization:
        try:
            from ...models import Practitioner
            club_practitioners = Practitioner.objects.filter(organization=club.organization)
            club_stats['total_practitioners'] = club_practitioners.count()
            club_stats['total_registrations'] = CompetitionRegistration.objects.filter(
                practitioner__organization=club.organization
            ).count()
            # Compétitions terminées
            club_stats['completed_competitions'] = managed_competitions.filter(
                status='completed'
            ).count()
        except Exception as e:
            logger.debug(f"Erreur stats club: {e}")

    # Statistiques de combat (optionnel)
    combat_stats = {
        'total_combats': 0,
    }
    try:
        from ...models import Combat
        if Combat:
            combat_stats['total_combats'] = Combat.objects.filter(
                poule__competition__in=managed_competitions,
                status__in=['scheduled', 'in_progress']
            ).count()
    except Exception:
        pass

    # Données mensuelles pour le graphique (12 derniers mois)
    monthly_registrations = []
    current_month = timezone.now().replace(day=1)
    for i in range(12):
        month_start = current_month - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        count = CompetitionRegistration.objects.filter(
            competition__in=managed_competitions,
            registration_date__gte=month_start,
            registration_date__lt=month_end
        ).count()
        monthly_registrations.insert(0, count)

    context = {
        'page_title': _('Dashboard Manager'),
        'section': 'manager',
        'user': user,
        'profile': profile,
        'user_role': getattr(profile, 'role', 'unknown') if profile else 'unknown',

        # Statistiques principales
        'total_managed_competitions': total_managed_competitions,
        'competition_statuses': competition_statuses,

        # Compétitions actives avec leurs stats
        'active_competitions_stats': active_competitions_stats,

        # Inscriptions récentes
        'recent_registrations': recent_registrations,

        # Tâches urgentes
        'urgent_tasks': urgent_tasks,

        # Fédération et club (optionnels)
        'default_federation': default_federation,
        'club': club,

        # Stats combat
        'combat_stats': combat_stats,

        # Stats détaillées du club
        'club_stats': club_stats,

        # Données pour les graphiques
        'monthly_registrations': monthly_registrations,
    }

    return render(request, 'competitions/dashboard/manager.html', context)
