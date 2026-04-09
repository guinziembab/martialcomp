"""
Service de gestion des saisons et périodes d'affiliation.
"""
from datetime import date
from decimal import Decimal
from typing import Optional, List, Tuple
import logging

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

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

User = get_user_model()
logger = logging.getLogger(__name__)


class AffiliationSeasonService:
    """
    Service pour la gestion des saisons sportives et des périodes d'affiliation.
    """

    @staticmethod
    def create_season(
        organization: Organization,
        name: str,
        start_date: date,
        end_date: date,
        renewal_reminder_days: int = 30,
        is_current: bool = False
    ) -> SportSeason:
        """
        Crée une nouvelle saison pour une organisation.

        Args:
            organization: L'organisation (fédération) propriétaire de la saison
            name: Nom de la saison (ex: "2024-2025")
            start_date: Date de début de la saison
            end_date: Date de fin de la saison
            renewal_reminder_days: Jours avant expiration pour rappels
            is_current: Si True, marque comme saison courante

        Returns:
            SportSeason: La saison créée
        """
        season = SportSeason.objects.create(
            organization=organization,
            name=name,
            start_date=start_date,
            end_date=end_date,
            renewal_reminder_days=renewal_reminder_days,
            is_current=is_current
        )
        logger.info(
            f"Saison {name} créée pour {organization.name} "
            f"({start_date} - {end_date})"
        )
        return season

    @staticmethod
    def get_current_season(organization: Organization) -> Optional[SportSeason]:
        """
        Récupère la saison courante d'une organisation.

        Args:
            organization: L'organisation dont on cherche la saison courante

        Returns:
            SportSeason ou None si aucune saison courante
        """
        # D'abord chercher la saison marquée comme courante
        season = SportSeason.objects.filter(
            organization=organization,
            is_current=True
        ).first()

        if season:
            return season

        # Sinon, chercher la saison active par dates
        today = timezone.now().date()
        return SportSeason.objects.filter(
            organization=organization,
            start_date__lte=today,
            end_date__gte=today
        ).first()

    @staticmethod
    def get_next_season(organization: Organization) -> Optional[SportSeason]:
        """
        Récupère la prochaine saison d'une organisation.

        Args:
            organization: L'organisation

        Returns:
            SportSeason ou None si aucune saison future
        """
        today = timezone.now().date()
        return SportSeason.objects.filter(
            organization=organization,
            start_date__gt=today
        ).order_by('start_date').first()

    @staticmethod
    def get_fee_for_affiliation(
        organization: Organization,
        season: SportSeason,
        affiliation_type: str
    ) -> Optional[AffiliationFeeConfiguration]:
        """
        Récupère la configuration de tarif pour un type d'affiliation.

        Args:
            organization: L'organisation (fédération)
            season: La saison
            affiliation_type: Le type d'affiliation

        Returns:
            AffiliationFeeConfiguration ou None
        """
        return AffiliationFeeConfiguration.objects.filter(
            organization=organization,
            season=season,
            affiliation_type=affiliation_type,
            is_active=True
        ).first()

    @staticmethod
    @transaction.atomic
    def create_affiliation_period(
        affiliation: Affiliation,
        season: SportSeason,
        amount: Optional[Decimal] = None,
        status: str = AffiliationPeriodStatus.PENDING_PAYMENT
    ) -> AffiliationPeriod:
        """
        Crée une période d'affiliation pour une saison.

        Args:
            affiliation: L'affiliation concernée
            season: La saison pour laquelle créer la période
            amount: Montant (si None, récupéré depuis la configuration)
            status: Statut initial de la période

        Returns:
            AffiliationPeriod: La période créée
        """
        # Si pas de montant fourni, chercher dans la config
        if amount is None:
            fee_config = AffiliationSeasonService.get_fee_for_affiliation(
                affiliation.parent_organization,
                season,
                affiliation.affiliation_type
            )
            if fee_config:
                amount = fee_config.amount_with_tax
            else:
                amount = Decimal('0.00')

        period = AffiliationPeriod.objects.create(
            affiliation=affiliation,
            season=season,
            status=status,
            amount=amount
        )

        # Mettre à jour la période courante si c'est la saison active
        if season.is_current or season.is_active:
            affiliation.current_period = period
            affiliation.save(update_fields=['current_period'])

        logger.info(
            f"Période d'affiliation créée: {affiliation} - {season.name} "
            f"({amount}€, statut: {status})"
        )
        return period

    @staticmethod
    @transaction.atomic
    def renew_affiliation(
        affiliation: Affiliation,
        new_season: SportSeason,
        requested_by: User
    ) -> AffiliationRenewalRequest:
        """
        Initie une demande de renouvellement d'affiliation.

        Args:
            affiliation: L'affiliation à renouveler
            new_season: La nouvelle saison
            requested_by: L'utilisateur qui fait la demande

        Returns:
            AffiliationRenewalRequest: La demande créée

        Raises:
            ValueError: Si pas de période courante ou demande déjà en cours
        """
        current_period = affiliation.current_period
        if not current_period:
            raise ValueError("Aucune période d'affiliation courante à renouveler")

        # Vérifier qu'il n'y a pas déjà une demande en cours pour cette saison
        existing_request = AffiliationRenewalRequest.objects.filter(
            affiliation=affiliation,
            to_season=new_season,
            status=AffiliationRenewalRequestStatus.PENDING
        ).exists()

        if existing_request:
            raise ValueError(
                "Une demande de renouvellement est déjà en cours pour cette saison"
            )

        # Vérifier qu'il n'y a pas déjà une période pour cette saison
        existing_period = AffiliationPeriod.objects.filter(
            affiliation=affiliation,
            season=new_season
        ).exists()

        if existing_period:
            raise ValueError(
                "Une période d'affiliation existe déjà pour cette saison"
            )

        renewal_request = AffiliationRenewalRequest.objects.create(
            affiliation=affiliation,
            from_period=current_period,
            to_season=new_season,
            requested_by=requested_by,
            status=AffiliationRenewalRequestStatus.PENDING
        )

        logger.info(
            f"Demande de renouvellement créée: {affiliation} → {new_season.name} "
            f"par {requested_by}"
        )
        return renewal_request

    @staticmethod
    @transaction.atomic
    def approve_renewal_request(
        renewal_request: AffiliationRenewalRequest,
        processed_by: User,
        amount: Optional[Decimal] = None
    ) -> AffiliationPeriod:
        """
        Approuve une demande de renouvellement et crée la nouvelle période.

        Args:
            renewal_request: La demande à approuver
            processed_by: L'utilisateur qui traite la demande
            amount: Montant optionnel (sinon utilise la config)

        Returns:
            AffiliationPeriod: La nouvelle période créée
        """
        if renewal_request.status != AffiliationRenewalRequestStatus.PENDING:
            raise ValueError("Cette demande a déjà été traitée")

        # Créer la nouvelle période
        new_period = AffiliationSeasonService.create_affiliation_period(
            affiliation=renewal_request.affiliation,
            season=renewal_request.to_season,
            amount=amount,
            status=AffiliationPeriodStatus.PENDING_PAYMENT
        )

        # Lier à la période précédente
        new_period.renewed_from = renewal_request.from_period
        new_period.save(update_fields=['renewed_from'])

        # Mettre à jour la demande
        renewal_request.status = AffiliationRenewalRequestStatus.APPROVED
        renewal_request.processed_at = timezone.now()
        renewal_request.processed_by = processed_by
        renewal_request.created_period = new_period
        renewal_request.save()

        logger.info(
            f"Demande de renouvellement approuvée: {renewal_request} "
            f"par {processed_by}"
        )
        return new_period

    @staticmethod
    @transaction.atomic
    def reject_renewal_request(
        renewal_request: AffiliationRenewalRequest,
        processed_by: User,
        reason: str = ""
    ) -> None:
        """
        Refuse une demande de renouvellement.

        Args:
            renewal_request: La demande à refuser
            processed_by: L'utilisateur qui traite la demande
            reason: Motif du refus
        """
        if renewal_request.status != AffiliationRenewalRequestStatus.PENDING:
            raise ValueError("Cette demande a déjà été traitée")

        renewal_request.status = AffiliationRenewalRequestStatus.REJECTED
        renewal_request.processed_at = timezone.now()
        renewal_request.processed_by = processed_by
        renewal_request.rejection_reason = reason
        renewal_request.save()

        logger.info(
            f"Demande de renouvellement refusée: {renewal_request} "
            f"par {processed_by}. Motif: {reason}"
        )

    @staticmethod
    def get_expiring_affiliations(
        days_before: int = 30
    ) -> List[Tuple[Affiliation, AffiliationPeriod]]:
        """
        Récupère les affiliations qui expirent dans les X prochains jours.

        Args:
            days_before: Nombre de jours avant expiration

        Returns:
            Liste de tuples (Affiliation, AffiliationPeriod)
        """
        today = timezone.now().date()
        expiring = []

        # Récupérer les périodes actives dont la saison expire bientôt
        active_periods = AffiliationPeriod.objects.filter(
            status=AffiliationPeriodStatus.ACTIVE
        ).select_related('affiliation', 'season')

        for period in active_periods:
            if period.season.days_remaining <= days_before:
                expiring.append((period.affiliation, period))

        return expiring

    @staticmethod
    @transaction.atomic
    def update_expired_affiliations() -> int:
        """
        Marque comme expirées les périodes d'affiliation dont la saison est terminée.

        Returns:
            int: Nombre de périodes marquées comme expirées
        """
        today = timezone.now().date()
        count = 0

        # Récupérer les périodes actives avec saison expirée
        expired_periods = AffiliationPeriod.objects.filter(
            status=AffiliationPeriodStatus.ACTIVE,
            season__end_date__lt=today
        )

        for period in expired_periods:
            period.status = AffiliationPeriodStatus.EXPIRED
            period.save(update_fields=['status', 'updated_at'])
            count += 1

            logger.info(
                f"Période d'affiliation expirée: {period.affiliation} - "
                f"{period.season.name}"
            )

        return count

    @staticmethod
    def generate_season_name(start_year: int) -> str:
        """
        Génère le nom d'une saison au format YYYY-YYYY.

        Args:
            start_year: Année de début

        Returns:
            str: Nom de la saison (ex: "2024-2025")
        """
        return f"{start_year}-{start_year + 1}"

    @staticmethod
    def get_default_season_dates(
        start_year: int,
        start_month: int = 9,
        start_day: int = 1
    ) -> Tuple[date, date]:
        """
        Retourne les dates par défaut d'une saison sportive.
        Par défaut: du 1er septembre au 31 août.

        Args:
            start_year: Année de début
            start_month: Mois de début (défaut: septembre)
            start_day: Jour de début (défaut: 1)

        Returns:
            Tuple[date, date]: (date_debut, date_fin)
        """
        start_date = date(start_year, start_month, start_day)
        # Fin le 31 août de l'année suivante
        end_date = date(start_year + 1, 8, 31)
        return start_date, end_date
