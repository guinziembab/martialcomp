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
def federations_list(request):
    """
    Liste des fédérations de l'utilisateur.
    Redirige automatiquement vers le dashboard de la première fédération trouvée.
    """
    # Chercher les fédérations dont l'utilisateur est owner
    user_federations = Federation.objects.filter(owner=request.user)

    if user_federations.exists():
        # Rediriger vers la première fédération
        federation = user_federations.first()
        return redirect('competitions:dashboard:federation', federation_id=federation.id)

    # Si pas de fédération, vérifier si admin d'une fédération
    try:
        from ...models import FederationAdministrator
        admin_federations = FederationAdministrator.objects.filter(user=request.user).values_list('federation_id', flat=True)
        if admin_federations:
            return redirect('competitions:dashboard:federation', federation_id=admin_federations[0])
    except ImportError:
        pass

    # Aucune fédération trouvée - rediriger vers le dashboard principal
    messages.info(request, _("Aucune fédération associée à votre compte."))
    return redirect('competitions:dashboard:dashboard')


@login_required
def federation_dashboard(request, federation_id):
    """
    Tableau de bord pour les responsables de fédération.
    Affiche les statistiques et les informations relatives à la fédération.
    """
    # Récupérer la fédération
    try:
        federation = get_object_or_404(Federation, id=federation_id)
    except Exception as e:
        logger.error(f"Erreur récupération fédération {federation_id}: {e}")
        messages.error(request, "Fédération introuvable.")
        return redirect('competitions:dashboard:dashboard')

    # Vérifier les permissions (version améliorée avec auto-correction)
    has_permission = False

    # Super admin
    if request.user.is_superuser:
        has_permission = True
        logger.info(f"Permission accordée via superuser pour {request.user.username}")

    # Owner de la fédération (comparaison par ID pour éviter les problèmes de proxy)
    if federation.owner_id == request.user.id:
        has_permission = True
        logger.info(f"Permission accordée via owner_id pour {request.user.username}")

    # Vérification alternative: owner object direct
    if federation.owner == request.user:
        has_permission = True
        logger.info(f"Permission accordée via owner object pour {request.user.username}")

    # Vérifier aussi si l'utilisateur est dans les administrateurs
    if hasattr(federation, 'administrators'):
        try:
            if federation.administrators.filter(user=request.user).exists():
                has_permission = True
                logger.info(f"Permission accordée via administrators pour {request.user.username}")
        except Exception as e:
            logger.warning(f"Erreur vérification administrators: {e}")

    # Vérifier via FederationAdministrator model
    try:
        from ...models import FederationAdministrator
        if FederationAdministrator.objects.filter(federation=federation, user=request.user).exists():
            has_permission = True
            logger.info(f"Permission accordée via FederationAdministrator pour {request.user.username}")
    except Exception as e:
        logger.warning(f"Erreur vérification FederationAdministrator: {e}")

    # Vérifier via le profil utilisateur (role federation_admin)
    if hasattr(request.user, 'profile') and request.user.profile.role == 'federation_admin':
        # Vérifier s'il existe une fédération dont l'utilisateur est owner
        user_federations = Federation.objects.filter(owner=request.user)
        if user_federations.filter(id=federation_id).exists():
            has_permission = True
            logger.info(f"Permission accordée via profile role pour {request.user.username}")
        # AUTO-CORRECTION: Si l'utilisateur a le rôle federation_admin et vient de créer cette fédération
        # mais l'owner_id n'est pas correctement défini, corriger automatiquement
        elif not federation.owner and not has_permission:
            # Vérifier si c'est la seule fédération et l'utilisateur vient de la créer
            recent_federations = Federation.objects.filter(
                created_at__gte=timezone.now() - timezone.timedelta(minutes=5)
            ).order_by('-created_at')
            if recent_federations.exists() and recent_federations.first().id == federation_id:
                # Correction automatique: assigner l'owner
                federation.owner = request.user
                federation.save(update_fields=['owner'])
                has_permission = True
                logger.info(f"AUTO-CORRECTION: Owner assigné automatiquement pour fédération {federation_id} à {request.user.username}")

    if not has_permission:
        logger.warning(f"Permission refusée pour {request.user.username} (ID: {request.user.id}) sur fédération {federation_id} (owner_id: {federation.owner_id}, owner: {federation.owner})")
        messages.error(request, "Vous n'avez pas les permissions pour accéder à cette fédération.")
        return redirect('competitions:dashboard:dashboard')
    
    # Recuperer les disciplines de la federation
    federation_disciplines = federation.disciplines.all()

    # Filtrer les clubs par discipline si la federation a des disciplines definies
    if federation_disciplines.exists():
        # Clubs qui ont au moins une discipline en commun avec la federation
        clubs_query = Club.objects.filter(
            federation=federation
        ).filter(
            Q(disciplines__in=federation_disciplines) | Q(disciplines__isnull=True)
        ).distinct()
    else:
        clubs_query = Club.objects.filter(federation=federation)

    # Statistiques de base
    stats = {
        'clubs_count': clubs_query.count(),
        'competitions_count': Competition.objects.filter(organizing_organization=federation.organization).count() if federation.organization else 0,
        'participants_count': Practitioner.objects.filter(organization=federation.organization).count() if federation.organization else 0,
        'judges_count': Judge.objects.filter(organization=federation.organization).count() if federation.organization else 0,
    }

    # Competitions a venir - inclure celles de l'organisation ET celles avec la discipline de la federation
    if federation.organization:
        # Construire les conditions de filtre
        conditions = Q(organizing_organization=federation.organization)

        # Ajouter aussi les compétitions de la même discipline
        if federation_disciplines.exists():
            conditions |= Q(discipline__in=federation_disciplines)

        upcoming_competitions = Competition.objects.filter(
            conditions,
            start_date__gte=timezone.now()
        ).select_related('discipline').order_by('start_date').distinct()[:5]
    else:
        # Si pas d'organisation, prendre celles avec la discipline de la fédération
        if federation_disciplines.exists():
            upcoming_competitions = Competition.objects.filter(
                discipline__in=federation_disciplines,
                start_date__gte=timezone.now()
            ).select_related('discipline').order_by('start_date')[:5]
        else:
            upcoming_competitions = []

    # Clubs recents (filtres par discipline)
    recent_clubs = clubs_query.order_by('-created_at')[:5]

    # MULTI-DEVISE: Détection de la devise préférée de l'utilisateur
    try:
        from apps.finances.currency_service import (
            get_preferred_currency_for_request,
            convert_amount,
        )
        preferred_currency, currency_source = get_preferred_currency_for_request(request)
    except Exception:
        preferred_currency = 'EUR'
        currency_source = 'default'

    # Statistiques financieres
    financial_stats = {
        'balance': 0,
        'income': 0,
        'expense': 0,
        'pending_invoices': 0,
        'currency': preferred_currency,
        'base_currency': 'EUR',
    }

    # Calculer les statistiques financieres reelles si l'organisation existe
    if federation.organization:
        try:
            # Revenus (paiements recus) en EUR
            income_eur = PaymentAttempt.objects.filter(
                organization=federation.organization,
                status='succeeded'
            ).aggregate(total=models.Sum('amount'))['total'] or 0

            # Factures en attente
            pending_invoices = Invoice.objects.filter(
                organization=federation.organization,
                status='pending'
            ).count()

            # MULTI-DEVISE: Convertir si nécessaire
            if preferred_currency != 'EUR' and income_eur > 0:
                try:
                    income_converted, _rate = convert_amount(float(income_eur), 'EUR', preferred_currency)
                    income_display = float(income_converted)
                except Exception:
                    income_display = float(income_eur)
            else:
                income_display = float(income_eur)

            financial_stats = {
                'balance': income_display,
                'income': income_display,
                'expense': 0,
                'pending_invoices': pending_invoices,
                'currency': preferred_currency,
                'base_currency': 'EUR',
                'income_eur': float(income_eur),  # Valeur originale pour référence
            }
        except Exception as e:
            logger.warning(f"Erreur calcul stats financieres: {e}")

    # Statistiques boutique
    shop_stats = {
        'total_orders': 0,
        'pending_orders': 0,
        'total_revenue': 0,
        'currency': preferred_currency,
    }

    if federation.organization:
        try:
            total_orders = Order.objects.filter(organization=federation.organization).count()
            pending_orders = Order.objects.filter(organization=federation.organization, status='pending').count()
            total_revenue_eur = Order.objects.filter(
                organization=federation.organization,
                status='completed'
            ).aggregate(total=models.Sum('total_amount'))['total'] or 0

            # MULTI-DEVISE: Convertir le revenu si nécessaire
            if preferred_currency != 'EUR' and total_revenue_eur > 0:
                try:
                    revenue_converted, _rate = convert_amount(float(total_revenue_eur), 'EUR', preferred_currency)
                    total_revenue_display = float(revenue_converted)
                except Exception:
                    total_revenue_display = float(total_revenue_eur)
            else:
                total_revenue_display = float(total_revenue_eur)

            shop_stats = {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'total_revenue': total_revenue_display,
                'total_revenue_eur': float(total_revenue_eur),
                'currency': preferred_currency,
            }
        except Exception as e:
            logger.warning(f"Erreur calcul stats shop: {e}")

    # Statistiques grades
    grades_stats = {
        'total_grades': 0,
        'pending_promotions': 0,
        'recent_promotions': 0
    }

    try:
        from apps.grades.models import Grade, GradePromotion
        if federation.organization:
            grades_stats = {
                'total_grades': Grade.objects.filter(
                    discipline__in=federation_disciplines
                ).count() if federation_disciplines.exists() else Grade.objects.count(),
                'pending_promotions': GradePromotion.objects.filter(
                    practitioner__organization=federation.organization,
                    status='pending'
                ).count(),
                'recent_promotions': GradePromotion.objects.filter(
                    practitioner__organization=federation.organization,
                    status='approved',
                    approved_date__gte=timezone.now() - timezone.timedelta(days=30)
                ).count()
            }
    except Exception as e:
        logger.warning(f"Erreur calcul stats grades: {e}")

    # Statistiques certifications
    certifications_stats = {
        'total_certifications': 0,
        'active_certifications': 0,
        'expiring_soon': 0
    }

    try:
        # Les certifications sont liees aux juges
        if federation.organization:
            certified_judges = Judge.objects.filter(
                organization=federation.organization,
                is_certified=True
            ).count()

            certifications_stats = {
                'total_certifications': certified_judges,
                'active_certifications': certified_judges,
                'expiring_soon': 0  # A implementer si date d'expiration existe
            }
    except Exception as e:
        logger.warning(f"Erreur calcul stats certifications: {e}")

    context = {
        'federation': federation,
        'stats': stats,
        'upcoming_competitions': upcoming_competitions,
        'recent_clubs': recent_clubs,
        'financial_stats': financial_stats,
        'shop_stats': shop_stats,
        'grades_stats': grades_stats,
        'certifications_stats': certifications_stats,
        'federation_disciplines': federation_disciplines,
    }

    return render(request, 'competitions/dashboard/federation.html', context)


# Fonctions de gestion simplifiées
# Note: federation_manage_clubs est définie plus bas avec le traitement POST complet


@login_required
def federation_manage_competitions(request, federation_id):
    """Gestion des compétitions de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)
    competitions = Competition.objects.filter(federation=federation)
    
    context = {
        'federation': federation,
        'competitions': competitions,
    }
    return render(request, 'competitions/dashboard/federation_competitions.html', context)


@login_required
def federation_manage_judges(request, federation_id):
    """Gestion des juges de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)
    judges = Judge.objects.filter(federation=federation)
    
    context = {
        'federation': federation,
        'judges': judges,
    }
    return render(request, 'competitions/dashboard/federation_judges.html', context)


@login_required
def federation_manage_settings(request, federation_id):
    """Paramètres de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)

    if request.method == 'POST':
        form = FederationForm(request.POST, instance=federation)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres mis à jour avec succès.")
            return redirect('competitions:dashboard:federation', federation_id=federation_id)
    else:
        form = FederationForm(instance=federation)

    context = {
        'federation': federation,
        'form': form,
    }
    return render(request, 'competitions/dashboard/federation_settings.html', context)


@login_required
def federation_certifications(request, federation_id):
    """Gestion des certifications de juges de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:dashboard')

    # Récupérer les juges certifiés par cette fédération
    judges = Judge.objects.filter(organization=federation.organization).select_related('practitioner', 'practitioner__user')

    # Récupérer aussi les juges des clubs affiliés
    affiliated_clubs = Club.objects.filter(federation=federation)
    club_orgs = affiliated_clubs.values_list('organization', flat=True)
    club_judges = Judge.objects.filter(
        practitioner__organization__in=club_orgs
    ).select_related('practitioner', 'practitioner__user').exclude(
        id__in=judges.values_list('id', flat=True)
    )

    # Traitement POST pour certifier/décertifier un juge
    if request.method == 'POST':
        action = request.POST.get('action')
        judge_id = request.POST.get('judge_id')

        if judge_id:
            try:
                judge = Judge.objects.get(id=judge_id)

                if action == 'certify':
                    judge.organization = federation.organization
                    judge.certified_since = timezone.now().date()
                    judge.certification_number = f"CERT-{federation.id}-{judge.id}-{timezone.now().strftime('%Y%m%d')}"
                    judge.save()
                    messages.success(request, _("Juge certifié avec succès."))

                elif action == 'revoke':
                    judge.organization = None
                    judge.certified_since = None
                    judge.certification_number = ""
                    judge.save()
                    messages.success(request, _("Certification révoquée."))

                elif action == 'update_level':
                    new_level = request.POST.get('qualification_level')
                    if new_level in ['novice', 'regional', 'national', 'international']:
                        judge.qualification_level = new_level
                        judge.save()
                        messages.success(request, _("Niveau de qualification mis à jour."))

            except Judge.DoesNotExist:
                messages.error(request, _("Juge non trouvé."))

        return redirect('competitions:federations:certifications', federation_id=federation_id)

    # Statistiques
    stats = {
        'total_certified': judges.count(),
        'novice': judges.filter(qualification_level='novice').count(),
        'regional': judges.filter(qualification_level='regional').count(),
        'national': judges.filter(qualification_level='national').count(),
        'international': judges.filter(qualification_level='international').count(),
        'pending': club_judges.filter(organization__isnull=True).count(),
    }

    context = {
        'federation': federation,
        'judges': judges,
        'club_judges': club_judges,
        'stats': stats,
        'qualification_levels': [
            ('novice', _('Novice')),
            ('regional', _('Régional')),
            ('national', _('National')),
            ('international', _('International')),
        ],
    }
    return render(request, 'competitions/dashboard/federation_certifications.html', context)


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
    # Statistiques de base - utiliser le système Organization/Affiliation
    affiliated_clubs = get_affiliated_clubs(federation)
    clubs_count = affiliated_clubs.count()
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
    """
    Vue pour gérer les clubs affiliés Ã  une fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Vérifier les permissions
    has_access = False
    if hasattr(request.user, 'federation_admin_roles'):
        is_admin = federation.administrators.filter(user=request.user).exists()
        if is_admin:
            has_access = True
    
    if request.user == federation.owner:
        has_access = True
        
    if not has_access:
        messages.error(request, _("Vous n'avez pas les droits d'accès Ã  cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation de la fédération
    from apps.organizations.models import Organization, Affiliation
    
    federation_org = federation.organization
    if not federation_org:
        # Fallback: chercher par l'ancien ID de federation
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()

    # Traiter les actions d'affiliation (POST)
    if request.method == 'POST' and federation_org:
        club_id = request.POST.get('club_id')
        action = request.POST.get('action', 'invite')

        if club_id:
            try:
                club = Club.objects.get(id=club_id)

                if action == 'invite':
                    # La federation invite un club (demande d'affiliation)
                    if club.organization:
                        affiliation, created = Affiliation.objects.get_or_create(
                            parent_organization=federation_org,
                            child_organization=club.organization,
                            defaults={
                                'affiliation_type': 'member',
                                'initiated_by': 'parent',
                                'parent_status': 'approved',
                                'child_status': 'pending',
                                'parent_approved_by': request.user,
                                'parent_approved_at': timezone.now(),
                                'is_active': False
                            }
                        )

                        if created:
                            messages.success(request, _("Invitation envoyee au club. En attente de leur approbation."))
                        else:
                            if affiliation.child_status == 'pending':
                                messages.info(request, _("Une invitation est deja en attente pour ce club."))
                            elif affiliation.is_active:
                                messages.info(request, _("Ce club est deja affilie."))
                            else:
                                # Relancer l'invitation
                                affiliation.parent_status = 'approved'
                                affiliation.child_status = 'pending'
                                affiliation.parent_approved_by = request.user
                                affiliation.parent_approved_at = timezone.now()
                                affiliation.save()
                                messages.success(request, _("Invitation renvoyee au club."))
                    else:
                        messages.error(request, _("Ce club n'a pas d'organisation associee."))

                elif action == 'approve':
                    # La federation approuve une demande d'un club
                    if club.organization:
                        affiliation = Affiliation.objects.filter(
                            parent_organization=federation_org,
                            child_organization=club.organization
                        ).first()

                        if affiliation and affiliation.parent_status == 'pending':
                            affiliation.parent_status = 'approved'
                            affiliation.parent_approved_by = request.user
                            affiliation.parent_approved_at = timezone.now()

                            # Verifier si les deux parties ont approuve
                            if affiliation.child_status == 'approved':
                                affiliation.is_active = True
                                club.federation = federation
                                club.save(update_fields=['federation'])
                                messages.success(request, _("Affiliation approuvee! Le club est maintenant affilie."))
                            else:
                                messages.success(request, _("Demande approuvee. En attente de l'approbation du club."))

                            affiliation.save()
                        else:
                            messages.warning(request, _("Aucune demande en attente pour ce club."))

                elif action == 'reject':
                    # La federation refuse une demande
                    if club.organization:
                        affiliation = Affiliation.objects.filter(
                            parent_organization=federation_org,
                            child_organization=club.organization
                        ).first()

                        if affiliation:
                            affiliation.parent_status = 'rejected'
                            affiliation.is_active = False
                            affiliation.save()
                            messages.success(request, _("Demande d'affiliation refusee."))

                elif action == 'unaffiliate':
                    # Desaffilier un club
                    if club.organization:
                        affiliation = Affiliation.objects.filter(
                            parent_organization=federation_org,
                            child_organization=club.organization
                        ).first()

                        if affiliation:
                            affiliation.is_active = False
                            affiliation.parent_status = 'pending'
                            affiliation.child_status = 'pending'
                            affiliation.save()
                            club.federation = None
                            club.save(update_fields=['federation'])
                            messages.success(request, _("Le club a ete desaffilie."))
                        else:
                            messages.warning(request, _("Ce club n'etait pas affilie."))

            except Club.DoesNotExist:
                messages.error(request, _("Club introuvable."))
            except Exception as e:
                logger.error(f"Erreur lors de l'operation d'affiliation: {e}")
                messages.error(request, _("Une erreur est survenue lors de l'operation."))

        return redirect('competitions:federations:clubs', federation_id=federation_id)

    if federation_org:
        # Recuperer tous les clubs affilies Ã  la fédération via les organisations
        affiliated_org_ids = Affiliation.objects.filter(
            parent_organization=federation_org,
            is_active=True
        ).values_list('child_organization_id', flat=True)

        affiliated_clubs = Club.objects.filter(
            organization_id__in=affiliated_org_ids
        ).order_by('name')

        # Invitations envoyees par la federation (en attente d'approbation du club)
        pending_invitations_org_ids = Affiliation.objects.filter(
            parent_organization=federation_org,
            initiated_by='parent',
            parent_status='approved',
            child_status='pending',
            is_active=False
        ).values_list('child_organization_id', flat=True)

        pending_invitations = Club.objects.filter(
            organization_id__in=pending_invitations_org_ids
        ).order_by('name')

        # Demandes recues des clubs (en attente d'approbation de la federation)
        pending_requests_org_ids = Affiliation.objects.filter(
            parent_organization=federation_org,
            initiated_by='child',
            child_status='approved',
            parent_status='pending',
            is_active=False
        ).values_list('child_organization_id', flat=True)

        pending_requests = Club.objects.filter(
            organization_id__in=pending_requests_org_ids
        ).order_by('name')

        # Clubs disponibles (pas d'affiliation ou affiliation rejetee/inactive)
        excluded_org_ids = list(affiliated_org_ids) + list(pending_invitations_org_ids) + list(pending_requests_org_ids)
        available_clubs = Club.objects.filter(
            organization__isnull=False
        ).exclude(
            organization_id__in=excluded_org_ids
        ).order_by('name')
    else:
        # Si pas d'organisation trouvee, retourner des querysets vides
        affiliated_clubs = Club.objects.none()
        pending_invitations = Club.objects.none()
        pending_requests = Club.objects.none()
        available_clubs = Club.objects.filter(organization__isnull=False).order_by('name')

    context = {
        'federation': federation,
        'affiliated_clubs': affiliated_clubs,
        'pending_invitations': pending_invitations,
        'pending_requests': pending_requests,
        'available_clubs': available_clubs,
        'title': _("Gestion des clubs affilies")
    }

    return render(request, 'competitions/dashboard/federation_clubs.html', context)

@login_required
def federation_manage_judges(request, federation_id):
    """Gestion des juges et arbitres de la fédération et des clubs affiliés"""
    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    has_access = False
    if request.user == federation.owner:
        has_access = True
    elif hasattr(federation, 'administrators'):
        has_access = federation.administrators.filter(user=request.user).exists()

    if not has_access and hasattr(request.user, 'is_staff') and request.user.is_staff:
        has_access = True

    if not has_access:
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les IDs des organisations affiliées
    affiliated_org_ids = get_affiliated_org_ids(federation)

    # Récupérer tous les juges des clubs affiliés
    judges = Judge.objects.filter(
        practitioner__organization_id__in=affiliated_org_ids
    ).select_related(
        'practitioner',
        'practitioner__organization',
        'user'
    ).prefetch_related('practitioner__qualifications').distinct()

    # Appliquer les filtres
    qualification_type = request.GET.get('qualification_type', '')
    level = request.GET.get('level', '')
    club_filter = request.GET.get('club', '')

    if level:
        judges = judges.filter(qualification_level=level)

    if club_filter:
        judges = judges.filter(practitioner__organization_id=club_filter)

    # Statistiques
    total_judges = judges.count()
    # Judge utilise is_technical_judge et is_combat_referee (booléens), pas judge_type
    technical_judges = judges.filter(
        Q(practitioner__qualifications__qualification_type='technical_judge') |
        Q(is_technical_judge=True)
    ).distinct().count()
    combat_referees = judges.filter(
        Q(practitioner__qualifications__qualification_type='combat_referee') |
        Q(is_combat_referee=True)
    ).distinct().count()

    # Liste des clubs pour le filtre
    affiliated_clubs = get_affiliated_clubs(federation)

    context = {
        'title': _('Juges & Arbitres'),
        'federation': federation,
        'judges': judges,
        'affiliated_clubs': affiliated_clubs,
        'total_judges': total_judges,
        'technical_judges': technical_judges,
        'combat_referees': combat_referees,
        'selected_qualification_type': qualification_type,
        'selected_level': level,
        'selected_club': club_filter,
    }
    return render(request, 'competitions/dashboard/federation_judges.html', context)

@login_required
def federation_manage_competitions(request, federation_id):
    """
    Vue pour gérer les compétitions d'une fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Vérifier les permissions
    has_access = False
    if hasattr(request.user, 'federation_admin_roles'):
        is_admin = federation.administrators.filter(user=request.user).exists()
        if is_admin:
            has_access = True
    
    if request.user == federation.owner:
        has_access = True
        
    if not has_access:
        messages.error(request, _("Vous n'avez pas les droits d'accès Ã  cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les compétitions de la fédération
    # Récupérer les compétitions organisées par la fédération
    if federation.organization:
        competitions = Competition.objects.filter(organizing_organization=federation.organization).order_by('-start_date')
    else:
        competitions = Competition.objects.none()
    
    context = {
        'federation': federation,
        'competitions': competitions,
        'title': _("Gestion des compétitions")
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
    """Gestion des certifications de juges de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    has_access = False
    if request.user == federation.owner:
        has_access = True
    elif hasattr(federation, 'administrators'):
        has_access = federation.administrators.filter(user=request.user).exists()

    if not has_access:
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les juges certifiés par la fédération
    judges = Judge.objects.filter(
        organization=federation.organization
    ).select_related('practitioner', 'practitioner__user', 'practitioner__organization')

    # Récupérer les juges des clubs affiliés qui peuvent être certifiés
    # Le Practitioner a un champ organization, on récupère les orgs des clubs affiliés
    affiliated_org_ids = Club.objects.filter(
        federation=federation
    ).exclude(
        organization__isnull=True
    ).values_list('organization_id', flat=True)

    club_judges = Judge.objects.filter(
        practitioner__organization_id__in=list(affiliated_org_ids)
    ).exclude(
        organization=federation.organization
    ).select_related('practitioner', 'practitioner__user', 'practitioner__organization')

    # Traitement des actions POST
    if request.method == 'POST':
        action = request.POST.get('action')
        judge_id = request.POST.get('judge_id')

        if judge_id:
            try:
                judge = Judge.objects.get(id=judge_id)

                if action == 'certify':
                    # Certifier un juge de club
                    judge.organization = federation.organization
                    judge.certified_since = timezone.now().date()
                    if not judge.certification_number:
                        # Générer un numéro de certification
                        import random
                        import string
                        prefix = federation.name[:3].upper() if federation.name else 'FED'
                        suffix = ''.join(random.choices(string.digits, k=6))
                        judge.certification_number = f"{prefix}-{suffix}"
                    judge.save()
                    messages.success(request, _("Le juge a été certifié avec succès."))

                elif action == 'revoke':
                    # Révoquer la certification
                    judge.organization = None
                    judge.certification_number = None
                    judge.certified_since = None
                    judge.save()
                    messages.success(request, _("La certification a été révoquée."))

                elif action == 'update_level':
                    # Mettre à jour le niveau de qualification
                    new_level = request.POST.get('new_level')
                    if new_level in ['novice', 'regional', 'national', 'international']:
                        judge.qualification_level = new_level
                        judge.save()
                        messages.success(request, _("Le niveau de qualification a été mis à jour."))
                    else:
                        messages.error(request, _("Niveau de qualification invalide."))

            except Judge.DoesNotExist:
                messages.error(request, _("Juge introuvable."))
            except Exception as e:
                logger.error(f"Erreur lors de l'action de certification: {e}")
                messages.error(request, _("Une erreur est survenue."))

        return redirect('competitions:federations:certifications', federation_id=federation_id)

    # Calculer les statistiques
    stats = {
        'total': judges.count(),
        'novice': judges.filter(qualification_level='novice').count(),
        'regional': judges.filter(qualification_level='regional').count(),
        'national': judges.filter(qualification_level='national').count(),
        'international': judges.filter(qualification_level='international').count(),
    }

    # Niveaux de qualification disponibles
    qualification_levels = [
        ('novice', _('Novice')),
        ('regional', _('Régional')),
        ('national', _('National')),
        ('international', _('International')),
    ]

    context = {
        'federation': federation,
        'judges': judges,
        'club_judges': club_judges,
        'stats': stats,
        'qualification_levels': qualification_levels,
        'title': _('Gestion des certifications'),
    }
    return render(request, 'competitions/dashboard/federation_certifications.html', context)

def get_affiliated_org_ids(federation):
    """Helper: récupère les IDs des organizations affiliées à une fédération"""
    if not federation.organization:
        return []

    from apps.organizations.models import Affiliation
    # Trouver les organizations affiliées à la fédération (child -> parent)
    return list(Affiliation.objects.filter(
        parent_organization=federation.organization,
        is_active=True
    ).values_list('child_organization_id', flat=True))


def get_affiliated_clubs(federation):
    """Helper: récupère les clubs affiliés à une fédération via le système Organization/Affiliation"""
    affiliated_org_ids = get_affiliated_org_ids(federation)
    if not affiliated_org_ids:
        return Club.objects.none()

    # Récupérer les clubs dont l'organization est affiliée
    return Club.objects.filter(
        organization_id__in=affiliated_org_ids
    ).distinct()


@login_required
def federation_manage_reports(request, federation_id):
    """Gestion des rapports et exports de la fédération"""
    federation = get_object_or_404(Federation, id=federation_id)

    # Récupérer les IDs des organizations affiliées et les clubs
    affiliated_org_ids = get_affiliated_org_ids(federation)
    affiliated_clubs = get_affiliated_clubs(federation)

    # Compter les pratiquants des organisations affiliées
    practitioners_count = Practitioner.objects.filter(
        organization_id__in=affiliated_org_ids
    ).count()

    # Compter les compétitions organisées par la fédération ou ses clubs affiliés
    # Competition utilise organizing_organization, pas federation/organizer
    all_org_ids = affiliated_org_ids.copy() if isinstance(affiliated_org_ids, list) else list(affiliated_org_ids)
    if federation.organization:
        all_org_ids.append(federation.organization.id)

    competitions_count = Competition.objects.filter(
        organizing_organization_id__in=all_org_ids
    ).distinct().count()

    # Compter les juges (via leur practitioner.organization affiliée)
    judges_count = Judge.objects.filter(
        practitioner__organization_id__in=affiliated_org_ids
    ).distinct().count()

    # Compter les résultats (CompetitionResult avec classement pour les compétitions de la fédération)
    from ...models import CompetitionResult
    results_count = CompetitionResult.objects.filter(
        competition__organizing_organization_id__in=all_org_ids,
        rank__isnull=False
    ).count()

    # Compter les certificats émis
    certificates_count = 0
    try:
        from ...models import IssuedCertificate
        certificates_count = IssuedCertificate.objects.filter(
            organization=federation
        ).count()
    except:
        pass

    stats = {
        'clubs_count': affiliated_clubs.count(),
        'practitioners_count': practitioners_count,
        'competitions_count': competitions_count,
        'judges_count': judges_count,
        'results_count': results_count,
        'certificates_count': certificates_count,
    }

    context = {
        'title': _('Rapports & Export'),
        'federation': federation,
        'stats': stats,
    }
    return render(request, 'competitions/dashboard/federation_reports.html', context)


@login_required
def export_clubs_csv(request, federation_id):
    """Export des clubs affiliés en CSV"""
    federation = get_object_or_404(Federation, id=federation_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="clubs_{federation.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')  # BOM pour Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nom', 'Adresse', 'Ville', 'Code postal', 'Responsable', 'Email', 'Téléphone', 'Date d\'affiliation', 'Statut'])

    clubs = get_affiliated_clubs(federation).select_related('owner')

    for club in clubs:
        writer.writerow([
            club.name,
            club.address or '',
            club.city or '',
            club.postal_code or '',
            club.owner.get_full_name() if club.owner else '',
            club.email or '',
            club.phone or '',
            club.created_at.strftime('%d/%m/%Y') if hasattr(club, 'created_at') and club.created_at else '',
            'Actif' if club.is_active else 'Inactif'
        ])

    return response


@login_required
def export_practitioners_csv(request, federation_id):
    """Export des pratiquants en CSV"""
    federation = get_object_or_404(Federation, id=federation_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="pratiquants_{federation.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nom', 'Prénom', 'Club', 'Grade', 'Licence', 'Date de naissance', 'Genre', 'Email'])

    affiliated_org_ids = get_affiliated_org_ids(federation)

    practitioners = Practitioner.objects.filter(
        organization_id__in=affiliated_org_ids
    ).select_related('organization', 'user')

    for p in practitioners:
        writer.writerow([
            p.last_name or '',
            p.first_name or '',
            p.organization.name if p.organization else '',
            p.current_grade or '',
            p.license_number or '',
            p.birth_date.strftime('%d/%m/%Y') if p.birth_date else '',
            p.gender or '',
            p.email or (p.user.email if p.user else ''),
        ])

    return response


@login_required
def export_competitions_csv(request, federation_id):
    """Export des compétitions en CSV"""
    federation = get_object_or_404(Federation, id=federation_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="competitions_{federation.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nom', 'Date', 'Lieu', 'Organisateur', 'Inscrits', 'Statut'])

    # Récupérer les IDs des organisations affiliées + la fédération elle-même
    affiliated_org_ids = get_affiliated_org_ids(federation)
    all_org_ids = list(affiliated_org_ids)
    if federation.organization:
        all_org_ids.append(federation.organization.id)

    competitions = Competition.objects.filter(
        organizing_organization_id__in=all_org_ids
    ).distinct().select_related('organizing_organization').annotate(
        registrations_count=Count('registrations')
    ).order_by('-start_date')

    for c in competitions:
        # Competition a title, pas name
        comp_name = c.title if hasattr(c, 'title') else (c.name if hasattr(c, 'name') else '')
        # Competition a venue_name, pas location
        location = c.venue_name if hasattr(c, 'venue_name') else (c.location if hasattr(c, 'location') else '')
        org_name = c.organizing_organization.name if c.organizing_organization else ''
        writer.writerow([
            comp_name,
            c.start_date.strftime('%d/%m/%Y') if c.start_date else '',
            location,
            org_name,
            c.registrations_count,
            c.status or '',
        ])

    return response


@login_required
def export_results_csv(request, federation_id):
    """Export des résultats de compétitions en CSV"""
    federation = get_object_or_404(Federation, id=federation_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="resultats_{federation.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Compétition', 'Date', 'Catégorie', 'Participant', 'Club', 'Classement'])

    # Récupérer les IDs des organisations affiliées + la fédération elle-même
    affiliated_org_ids = get_affiliated_org_ids(federation)
    all_org_ids = list(affiliated_org_ids)
    if federation.organization:
        all_org_ids.append(federation.organization.id)

    # Utiliser CompetitionResult qui a le champ rank (pas CompetitionRegistration)
    from ...models import CompetitionResult
    results = CompetitionResult.objects.filter(
        competition__organizing_organization_id__in=all_org_ids,
        rank__isnull=False
    ).select_related('competition', 'practitioner', 'practitioner__organization', 'category').order_by(
        'competition__start_date', 'category__name', 'rank'
    )

    for r in results:
        org_name = ''
        if r.practitioner and r.practitioner.organization:
            org_name = r.practitioner.organization.name
        # Competition a 'title' pas 'name'
        comp_title = r.competition.title if r.competition else ''
        writer.writerow([
            comp_title,
            r.competition.start_date.strftime('%d/%m/%Y') if r.competition and r.competition.start_date else '',
            r.category.name if r.category else '',
            f"{r.practitioner.first_name} {r.practitioner.last_name}" if r.practitioner else '',
            org_name,
            r.rank,
        ])

    return response


@login_required
def export_judges_csv(request, federation_id):
    """Export des juges en CSV"""
    federation = get_object_or_404(Federation, id=federation_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="juges_{federation.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nom', 'Prénom', 'Club', 'Niveau', 'Date certification', 'Expérience', 'Statut'])

    # Récupérer les IDs des organisations affiliées
    affiliated_org_ids = get_affiliated_org_ids(federation)

    # Filtrer les juges via leur practitioner.organization
    judges = Judge.objects.filter(
        practitioner__organization_id__in=affiliated_org_ids
    ).distinct().select_related('user', 'practitioner', 'practitioner__organization')

    for j in judges:
        org_name = ''
        if j.practitioner and j.practitioner.organization:
            org_name = j.practitioner.organization.name
        writer.writerow([
            j.user.last_name if j.user else (j.practitioner.last_name if j.practitioner else ''),
            j.user.first_name if j.user else (j.practitioner.first_name if j.practitioner else ''),
            org_name,
            j.get_qualification_level_display() if hasattr(j, 'get_qualification_level_display') else (j.qualification_level or ''),
            j.certified_since.strftime('%d/%m/%Y') if j.certified_since else '',
            f"{j.years_experience} ans" if j.years_experience else '',
            'Actif' if j.active else 'Inactif',
        ])

    return response


@login_required
def export_certificates_csv(request, federation_id):
    """Export des certificats émis en CSV"""
    federation = get_object_or_404(Federation, id=federation_id)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="certificats_{federation.name}_{timezone.now().strftime("%Y%m%d")}.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Numéro', 'Bénéficiaire', 'Type', 'Titre', 'Date émission', 'Validité', 'Statut'])

    try:
        from ...models import IssuedCertificate
        certificates = IssuedCertificate.objects.filter(
            organization=federation
        ).order_by('-issue_date')

        for cert in certificates:
            writer.writerow([
                cert.certificate_number,
                cert.recipient_name,
                cert.certification_type or '',
                cert.title or '',
                cert.issue_date.strftime('%d/%m/%Y') if cert.issue_date else '',
                cert.valid_until.strftime('%d/%m/%Y') if cert.valid_until else 'Illimité',
                cert.get_status_display() if hasattr(cert, 'get_status_display') else cert.status,
            ])
    except Exception as e:
        logger.error(f"Erreur export certificats: {e}")

    return response


@login_required
def federation_manage_grades(request, federation_id):
    """
    Tableau de bord des grades pour les fédérations.
    Affiche les pratiquants et leurs grades de tous les clubs affiliés.
    """
    from django.core.paginator import Paginator
    from apps.grades.models import Grade, GradeCategory

    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    has_access = False
    if request.user == federation.owner:
        has_access = True
    elif hasattr(federation, 'administrators'):
        has_access = federation.administrators.filter(user=request.user).exists()

    if not has_access and hasattr(request.user, 'is_staff') and request.user.is_staff:
        has_access = True

    if not has_access:
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les IDs des organisations affiliées
    affiliated_org_ids = get_affiliated_org_ids(federation)
    affiliated_clubs = get_affiliated_clubs(federation)

    # Récupérer tous les pratiquants des clubs affiliés
    practitioners = Practitioner.objects.filter(
        organization_id__in=affiliated_org_ids
    ).select_related('organization', 'user', 'grade').prefetch_related('disciplines')

    # Filtrer par club si demandé
    club_filter = request.GET.get('club', '')
    if club_filter:
        practitioners = practitioners.filter(organization_id=club_filter)

    # Filtrer par discipline si demandé
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        try:
            discipline = Discipline.objects.get(id=discipline_id)
            practitioners = practitioners.filter(disciplines=discipline)
        except Discipline.DoesNotExist:
            pass

    # Filtrer par statut de grade si demandé
    # Practitioner utilise 'grade' (ForeignKey) et 'grade_text' (CharField)
    grade_status = request.GET.get('grade_status')
    if grade_status:
        if grade_status == 'with_grade':
            # Pratiquants avec un grade FK ou un grade_text
            practitioners = practitioners.filter(
                Q(grade__isnull=False) | ~Q(grade_text='')
            ).exclude(grade_text__isnull=True)
        elif grade_status == 'without_grade':
            # Pratiquants sans grade FK et sans grade_text
            practitioners = practitioners.filter(
                Q(grade__isnull=True) & (Q(grade_text__isnull=True) | Q(grade_text=''))
            )

    # Filtrer par nom si recherche
    search_query = request.GET.get('q')
    if search_query:
        practitioners = practitioners.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(license_number__icontains=search_query)
        )

    # Statistiques - utiliser grade (FK) et grade_text
    total_practitioners = practitioners.count()
    with_grade = practitioners.filter(
        Q(grade__isnull=False) | (~Q(grade_text='') & ~Q(grade_text__isnull=True))
    ).count()
    without_grade = total_practitioners - with_grade

    # Statistiques par grade
    grade_distribution = {}
    for p in practitioners.select_related('grade'):
        # Priorité au grade FK, sinon grade_text
        grade_name = None
        if p.grade:
            grade_name = str(p.grade.name) if hasattr(p.grade, 'name') else str(p.grade)
        elif p.grade_text:
            grade_name = p.grade_text

        if grade_name:
            grade_distribution[grade_name] = grade_distribution.get(grade_name, 0) + 1

    # Pagination
    paginator = Paginator(practitioners.order_by('organization__name', 'last_name', 'first_name'), 25)
    page = request.GET.get('page')
    practitioners_page = paginator.get_page(page)

    # Récupérer les disciplines de la fédération pour les filtres
    disciplines = federation.disciplines.all() if federation.disciplines.exists() else Discipline.objects.filter(is_active=True)

    # Récupérer les catégories de grades disponibles
    grade_categories = []
    try:
        grade_categories = GradeCategory.objects.filter(is_active=True).order_by('order')
    except:
        pass

    context = {
        'title': _('Examens & Grades'),
        'federation': federation,
        'practitioners': practitioners_page,
        'affiliated_clubs': affiliated_clubs,
        'disciplines': disciplines,
        'grade_categories': grade_categories,
        'total_practitioners': total_practitioners,
        'with_grade': with_grade,
        'without_grade': without_grade,
        'grade_distribution': grade_distribution,
        'selected_club': club_filter,
        'selected_discipline': discipline_id,
        'selected_grade_status': grade_status,
        'search_query': search_query,
    }
    return render(request, 'competitions/dashboard/federation_grades.html', context)


# =============================================================================
# VUES ENTRAINEMENT FEDERATION
# =============================================================================

@login_required
def federation_training_programs(request, federation_id):
    """Liste des programmes d'entraînement de la fédération."""
    from django.core.paginator import Paginator
    from ...models import TrainingProgram

    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les programmes d'entraînement
    # Les programmes peuvent être liés à la fédération ou aux clubs affiliés
    affiliated_org_ids = get_affiliated_org_ids(federation)

    programs = TrainingProgram.objects.filter(
        is_active=True
    ).prefetch_related('disciplines', 'modules').order_by('-created_at')

    # Filtres
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        programs = programs.filter(disciplines__id=discipline_id)

    search_query = request.GET.get('q')
    if search_query:
        programs = programs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(programs, 12)
    page = request.GET.get('page')
    programs_page = paginator.get_page(page)

    # Disciplines pour le filtre
    disciplines = federation.disciplines.filter(is_active=True).order_by('name')

    context = {
        'title': _('Programmes d\'entraînement'),
        'federation': federation,
        'programs': programs_page,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
        'search_query': search_query,
    }
    return render(request, 'competitions/dashboard/federation_training_programs.html', context)


@login_required
def federation_create_training_program(request, federation_id):
    """Créer un nouveau programme d'entraînement pour la fédération."""
    from ...models import TrainingProgram
    from ...forms.trainings import TrainingProgramForm

    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:index')

    if request.method == 'POST':
        form = TrainingProgramForm(request.POST)
        if form.is_valid():
            program = form.save(commit=False)
            program.created_by = request.user
            # Associer le programme à la fédération si le modèle le permet
            if hasattr(program, 'federation'):
                program.federation = federation
            program.save()
            form.save_m2m()

            messages.success(request, _("Le programme d'entraînement a été créé avec succès."))
            return redirect('competitions:federations:training_programs', federation_id=federation_id)
    else:
        form = TrainingProgramForm()
        # Filtrer les disciplines par celles de la fédération
        form.fields['disciplines'].queryset = federation.disciplines.filter(is_active=True)

    context = {
        'title': _('Créer un programme'),
        'federation': federation,
        'form': form,
    }
    return render(request, 'competitions/dashboard/federation_create_training_program.html', context)


@login_required
def federation_training_sessions(request, federation_id):
    """Liste des sessions d'entraînement de la fédération."""
    from django.core.paginator import Paginator
    from ...models import TrainingSession, TrainingSlot
    from django.db.models import Count

    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les clubs affiliés
    affiliated_clubs = get_affiliated_clubs(federation)

    # Récupérer les sessions des clubs affiliés
    sessions = TrainingSession.objects.filter(
        training_slot__club__in=affiliated_clubs
    ).select_related(
        'training_slot',
        'training_slot__club',
        'training_slot__discipline',
        'actual_instructor'
    ).annotate(
        attendance_count=Count('attendances')
    ).order_by('-date')

    # Filtres
    club_filter = request.GET.get('club')
    if club_filter:
        sessions = sessions.filter(training_slot__club_id=club_filter)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        sessions = sessions.filter(date__gte=date_from)
    if date_to:
        sessions = sessions.filter(date__lte=date_to)

    # Pagination
    paginator = Paginator(sessions, 20)
    page = request.GET.get('page')
    sessions_page = paginator.get_page(page)

    context = {
        'title': _('Sessions d\'entraînement'),
        'federation': federation,
        'sessions': sessions_page,
        'affiliated_clubs': affiliated_clubs,
        'selected_club': club_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'competitions/dashboard/federation_training_sessions.html', context)


@login_required
def federation_create_training_session(request, federation_id):
    """Créer une nouvelle session d'entraînement."""
    from ...models import TrainingSession, TrainingSlot, Attendance, Practitioner
    from django.utils import timezone

    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les clubs affiliés
    affiliated_clubs = get_affiliated_clubs(federation)

    # Récupérer les créneaux d'entraînement des clubs affiliés
    training_slots = TrainingSlot.objects.filter(
        club__in=affiliated_clubs,
        is_active=True
    ).select_related('club', 'discipline', 'instructor')

    if request.method == 'POST':
        training_slot_id = request.POST.get('training_slot')
        date = request.POST.get('date')
        notes = request.POST.get('notes', '')

        if training_slot_id and date:
            try:
                training_slot = TrainingSlot.objects.get(
                    id=training_slot_id,
                    club__in=affiliated_clubs
                )

                session = TrainingSession.objects.create(
                    training_slot=training_slot,
                    date=date,
                    notes=notes
                )

                # Créer les entrées de présence pour les pratiquants du club
                club_org = training_slot.club.organization or getattr(training_slot.club, 'as_organization', None)
                if club_org:
                    practitioners = Practitioner.objects.filter(
                        organization=club_org,
                        is_active=True
                    )
                    for practitioner in practitioners:
                        Attendance.objects.create(
                            session=session,
                            practitioner=practitioner,
                            status='absent',
                            recorded_by=request.user
                        )

                messages.success(request, _("La session d'entraînement a été créée."))
                return redirect('competitions:federations:training_sessions', federation_id=federation_id)

            except TrainingSlot.DoesNotExist:
                messages.error(request, _("Créneau d'entraînement invalide."))
        else:
            messages.error(request, _("Veuillez remplir tous les champs requis."))

    context = {
        'title': _('Créer une session'),
        'federation': federation,
        'training_slots': training_slots,
        'affiliated_clubs': affiliated_clubs,
        'today': timezone.now().date(),
    }
    return render(request, 'competitions/dashboard/federation_create_training_session.html', context)


@login_required
def federation_training_slots(request, federation_id):
    """Liste des créneaux d'entraînement de la fédération."""
    from django.core.paginator import Paginator
    from ...models import TrainingSlot

    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les clubs affiliés
    affiliated_clubs = get_affiliated_clubs(federation)

    # Récupérer les créneaux des clubs affiliés
    slots = TrainingSlot.objects.filter(
        club__in=affiliated_clubs
    ).select_related('club', 'discipline', 'instructor').order_by('club__name', 'day_of_week', 'start_time')

    # Filtres
    club_filter = request.GET.get('club')
    if club_filter:
        slots = slots.filter(club_id=club_filter)

    active_only = request.GET.get('active', 'true') == 'true'
    if active_only:
        slots = slots.filter(is_active=True)

    # Pagination
    paginator = Paginator(slots, 20)
    page = request.GET.get('page')
    slots_page = paginator.get_page(page)

    context = {
        'title': _('Créneaux d\'entraînement'),
        'federation': federation,
        'slots': slots_page,
        'affiliated_clubs': affiliated_clubs,
        'selected_club': club_filter,
        'active_only': active_only,
    }
    return render(request, 'competitions/dashboard/federation_training_slots.html', context)


@login_required
def federation_create_training_slot(request, federation_id):
    """Créer un nouveau créneau d'entraînement."""
    from ...models import TrainingSlot
    from ...forms.trainings import TrainingSlotForm

    federation = get_object_or_404(Federation, id=federation_id)

    # Vérifier les permissions
    if not _user_can_access_federation(request.user, federation):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à cette fédération."))
        return redirect('competitions:dashboard:index')

    # Récupérer les clubs affiliés
    affiliated_clubs = get_affiliated_clubs(federation)

    if request.method == 'POST':
        club_id = request.POST.get('club')

        if club_id:
            try:
                club = Club.objects.get(id=club_id, id__in=affiliated_clubs.values_list('id', flat=True))
                form = TrainingSlotForm(request.POST, club=club)

                if form.is_valid():
                    slot = form.save(commit=False)
                    slot.club = club
                    slot.save()

                    messages.success(request, _("Le créneau d'entraînement a été créé avec succès."))
                    return redirect('competitions:federations:training_slots', federation_id=federation_id)
            except Club.DoesNotExist:
                messages.error(request, _("Club invalide."))
                form = TrainingSlotForm()
        else:
            messages.error(request, _("Veuillez sélectionner un club."))
            form = TrainingSlotForm()
    else:
        form = TrainingSlotForm()
        # Filtrer les disciplines
        form.fields['discipline'].queryset = federation.disciplines.filter(is_active=True)

    context = {
        'title': _('Créer un créneau'),
        'federation': federation,
        'form': form,
        'affiliated_clubs': affiliated_clubs,
    }
    return render(request, 'competitions/dashboard/federation_create_training_slot.html', context)