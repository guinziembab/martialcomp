# -*- coding: utf-8 -*-
"""
Service pour l'import de relevés bancaires et la réconciliation.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.finances.models import (
    BankImportBatch,
    BankTransaction,
    ReconciliationRule,
    PractitionerBankInfo,
    Transaction,
    TransactionCategory,
    FinancialAccount,
)
from apps.finances.parsers import get_parser, detect_bank_format, BankTransactionData
from apps.competitions.models import Practitioner

logger = logging.getLogger(__name__)
User = get_user_model()


@dataclass
class ImportResult:
    """Résultat d'un import de relevé bancaire."""
    success: bool
    batch: Optional[BankImportBatch]
    imported_count: int
    duplicate_count: int
    error_count: int
    errors: List[str]
    transactions: List[BankTransaction]


@dataclass
class ReconciliationSuggestion:
    """Suggestion de réconciliation pour une transaction."""
    bank_transaction: BankTransaction
    suggested_practitioner: Optional[Practitioner]
    suggested_category: Optional[TransactionCategory]
    confidence_score: int  # 0-100
    match_reason: str


class BankImportService:
    """
    Service pour l'import et le traitement des relevés bancaires.
    """

    def __init__(self, user: User = None):
        self.user = user
        self.errors = []

    def import_file(
        self,
        file_content: bytes,
        file_name: str,
        financial_account: FinancialAccount,
        bank_format: str = None,
        auto_detect: bool = True
    ) -> ImportResult:
        """
        Importe un fichier de relevé bancaire.

        Args:
            file_content: Contenu du fichier en bytes
            file_name: Nom du fichier
            financial_account: Compte financier cible
            bank_format: Format bancaire (optionnel si auto_detect=True)
            auto_detect: Tenter la détection automatique du format

        Returns:
            ImportResult avec le statut et les statistiques
        """
        self.errors = []
        imported_transactions = []

        try:
            # Détecter le format si nécessaire
            if not bank_format and auto_detect:
                try:
                    bank_format = detect_bank_format(file_content)
                except ValueError as e:
                    return ImportResult(
                        success=False,
                        batch=None,
                        imported_count=0,
                        duplicate_count=0,
                        error_count=1,
                        errors=[str(e)],
                        transactions=[]
                    )

            # Obtenir le parseur
            parser = get_parser(bank_format)

            # Parser le fichier
            parsed_transactions = parser.parse(file_content)

            if not parsed_transactions:
                return ImportResult(
                    success=False,
                    batch=None,
                    imported_count=0,
                    duplicate_count=0,
                    error_count=0,
                    errors=["Aucune transaction trouvée dans le fichier"],
                    transactions=[]
                )

            # Créer le lot d'import
            with transaction.atomic():
                batch = BankImportBatch.objects.create(
                    financial_account=financial_account,
                    imported_by=self.user,
                    file_name=file_name,
                    file_format=self._get_file_format(file_name),
                    bank_format=bank_format,
                    status='processing',
                    total_transactions=len(parsed_transactions),
                )

                imported_count = 0
                duplicate_count = 0
                error_count = 0

                for tx_data in parsed_transactions:
                    try:
                        # Vérifier les doublons
                        if self._is_duplicate(tx_data, financial_account):
                            duplicate_count += 1
                            continue

                        # Créer la transaction bancaire
                        bank_tx = self._create_bank_transaction(tx_data, batch)
                        imported_transactions.append(bank_tx)
                        imported_count += 1

                    except Exception as e:
                        error_count += 1
                        self.errors.append(
                            f"Ligne {tx_data.line_number}: {str(e)}"
                        )
                        logger.error(
                            f"Erreur import transaction ligne {tx_data.line_number}: {e}"
                        )

                # Mettre à jour les statistiques du lot
                batch.imported_count = imported_count
                batch.duplicate_count = duplicate_count
                batch.error_count = error_count
                batch.error_log = '\n'.join(self.errors)

                if error_count > 0:
                    batch.status = 'completed_with_errors'
                else:
                    batch.status = 'completed'

                batch.completed_at = timezone.now()
                batch.save()

                # Mettre à jour les statistiques
                batch.update_statistics()

            return ImportResult(
                success=True,
                batch=batch,
                imported_count=imported_count,
                duplicate_count=duplicate_count,
                error_count=error_count,
                errors=self.errors,
                transactions=imported_transactions
            )

        except Exception as e:
            logger.exception(f"Erreur lors de l'import: {e}")
            return ImportResult(
                success=False,
                batch=None,
                imported_count=0,
                duplicate_count=0,
                error_count=1,
                errors=[str(e)],
                transactions=[]
            )

    def preview_import(
        self,
        file_content: bytes,
        bank_format: str = None,
        max_rows: int = 20
    ) -> Tuple[List[BankTransactionData], str, List[str]]:
        """
        Prévisualise un import sans l'enregistrer.

        Args:
            file_content: Contenu du fichier
            bank_format: Format bancaire (optionnel)
            max_rows: Nombre maximum de lignes à retourner

        Returns:
            Tuple (transactions, format_détecté, erreurs)
        """
        errors = []

        try:
            # Détecter le format
            if not bank_format:
                try:
                    bank_format = detect_bank_format(file_content)
                except ValueError as e:
                    return [], '', [str(e)]

            # Parser
            parser = get_parser(bank_format)
            transactions = parser.parse(file_content)

            # Limiter le nombre de résultats
            preview_transactions = transactions[:max_rows]

            return preview_transactions, bank_format, errors

        except Exception as e:
            logger.exception(f"Erreur lors de la prévisualisation: {e}")
            return [], bank_format or '', [str(e)]

    def _is_duplicate(
        self,
        tx_data: BankTransactionData,
        financial_account: FinancialAccount
    ) -> bool:
        """Vérifie si une transaction existe déjà."""
        return BankTransaction.objects.filter(
            import_batch__financial_account=financial_account,
            external_reference=tx_data.external_reference,
            transaction_date=tx_data.transaction_date,
            amount=abs(tx_data.amount)
        ).exists()

    def _create_bank_transaction(
        self,
        tx_data: BankTransactionData,
        batch: BankImportBatch
    ) -> BankTransaction:
        """Crée une BankTransaction à partir des données parsées."""
        return BankTransaction.objects.create(
            import_batch=batch,
            **tx_data.to_dict()
        )

    def _get_file_format(self, file_name: str) -> str:
        """Détermine le format de fichier à partir du nom."""
        file_name_lower = file_name.lower()
        if file_name_lower.endswith('.csv'):
            return 'csv'
        elif file_name_lower.endswith('.xlsx'):
            return 'xlsx'
        elif file_name_lower.endswith('.xls'):
            return 'xls'
        elif file_name_lower.endswith('.ofx'):
            return 'ofx'
        elif file_name_lower.endswith('.qif'):
            return 'qif'
        return 'csv'


class ReconciliationService:
    """
    Service pour la réconciliation des transactions bancaires.
    """

    def __init__(self, organization_id: str = None):
        self.organization_id = organization_id

    def get_suggestions(
        self,
        bank_transaction: BankTransaction
    ) -> List[ReconciliationSuggestion]:
        """
        Génère des suggestions de réconciliation pour une transaction.

        Args:
            bank_transaction: Transaction bancaire à réconcilier

        Returns:
            Liste de suggestions triées par score de confiance
        """
        suggestions = []

        # 1. Matching par référence structurée belge (priorité maximale)
        structured_match = self._match_by_structured_reference(bank_transaction)
        if structured_match:
            suggestions.append(structured_match)

        # 2. Matching par IBAN
        iban_match = self._match_by_iban(bank_transaction)
        if iban_match:
            suggestions.append(iban_match)

        # 3. Matching par nom dans la communication
        name_matches = self._match_by_name(bank_transaction)
        suggestions.extend(name_matches)

        # 4. Matching par montant et période (cotisations)
        amount_matches = self._match_by_amount_period(bank_transaction)
        suggestions.extend(amount_matches)

        # 5. Appliquer les règles personnalisées
        rule_matches = self._apply_rules(bank_transaction)
        suggestions.extend(rule_matches)

        # Trier par score décroissant et dédupliquer
        suggestions = self._deduplicate_suggestions(suggestions)
        suggestions.sort(key=lambda s: s.confidence_score, reverse=True)

        return suggestions[:5]  # Top 5 suggestions

    def auto_reconcile(
        self,
        bank_transaction: BankTransaction,
        min_confidence: int = 90
    ) -> bool:
        """
        Tente de réconcilier automatiquement une transaction.

        Args:
            bank_transaction: Transaction à réconcilier
            min_confidence: Score minimum requis

        Returns:
            True si réconciliation réussie
        """
        suggestions = self.get_suggestions(bank_transaction)

        if suggestions and suggestions[0].confidence_score >= min_confidence:
            best = suggestions[0]

            bank_transaction.matched_practitioner = best.suggested_practitioner
            bank_transaction.matched_category = best.suggested_category
            bank_transaction.reconciliation_status = 'matched'
            bank_transaction.reconciliation_score = best.confidence_score
            bank_transaction.reconciliation_notes = best.match_reason
            bank_transaction.reconciled_at = timezone.now()
            bank_transaction.save()

            return True

        return False

    def _match_by_iban(
        self,
        bank_transaction: BankTransaction
    ) -> Optional[ReconciliationSuggestion]:
        """Cherche un pratiquant par IBAN."""
        if not bank_transaction.counterparty_iban:
            return None

        try:
            bank_info = PractitionerBankInfo.objects.get(
                iban=bank_transaction.counterparty_iban
            )

            return ReconciliationSuggestion(
                bank_transaction=bank_transaction,
                suggested_practitioner=bank_info.practitioner,
                suggested_category=None,
                confidence_score=95,
                match_reason=f"IBAN correspondant: {bank_info.iban}"
            )

        except PractitionerBankInfo.DoesNotExist:
            return None

    def _match_by_structured_reference(
        self,
        bank_transaction: BankTransaction
    ) -> Optional[ReconciliationSuggestion]:
        """
        Cherche une correspondance par référence structurée belge.

        Format belge: +++123/4567/89012+++ ou ***123/4567/89012***
        La référence peut contenir:
        - Un numéro de facture
        - Un numéro de membre/licence
        - Un code identifiant le pratiquant
        """
        import re

        communication = bank_transaction.communication or ''

        # Pattern pour référence structurée belge
        # Format: +++XXX/XXXX/XXXXX+++ ou ***XXX/XXXX/XXXXX***
        patterns = [
            r'\+\+\+(\d{3}/\d{4}/\d{5})\+\+\+',  # Format standard +++
            r'\*\*\*(\d{3}/\d{4}/\d{5})\*\*\*',  # Format alternatif ***
            r'\+\+\+(\d{12})\+\+\+',              # Format sans séparateurs
            r'RF\d{2}\s*\d+',                      # Format européen SEPA
        ]

        for pattern in patterns:
            match = re.search(pattern, communication)
            if match:
                reference = match.group(0)
                reference_clean = re.sub(r'[^\d]', '', reference)

                # Chercher une facture avec cette référence
                try:
                    from apps.finances.models import Invoice
                    invoice = Invoice.objects.filter(
                        Q(number__icontains=reference_clean) |
                        Q(reference__icontains=reference_clean)
                    ).first()

                    if invoice:
                        # Essayer de trouver le pratiquant lié à la facture
                        practitioner = None
                        if hasattr(invoice, 'practitioner') and invoice.practitioner:
                            practitioner = invoice.practitioner

                        return ReconciliationSuggestion(
                            bank_transaction=bank_transaction,
                            suggested_practitioner=practitioner,
                            suggested_category=None,
                            confidence_score=98,
                            match_reason=f"Référence structurée trouvée: {reference} → Facture {invoice.number}"
                        )
                except Exception:
                    pass

                # Chercher un pratiquant par numéro de licence
                try:
                    practitioner = Practitioner.objects.filter(
                        Q(license_number__icontains=reference_clean) |
                        Q(member_number__icontains=reference_clean)
                    ).first()

                    if practitioner:
                        return ReconciliationSuggestion(
                            bank_transaction=bank_transaction,
                            suggested_practitioner=practitioner,
                            suggested_category=None,
                            confidence_score=92,
                            match_reason=f"Référence structurée: {reference} → Licence {practitioner.license_number}"
                        )
                except Exception:
                    pass

                # Référence trouvée mais pas de correspondance
                return ReconciliationSuggestion(
                    bank_transaction=bank_transaction,
                    suggested_practitioner=None,
                    suggested_category=None,
                    confidence_score=50,
                    match_reason=f"Référence structurée détectée: {reference} (non résolue)"
                )

        return None

    def _match_by_amount_period(
        self,
        bank_transaction: BankTransaction
    ) -> List[ReconciliationSuggestion]:
        """
        Cherche des correspondances par montant exact et période.
        Utile pour les cotisations et inscriptions à montant fixe.
        """
        from datetime import timedelta

        suggestions = []

        # Seulement pour les revenus (cotisations entrantes)
        if bank_transaction.transaction_type != 'INCOME':
            return suggestions

        amount = abs(bank_transaction.amount)
        tx_date = bank_transaction.transaction_date

        # Fenêtre de recherche: 30 jours avant et après
        date_start = tx_date - timedelta(days=30)
        date_end = tx_date + timedelta(days=30)

        # Chercher des factures avec ce montant exact dans la période
        try:
            from apps.finances.models import Invoice
            matching_invoices = Invoice.objects.filter(
                total=amount,
                due_date__gte=date_start,
                due_date__lte=date_end,
                status__in=['sent', 'unpaid']  # Factures en attente de paiement
            ).select_related('recipient_content_type')[:10]

            for invoice in matching_invoices:
                # Essayer de récupérer le pratiquant
                practitioner = None
                if invoice.recipient_content_type:
                    try:
                        from django.contrib.contenttypes.models import ContentType
                        ct = invoice.recipient_content_type
                        if ct.model == 'practitioner':
                            practitioner = ct.get_object_for_this_type(pk=invoice.recipient_object_id)
                    except Exception:
                        pass

                suggestions.append(ReconciliationSuggestion(
                    bank_transaction=bank_transaction,
                    suggested_practitioner=practitioner,
                    suggested_category=None,
                    confidence_score=70,
                    match_reason=f"Montant correspondant: {amount}€ → Facture {invoice.number} (échéance {invoice.due_date})"
                ))
        except Exception as e:
            logger.debug(f"Erreur matching par montant: {e}")

        # Chercher des cotisations en attente avec ce montant
        try:
            from apps.finances.models import MembershipFee
            matching_fees = MembershipFee.objects.filter(
                amount=amount,
            ).select_related('practitioner')[:5]

            for fee in matching_fees:
                if hasattr(fee, 'practitioner') and fee.practitioner:
                    suggestions.append(ReconciliationSuggestion(
                        bank_transaction=bank_transaction,
                        suggested_practitioner=fee.practitioner,
                        suggested_category=None,
                        confidence_score=65,
                        match_reason=f"Cotisation correspondante: {amount}€ → {fee.practitioner.full_name}"
                    ))
        except Exception as e:
            logger.debug(f"Erreur matching cotisations: {e}")

        return suggestions

    def _match_by_name(
        self,
        bank_transaction: BankTransaction
    ) -> List[ReconciliationSuggestion]:
        """Cherche des pratiquants par nom dans la communication."""
        suggestions = []

        # Texte à analyser
        search_text = f"{bank_transaction.communication} {bank_transaction.counterparty_name}"
        search_text = search_text.lower()

        # Chercher les pratiquants
        practitioners = Practitioner.objects.all()

        if self.organization_id:
            practitioners = practitioners.filter(
                organization_id=self.organization_id
            )

        for practitioner in practitioners[:100]:  # Limiter la recherche
            full_name = practitioner.full_name.lower()
            first_name = (practitioner.first_name or '').lower()
            last_name = (practitioner.last_name or '').lower()

            score = 0
            reason = ""

            # Nom complet présent
            if full_name and full_name in search_text:
                score = 85
                reason = f"Nom complet trouvé: {practitioner.full_name}"
            # Nom de famille + prénom séparément
            elif last_name and first_name:
                if last_name in search_text and first_name in search_text:
                    score = 80
                    reason = f"Prénom et nom trouvés: {practitioner.full_name}"
                elif last_name in search_text:
                    score = 60
                    reason = f"Nom de famille trouvé: {last_name}"

            if score > 0:
                suggestions.append(ReconciliationSuggestion(
                    bank_transaction=bank_transaction,
                    suggested_practitioner=practitioner,
                    suggested_category=None,
                    confidence_score=score,
                    match_reason=reason
                ))

        return suggestions

    def _apply_rules(
        self,
        bank_transaction: BankTransaction
    ) -> List[ReconciliationSuggestion]:
        """Applique les règles de réconciliation personnalisées."""
        suggestions = []

        rules = ReconciliationRule.objects.filter(is_active=True)

        if self.organization_id:
            rules = rules.filter(
                Q(organization_id=self.organization_id) |
                Q(organization_id='')
            )

        rules = rules.order_by('-priority')

        for rule in rules:
            if self._rule_matches(rule, bank_transaction):
                suggestion = ReconciliationSuggestion(
                    bank_transaction=bank_transaction,
                    suggested_practitioner=rule.assign_practitioner,
                    suggested_category=rule.assign_category,
                    confidence_score=75,
                    match_reason=f"Règle: {rule.name}"
                )
                suggestions.append(suggestion)

                # Incrémenter le compteur d'application
                rule.increment_applied()

        return suggestions

    def _rule_matches(
        self,
        rule: ReconciliationRule,
        bank_transaction: BankTransaction
    ) -> bool:
        """Vérifie si une règle correspond à la transaction."""
        import re

        # Obtenir la valeur du champ à matcher
        field_value = ''
        if rule.match_field == 'communication':
            field_value = bank_transaction.communication or ''
        elif rule.match_field == 'counterparty_name':
            field_value = bank_transaction.counterparty_name or ''
        elif rule.match_field == 'counterparty_iban':
            field_value = bank_transaction.counterparty_iban or ''
        elif rule.match_field == 'amount':
            # Vérifier la plage de montant
            amount = bank_transaction.amount
            if rule.min_amount and amount < rule.min_amount:
                return False
            if rule.max_amount and amount > rule.max_amount:
                return False
            return True
        elif rule.match_field == 'raw_details':
            field_value = bank_transaction.raw_details or ''

        field_value = field_value.lower()
        match_value = rule.match_value.lower()

        # Vérifier le type de transaction si spécifié
        if rule.transaction_type:
            if bank_transaction.transaction_type != rule.transaction_type:
                return False

        # Appliquer le type de matching
        if rule.match_type == 'contains':
            return match_value in field_value
        elif rule.match_type == 'exact':
            return field_value == match_value
        elif rule.match_type == 'starts_with':
            return field_value.startswith(match_value)
        elif rule.match_type == 'ends_with':
            return field_value.endswith(match_value)
        elif rule.match_type == 'regex':
            try:
                return bool(re.search(rule.match_value, field_value, re.IGNORECASE))
            except re.error:
                return False

        return False

    def _deduplicate_suggestions(
        self,
        suggestions: List[ReconciliationSuggestion]
    ) -> List[ReconciliationSuggestion]:
        """Déduplique les suggestions en gardant le meilleur score."""
        seen = {}

        for suggestion in suggestions:
            key = (
                suggestion.suggested_practitioner.id
                if suggestion.suggested_practitioner else None,
                suggestion.suggested_category.id
                if suggestion.suggested_category else None
            )

            if key not in seen or seen[key].confidence_score < suggestion.confidence_score:
                seen[key] = suggestion

        return list(seen.values())
