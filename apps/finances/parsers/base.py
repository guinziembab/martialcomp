# -*- coding: utf-8 -*-
"""
Classe de base pour les parseurs de relevés bancaires.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional
import re


@dataclass
class BankTransactionData:
    """
    Structure de données pour une transaction bancaire parsée.
    Représentation intermédiaire avant création du modèle BankTransaction.
    """
    external_reference: str
    transaction_date: date
    value_date: date
    amount: Decimal
    currency: str = 'EUR'
    transaction_type: str = 'INCOME'  # INCOME ou EXPENSE
    payment_method: str = 'autre'
    payment_method_raw: str = ''
    counterparty_iban: str = ''
    counterparty_name: str = ''
    communication: str = ''
    raw_details: str = ''
    bank_status: str = 'Accepté'

    # Métadonnées pour le parsing
    raw_row: dict = field(default_factory=dict)
    parsing_errors: List[str] = field(default_factory=list)
    line_number: int = 0

    def is_valid(self) -> bool:
        """Vérifie si la transaction a les données minimales requises."""
        return bool(
            self.external_reference and
            self.transaction_date and
            self.amount is not None
        )

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour création du modèle."""
        return {
            'external_reference': self.external_reference,
            'transaction_date': self.transaction_date,
            'value_date': self.value_date,
            'amount': abs(self.amount),  # Toujours positif
            'currency': self.currency,
            'transaction_type': self.transaction_type,
            'payment_method': self.payment_method,
            'payment_method_raw': self.payment_method_raw,
            'counterparty_iban': self.counterparty_iban,
            'counterparty_name': self.counterparty_name,
            'communication': self.communication,
            'raw_details': self.raw_details,
            'bank_status': self.bank_status,
        }


class BaseBankParser(ABC):
    """
    Classe abstraite pour les parseurs de relevés bancaires.
    Chaque format bancaire doit implémenter cette interface.
    """

    # Identifiant unique du format
    BANK_CODE = 'GENERIC'
    BANK_NAME = 'Format Générique'

    # Formats supportés
    SUPPORTED_FORMATS = ['csv']

    # Configuration du parsing
    ENCODING = 'utf-8'
    DELIMITER = ';'
    DATE_FORMAT = '%d/%m/%Y'
    DECIMAL_SEPARATOR = ','
    THOUSANDS_SEPARATOR = ' '

    # Mapping des méthodes de paiement
    PAYMENT_METHOD_MAPPING = {
        'virement instantané': 'virement_instantane',
        'virement instantane': 'virement_instantane',
        'instant transfer': 'virement_instantane',
        'virement': 'virement',
        'transfer': 'virement',
        'paiement par carte': 'paiement_carte',
        'card payment': 'paiement_carte',
        'paiement carte': 'paiement_carte',
        'carte de crédit': 'paiement_carte_credit',
        'credit card': 'paiement_carte_credit',
        'prélèvement': 'prelevement',
        'direct debit': 'prelevement',
        'domiciliation': 'prelevement',
        'chèque': 'cheque',
        'check': 'cheque',
        'espèces': 'especes',
        'cash': 'especes',
        'mobile money': 'mobile_money',
    }

    @abstractmethod
    def detect_format(self, file_content: bytes) -> bool:
        """
        Détecte si le fichier correspond à ce format bancaire.

        Args:
            file_content: Contenu du fichier en bytes

        Returns:
            True si le fichier correspond au format
        """
        pass

    @abstractmethod
    def parse(self, file_content: bytes) -> List[BankTransactionData]:
        """
        Parse le fichier et retourne les transactions.

        Args:
            file_content: Contenu du fichier en bytes

        Returns:
            Liste des transactions parsées
        """
        pass

    def normalize_amount(self, amount_str: str) -> Decimal:
        """
        Normalise une chaîne de montant en Decimal.

        Args:
            amount_str: Chaîne représentant le montant

        Returns:
            Montant en Decimal
        """
        if not amount_str:
            return Decimal('0.00')

        # Nettoyer la chaîne
        amount_str = str(amount_str).strip()

        # Supprimer les espaces (séparateurs de milliers)
        amount_str = amount_str.replace(' ', '').replace('\xa0', '')

        # Remplacer le séparateur décimal
        if self.DECIMAL_SEPARATOR != '.':
            amount_str = amount_str.replace(self.DECIMAL_SEPARATOR, '.')

        # Supprimer les séparateurs de milliers restants
        if self.THOUSANDS_SEPARATOR and self.THOUSANDS_SEPARATOR != '.':
            amount_str = amount_str.replace(self.THOUSANDS_SEPARATOR, '')

        try:
            return Decimal(amount_str)
        except InvalidOperation:
            return Decimal('0.00')

    def normalize_date(self, date_str: str) -> Optional[date]:
        """
        Normalise une chaîne de date.

        Args:
            date_str: Chaîne représentant la date

        Returns:
            Date ou None si invalide
        """
        if not date_str:
            return None

        from datetime import datetime

        date_str = str(date_str).strip()

        # Essayer plusieurs formats
        formats_to_try = [
            self.DATE_FORMAT,
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y/%m/%d',
        ]

        for fmt in formats_to_try:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def normalize_payment_method(self, method_str: str) -> str:
        """
        Normalise la méthode de paiement vers le code interne.

        Args:
            method_str: Chaîne décrivant la méthode de paiement

        Returns:
            Code de méthode de paiement normalisé
        """
        if not method_str:
            return 'autre'

        method_lower = method_str.lower().strip()

        # Chercher une correspondance dans le mapping
        for key, value in self.PAYMENT_METHOD_MAPPING.items():
            if key in method_lower:
                return value

        return 'autre'

    def clean_text(self, text: str) -> str:
        """
        Nettoie une chaîne de texte.

        Args:
            text: Texte à nettoyer

        Returns:
            Texte nettoyé
        """
        if not text:
            return ''

        # Convertir en string si nécessaire
        text = str(text)

        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)

        # Supprimer les espaces en début et fin
        text = text.strip()

        return text

    def extract_iban(self, text: str) -> str:
        """
        Extrait un IBAN d'une chaîne de texte.

        Args:
            text: Texte contenant potentiellement un IBAN

        Returns:
            IBAN extrait ou chaîne vide
        """
        if not text:
            return ''

        # Pattern IBAN générique (2 lettres + 2 chiffres + jusqu'à 30 caractères)
        iban_pattern = r'[A-Z]{2}\d{2}[A-Z0-9]{4,30}'

        # Nettoyer les espaces
        text_cleaned = text.replace(' ', '').upper()

        match = re.search(iban_pattern, text_cleaned)
        if match:
            return match.group()

        return ''

    def determine_transaction_type(self, amount: Decimal) -> str:
        """
        Détermine le type de transaction basé sur le montant.

        Args:
            amount: Montant de la transaction

        Returns:
            'INCOME' si positif, 'EXPENSE' si négatif
        """
        return 'INCOME' if amount >= 0 else 'EXPENSE'

    def validate_transactions(
        self, transactions: List[BankTransactionData]
    ) -> List[BankTransactionData]:
        """
        Valide et filtre les transactions parsées.

        Args:
            transactions: Liste des transactions à valider

        Returns:
            Liste des transactions valides
        """
        valid_transactions = []

        for tx in transactions:
            if tx.is_valid():
                valid_transactions.append(tx)
            else:
                tx.parsing_errors.append("Données minimales manquantes")

        return valid_transactions
