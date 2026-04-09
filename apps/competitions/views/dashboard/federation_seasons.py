"""
Vues pour la gestion des saisons et affiliations saisonnières côté fédération.
"""
from datetime import date
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.core.paginator import Paginator

import logging

from apps.competitions.models import Federation
from apps.organizations.models import (
    Organization,
    Affiliation,
    SportSeason,
    AffiliationFeeConfiguration,
    AffiliationPeriod,
    AffiliationPeriodStatus,
    AffiliationRenewalRequest,
    AffiliationRenewalRequestStatus,
    AffiliationType,
)
from apps.organizations.services import (
    AffiliationSeasonService,
    AffiliationInvoiceService,
)

logger = logging.getLogger(__name__)


def get_federation_organization(federation):
    """Récupère l'organisation associée à une fédération."""
    if hasattr(federation, 'organization') and federation.organization:
        return federation.organization
    # Chercher par old_federation_id
    return Organization.objects.filter(old_federation_id=federation.id).first()


@login_required
def manage_seasons(request, federation_id):
    """
    Liste et gestion des saisons sportives d'une fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    if not organization:
        messages.error(request, _("Organisation non trouvée pour cette fédération."))
        return redirect('competitions:dashboard:federation', federation_id=federation_id)

    seasons = SportSeason.objects.filter(organization=organization).order_by('-start_date')

    # Statistiques par saison
    season_stats = []
    for season in seasons:
        active_count = AffiliationPeriod.objects.filter(
            season=season,
            status=AffiliationPeriodStatus.ACTIVE
        ).count()
        pending_count = AffiliationPeriod.objects.filter(
            season=season,
            status=AffiliationPeriodStatus.PENDING_PAYMENT
        ).count()
        total_revenue = AffiliationPeriod.objects.filter(
            season=season,
            status=AffiliationPeriodStatus.ACTIVE
        ).aggregate(total=models.Sum('paid_amount'))['total'] or Decimal('0.00')

        season_stats.append({
            'season': season,
            'active_count': active_count,
            'pending_count': pending_count,
            'total_revenue': total_revenue,
        })

    context = {
        'federation': federation,
        'organization': organization,
        'season_stats': season_stats,
        'title': _("Gestion des saisons")
    }

    return render(request, 'competitions/dashboard/federation_seasons.html', context)


@login_required
def create_season(request, federation_id):
    """
    Création d'une nouvelle saison sportive.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    if not organization:
        messages.error(request, _("Organisation non trouvée pour cette fédération."))
        return redirect('competitions:dashboard:federation', federation_id=federation_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        reminder_days = request.POST.get('reminder_days', 30)
        is_current = request.POST.get('is_current') == 'on'

        # Validation
        errors = []
        if not name:
            errors.append(_("Le nom de la saison est requis."))

        try:
            start_date = date.fromisoformat(start_date_str)
        except (ValueError, TypeError):
            errors.append(_("Date de début invalide."))
            start_date = None

        try:
            end_date = date.fromisoformat(end_date_str)
        except (ValueError, TypeError):
            errors.append(_("Date de fin invalide."))
            end_date = None

        if start_date and end_date and start_date >= end_date:
            errors.append(_("La date de début doit être avant la date de fin."))

        try:
            reminder_days = int(reminder_days)
            if reminder_days < 0:
                errors.append(_("Le nombre de jours de rappel doit être positif."))
        except (ValueError, TypeError):
            reminder_days = 30

        # Vérifier unicité du nom
        if SportSeason.objects.filter(organization=organization, name=name).exists():
            errors.append(_("Une saison avec ce nom existe déjà."))

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                season = AffiliationSeasonService.create_season(
                    organization=organization,
                    name=name,
                    start_date=start_date,
                    end_date=end_date,
                    renewal_reminder_days=reminder_days,
                    is_current=is_current
                )
                messages.success(
                    request,
                    _("Saison '%(name)s' créée avec succès.") % {'name': name}
                )
                return redirect(
                    'competitions:dashboard:federation_manage_fees',
                    federation_id=federation_id,
                    season_id=season.id
                )
            except Exception as e:
                logger.error(f"Erreur création saison: {e}")
                messages.error(request, _("Erreur lors de la création de la saison."))

    # Suggestion de nom pour la prochaine saison
    current_year = timezone.now().year
    suggested_name = AffiliationSeasonService.generate_season_name(current_year)
    start_date_default, end_date_default = AffiliationSeasonService.get_default_season_dates(
        current_year
    )

    context = {
        'federation': federation,
        'organization': organization,
        'suggested_name': suggested_name,
        'start_date_default': start_date_default.isoformat(),
        'end_date_default': end_date_default.isoformat(),
        'title': _("Créer une saison")
    }

    return render(request, 'competitions/dashboard/federation_season_form.html', context)


@login_required
def edit_season(request, federation_id, season_id):
    """
    Modification d'une saison sportive existante.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)
    season = get_object_or_404(SportSeason, id=season_id, organization=organization)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        reminder_days = request.POST.get('reminder_days', 30)
        is_current = request.POST.get('is_current') == 'on'

        errors = []
        try:
            start_date = date.fromisoformat(start_date_str)
        except (ValueError, TypeError):
            errors.append(_("Date de début invalide."))
            start_date = season.start_date

        try:
            end_date = date.fromisoformat(end_date_str)
        except (ValueError, TypeError):
            errors.append(_("Date de fin invalide."))
            end_date = season.end_date

        try:
            reminder_days = int(reminder_days)
        except (ValueError, TypeError):
            reminder_days = 30

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            season.name = name or season.name
            season.start_date = start_date
            season.end_date = end_date
            season.renewal_reminder_days = reminder_days
            season.is_current = is_current
            season.save()

            messages.success(request, _("Saison mise à jour avec succès."))
            return redirect(
                'competitions:dashboard:federation_seasons',
                federation_id=federation_id
            )

    context = {
        'federation': federation,
        'organization': organization,
        'season': season,
        'title': _("Modifier la saison")
    }

    return render(request, 'competitions/dashboard/federation_season_form.html', context)


@login_required
def manage_fees(request, federation_id, season_id):
    """
    Gestion des tarifs d'affiliation pour une saison.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)
    season = get_object_or_404(SportSeason, id=season_id, organization=organization)

    if request.method == 'POST':
        # Traiter les tarifs pour chaque type d'affiliation
        for aff_type, label in AffiliationType.choices:
            amount_key = f'amount_{aff_type}'
            tax_key = f'tax_{aff_type}'
            desc_key = f'description_{aff_type}'
            active_key = f'active_{aff_type}'

            amount_str = request.POST.get(amount_key, '0')
            tax_str = request.POST.get(tax_key, '0')
            description = request.POST.get(desc_key, '')
            is_active = request.POST.get(active_key) == 'on'

            try:
                amount = Decimal(amount_str.replace(',', '.'))
                tax_rate = Decimal(tax_str.replace(',', '.'))
            except InvalidOperation:
                continue

            # Créer ou mettre à jour la configuration
            fee_config, created = AffiliationFeeConfiguration.objects.update_or_create(
                organization=organization,
                season=season,
                affiliation_type=aff_type,
                defaults={
                    'amount': amount,
                    'tax_rate': tax_rate,
                    'description': description,
                    'is_active': is_active
                }
            )

        messages.success(request, _("Tarifs enregistrés avec succès."))
        return redirect(
            'competitions:dashboard:federation_seasons',
            federation_id=federation_id
        )

    # Récupérer les configurations existantes
    fee_configs = {
        fc.affiliation_type: fc
        for fc in AffiliationFeeConfiguration.objects.filter(
            organization=organization,
            season=season
        )
    }

    # Préparer les données pour le formulaire
    affiliation_types = []
    for aff_type, label in AffiliationType.choices:
        config = fee_configs.get(aff_type)
        affiliation_types.append({
            'type': aff_type,
            'label': label,
            'amount': config.amount if config else Decimal('0.00'),
            'tax_rate': config.tax_rate if config else Decimal('0.00'),
            'description': config.description if config else '',
            'is_active': config.is_active if config else True,
        })

    context = {
        'federation': federation,
        'organization': organization,
        'season': season,
        'affiliation_types': affiliation_types,
        'title': _("Tarifs d'affiliation - %(season)s") % {'season': season.name}
    }

    return render(request, 'competitions/dashboard/federation_fees.html', context)


@login_required
def renewal_requests(request, federation_id):
    """
    Liste des demandes de renouvellement d'affiliation.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    if not organization:
        messages.error(request, _("Organisation non trouvée."))
        return redirect('competitions:dashboard:federation', federation_id=federation_id)

    # Récupérer les demandes de renouvellement
    pending_requests = AffiliationRenewalRequest.objects.filter(
        affiliation__parent_organization=organization,
        status=AffiliationRenewalRequestStatus.PENDING
    ).select_related(
        'affiliation',
        'affiliation__child_organization',
        'from_period',
        'to_season',
        'requested_by'
    ).order_by('-requested_at')

    processed_requests = AffiliationRenewalRequest.objects.filter(
        affiliation__parent_organization=organization
    ).exclude(
        status=AffiliationRenewalRequestStatus.PENDING
    ).select_related(
        'affiliation',
        'affiliation__child_organization',
        'from_period',
        'to_season',
        'requested_by',
        'processed_by'
    ).order_by('-processed_at')[:20]

    context = {
        'federation': federation,
        'organization': organization,
        'pending_requests': pending_requests,
        'processed_requests': processed_requests,
        'title': _("Demandes de renouvellement")
    }

    return render(
        request,
        'competitions/dashboard/federation_renewal_requests.html',
        context
    )


@login_required
@require_POST
def process_renewal_request(request, federation_id, request_id):
    """
    Traite une demande de renouvellement (approuver/refuser).
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    renewal_request = get_object_or_404(
        AffiliationRenewalRequest,
        id=request_id,
        affiliation__parent_organization=organization
    )

    action = request.POST.get('action')
    reason = request.POST.get('reason', '')

    try:
        if action == 'approve':
            AffiliationSeasonService.approve_renewal_request(
                renewal_request=renewal_request,
                processed_by=request.user
            )
            messages.success(
                request,
                _("Demande de renouvellement approuvée. Une facture a été générée.")
            )
        elif action == 'reject':
            AffiliationSeasonService.reject_renewal_request(
                renewal_request=renewal_request,
                processed_by=request.user,
                reason=reason
            )
            messages.success(request, _("Demande de renouvellement refusée."))
        else:
            messages.error(request, _("Action non reconnue."))

    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        logger.error(f"Erreur traitement demande renouvellement: {e}")
        messages.error(request, _("Une erreur est survenue."))

    return redirect(
        'competitions:dashboard:federation_renewal_requests',
        federation_id=federation_id
    )


@login_required
def affiliation_invoices(request, federation_id):
    """
    Liste des factures d'affiliation émises par la fédération.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    if not organization:
        messages.error(request, _("Organisation non trouvée."))
        return redirect('competitions:dashboard:federation', federation_id=federation_id)

    # Périodes avec factures
    periods_with_invoices = AffiliationPeriod.objects.filter(
        affiliation__parent_organization=organization,
        invoice__isnull=False
    ).select_related(
        'affiliation',
        'affiliation__child_organization',
        'season',
        'invoice'
    ).order_by('-created_at')

    # Périodes en attente sans facture
    periods_pending = AffiliationPeriod.objects.filter(
        affiliation__parent_organization=organization,
        status=AffiliationPeriodStatus.PENDING_PAYMENT,
        invoice__isnull=True
    ).select_related(
        'affiliation',
        'affiliation__child_organization',
        'season'
    ).order_by('-created_at')

    # Pagination
    paginator = Paginator(periods_with_invoices, 20)
    page = request.GET.get('page', 1)
    periods_page = paginator.get_page(page)

    context = {
        'federation': federation,
        'organization': organization,
        'periods_page': periods_page,
        'periods_pending': periods_pending,
        'title': _("Factures d'affiliation")
    }

    return render(
        request,
        'competitions/dashboard/federation_affiliation_invoices.html',
        context
    )


@login_required
@require_POST
def generate_invoice(request, federation_id, period_id):
    """
    Génère une facture pour une période d'affiliation.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    period = get_object_or_404(
        AffiliationPeriod,
        id=period_id,
        affiliation__parent_organization=organization
    )

    try:
        invoice = AffiliationInvoiceService.generate_invoice(period)
        messages.success(
            request,
            _("Facture %(number)s générée avec succès.") % {
                'number': invoice.invoice_number
            }
        )
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        logger.error(f"Erreur génération facture: {e}")
        messages.error(request, _("Erreur lors de la génération de la facture."))

    return redirect(
        'competitions:dashboard:federation_affiliation_invoices',
        federation_id=federation_id
    )


@login_required
@require_POST
def record_affiliation_payment(request, federation_id, period_id):
    """
    Enregistre un paiement pour une période d'affiliation.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    period = get_object_or_404(
        AffiliationPeriod,
        id=period_id,
        affiliation__parent_organization=organization
    )

    amount_str = request.POST.get('amount', '0')
    payment_method = request.POST.get('payment_method', '')
    reference = request.POST.get('reference', '')

    try:
        amount = Decimal(amount_str.replace(',', '.'))
        if amount <= 0:
            raise ValueError(_("Le montant doit être positif."))

        AffiliationInvoiceService.record_payment(
            affiliation_period=period,
            amount=amount,
            payment_method=payment_method,
            reference=reference
        )
        messages.success(
            request,
            _("Paiement de %(amount)s€ enregistré.") % {'amount': amount}
        )
    except (InvalidOperation, ValueError) as e:
        messages.error(request, str(e))
    except Exception as e:
        logger.error(f"Erreur enregistrement paiement: {e}")
        messages.error(request, _("Erreur lors de l'enregistrement du paiement."))

    return redirect(
        'competitions:dashboard:federation_affiliation_invoices',
        federation_id=federation_id
    )


@login_required
def affiliation_periods(request, federation_id, affiliation_id):
    """
    Historique des périodes d'une affiliation spécifique.
    """
    federation = get_object_or_404(Federation, id=federation_id)
    organization = get_federation_organization(federation)

    affiliation = get_object_or_404(
        Affiliation,
        id=affiliation_id,
        parent_organization=organization
    )

    periods = AffiliationPeriod.objects.filter(
        affiliation=affiliation
    ).select_related('season', 'invoice').order_by('-season__start_date')

    context = {
        'federation': federation,
        'organization': organization,
        'affiliation': affiliation,
        'periods': periods,
        'title': _("Historique d'affiliation - %(club)s") % {
            'club': affiliation.child_organization.name
        }
    }

    return render(
        request,
        'competitions/dashboard/federation_affiliation_periods.html',
        context
    )


# Import models pour aggregate
from django.db import models
