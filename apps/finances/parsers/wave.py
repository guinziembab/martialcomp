# -*- coding: utf-8 -*-
"""
Parseur pour les relevés Wave (Sénégal et Afrique de l'Ouest).

Format CSV avec les caractéristiques:
- Encodage: UTF-8
- Séparateur: Virgule (,)
- Format de date: YYYY-MM-DD ou DD/MM/YYYY
- Montants en FCFA (XOF)
"""

import csv
import io
from datetime import date
from decimal import Decimal
from typing import List, Optional

from .base import BaseBankParser, BankTransactionData


class WaveParser(BaseBankParser):
    """
    Parseur pour les relevés Wave (Sénégal et Afrique de l'Ouest).
    Supporte les exports de l'application mobile et web.
    """

    BANK_CODE = 'WAVE_SN'
    BANK_NAME = 'Wave (Sénégal)'

    SUPPORTED_FORMATS = ['csv']
    ENCODING = 'utf-8'
    DELIMITER = ','
    DATE_FORMAT = '%Y-%m-%d'
    DECIMAL_SEPARATOR = '.'
    THOUSANDS_SEPARATOR = ','

    # Mapping des colonnes
    COLUMN_MAPPING = {
        # Variations des noms de colonnes (anglais et français)
        'Date': 'transaction_date',
        'Transaction Date': 'transaction_date',
        'Date de transaction': 'transaction_date',
        'Created At': 'transaction_date',
        'Time': 'time',
        'Heure': 'time',
        'Type': 'transaction_type_raw',
        'Transaction Type': 'transaction_type_raw',
        'Type de transaction': 'transaction_type_raw',
        'Amount': 'amount',
        'Montant': 'amount',
        'Amount (XOF)': 'amount',
        'Fee': 'fees',
        'Fees': 'fees',
        'Frais': 'fees',
        'Balance': 'balance',
        'Solde': 'balance',
        'Recipient': 'counterparty_name',
        'Destinataire': 'counterparty_name',
        'Sender': 'counterparty_name',
        'Expéditeur': 'counterparty_name',
        'Name': 'counterparty_name',
        'Nom': 'counterparty_name',
        'Phone': 'counterparty_phone',
        'Téléphone': 'counterparty_phone',
        'Phone Number': 'counterparty_phone',
        'Numéro': 'counterparty_phone',
        'Reference': 'external_reference',
        'Référence': 'external_reference',
        'Transaction ID': 'external_reference',
        'ID': 'external_reference',
        'Note': 'communication',
        'Description': 'communication',
        'Motif': 'communication',
        'Status': 'status',
        'Statut': 'status',
    }

    # Types de transactions Wave
    TRANSACTION_TYPES = {
        # Entrées
        'deposit': 'INCOME',
        'dépôt': 'INCOME',
        'receive': 'INCOME',
        'received': 'INCOME',
        'reçu': 'INCOME',
        'incoming': 'INCOME',
        'cash in': 'INCOME',
        'cash-in': 'INCOME',
        'remboursement': 'INCOME',
        'refund': 'INCOME',
        # Sorties
        'withdrawal': 'EXPENSE',
        'retrait': 'EXPENSE',
        'send': 'EXPENSE',
        'sent': 'EXPENSE',
        'envoi': 'EXPENSE',
        'envoyé': 'EXPENSE',
        'outgoing': 'EXPENSE',
        'cash out': 'EXPENSE',
        'cash-out': 'EXPENSE',
        'payment': 'EXPENSE',
        'paiement': 'EXPENSE',
        'transfer': 'EXPENSE',
        'transfert': 'EXPENSE',
        'bill': 'EXPENSE',
        'facture': 'EXPENSE',
        'merchant': 'EXPENSE',
        'marchand': 'EXPENSE',
    }

    def detect_format(self, file_content: bytes) -> bool:
        """
        Détecte si le fichier est un relevé Wave.
        """
        try:
            # Essayer plusieurs encodages
            text = None
            for encoding in ['utf-8-sig', 'utf-8', 'iso-8859-1']:
                try:
                    text = file_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if not text:
                return False

            text_lower = text.lower()
            first_lines = text.split('\n')[:10]
            header = first_lines[0].lower() if first_lines else ''

            # Indicateurs Wave
            indicators = [
                'wave' in text_lower[:1000],
                'xof' in text_lower[:1000] or 'fcfa' in text_lower[:1000],
                ('transaction' in header and 'amount' in header) or (
                    'transaction' in header and 'montant' in header
                ),
                any(
                    keyword in header
                    for keyword in ['recipient', 'sender', 'destinataire']
                ),
                'cash in' in text_lower[:500] or 'cash out' in text_lower[:500],
            ]

            return sum(indicators) >= 2

        except Exception:
            return False

    def parse(self, file_content: bytes) -> List[BankTransactionData]:
        """
        Parse le fichier CSV Wave.
        """
        transactions = []

        # Détecter l'encodage
        text = None
        for encoding in ['utf-8-sig', 'utf-8', 'iso-8859-1']:
            try:
                text = file_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if not text:
            raise ValueError("Impossible de décoder le fichier")

        # Détecter le délimiteur
        first_line = text.split('\n')[0] if text else ''
        if ';' in first_line and ',' not in first_line:
            delimiter = ';'
        else:
            delimiter = ','

        try:
            reader = csv.DictReader(
                io.StringIO(text),
                delimiter=delimiter
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
                        currency='XOF',
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

        # Montant
        amount_str = get_value('amount')
        if not amount_str:
            return None

        # Wave utilise généralement le point comme séparateur décimal
        amount = self._parse_wave_amount(amount_str)
        if amount == Decimal('0.00'):
            return None

        # Type de transaction
        tx_type_raw = get_value('transaction_type_raw')
        tx_type = self._determine_transaction_type(tx_type_raw, amount)

        # Référence externe
        external_ref = get_value('external_reference')
        if not external_ref:
            # Générer une référence
            tx_date_str = get_value('transaction_date')
            external_ref = f"WAVE-{tx_date_str}-{abs(amount)}-{line_num}"

        # Date
        tx_date = self.normalize_date(get_value('transaction_date'))
        if not tx_date:
            return None

        # Communication
        communication = get_value('communication')
        if not communication:
            communication = tx_type_raw

        # Contrepartie
        counterparty_name = get_value('counterparty_name')
        counterparty_phone = get_value('counterparty_phone')

        # Frais (optionnel)
        fees_str = get_value('fees')
        fees = self._parse_wave_amount(fees_str) if fees_str else Decimal('0.00')

        # Construire les détails bruts
        raw_details = f"Type: {tx_type_raw}"
        if counterparty_phone:
            raw_details += f" | Tél: {counterparty_phone}"
        if fees > 0:
            raw_details += f" | Frais: {fees} XOF"

        # Statut
        status = get_value('status')
        if not status or status.lower() in ['completed', 'success', 'terminé']:
            bank_status = 'Accepté'
        elif status.lower() in ['pending', 'en attente']:
            bank_status = 'En attente'
        elif status.lower() in ['failed', 'échec', 'annulé']:
            bank_status = 'Rejeté'
        else:
            bank_status = status

        return BankTransactionData(
            external_reference=external_ref,
            transaction_date=tx_date,
            value_date=tx_date,  # Wave n'a pas de date valeur
            amount=abs(amount),
            currency='XOF',  # Franc CFA (BCEAO)
            transaction_type=tx_type,
            payment_method='mobile_money',
            payment_method_raw=tx_type_raw,
            counterparty_iban='',  # Pas d'IBAN pour mobile money
            counterparty_name=counterparty_name or counterparty_phone,
            communication=communication,
            raw_details=raw_details,
            bank_status=bank_status,
            raw_row=dict(row),
            line_number=line_num,
        )

    def _parse_wave_amount(self, amount_str: str) -> Decimal:
        """
        Parse un montant Wave (format anglophone avec point décimal).
        """
        if not amount_str:
            return Decimal('0.00')

        # Nettoyer la chaîne
        amount_str = str(amount_str).strip()

        # Supprimer les espaces et symboles de devise
        amount_str = amount_str.replace(' ', '').replace('XOF', '').replace('FCFA', '')
        amount_str = amount_str.replace('\xa0', '')

        # Wave peut utiliser virgule ou point
        # Si les deux sont présents, le dernier est le séparateur décimal
        if ',' in amount_str and '.' in amount_str:
            # Format 1,234.56 ou 1.234,56
            if amount_str.rfind('.') > amount_str.rfind(','):
                # Format anglais: 1,234.56
                amount_str = amount_str.replace(',', '')
            else:
                # Format français: 1.234,56
                amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str:
            # Peut être 1234,56 (français) ou 1,234 (anglais sans décimales)
            # Si la virgule est suivie de exactement 2 chiffres, c'est le séparateur décimal
            parts = amount_str.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                amount_str = amount_str.replace(',', '.')
            else:
                amount_str = amount_str.replace(',', '')

        try:
            return Decimal(amount_str)
        except Exception:
            return Decimal('0.00')

    def _determine_transaction_type(
        self,
        type_raw: str,
        amount: Decimal
    ) -> str:
        """
        Détermine le type de transaction (INCOME/EXPENSE).
        """
        if type_raw:
            type_lower = type_raw.lower().strip()
            for keyword, tx_type in self.TRANSACTION_TYPES.items():
                if keyword in type_lower:
                    return tx_type

        # Par défaut, basé sur le signe du montant
        return 'INCOME' if amount >= 0 else 'EXPENSE'
