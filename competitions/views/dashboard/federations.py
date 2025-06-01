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
from finances.models import PaymentAttempt, Invoice, Transaction
from shop.models import Order

# Imports de vos formulaires
from competitions.forms.federations import FederationForm

logger = logging.getLogger(__name__)

@login_required
@federation_admin_required
def federation_dashboard(request, federation_id):
    """
    Vue principale pour le tableau de bord d'une fédération.
    Affiche les statistiques et les actions disponibles pour une fédération.
    """
    # Si federation_id n'est pas fourni, essayer de trouver une fédération associée à l'utilisateur
    if federation_id is None:
        # Vérifier si l'utilisateur est administrateur d'une fédération
        user_federations = None
        
        # Vérifier via le modèle FederationAdministrator
        if hasattr(request.user, 'federation_admin_roles'):
            user_federations = Federation.objects.filter(
                administrators__user=request.user
            )
        
        # Vérifier via l'ancienne relation owner
        if not user_federations or not user_federations.exists():
            user_federations = Federation.objects.filter(owner=request.user)
            
        # Si l'utilisateur est associé à au moins une fédération, rediriger vers cette fédération
        if user_federations and user_federations.exists():
            federation = user_federations.first()
            return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
        else:
            # L'utilisateur n'est associé à aucune fédération, afficher un message
            messages.warning(request, _("Vous n'êtes associé à aucune fédération pour le moment."))
            # Rediriger vers la liste des fédérations ou la création
            return redirect('competitions:federations:list')
    
    # Récupérer la fédération par son ID
    federation = get_object_or_404(Federation, pk=federation_id)
    
    # Vérification que l'utilisateur a les droits sur cette fédération
    has_access = False
    
    # Vérifier via le rôle de l'utilisateur et la relation owner
    user_role = None
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'role'):
        user_role = request.user.profile.role
    
    if user_role == 'federation_admin' or request.user == federation.owner:
        has_access = True
    
    # Vérifier via FederationAdministrator
    if hasattr(request.user, 'federation_admin_roles'):
        is_admin = federation.administrators.filter(
            user=request.user
        ).exists()
        if is_admin:
            has_access = True
    
    if not has_access:
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les disciplines gérées par cette fédération
    disciplines = federation.disciplines.all()
    
    # Récupérer les statistiques en utilisant les relations correctes
    clubs_count = Club.objects.filter(federation=federation).count() if hasattr(Club, 'federation') else 0
    
    # Utiliser la relation via les disciplines pour accéder aux compétitions
    competitions = Competition.objects.filter(discipline__in=disciplines)
    competitions_count = competitions.count()
    
    # Récupérer les compétitions à venir
    now = timezone.now().date()
    upcoming_events = Competition.objects.filter(
        discipline__in=disciplines,
        status__in=['published', 'open'],
        start_date__gte=now
    ).count()
    
    # Utiliser le nouveau modèle Organization à la place de Club
    from organizations.models import Organization
    
    # Récupérer la représentation Organization de la fédération
    federation_org = federation.as_organization
    
    if federation_org:
        # Trouver les clubs affiliés en tant qu'Organizations
        affiliated_orgs = Organization.objects.filter(
            parent_affiliations__parent_organization=federation_org,
            organization_type='club'
        ).order_by('name')
        
        # Obtenir aussi les anciens clubs liés directement à la fédération si la relation existe encore
        if hasattr(Club, 'federation'):
            old_clubs = Club.objects.filter(federation=federation)
            old_club_orgs = []
            # Convertir les Club en Organization
            for club in old_clubs:
                club_org = club.as_organization
                if club_org:
                    old_club_orgs.append(club_org.id)
            
            # Ajouter ces clubs aux organizations si ne sont pas déjà inclus
            if old_club_orgs:
                additional_orgs = Organization.objects.filter(id__in=old_club_orgs)
                # Combine les querysets d'organisations
                affiliated_orgs = (affiliated_orgs | additional_orgs).distinct()
        
        participants_count = Practitioner.objects.filter(organization__in=affiliated_orgs).count()
    else:
        # Utiliser l'ancienne méthode avec les clubs
        if hasattr(Club, 'federation'):
            old_clubs = Club.objects.filter(federation=federation).order_by('name')
            # Convertir les Club en Organization pour éviter l'erreur
            affiliated_orgs = Organization.objects.filter(old_club_id__in=old_clubs.values_list('id', flat=True))
            participants_count = Practitioner.objects.filter(organization__in=affiliated_orgs).count()
        else:
            # Rechercher les clubs liés aux mêmes disciplines que la fédération
            old_clubs = Club.objects.filter(disciplines__in=disciplines).distinct().order_by('name')
            # Convertir les Club en Organization
            affiliated_orgs = Organization.objects.filter(old_club_id__in=old_clubs.values_list('id', flat=True))
            participants_count = Practitioner.objects.filter(organization__in=affiliated_orgs).count()
    
    # Pour la compatibilité avec le reste du code, conserver une variable nommée affiliated_clubs
    affiliated_clubs = affiliated_orgs
    
    # NOUVELLE SECTION: Récupérer les compétitions que cette fédération peut gérer
    competitions_to_manage = Competition.objects.none()
    
    try:
        # Compétitions où la fédération est organisatrice ou où l'utilisateur a un rôle de gestionnaire
        from ...models import CompetitionRole
        
        # Récupérer la représentation Organization de la fédération
        from organizations.models import Organization
        federation_org = federation.as_organization
        
        if federation_org:
            # Compétitions organisées par l'organisation de la fédération
            competitions_to_manage = Competition.objects.filter(
                Q(organizing_organization=federation_org) |  # Compétitions organisées par la fédération
                Q(roles__user=request.user, roles__role__in=['manager', 'owner', 'administrator'])  # Compétitions où l'utilisateur a un rôle de gestionnaire
            ).distinct().select_related('discipline').prefetch_related('registrations', 'categories')
        else:
            # Si pas d'organization correspondante, utiliser l'ancienne relation si elle existe
            competitions_to_manage = Competition.objects.filter(
                Q(federation=federation) |  # Ancienne relation si elle existe encore
                Q(roles__user=request.user, roles__role__in=['manager', 'owner', 'administrator'])  # Compétitions où l'utilisateur a un rôle de gestionnaire
            ).distinct().select_related('discipline').prefetch_related('registrations', 'categories')
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des compétitions à gérer: {str(e)}")
        # Fallback simple - prendre uniquement les compétitions de la fédération
        if hasattr(Competition, 'organizing_organization'):
            federation_org = federation.as_organization
            if federation_org:
                competitions_to_manage = Competition.objects.filter(organizing_organization=federation_org)
            else:
                competitions_to_manage = Competition.objects.filter(discipline__in=disciplines)
        elif hasattr(Competition, 'federation'):
            competitions_to_manage = Competition.objects.filter(federation=federation)
        else:
            competitions_to_manage = Competition.objects.filter(discipline__in=disciplines)
    
    # Récupérer les inscriptions récentes aux compétitions
    recent_registrations = CompetitionRegistration.objects.filter(
        practitioner__organization__in=affiliated_clubs,
        registration_date__gte=now - timezone.timedelta(days=30)
    ).order_by('-registration_date')[:5]
    
    # Récupérer les prochaines compétitions à superviser
    upcoming_competitions = Competition.objects.filter(
        discipline__in=disciplines,
        status__in=['published', 'open'],
        start_date__gte=now
    ).order_by('start_date')[:5]
    
    # Récupérer les compétitions actives (en cours)
    active_competitions = Competition.objects.filter(
        discipline__in=disciplines,
        status__in=['published', 'open'],
        start_date__lte=now,
        end_date__gte=now
    ).order_by('end_date')
    
    # Récupérer les demandes en attente (si le modèle existe)
    pending_requests = []
    try:
        from ...models import AffiliationRequest
        from organizations.models import Organization
        
        # Récupérer la représentation Organization de la fédération
        federation_org = federation.as_organization
        
        if federation_org:
            # Récupérer les demandes d'affiliation faites à l'organisation correspondant à cette fédération
            pending_requests = AffiliationRequest.objects.filter(
                target_organization=federation_org,
                status='pending'
            ).order_by('-created_at')[:5]
        else:
            # Si pas d'organisation correspondante, ne pas récupérer de demandes
            pending_requests = []
    except ImportError:
        pass
    
    # Récupérer l'activité récente
    recent_activity = []
    
    # Ajouter l'activité de création de fédération
    if hasattr(federation, 'created_at') and federation.created_at:
        recent_activity.append({
            'type': 'federation_created',
            'date': federation.created_at,
            'message': _("Fédération créée"),
            'entity': federation
        })
    
    # Ajouter les dernières inscriptions aux compétitions
    for registration in recent_registrations:
        recent_activity.append({
            'type': 'participant_registered',
            'date': registration.registration_date,
            'message': _("Inscription de {0} à {1}").format(
                registration.practitioner.full_name,
                registration.competition.title
            ),
            'entity': registration
        })
    
    # Ajouter les derniers clubs affiliés
    try:
        recent_clubs = affiliated_clubs.order_by('-created_at')[:3] if hasattr(Club, 'created_at') else []
        for club in recent_clubs:
            if hasattr(club, 'created_at') and club.created_at:  # Vérifier que le champ existe et n'est pas nul
                recent_activity.append({
                    'type': 'club_affiliated',
                    'date': club.created_at,
                    'message': _("Affiliation du club {0}").format(club.name),
                    'entity': club
                })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des clubs récents: {str(e)}")
    
    # Trier l'activité par date (la plus récente en premier)
    # Utiliser une fonction de tri sécurisée qui gère les dates nulles
    def sort_key(activity):
        date = activity.get('date')
        return date if date else timezone.now()
    
    recent_activity.sort(key=sort_key, reverse=True)
    recent_activity = recent_activity[:5]  # Limiter à 5 éléments
    
    # Obtenir les 5 premiers clubs pour l'affichage sur le dashboard
    displayed_clubs = affiliated_clubs[:5]
    
    # Compter les inscriptions par club
    club_registrations = {}
    for org in affiliated_clubs:
        count = CompetitionRegistration.objects.filter(
            practitioner__organization=org
        ).count()
        club_registrations[org.id] = count
    
    # Compter les juges
    judge_count = 0
    try:
        if hasattr(federation, 'judges'):
            judge_count = federation.judges.count()
        else:
            # Compter les juges
            judge_count = Judge.objects.filter(practitioner__organization__in=affiliated_clubs).count()
    except Exception as e:
        logger.error(f"Erreur lors du comptage des juges: {str(e)}")
    
    # NOUVELLES DONNÉES POUR LE SUIVI
    
    # Récupérer les commandes récentes de la boutique fédérale
    recent_orders = []
    try:
        from shop.models import Order
        if hasattr(federation, 'shop_products'):
            # Si la fédération a une boutique, récupérer les commandes
            recent_orders = Order.objects.filter(
                products__federation=federation
            ).distinct().order_by('-created_at')[:5]
        else:
            # Alternative : récupérer toutes les commandes liées aux clubs affiliés
            recent_orders = Order.objects.filter(
                user__practitioner__organization__in=affiliated_clubs
            ).distinct().order_by('-created_at')[:5]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commandes: {str(e)}")
    
    # Récupérer les paiements récents
    recent_payments = []
    payment_stats = {'total': 0, 'paid': 0, 'pending': 0}
    try:
        # Utiliser PaymentAttempt
        # Paiements liés à la fédération
        recent_payments = PaymentAttempt.objects.filter(
            Q(transaction__accounting_accounts__federation=federation) | 
            Q(transaction__club__federation=federation)
        ).order_by('-initiated_at')[:10]
        
        # Statistiques des paiements
        all_payments = PaymentAttempt.objects.filter(
            Q(transaction__accounting_accounts__federation=federation) | 
            Q(transaction__club__federation=federation)
        )
        payment_stats['total'] = all_payments.aggregate(total=models.Sum('amount'))['total'] or 0
        payment_stats['paid'] = all_payments.filter(status='succeeded').count()
        payment_stats['pending'] = all_payments.filter(status='pending').count()
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paiements: {str(e)}")
    
    # Récupérer les demandes d'affiliation en attente et récentes
    pending_affiliations = []
    recent_affiliations = []
    try:
        from organizations.models import AffiliationRequest, Affiliation
        federation_org = federation.as_organization
        
        if federation_org:
            # Demandes d'affiliation en attente
            pending_affiliations = AffiliationRequest.objects.filter(
                target_organization=federation_org,
                status='pending'
            ).order_by('-created_at')[:5]
            
            # Clubs récemment affiliés
            recent_affiliations = Affiliation.objects.filter(
                parent_organization=federation_org,
                child_organization__organization_type='club',
                status='active'
            ).order_by('-date_affiliated')[:5]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des affiliations: {str(e)}")
    
    # Récupérer les notifications
    recent_notifications = []
    unread_notifications = []
    try:
        from ...models import Notification
        # Notifications pour l'administrateur de la fédération
        all_notifications = Notification.objects.filter(
            user=request.user,
            federation=federation
        ).order_by('-created_at')
        
        recent_notifications = all_notifications[:10]
        unread_notifications = all_notifications.filter(is_read=False)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des notifications: {str(e)}")
    
    # Récupérer les tickets de support
    support_tickets = []
    support_stats = {'open': 0, 'in_progress': 0, 'resolved': 0, 'closed': 0}
    try:
        from ...models import SupportTicket
        # Tickets liés à la fédération
        support_tickets = SupportTicket.objects.filter(
            Q(federation=federation) |
            Q(club__federation=federation)
        ).order_by('-created_at')[:10]
        
        # Statistiques des tickets
        all_tickets = SupportTicket.objects.filter(
            Q(federation=federation) |
            Q(club__federation=federation)
        )
        support_stats['open'] = all_tickets.filter(status='open').count()
        support_stats['in_progress'] = all_tickets.filter(status='in_progress').count()
        support_stats['resolved'] = all_tickets.filter(status='resolved').count()
        support_stats['closed'] = all_tickets.filter(status='closed').count()
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tickets de support: {str(e)}")
    
    # Statistiques financières
    financial_stats = {
        'balance': 0,
        'income': 0,
        'expense': 0,
        'pending_invoices': 0
    }
    try:
        from finances.models import Invoice, Account
        # Compte de la fédération
        federation_account = Account.objects.filter(
            object_id=federation.id,
            content_type__model='federation'
        ).first()
        
        if federation_account:
            financial_stats['balance'] = federation_account.balance
            # Revenus (derniers 30 jours)
            last_month = now - timezone.timedelta(days=30)
            income_payments = PaymentAttempt.objects.filter(
                transaction__accounting_accounts=federation_account,
                status='succeeded',
                initiated_at__gte=last_month
            ).aggregate(total=models.Sum('amount'))
            financial_stats['income'] = income_payments['total'] or 0
            
            # Dépenses (derniers 30 jours)
            expense_payments = Transaction.objects.filter(
                accounting_accounts=federation_account,
                category__type='expense',
                created_at__gte=last_month
            ).aggregate(total=models.Sum('amount'))
            financial_stats['expense'] = expense_payments['total'] or 0
        
        # Factures en attente
        financial_stats['pending_invoices'] = Invoice.objects.filter(
            federation=federation,
            status='pending'
        ).count()
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques financières: {str(e)}")
    
    context = {
        'federation': federation,
        'disciplines': disciplines,
        'stats': {
            'clubs_count': clubs_count,
            'competitions_count': competitions_count,
            'upcoming_events': upcoming_events,
            'participants_count': participants_count,
            'judge_count': judge_count
        },
        'upcoming_competitions': upcoming_competitions,
        'active_competitions': active_competitions,
        'affiliated_clubs': displayed_clubs,
        'recent_activity': recent_activity,
        'club_registrations': club_registrations,
        
        # Variables pour le gestionnaire de compétition (NOUVEAU)
        'competitions_to_manage': competitions_to_manage,
        'pending_requests': pending_requests,
        
        # Nouvelles variables pour gérer l'inscription des participants
        'can_register_participants': True,  # Permet l'affichage du bouton d'inscription
        'total_clubs': affiliated_clubs.count(),  # Nombre total de clubs affiliés
        'recent_registrations': recent_registrations,  # Inscriptions récentes
        
        # Compteurs pour le sidebar
        'competition_count': competitions_count,
        'club_count': clubs_count,
        'practitioner_count': participants_count,
        
        # NOUVELLES DONNÉES POUR LE SUIVI
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'payment_stats': payment_stats,
        'pending_affiliations': pending_affiliations,
        'recent_affiliations': recent_affiliations,
        'recent_notifications': recent_notifications,
        'unread_notifications': unread_notifications,
        'support_tickets': support_tickets,
        'support_stats': support_stats,
        'financial_stats': financial_stats,
    }
    
    return render(request, 'competitions/dashboard/federation.html', context)


@login_required
def federation_manage_clubs(request, federation_id):
    """
    Vue pour gérer les clubs affiliés à une fédération.
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
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer tous les clubs affiliés à la fédération
    affiliated_clubs = Club.objects.filter(federation=federation).order_by('name')
    
    # Récupérer les clubs qui peuvent être affiliés
    available_clubs = Club.objects.filter(federation__isnull=True).order_by('name')
    
    context = {
        'federation': federation,
        'affiliated_clubs': affiliated_clubs,
        'available_clubs': available_clubs,
        'title': _("Gestion des clubs affiliés")
    }
    
    return render(request, 'competitions/federations/manage_clubs.html', context)


@login_required
def federation_competitions(request, federation_id):
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
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les compétitions de la fédération
    competitions = Competition.objects.filter(organizing_organization__federation=federation).order_by('-start_date')
    
    context = {
        'federation': federation,
        'competitions': competitions,
        'title': _("Gestion des compétitions")
    }
    
    return render(request, 'competitions/federations/competitions.html', context)


@login_required
def federation_judges(request, federation_id):
    """
    Vue pour gérer les juges certifiés d'une fédération.
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
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les juges certifiés par la fédération
    judges = Judge.objects.filter(federation=federation).order_by('practitioner__last_name')
    
    context = {
        'federation': federation,
        'judges': judges,
        'title': _("Juges certifiés")
    }
    
    return render(request, 'competitions/federations/judges.html', context)


@login_required
def federation_index(request):
    """
    Vue de la page d'index des fédérations pour un utilisateur.
    Affiche la liste des fédérations administrées par l'utilisateur.
    """
    # Récupérer les fédérations dont l'utilisateur est administrateur
    administered_federations = []
    
    try:
        # Vérifier les fédérations administrées via la relation FederationAdministrator
        administered_federations = Federation.objects.filter(
            administrators__user=request.user
        ).distinct()
        
        # Si l'utilisateur n'administre aucune fédération mais a le rôle, afficher toutes les fédérations
        if not administered_federations.exists() and hasattr(request.user, 'profile') and request.user.profile.role == 'federation_admin':
            # Vérifier s'il y a des fédérations dont l'utilisateur est propriétaire
            owned_federations = Federation.objects.filter(owner=request.user)
            
            if owned_federations.exists():
                administered_federations = owned_federations
            else:
                messages.info(request, _("Vous n'êtes associé à aucune fédération. Créez-en une pour commencer."))
                return redirect('competitions:federations:create')
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des fédérations administrées: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors de la récupération de vos fédérations."))
    
    context = {
        'administered_federations': administered_federations,
        'federation_count': administered_federations.count(),
    }
    
    return render(request, 'competitions/dashboard/federation_index.html', context)



# Vue pour afficher les competitions qu'une fédération peut gérer
@login_required
def federation_managed_competitions(request, federation_id):
    """
    Vue pour afficher toutes les compétitions qu'une fédération peut gérer.
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
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les compétitions à gérer
    try:
        from ...models import CompetitionRole
        
        competitions_to_manage = Competition.objects.filter(
            Q(federation=federation) |
            Q(roles__user=request.user, roles__role__in=['manager', 'owner', 'administrator'])
        ).distinct().order_by('-start_date')
    except:
        competitions_to_manage = Competition.objects.filter(organizing_organization__federation=federation).order_by('-start_date')
    
    context = {
        'federation': federation,
        'competitions_to_manage': competitions_to_manage,
        'title': _("Compétitions gérées")
    }
    
    return render(request, 'competitions/federations/managed_competitions.html', context)


@login_required
def federation_settings(request, federation_id):
    """
    Vue pour modifier les paramètres d'une fédération.
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
        messages.error(request, _("Vous n'avez pas les droits d'accès à cette fédération."))
        return redirect('competitions:dashboard:index')
    
    if request.method == 'POST':
        form = FederationForm(request.POST, request.FILES, instance=federation)
        if form.is_valid():
            form.save()
            messages.success(request, _("Les paramètres de la fédération ont été mis à jour avec succès."))
            return redirect('competitions:dashboard:federation', federation_id=federation.id)
    else:
        form = FederationForm(instance=federation)
    
    context = {
        'form': form,
        'federation': federation,
        'title': _("Paramètres de la fédération")
    }
    
    return render(request, 'competitions/federations/settings.html', context)

