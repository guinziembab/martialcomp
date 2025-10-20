from django.core.exceptions import PermissionDenied
#  Dashboard Fédération
# Imports de Django
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ...utils.decorators import federation_admin_required
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Count

# Imports de bibliothèques standards
import csv
import json
import logging
from io import StringIO

# Imports de vos modèles (simplifiés et dédupliqués)
from ...models import (
    Federation,
    Club,
    Discipline,
    Competition, 
    Practitioner,
    CompetitionRegistration,
    Judge,
    Notification
)
from apps.finances.models import PaymentAttempt, Invoice, Transaction
from apps.shop.models import Order

# Imports de vos formulaires
from apps.competitions.forms.federations import FederationForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

# Task Management Integration
# TEMPORAIREMENT DÉSACTIVÉ à cause de l'erreur Notification.federation
TASK_MANAGEMENT_AVAILABLE = False

# Version originale commentée pour référence:
# try:
#     from apps.task_management.dashboard_utils import get_dashboard_task_data, get_federation_dashboard_task_data
#     TASK_MANAGEMENT_AVAILABLE = True
# except ImportError:
#     TASK_MANAGEMENT_AVAILABLE = False
#     logger.warning("Task Management module not available")

# Fonctions mock pour éviter les erreurs
def get_dashboard_task_data(*args, **kwargs):
    return {}

def get_federation_dashboard_task_data(*args, **kwargs):
    return {}

@login_required
def federation_dashboard(request, federation_id=None):
    """
    Vue principale pour le tableau de bord d'une fédération.
    Affiche les statistiques et les actions disponibles pour une fédération.
    """
    # Si federation_id n'est pas fourni, essayer de trouver une fédération associée à l'utilisateur
    if federation_id is None:
        # Vérifier si l'utilisateur est administrateur d'une fédération
        user_federations = None
        
        # Vérifier via l'attribut owner (plus courant)
        user_federations = Federation.objects.filter(owner=request.user)
        
        # Si aucune fédération trouvée, vérifier via le modèle FederationAdministrator
        if not user_federations.exists():
            try:
                from ...models import FederationAdministrator
                user_federations = Federation.objects.filter(
                    administrators__user=request.user
                )
            except ImportError:
                pass
            
        # Si l'utilisateur est associé à au moins une fédération, utiliser la première
        if user_federations and user_federations.exists():
            federation = user_federations.first()
        else:
            # L'utilisateur n'est associé à aucune fédération
            messages.warning(request, _("Vous n'êtes associé à aucune fédération pour le moment."))
            # Rediriger vers la création d'une fédération si en cours d'onboarding
            if hasattr(request.user, 'profile') and request.user.profile.role == 'federation_admin':
                return redirect('competitions:onboarding:federation')
            # Sinon, rediriger vers le dashboard principal
            return redirect('competitions:dashboard:dashboard')
    else:
        # Récupérer la fédération par son ID
        federation = get_object_or_404(Federation, id=federation_id)
    
    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')
    
    # Logique du dashboard existante continue ici...
    context = _get_federation_dashboard_context(request, federation)
    
    return render(request, 'competitions/dashboard/federations/dashboard.html', context)


def _user_can_access_federation(user, federation):
    """Vérifier si l'utilisateur peut accéder à cette fédération"""
    # Super admin peut tout voir
    if user.is_superuser:
        return True
    
    # Owner de la fédération
    if federation.owner == user:
        return True
    
    # Administrateur de la fédération
    try:
        from ...models import FederationAdministrator
        if FederationAdministrator.objects.filter(federation=federation, user=user).exists():
            return True
    except ImportError:
        pass
    
    return False


def _get_practitioners_count_for_federation(federation):
    """
    Obtenir le nombre de pratiquants pour une fédération.
    Gère la relation Practitioner -> Organization -> Federation via Club
    """
    # Option 1: Si la fédération a une organisation associée
    if hasattr(federation, 'organization') and federation.organization:
        try:
            # Chercher les pratiquants de cette organisation
            from apps.organizations.models import Organization
            # L'organisation de type federation peut avoir des practitioners directs
            count = Practitioner.objects.filter(organization=federation.organization).count()
            
            # Chercher aussi les organisations affiliées (clubs)
            affiliated_orgs = Organization.objects.filter(
                parent_affiliations__parent_organization=federation.organization,
                parent_affiliations__is_active=True
            )
            for org in affiliated_orgs:
                count += Practitioner.objects.filter(organization=org).count()
            
            return count
        except Exception as e:
            logger.debug(f"Erreur option 1: {e}")
            pass
    
    # Option 2: Via la relation directe Club -> Federation
    try:
        # Obtenir toutes les organisations des clubs de la fédération
        club_orgs = Club.objects.filter(federation=federation).values_list('organization', flat=True)
        return Practitioner.objects.filter(organization__in=club_orgs).count()
    except Exception as e:
        logger.debug(f"Erreur option 2: {e}")
        pass
    
    # Option 3: Approche détaillée club par club
    try:
        # Compter les pratiquants dont l'organisation est liée à un club de la fédération
        count = 0
        for club in Club.objects.filter(federation=federation):
            if hasattr(club, 'organization') and club.organization:
                count += Practitioner.objects.filter(organization=club.organization).count()
        return count
    except Exception as e:
        logger.debug(f"Erreur option 3: {e}")
        return 0



def _get_competitions_for_federation(federation, filter_params=None):
    """
    Récupère les compétitions pour une fédération donnée.
    Gère la relation via Organization.
    """
    from django.db.models import Q
    
    # Base query
    base_q = Q()
    
    # Option 1: Si la fédération a une organisation associée
    if hasattr(federation, 'organization') and federation.organization:
        base_q |= Q(organizing_organization=federation.organization)
    
    # Option 2: Via les clubs de la fédération
    try:
        # Obtenir toutes les organisations des clubs de la fédération
        club_orgs = Club.objects.filter(federation=federation).values_list('organization', flat=True)
        if club_orgs:
            base_q |= Q(organizing_organization__in=club_orgs)
    except Exception as e:
        logger.debug(f"Erreur lors de la récupération des organisations de clubs: {e}")
    
    # Option 3: Via les clubs directement (legacy)
    # Note: organizing_club n'existe peut-être pas non plus
    # base_q |= Q(organizing_club__federation=federation)
    
    # Appliquer le filtre de base
    queryset = Competition.objects.filter(base_q)
    
    # Appliquer des filtres supplémentaires si fournis
    if filter_params:
        queryset = queryset.filter(**filter_params)
    
    return queryset


def _get_federation_dashboard_context(request, federation):
    """
    Construire le contexte pour le dashboard de la fédération
    
    IMPORTANT: Le modèle Notification n'a pas de champ 'federation'.
    Ne jamais faire Notification.objects.filter(federation=...)
    """
    # Statistiques de base
    clubs_count = Club.objects.filter(federation=federation).count()
    practitioners_count = _get_practitioners_count_for_federation(federation)
    competitions_count = _get_competitions_for_federation(federation).count()
    
    # Compétitions récentes et à venir
    upcoming_competitions = _get_competitions_for_federation(
        federation,
        {'start_date__gte': timezone.now().date()}
    ).order_by('start_date')[:5]
    
    recent_competitions = _get_competitions_for_federation(
        federation,
        {'end_date__lt': timezone.now().date()}
    ).order_by('-end_date')[:5]
    
    # Disciplines
    disciplines = federation.disciplines.all() if hasattr(federation, 'disciplines') else []
    
    # Notifications récentes
    # Note: Le modèle Notification n'a pas de champ federation
    # On peut soit:
    # 1. Filtrer par les utilisateurs de la fédération
    # 2. Ajouter un champ federation au modèle
    # 3. Utiliser une table de liaison
    
    recent_notifications = []
    try:
        # Option 1: Notifications des administrateurs de la fédération
        if hasattr(federation, 'owner') and federation.owner:
            recent_notifications = Notification.objects.filter(
                user=federation.owner
            ).order_by('-created_at')[:10]
        
        # Option 2: Si FederationAdministrator existe
        try:
            from ...models import FederationAdministrator
            admin_users = FederationAdministrator.objects.filter(
                federation=federation
            ).values_list('user', flat=True)
            if admin_users:
                recent_notifications = Notification.objects.filter(
                    user__in=admin_users
                ).order_by('-created_at')[:10]
        except ImportError:
            pass
    except Exception as e:
        logger.debug(f"Erreur lors de la récupération des notifications: {e}")
        recent_notifications = []
    
    # Statistiques financières
    financial_stats = {
        'total_revenue': 0,
        'pending_payments': 0,
        'total_invoices': 0,
    }
    
    # Task management data si disponible
    task_data = {}
    if TASK_MANAGEMENT_AVAILABLE:
        try:
            # Protéger contre les erreurs de champs manquants
            task_data = get_federation_dashboard_task_data(federation)
        except Exception as e:
            logger.error(f"Error getting task data: {str(e)}")
            task_data = {}  # Valeur par défaut en cas d'erreur
    
    context = {
        'federation': federation,
        'clubs_count': clubs_count,
        'practitioners_count': practitioners_count,
        'competitions_count': competitions_count,
        'upcoming_competitions': upcoming_competitions,
        'recent_competitions': recent_competitions,
        'disciplines': disciplines,
        'recent_notifications': recent_notifications,
        'financial_stats': financial_stats,
        'task_data': task_data,
        'has_task_management': TASK_MANAGEMENT_AVAILABLE,
    }
    
    return context


# Conserver le reste du fichier original...


@login_required
def federation_manage_clubs(request, federation_id):
    """Gestion des clubs de la fédération"""
    context = {
        'title': _('Gestion des clubs'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_clubs.html', context)

@login_required
def federation_manage_judges(request, federation_id):
    """Gestion des juges de la fédération"""
    context = {
        'title': _('Gestion des juges'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_judges.html', context)

@login_required
def federation_manage_competitions(request, federation_id):
    """Gestion des compétitions de la fédération"""
    context = {
        'title': _('Gestion des compétitions'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_competitions.html', context)

@login_required
def federation_manage_practitioners(request, federation_id):
    """Gestion des pratiquants de la fédération"""
    context = {
        'title': _('Gestion des pratiquants'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_practitioners.html', context)

@login_required
def federation_manage_licenses(request, federation_id):
    """Gestion des licences de la fédération"""
    context = {
        'title': _('Gestion des licences'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_licenses.html', context)

@login_required
def federation_manage_certifications(request, federation_id):
    """Gestion des certifications de la fédération"""
    context = {
        'title': _('Gestion des certifications'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_certifications.html', context)

@login_required
def federation_manage_reports(request, federation_id):
    """Gestion des rapports de la fédération"""
    context = {
        'title': _('Gestion des rapports'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_reports.html', context)

@login_required
def federation_manage_settings(request, federation_id):
    """Gestion des paramètres de la fédération"""
    context = {
        'title': _('Paramètres de la fédération'),
        'federation_id': federation_id,
        'message': _('Fonctionnalité temporairement indisponible')
    }
    return render(request, 'competitions/dashboard/federation_settings.html', context)