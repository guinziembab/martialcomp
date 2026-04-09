# -*- coding: utf-8 -*-
"""
Parseur pour les relevés bancaires Société Générale (France).

Format CSV avec les caractéristiques:
- Encodage: ISO-8859-1 ou UTF-8
- Séparateur: Point-virgule (;)
- Format de date: DD/MM/YYYY
- Décimales: Virgule (,)
"""

import csv
import io
from datetime import date
from decimal import Decimal
from typing import List, Optional

from .base import BaseBankParser, BankTransactionData


class SocieteGeneraleParser(BaseBankParser):
    """
    Parseur pour les relevés Société Générale (France).
    """

    BANK_CODE = 'SOCIETE_GENERALE_FR'
    BANK_NAME = 'Société Générale (France)'

    SUPPORTED_FORMATS = ['csv']
    ENCODING = 'iso-8859-1'  # Latin-1, commun en France
    DELIMITER = ';'
    DATE_FORMAT = '%d/%m/%Y'
    DECIMAL_SEPARATOR = ','
    THOUSANDS_SEPARATOR = ' '

    # Mapping des colonnes du CSV vers les champs internes
    COLUMN_MAPPING = {
        # Variations possibles des noms de colonnes
        'Date': 'transaction_date',
        'Date opération': 'transaction_date',
        'Date operation': 'transaction_date',
        'Date de valeur': 'value_date',
        'Date valeur': 'value_date',
        'Libellé': 'communication',
        'Libelle': 'communication',
        'Libellé opération': 'communication',
        'Détail': 'raw_details',
        'Detail': 'raw_details',
        'Montant': 'amount',
        'Débit': 'debit',
        'Debit': 'debit',
        'Crédit': 'credit',
        'Credit': 'credit',
        'Devise': 'currency',
        'Référence': 'external_reference',
        'Reference': 'external_reference',
        'Numéro de compte': 'account_iban',
        'IBAN': 'account_iban',
        'Catégorie': 'category',
        'Type': 'payment_method_raw',
    }

    def detect_format(self, file_content: bytes) -> bool:
        """
        Détecte si le fichier est un relevé Société Générale.
        """
        try:
            # Essayer plusieurs encodages
            text = None
            for encoding in ['utf-8-sig', 'utf-8', 'iso-8859-1', 'cp1252']:
                try:
                    text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if not text:
                return False

            first_lines = text.split('\n')[:5]
            header = first_lines[0].lower() if first_lines else ''

            # Indicateurs Société Générale
            indicators = [
                'société générale' in text.lower()[:500],
                'societe generale' in text.lower()[:500],
                ('date' in header and ('libellé' in header or 'libelle' in header)),
                ('débit' in header or 'debit' in header) and (
                    'crédit' in header or 'credit' in header
                ),
            ]

            return sum(indicators) >= 2

        except Exception:
            return False

    def parse(self, file_content: bytes) -> List[BankTransactionData]:
        """
        Parse le fichier CSV Société Générale.
        """
        transactions = []

        # Détecter l'encodage
        text = None
        used_encoding = self.ENCODING
        for encoding in ['utf-8-sig', 'utf-8', 'iso-8859-1', 'cp1252']:
            try:
                text = file_content.decode(encoding)
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue

        if not text:
            raise ValueError("Impossible de décoder le fichier")

        try:
            # Parser le CSV
            reader = csv.DictReader(
                io.StringIO(text),
                delimiter=self.DELIMITER
            )

            column_map = self._create_column_map(reader.fieldnames or [])

            for line_num, row in enumerate(reader, start=2):
                try:
                    transaction = self._parse_row(row, column_map, line_num)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    error_tx = BankTransactionData(
                        external_reference=f"ERROR-{line_num}",
                        transaction_date=date.today(),
                        value_date=date.today(),
                        amount=Decimal('0.00'),
                        line_number=line_num,
                        raw_row=dict(row),
                        parsing_errors=[str(e)]
                    )
                    transactions.append(error_tx)

        except Exception as e:
            raise ValueError(f"Erreur lors du parsing: {str(e)}")

        return self.validate_transactions(transactions)

    def _create_column_map(self, fieldnames: List[str]) -> dict:
        """Crée le mapping des colonnes."""
        column_map = {}

        for csv_col in fieldnames:
            csv_col_clean = csv_col.strip()
            # Chercher correspondance directe
            if csv_col_clean in self.COLUMN_MAPPING:
                column_map[csv_col] = self.COLUMN_MAPPING[csv_col_clean]
                continue

            # Chercher correspondance insensible à la casse
            csv_lower = csv_col_clean.lower()
            for ref_col, field in self.COLUMN_MAPPING.items():
                if ref_col.lower() == csv_lower:
                    column_map[csv_col] = field
                    break

        return column_map

    def _parse_row(
        self,
        row: dict,
        column_map: dict,
        line_num: int
    ) -> Optional[BankTransactionData]:
        """Parse une ligne du CSV."""

        def get_value(field: str) -> str:
            for csv_col, mapped_field in column_map.items():
                if mapped_field == field:
                    return self.clean_text(row.get(csv_col, ''))
            return ''

        # Gérer le format avec colonnes séparées Débit/Crédit
        debit = get_value('debit')
        credit = get_value('credit')
        amount_str = get_value('amount')

        if debit or credit:
            # Format avec colonnes séparées
            if credit and self.normalize_amount(credit) != Decimal('0.00'):
                amount = self.normalize_amount(credit)
                tx_type = 'INCOME'
            elif debit and self.normalize_amount(debit) != Decimal('0.00'):
                amount = self.normalize_amount(debit)
                tx_type = 'EXPENSE'
            else:
                return None
        elif amount_str:
            # Format avec une seule colonne montant
            amount = self.normalize_amount(amount_str)
            tx_type = self.determine_transaction_type(amount)
        else:
            return None

        # Référence externe
        external_ref = get_value('external_reference')
        if not external_ref:
            # Générer une référence basée sur la date et le montant
            tx_date_str = get_value('transaction_date')
            external_ref = f"SG-{tx_date_str}-{abs(amount)}"

        # Dates
        tx_date = self.normalize_date(get_value('transaction_date'))
        value_date = self.normalize_date(get_value('value_date'))

        if not tx_date:
            return None
        if not value_date:
            value_date = tx_date

        # Communication / Libellé
        communication = get_value('communication')
        raw_details = get_value('raw_details')

        # Méthode de paiement
        payment_method_raw = get_value('payment_method_raw')
        payment_method = self.normalize_payment_method(
            payment_method_raw or communication
        )

        # Extraire IBAN si présent dans les détails
        counterparty_iban = self.extract_iban(raw_details or communication)

        # Extraire nom contrepartie du libellé
        counterparty_name = self._extract_counterparty_name(communication)

        # Devise
        currency = get_value('currency') or 'EUR'

        return BankTransactionData(
            external_reference=external_ref,
            transaction_date=tx_date,
            value_date=value_date,
            amount=abs(amount),
            currency=currency,
            transaction_type=tx_type,
            payment_method=payment_method,
            payment_method_raw=payment_method_raw,
            counterparty_iban=counterparty_iban,
            counterparty_name=counterparty_name,
            communication=communication,
            raw_details=raw_details,
            bank_status='Accepté',
            raw_row=dict(row),
            line_number=line_num,
        )

    def _extract_counterparty_name(self, libelle: str) -> str:
        """
        Extrait le nom de la contrepartie du libellé.

        Formats courants Société Générale:
        - "VIR RECU DE DUPONT JEAN"
        - "PAIEMENT CB AMAZON"
        - "PRLV SEPA EDF"
        """
        if not libelle:
            return ''

        import re

        # Patterns pour extraire le nom
        patterns = [
            r'VIR (?:RECU DE |EMIS POUR |SEPA )?(.+?)(?:\s*-|$)',
            r'PRLV (?:SEPA )?(.+?)(?:\s*-|$)',
            r'PAIEMENT CB (.+?)(?:\s*-|\s+\d|$)',
            r'RETRAIT DAB (.+?)(?:\s*-|$)',
            r'CHQ (?:EMIS|RECU) (.+?)(?:\s*-|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, libelle, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Nettoyer les références numériques à la fin
                name = re.sub(r'\s+\d+\s*$', '', name)
                return name[:100]  # Limiter la longueur

        # Par défaut, prendre les 50 premiers caractères
        return libelle[:50].strip()
