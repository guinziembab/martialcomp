"""
Vues pour la gestion des affiliations côté club.
Permet aux clubs de répondre aux invitations de fédérations et de demander des affiliations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import connection
import logging

from ...models import Club
from apps.organizations.models import (
    Organization,
    Affiliation,
    SportSeason,
    AffiliationPeriod,
    AffiliationPeriodStatus,
    AffiliationRenewalRequest,
    AffiliationRenewalRequestStatus,
)
from apps.organizations.services import AffiliationSeasonService, AffiliationInvoiceService

logger = logging.getLogger(__name__)


def get_user_club(user):
    """Récupère le club de l'utilisateur connecté."""
    club = None

    # Méthode 1: Via attribut direct
    if hasattr(user, 'club_id') and user.club_id:
        club = Club.objects.filter(id=user.club_id).first()

    # Méthode 2: Via relation de propriété
    if not club:
        club = Club.objects.filter(owner=user).first()

    # Méthode 3: Via OrganizationMember
    if not club:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT c.id
                    FROM competitions_club c
                    INNER JOIN organizations_organizationmember om ON c.organization_id = om.organization_id
                    WHERE om.user_id = %s
                    LIMIT 1
                """, [user.id])
                row = cursor.fetchone()
                if row:
                    club = Club.objects.filter(id=row[0]).first()
        except Exception as e:
            logger.warning(f"Erreur récupération club via OrganizationMember: {e}")

    return club


@login_required
def affiliation_action(request):
    """
    Traite les actions d'affiliation (accepter/refuser une invitation).
    """
    logger.info(f"[AFFILIATION] affiliation_action called - method: {request.method}, user: {request.user}")

    if request.method != 'POST':
        logger.warning("[AFFILIATION] Not a POST request, redirecting")
        return redirect('competitions:dashboard:club')

    club = get_user_club(request.user)
    logger.info(f"[AFFILIATION] Club found: {club.name if club else 'None'}")

    if not club:
        messages.error(request, _("Club non trouvé."))
        return redirect('competitions:dashboard:club')

    if not club.organization:
        messages.error(request, _("Ce club n'a pas d'organisation associée."))
        logger.warning(f"[AFFILIATION] Club {club.name} has no organization")
        return redirect('competitions:dashboard:club')

    affiliation_id = request.POST.get('affiliation_id')
    action = request.POST.get('action')
    logger.info(f"[AFFILIATION] POST data - affiliation_id: {affiliation_id}, action: {action}")

    if not affiliation_id or not action:
        logger.warning(f"[AFFILIATION] Missing params - affiliation_id: {affiliation_id}, action: {action}")
        messages.error(request, _("Paramètres manquants."))
        return redirect('competitions:dashboard:club')

    try:
        logger.info(f"[AFFILIATION] Looking for affiliation id={affiliation_id}, child_org={club.organization_id}")
        affiliation = Affiliation.objects.get(
            id=affiliation_id,
            child_organization=club.organization
        )
        logger.info(f"[AFFILIATION] Found affiliation: {affiliation.id}")

        if action == 'accept':
            # Le club accepte l'invitation
            affiliation.child_status = 'approved'
            affiliation.child_approved_by = request.user
            affiliation.child_approved_at = timezone.now()

            # Vérifier si les deux parties ont approuvé
            if affiliation.parent_status == 'approved':
                affiliation.is_active = True
                affiliation.start_date = timezone.now().date()
                logger.info(f"[AFFILIATION] Both parties approved - activating affiliation {affiliation.id}")
                messages.success(request, _("Affiliation acceptée ! Vous êtes maintenant membre de cette fédération."))
            else:
                logger.info(f"[AFFILIATION] Club approved, waiting for federation approval")
                messages.success(request, _("Invitation acceptée. En attente de confirmation de la fédération."))

            affiliation.save()
            logger.info(f"[AFFILIATION] Saved - child_status: {affiliation.child_status}, is_active: {affiliation.is_active}")

        elif action == 'reject':
            # Le club refuse l'invitation
            affiliation.child_status = 'rejected'
            affiliation.is_active = False
            affiliation.save()
            messages.success(request, _("Invitation refusée."))

        else:
            messages.error(request, _("Action non reconnue."))

    except Affiliation.DoesNotExist:
        logger.error(f"[AFFILIATION] Affiliation not found - id={affiliation_id}, club_org={club.organization_id}")
        messages.error(request, _("Affiliation non trouvée."))
    except Exception as e:
        logger.error(f"[AFFILIATION] Exception: {e}", exc_info=True)
        messages.error(request, _("Une erreur est survenue."))

    return redirect('competitions:dashboard:club')


@login_required
def request_affiliation(request):
    """
    Affiche la liste des fédérations disponibles et permet de demander une affiliation.
    """
    club = get_user_club(request.user)
    if not club:
        messages.error(request, _("Club non trouvé."))
        return redirect('competitions:dashboard:club')

    if not club.organization:
        messages.error(request, _("Ce club n'a pas d'organisation associée."))
        return redirect('competitions:dashboard:club')

    # Traitement du POST (demande d'affiliation)
    if request.method == 'POST':
        federation_org_id = request.POST.get('federation_org_id')

        if federation_org_id:
            try:
                federation_org = Organization.objects.get(
                    id=federation_org_id,
                    organization_type='federation'
                )

                # Créer ou mettre à jour l'affiliation
                affiliation, created = Affiliation.objects.get_or_create(
                    parent_organization=federation_org,
                    child_organization=club.organization,
                    defaults={
                        'affiliation_type': 'member',
                        'initiated_by': 'child',
                        'parent_status': 'pending',
                        'child_status': 'approved',
                        'child_approved_by': request.user,
                        'child_approved_at': timezone.now(),
                        'is_active': False
                    }
                )

                if created:
                    messages.success(request, _("Demande d'affiliation envoyée à la fédération."))
                else:
                    if affiliation.is_active:
                        messages.info(request, _("Vous êtes déjà affilié à cette fédération."))
                    elif affiliation.parent_status == 'pending':
                        messages.info(request, _("Une demande est déjà en attente pour cette fédération."))
                    else:
                        # Relancer la demande
                        affiliation.initiated_by = 'child'
                        affiliation.parent_status = 'pending'
                        affiliation.child_status = 'approved'
                        affiliation.child_approved_by = request.user
                        affiliation.child_approved_at = timezone.now()
                        affiliation.save()
                        messages.success(request, _("Demande d'affiliation renvoyée."))

                return redirect('competitions:dashboard:club')

            except Organization.DoesNotExist:
                messages.error(request, _("Fédération non trouvée."))
            except Exception as e:
                logger.error(f"Erreur lors de la demande d'affiliation: {e}")
                messages.error(request, _("Une erreur est survenue."))

    # Récupérer les fédérations disponibles
    # Exclure celles où il y a déjà une affiliation active ou en attente
    existing_affiliations = Affiliation.objects.filter(
        child_organization=club.organization
    ).exclude(
        parent_status='rejected',
        child_status='rejected'
    ).values_list('parent_organization_id', flat=True)

    available_federations = Organization.objects.filter(
        organization_type='federation'
    ).exclude(
        id__in=existing_affiliations
    ).order_by('name')

    # Récupérer les affiliations en cours pour affichage
    pending_requests = Affiliation.objects.filter(
        child_organization=club.organization,
        initiated_by='child',
        child_status='approved',
        parent_status='pending',
        is_active=False
    ).select_related('parent_organization')

    active_affiliations = Affiliation.objects.filter(
        child_organization=club.organization,
        is_active=True
    ).select_related('parent_organization')

    context = {
        'club': club,
        'available_federations': available_federations,
        'pending_requests': pending_requests,
        'active_affiliations': active_affiliations,
        'title': _("Demander une affiliation")
    }

    return render(request, 'competitions/club/request_affiliation.html', context)


@login_required
def affiliation_history(request, affiliation_id):
    """
    Affiche l'historique des périodes d'affiliation pour une affiliation spécifique.
    """
    club = get_user_club(request.user)
    if not club:
        messages.error(request, _("Club non trouvé."))
        return redirect('competitions:dashboard:club')

    if not club.organization:
        messages.error(request, _("Ce club n'a pas d'organisation associée."))
        return redirect('competitions:dashboard:club')

    affiliation = get_object_or_404(
        Affiliation,
        id=affiliation_id,
        child_organization=club.organization
    )

    # Récupérer l'historique des périodes
    periods = AffiliationPeriod.objects.filter(
        affiliation=affiliation
    ).select_related('season', 'invoice').order_by('-season__start_date')

    # Récupérer les demandes de renouvellement en cours
    pending_renewals = AffiliationRenewalRequest.objects.filter(
        affiliation=affiliation,
        status=AffiliationRenewalRequestStatus.PENDING
    ).select_related('to_season')

    context = {
        'club': club,
        'affiliation': affiliation,
        'periods': periods,
        'pending_renewals': pending_renewals,
        'title': _("Historique d'affiliation - %(federation)s") % {
            'federation': affiliation.parent_organization.name
        }
    }

    return render(request, 'competitions/club/affiliation_history.html', context)


@login_required
def request_renewal(request, affiliation_id):
    """
    Permet au club de demander le renouvellement d'une affiliation.
    """
    club = get_user_club(request.user)
    if not club:
        messages.error(request, _("Club non trouvé."))
        return redirect('competitions:dashboard:club')

    if not club.organization:
        messages.error(request, _("Ce club n'a pas d'organisation associée."))
        return redirect('competitions:dashboard:club')

    affiliation = get_object_or_404(
        Affiliation,
        id=affiliation_id,
        child_organization=club.organization,
        is_active=True
    )

    # Récupérer les saisons disponibles pour le renouvellement
    federation_org = affiliation.parent_organization
    current_season = AffiliationSeasonService.get_current_season(federation_org)
    next_season = AffiliationSeasonService.get_next_season(federation_org)

    # Déterminer les saisons pour lesquelles on peut renouveler
    available_seasons = []

    if next_season:
        # Vérifier qu'il n'y a pas déjà une période pour cette saison
        existing_period = AffiliationPeriod.objects.filter(
            affiliation=affiliation,
            season=next_season
        ).exists()
        if not existing_period:
            available_seasons.append(next_season)

    if request.method == 'POST':
        season_id = request.POST.get('season_id')

        if season_id:
            try:
                season = SportSeason.objects.get(
                    id=season_id,
                    organization=federation_org
                )

                renewal_request = AffiliationSeasonService.renew_affiliation(
                    affiliation=affiliation,
                    new_season=season,
                    requested_by=request.user
                )

                messages.success(
                    request,
                    _("Demande de renouvellement envoyée pour la saison %(season)s.") % {
                        'season': season.name
                    }
                )
                return redirect('competitions:dashboard:club')

            except SportSeason.DoesNotExist:
                messages.error(request, _("Saison non trouvée."))
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error(f"Erreur demande renouvellement: {e}")
                messages.error(request, _("Une erreur est survenue."))

    context = {
        'club': club,
        'affiliation': affiliation,
        'current_season': current_season,
        'available_seasons': available_seasons,
        'title': _("Renouveler l'affiliation - %(federation)s") % {
            'federation': affiliation.parent_organization.name
        }
    }

    return render(request, 'competitions/club/request_renewal.html', context)


@login_required
def my_affiliation_invoices(request):
    """
    Affiche les factures d'affiliation du club.
    """
    club = get_user_club(request.user)
    if not club:
        messages.error(request, _("Club non trouvé."))
        return redirect('competitions:dashboard:club')

    if not club.organization:
        messages.error(request, _("Ce club n'a pas d'organisation associée."))
        return redirect('competitions:dashboard:club')

    # Récupérer toutes les périodes avec factures
    periods_with_invoices = AffiliationPeriod.objects.filter(
        affiliation__child_organization=club.organization,
        invoice__isnull=False
    ).select_related(
        'affiliation',
        'affiliation__parent_organization',
        'season',
        'invoice'
    ).order_by('-created_at')

    # Périodes en attente de paiement
    pending_periods = AffiliationPeriod.objects.filter(
        affiliation__child_organization=club.organization,
        status=AffiliationPeriodStatus.PENDING_PAYMENT
    ).select_related(
        'affiliation',
        'affiliation__parent_organization',
        'season',
        'invoice'
    ).order_by('-created_at')

    context = {
        'club': club,
        'periods_with_invoices': periods_with_invoices,
        'pending_periods': pending_periods,
        'title': _("Mes factures d'affiliation")
    }

    return render(request, 'competitions/club/my_affiliation_invoices.html', context)
