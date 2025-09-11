from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from django.db import models
import logging

from ...models import Club, Practitioner, Competition, CompetitionRegistration, Notification
from apps.finances.models import PaymentAttempt, Invoice
from apps.shop.models import Order
from apps.finances.currency_service import COUNTRY_TO_CURRENCY
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

# Task Management Integration
try:
    from apps.task_management.dashboard_utils import get_dashboard_task_data, get_club_dashboard_task_data
    TASK_MANAGEMENT_AVAILABLE = True
except ImportError:
    TASK_MANAGEMENT_AVAILABLE = False
    logger.warning("Task Management module not available")


@login_required
def club_dashboard_anti_scroll(request):
    """
    Tableau de bord anti-scroll pour les responsables de club.
    Version avec onglets qui préserve toutes les fonctionnalités du dashboard original.
    """
    # Import de la fonction dashboard existante pour réutiliser toute la logique
    from .club import club_dashboard
    
    # Exécuter la logique complète du dashboard existant
    # On simule la requête pour récupérer le context complet
    try:
        # Méthode alternative: créer le context directement
        context = _get_club_dashboard_context(request)
        
        # Utiliser le template anti-scroll
        return render(request, 'competitions/dashboard/club_anti_scroll.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans club_dashboard_anti_scroll: {str(e)}")
        # Fallback vers le dashboard original en cas de problème
        messages.error(request, _("Erreur lors du chargement du dashboard. Retour à la version classique."))
        return club_dashboard(request)


def _get_club_dashboard_context(request):
    """
    Génère le même contexte que le dashboard original.
    Cette fonction reprend la logique complète de club_dashboard.
    """
    # Debug des informations utilisateur
    logger.info(f"User: {request.user.username}, authenticated: {request.user.is_authenticated}")
    if hasattr(request.user, 'profile'):
        logger.info(f"User profile role: {request.user.profile.role}")
    
    # Récupérer le club associé à l'utilisateur
    club = None
    club_found_via = "non trouvé"
    
    # Méthode 1: Via attribut direct
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
        club_found_via = "attribut direct"
    
    # Méthode 2: Via relation de propriété
    elif Club.objects.filter(owner=request.user).exists():
        club = Club.objects.filter(owner=request.user).first()
        club_found_via = "propriété"
    
    # Méthode 3: Via profil utilisateur
    elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
        club = request.user.profile.club
        club_found_via = "profil"
    
    # Méthode 4: Via appartenances aux clubs
    elif hasattr(request.user, 'club_memberships') and request.user.club_memberships.exists():
        club = request.user.club_memberships.first().club
        club_found_via = "adhésion"
    
    logger.info(f"Club: {club}, trouvé via: {club_found_via}")
    
    # Si aucun club n'est trouvé, lever une exception pour déclencher le fallback
    if not club:
        raise Exception("Aucun club trouvé pour l'utilisateur")
    
    # S'assurer qu'une Organization associée est attachée au club si possible
    if not club.organization:
        if getattr(club, 'as_organization', None):
            club.organization = club.as_organization
        else:
            try:
                org_created = club._create_associated_organization()
                if org_created:
                    club.organization = org_created
            except Exception:
                pass
        try:
            if club.organization:
                club.save(update_fields=['organization'])
        except Exception:
            pass

    # Récupérer les statistiques et données nécessaires
    stats = {}
    financial_stats = {}
    
    try:
        # Statistiques de base
        stats = {
            'total_practitioners': Practitioner.objects.filter(club=club).count(),
            'active_practitioners': Practitioner.objects.filter(club=club, is_active=True).count(),
            'club_competitions': Competition.objects.filter(organizing_organization=club.organization).count() if club.organization else 0,
            'active_registrations': CompetitionRegistration.objects.filter(practitioner__club=club, status='confirmed').count(),
            'pending_registrations': CompetitionRegistration.objects.filter(practitioner__club=club, status='pending').count(),
        }
        
        # Statistiques financières
        financial_stats = {
            'total_invoices': Invoice.objects.filter(club=club).count() if hasattr(Invoice, 'club') else 0,
            'pending_payments': PaymentAttempt.objects.filter(club=club, status='pending').count() if hasattr(PaymentAttempt, 'club') else 0,
            'total_orders': Order.objects.filter(club=club).count() if hasattr(Order, 'club') else 0,
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
        stats = {'total_practitioners': 0, 'active_practitioners': 0, 'club_competitions': 0, 'active_registrations': 0}
        financial_stats = {'total_invoices': 0, 'pending_payments': 0, 'total_orders': 0}

    # Récupérer les compétitions
    try:
        competitions_to_manage = Competition.objects.none()
        if club.organization:
            competitions_to_manage = Competition.objects.filter(
                organizing_organization=club.organization
            ).distinct().select_related('discipline').prefetch_related('registrations', 'categories')
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des compétitions: {str(e)}")
        competitions_to_manage = Competition.objects.none()

    # Récupérer les pratiquants
    try:
        practitioners = Practitioner.objects.filter(club=club).select_related('user')
        recent_practitioners = practitioners[:10]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des pratiquants: {str(e)}")
        practitioners = Practitioner.objects.none()
        recent_practitioners = []

    # Récupérer les notifications
    try:
        notifications = Notification.objects.filter(
            Q(recipient=request.user) | Q(club=club)
        ).order_by('-created_at')[:5]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des notifications: {str(e)}")
        notifications = []

    # Récupérer les compétitions à venir
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        upcoming_competitions = Competition.objects.filter(
            start_date__gte=timezone.now(),
            start_date__lte=timezone.now() + timedelta(days=90),
            status='published'
        ).exclude(organizing_organization=club.organization if club.organization else None)[:5]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des compétitions à venir: {str(e)}")
        upcoming_competitions = []

    # Récupérer les commandes récentes (si module shop disponible)
    recent_orders = []
    try:
        recent_orders = Order.objects.filter(club=club).order_by('-created_at')[:10]
    except Exception as e:
        logger.debug(f"Module boutique non disponible: {str(e)}")

    # Données d'adhésions (si module membership disponible)
    membership_stats = {
        'total_active': 0,
        'revenue_this_month': 0,
        'expiring_soon': 0,
        'new_this_month': 0,
        'total_packages': 0,
        'retention_rate': {'retention_rate': 85}  # Valeur par défaut
    }
    recent_subscriptions = []
    membership_alerts = []

    try:
        # Placeholder pour les données d'adhésions
        # À remplacer par les vrais modèles quand le module membership sera disponible
        pass
    except Exception as e:
        logger.debug(f"Module membership non disponible: {str(e)}")

    # Task Management Integration
    task_data = {}
    if TASK_MANAGEMENT_AVAILABLE:
        try:
            task_data = get_club_dashboard_task_data(request.user, club)
        except Exception as e:
            logger.error(f"Erreur Task Management: {str(e)}")
            task_data = {}

    # Construction du contexte complet
    context = {
        'club': club,
        'club_found_via': club_found_via,
        'stats': stats,
        'financial_stats': financial_stats,
        'competitions_to_manage': competitions_to_manage,
        'practitioners': practitioners,
        'recent_practitioners': recent_practitioners,
        'upcoming_competitions': upcoming_competitions,
        'recent_orders': recent_orders,
        'membership_stats': membership_stats,
        'recent_subscriptions': recent_subscriptions,
        'membership_alerts': membership_alerts,
        'notifications': notifications,
        'task_data': task_data,
        'user': request.user,
        'current_time': timezone.now(),
        'TASK_MANAGEMENT_AVAILABLE': TASK_MANAGEMENT_AVAILABLE,
    }
    
    return context