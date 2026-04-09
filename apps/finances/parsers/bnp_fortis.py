# -*- coding: utf-8 -*-
"""
Parseur pour les relevés bancaires BNP Paribas Fortis (Belgique).

Format CSV avec les caractéristiques:
- Encodage: UTF-8 avec BOM
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


class BNPParibasFortisParser(BaseBankParser):
    """
    Parseur pour les relevés BNP Paribas Fortis (Belgique).
    """

    BANK_CODE = 'BNP_FORTIS_BE'
    BANK_NAME = 'BNP Paribas Fortis (Belgique)'

    SUPPORTED_FORMATS = ['csv']
    ENCODING = 'utf-8-sig'  # UTF-8 avec BOM
    DELIMITER = ';'
    DATE_FORMAT = '%d/%m/%Y'
    DECIMAL_SEPARATOR = ','
    THOUSANDS_SEPARATOR = ' '

    # Mapping des colonnes du CSV vers les champs internes
    COLUMN_MAPPING = {
        'Nº de séquence': 'external_reference',
        'N° de séquence': 'external_reference',
        'Numero de sequence': 'external_reference',
        "Date d'exécution": 'transaction_date',
        'Date d\'exécution': 'transaction_date',
        'Date execution': 'transaction_date',
        'Date valeur': 'value_date',
        'Montant': 'amount',
        'Devise du compte': 'currency',
        'Numéro de compte': 'account_iban',
        'Numero de compte': 'account_iban',
        'Type de transaction': 'payment_method_raw',
        'Contrepartie': 'counterparty_iban',
        'Nom de la contrepartie': 'counterparty_name',
        'Communication': 'communication',
        'Détails': 'raw_details',
        'Details': 'raw_details',
        'Statut': 'bank_status',
        'Motif du refus': 'rejection_reason',
    }

    # Normalisation des noms de colonnes (pour gérer les variantes)
    @staticmethod
    def normalize_column_name(name: str) -> str:
        """Normalise un nom de colonne pour le matching."""
        import unicodedata
        # Supprimer les accents
        name = unicodedata.normalize('NFKD', name)
        name = name.encode('ascii', 'ignore').decode('ascii')
        # Minuscules et sans espaces multiples
        name = name.lower().strip()
        return name

    def detect_format(self, file_content: bytes) -> bool:
        """
        Détecte si le fichier est un relevé BNP Paribas Fortis.

        Args:
            file_content: Contenu du fichier en bytes

        Returns:
            True si le fichier correspond au format BNP Fortis
        """
        try:
            # Essayer de décoder avec UTF-8 BOM
            text = file_content.decode(self.ENCODING)
            first_line = text.split('\n')[0]

            # Vérifier les colonnes caractéristiques
            indicators = [
                'séquence' in first_line.lower() or 'sequence' in first_line.lower(),
                "d'exécution" in first_line.lower() or 'execution' in first_line.lower(),
                'contrepartie' in first_line.lower(),
            ]

            return sum(indicators) >= 2

        except (UnicodeDecodeError, IndexError):
            return False

    def parse(self, file_content: bytes) -> List[BankTransactionData]:
        """
        Parse le fichier CSV BNP Paribas Fortis.

        Args:
            file_content: Contenu du fichier en bytes

        Returns:
            Liste des transactions parsées
        """
        transactions = []

        try:
            # Décoder le contenu
            text = file_content.decode(self.ENCODING)

            # Parser le CSV
            reader = csv.DictReader(
                io.StringIO(text),
                delimiter=self.DELIMITER
            )

            # Créer le mapping des colonnes
            column_map = self._create_column_map(reader.fieldnames or [])

            for line_num, row in enumerate(reader, start=2):
                try:
                    transaction = self._parse_row(row, column_map, line_num)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    # Créer une transaction avec erreur pour traçabilité
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
            raise ValueError(f"Erreur lors du parsing du fichier: {str(e)}")

        return self.validate_transactions(transactions)

    def _create_column_map(self, fieldnames: List[str]) -> dict:
        """
        Crée un mapping entre les noms de colonnes du fichier et les champs internes.

        Args:
            fieldnames: Noms des colonnes du CSV

        Returns:
            Dictionnaire de mapping {nom_colonne_csv: champ_interne}
        """
        column_map = {}

        for csv_col in fieldnames:
            # Chercher dans le mapping direct
            if csv_col in self.COLUMN_MAPPING:
                column_map[csv_col] = self.COLUMN_MAPPING[csv_col]
                continue

            # Essayer avec normalisation
            normalized = self.normalize_column_name(csv_col)
            for ref_col, field in self.COLUMN_MAPPING.items():
                if self.normalize_column_name(ref_col) == normalized:
                    column_map[csv_col] = field
                    break

        return column_map

    def _parse_row(
        self,
        row: dict,
        column_map: dict,
        line_num: int
    ) -> Optional[BankTransactionData]:
        """
        Parse une ligne du CSV en BankTransactionData.

        Args:
            row: Dictionnaire représentant la ligne
            column_map: Mapping des colonnes
            line_num: Numéro de ligne

        Returns:
            BankTransactionData ou None si la ligne est vide/invalide
        """
        # Extraire les valeurs selon le mapping
        def get_value(field: str) -> str:
            for csv_col, mapped_field in column_map.items():
                if mapped_field == field:
                    return self.clean_text(row.get(csv_col, ''))
            return ''

        # Référence externe
        external_ref = get_value('external_reference')
        if not external_ref:
            return None  # Ligne vide ou invalide

        # Montant
        amount_str = get_value('amount')
        amount = self.normalize_amount(amount_str)

        # Dates
        tx_date = self.normalize_date(get_value('transaction_date'))
        value_date = self.normalize_date(get_value('value_date'))

        if not tx_date:
            tx_date = date.today()
        if not value_date:
            value_date = tx_date

        # Type de transaction basé sur le signe du montant
        tx_type = self.determine_transaction_type(amount)

        # Méthode de paiement
        payment_method_raw = get_value('payment_method_raw')
        payment_method = self.normalize_payment_method(payment_method_raw)

        # Contrepartie
        counterparty_iban = get_value('counterparty_iban')
        counterparty_name = get_value('counterparty_name')

        # Si l'IBAN n'est pas dans le champ dédié, essayer de l'extraire
        if not counterparty_iban:
            raw_details = get_value('raw_details')
            counterparty_iban = self.extract_iban(raw_details)

        # Communication
        communication = get_value('communication')

        # Détails bruts
        raw_details = get_value('raw_details')

        # Statut bancaire
        bank_status = get_value('bank_status') or 'Accepté'

        # Devise
        currency = get_value('currency') or 'EUR'

        return BankTransactionData(
            external_reference=external_ref,
            transaction_date=tx_date,
            value_date=value_date,
            amount=amount,
            currency=currency,
            transaction_type=tx_type,
            payment_method=payment_method,
            payment_method_raw=payment_method_raw,
            counterparty_iban=counterparty_iban,
            counterparty_name=counterparty_name,
            communication=communication,
            raw_details=raw_details,
            bank_status=bank_status,
            raw_row=dict(row),
            line_number=line_num,
        )

    def extract_practitioner_name(self, communication: str) -> Optional[str]:
        """
        Tente d'extraire un nom de pratiquant de la communication.

        Args:
            communication: Texte de la communication

        Returns:
            Nom extrait ou None
        """
        if not communication:
            return None

        # Patterns courants dans les communications
        patterns = [
            # "Prénom Nom" suivi de "cotisation", "inscription", etc.
            r'([A-Z][a-zéèêëàâäùûü]+\s+[A-Z][a-zéèêëàâäùûü]+)\s*[-:]?\s*(?:cotisation|inscription|adhésion|assurance)',
            # "Nom Prénom" au début
            r'^([A-Z][a-zéèêëàâäùûü]+\s+[A-Z][a-zéèêëàâäùûü]+)',
            # Entre guillemets ou parenthèses
            r'["\(]([A-Z][a-zéèêëàâäùûü]+\s+[A-Z][a-zéèêëàâäùûü]+)["\)]',
        ]

        import re
        for pattern in patterns:
            match = re.search(pattern, communication, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def categorize_transaction(self, transaction: BankTransactionData) -> str:
        """
        Suggère une catégorie basée sur la communication.

        Args:
            transaction: Transaction à catégoriser

        Returns:
            Code de catégorie suggérée
        """
        comm_lower = (transaction.communication or '').lower()
        details_lower = (transaction.raw_details or '').lower()
        text = f"{comm_lower} {details_lower}"

        # Revenus
        if transaction.transaction_type == 'INCOME':
            if any(w in text for w in ['cotisation', 'adhésion', 'adhesion']):
                return 'cotisation'
            if any(w in text for w in ['inscription', 'inscription']):
                return 'inscription'
            if any(w in text for w in ['équipement', 'equipement', 'materiel', 'matériel']):
                return 'vente_equipement'
            if 'assurance' in text:
                return 'assurance'
            return 'autre_revenu'

        # Dépenses
        if transaction.transaction_type == 'EXPENSE':
            if any(w in text for w in ['équipement', 'equipement', 'alibaba', 'amazon']):
                return 'achat_equipement'
            if any(w in text for w in ['remboursement', 'reimbursement']):
                return 'remboursement'
            if any(w in text for w in ['location', 'salle', 'loyer']):
                return 'location_salle'
            return 'autre_depense'

        return 'non_categorise'
