"""
Service de génération et gestion des factures d'affiliation.
"""
from decimal import Decimal
from typing import Optional, List
import logging

from django.db import transaction
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.organizations.models import (
    Organization,
    Affiliation,
    AffiliationPeriod,
    AffiliationPeriodStatus,
    AffiliationFeeConfiguration,
)
from apps.finances.models import Invoice, InvoiceItem

logger = logging.getLogger(__name__)


class AffiliationInvoiceService:
    """
    Service pour la génération et gestion des factures d'affiliation.
    """

    @staticmethod
    @transaction.atomic
    def generate_invoice(
        affiliation_period: AffiliationPeriod,
        description: Optional[str] = None
    ) -> Invoice:
        """
        Génère une facture pour une période d'affiliation.

        Args:
            affiliation_period: La période d'affiliation à facturer
            description: Description personnalisée (optionnel)

        Returns:
            Invoice: La facture générée

        Raises:
            ValueError: Si la période a déjà une facture
        """
        if affiliation_period.invoice:
            raise ValueError("Cette période a déjà une facture associée")

        affiliation = affiliation_period.affiliation
        federation = affiliation.parent_organization
        club = affiliation.child_organization

        # Récupérer les ContentTypes pour les relations génériques
        org_content_type = ContentType.objects.get_for_model(Organization)

        # Générer la description si non fournie
        if not description:
            description = (
                f"Cotisation d'affiliation {affiliation_period.season.name} - "
                f"{affiliation.get_affiliation_type_display()}"
            )

        # Créer la facture
        invoice = Invoice.objects.create(
            issuer_content_type=org_content_type,
            issuer_object_id=federation.id,
            recipient_content_type=org_content_type,
            recipient_object_id=club.id,
            status='issued',
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            notes=f"Affiliation {club.name} à {federation.name}"
        )

        # Récupérer les infos de tarification
        fee_config = AffiliationFeeConfiguration.objects.filter(
            organization=federation,
            season=affiliation_period.season,
            affiliation_type=affiliation.affiliation_type,
            is_active=True
        ).first()

        # Créer la ligne de facture
        if fee_config:
            amount = fee_config.amount
            tax_rate = fee_config.tax_rate
            item_description = fee_config.description or description
        else:
            amount = affiliation_period.amount
            tax_rate = Decimal('0.00')
            item_description = description

        InvoiceItem.objects.create(
            invoice=invoice,
            description=item_description,
            quantity=1,
            unit_price=amount,
            tax_rate=tax_rate
        )

        # Lier la facture à la période
        affiliation_period.invoice = invoice
        affiliation_period.save(update_fields=['invoice', 'updated_at'])

        logger.info(
            f"Facture {invoice.invoice_number} générée pour "
            f"{affiliation} - {affiliation_period.season.name}"
        )

        return invoice

    @staticmethod
    @transaction.atomic
    def record_payment(
        affiliation_period: AffiliationPeriod,
        amount: Decimal,
        payment_method: Optional[str] = None,
        reference: Optional[str] = None
    ) -> AffiliationPeriod:
        """
        Enregistre un paiement sur une période d'affiliation.

        Args:
            affiliation_period: La période concernée
            amount: Montant du paiement
            payment_method: Méthode de paiement (optionnel)
            reference: Référence du paiement (optionnel)

        Returns:
            AffiliationPeriod: La période mise à jour
        """
        affiliation_period.paid_amount += amount

        # Si paiement complet, marquer comme active
        if affiliation_period.is_paid:
            affiliation_period.status = AffiliationPeriodStatus.ACTIVE
            affiliation_period.payment_date = timezone.now()

            # Mettre à jour le statut de la facture si existante
            if affiliation_period.invoice:
                affiliation_period.invoice.status = 'paid'
                affiliation_period.invoice.save(update_fields=['status'])

            # Mettre à jour la période courante de l'affiliation
            affiliation = affiliation_period.affiliation
            affiliation.current_period = affiliation_period
            affiliation.save(update_fields=['current_period', 'updated_at'])

            logger.info(
                f"Période d'affiliation activée: {affiliation} - "
                f"{affiliation_period.season.name}"
            )
        else:
            # Paiement partiel
            if affiliation_period.invoice:
                affiliation_period.invoice.status = 'partially_paid'
                affiliation_period.invoice.save(update_fields=['status'])

        # Ajouter une note avec les détails du paiement
        payment_note = (
            f"Paiement de {amount}€ enregistré le "
            f"{timezone.now().strftime('%d/%m/%Y %H:%M')}"
        )
        if payment_method:
            payment_note += f" - Mode: {payment_method}"
        if reference:
            payment_note += f" - Réf: {reference}"

        if affiliation_period.notes:
            affiliation_period.notes += f"\n{payment_note}"
        else:
            affiliation_period.notes = payment_note

        affiliation_period.save()

        logger.info(
            f"Paiement de {amount}€ enregistré pour {affiliation_period}"
        )

        return affiliation_period

    @staticmethod
    def get_pending_invoices(
        organization: Organization,
        as_issuer: bool = True
    ) -> List[AffiliationPeriod]:
        """
        Récupère les périodes avec factures en attente de paiement.

        Args:
            organization: L'organisation concernée
            as_issuer: Si True, cherche les factures émises par l'org.
                       Si False, cherche les factures reçues par l'org.

        Returns:
            List[AffiliationPeriod]: Liste des périodes en attente
        """
        if as_issuer:
            # Factures émises par cette organisation (fédération)
            return list(
                AffiliationPeriod.objects.filter(
                    affiliation__parent_organization=organization,
                    status=AffiliationPeriodStatus.PENDING_PAYMENT,
                    invoice__isnull=False
                ).select_related(
                    'affiliation',
                    'affiliation__child_organization',
                    'season',
                    'invoice'
                ).order_by('-created_at')
            )
        else:
            # Factures reçues par cette organisation (club)
            return list(
                AffiliationPeriod.objects.filter(
                    affiliation__child_organization=organization,
                    status=AffiliationPeriodStatus.PENDING_PAYMENT,
                    invoice__isnull=False
                ).select_related(
                    'affiliation',
                    'affiliation__parent_organization',
                    'season',
                    'invoice'
                ).order_by('-created_at')
            )

    @staticmethod
    def get_unpaid_affiliations(
        organization: Organization,
        as_issuer: bool = True
    ) -> List[AffiliationPeriod]:
        """
        Récupère les périodes d'affiliation non payées (avec ou sans facture).

        Args:
            organization: L'organisation concernée
            as_issuer: Si True, pour la fédération. Si False, pour le club.

        Returns:
            List[AffiliationPeriod]: Liste des périodes non payées
        """
        if as_issuer:
            return list(
                AffiliationPeriod.objects.filter(
                    affiliation__parent_organization=organization,
                    status=AffiliationPeriodStatus.PENDING_PAYMENT
                ).select_related(
                    'affiliation',
                    'affiliation__child_organization',
                    'season',
                    'invoice'
                ).order_by('-created_at')
            )
        else:
            return list(
                AffiliationPeriod.objects.filter(
                    affiliation__child_organization=organization,
                    status=AffiliationPeriodStatus.PENDING_PAYMENT
                ).select_related(
                    'affiliation',
                    'affiliation__parent_organization',
                    'season',
                    'invoice'
                ).order_by('-created_at')
            )

    @staticmethod
    def get_affiliation_history(
        organization: Organization,
        as_child: bool = True
    ) -> List[AffiliationPeriod]:
        """
        Récupère l'historique complet des périodes d'affiliation.

        Args:
            organization: L'organisation concernée
            as_child: Si True, l'org est le club affilié.
                      Si False, l'org est la fédération.

        Returns:
            List[AffiliationPeriod]: Historique des périodes
        """
        if as_child:
            return list(
                AffiliationPeriod.objects.filter(
                    affiliation__child_organization=organization
                ).select_related(
                    'affiliation',
                    'affiliation__parent_organization',
                    'season',
                    'invoice'
                ).order_by('-season__start_date')
            )
        else:
            return list(
                AffiliationPeriod.objects.filter(
                    affiliation__parent_organization=organization
                ).select_related(
                    'affiliation',
                    'affiliation__child_organization',
                    'season',
                    'invoice'
                ).order_by('-season__start_date')
            )

    @staticmethod
    def calculate_total_revenue(
        organization: Organization,
        season=None
    ) -> Decimal:
        """
        Calcule le total des revenus d'affiliation pour une organisation.

        Args:
            organization: L'organisation (fédération)
            season: Saison spécifique (optionnel)

        Returns:
            Decimal: Total des revenus
        """
        queryset = AffiliationPeriod.objects.filter(
            affiliation__parent_organization=organization,
            status=AffiliationPeriodStatus.ACTIVE
        )

        if season:
            queryset = queryset.filter(season=season)

        total = queryset.aggregate(
            total=models.Sum('paid_amount')
        )['total'] or Decimal('0.00')

        return total
