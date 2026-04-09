# -*- coding: utf-8 -*-
"""
Parseurs pour l'import de relevés bancaires.
"""

from .base import BaseBankParser, BankTransactionData
from .bnp_fortis import BNPParibasFortisParser
from .societe_generale import SocieteGeneraleParser
from .orange_money import OrangeMoneyParser
from .wave import WaveParser

# Registry des parseurs disponibles
PARSER_REGISTRY = {
    # Banques européennes
    'BNP_FORTIS_BE': BNPParibasFortisParser,
    'SOCIETE_GENERALE_FR': SocieteGeneraleParser,
    # Mobile Money Afrique
    'ORANGE_MONEY_CI': OrangeMoneyParser,
    'WAVE_SN': WaveParser,
}


def get_parser(bank_format: str) -> BaseBankParser:
    """
    Retourne une instance du parseur pour le format bancaire spécifié.

    Args:
        bank_format: Code du format bancaire (ex: 'BNP_FORTIS_BE')

    Returns:
        Instance du parseur

    Raises:
        ValueError: Si le format n'est pas supporté
    """
    parser_class = PARSER_REGISTRY.get(bank_format)
    if not parser_class:
        raise ValueError(f"Format bancaire non supporté: {bank_format}")
    return parser_class()


def detect_bank_format(file_content: bytes) -> str:
    """
    Détecte automatiquement le format bancaire d'un fichier.

    Args:
        file_content: Contenu du fichier en bytes

    Returns:
        Code du format bancaire détecté

    Raises:
        ValueError: Si le format n'est pas reconnu
    """
    for bank_code, parser_class in PARSER_REGISTRY.items():
        parser = parser_class()
        if parser.detect_format(file_content):
            return bank_code

    raise ValueError("Format bancaire non reconnu")


__all__ = [
    'BaseBankParser',
    'BankTransactionData',
    'BNPParibasFortisParser',
    'SocieteGeneraleParser',
    'OrangeMoneyParser',
    'WaveParser',
    'PARSER_REGISTRY',
    'get_parser',
    'detect_bank_format',
]
