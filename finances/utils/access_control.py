"""
Contrôle d'accès avancé pour le module finances.
Ce module fournit des fonctions pour vérifier les droits d'accès avancés
en fonction des montants, des entités et des limites utilisateur.
"""

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import Group, User
from django.db.models import Sum, Q
from django.core.exceptions import PermissionDenied
from decimal import Decimal

from ..models.transactions import Transaction
from .permissions import can_view_transaction, can_validate_transaction

def get_user_transaction_limits(user):
    """
    Récupère les limites de transaction pour un utilisateur en fonction de son rôle.
    
    Args:
        user (User): L'utilisateur dont on veut connaître les limites
    
    Returns:
        dict: Dictionnaire contenant les limites de transaction
    """
    # Par défaut, limites minimales
    default_limits = {
        'daily_limit': Decimal('1000.00'),
        'transaction_limit': Decimal('500.00'),
    }
    
    # Si l'utilisateur est superutilisateur, pas de limites
    if user.is_superuser:
        return {
            'daily_limit': Decimal('1000000.00'),  # Un million (pratiquement pas de limite)
            'transaction_limit': Decimal('1000000.00'),
        }
    
    # Vérifier les groupes de l'utilisateur
    user_groups = user.groups.values_list('name', flat=True)
    
    # Récupérer les limites selon les paramètres
    transaction_limits = getattr(settings, 'TRANSACTION_LIMITS', {})
    
    # Définir le rôle le plus élevé
    if 'Finance Admin' in user_groups:
        role = 'finance_admin'
    elif 'Finance Manager' in user_groups:
        role = 'finance_manager'
    elif 'Transaction Manager' in user_groups or 'Invoice Manager' in user_groups:
        role = 'club_manager'
    else:
        role = 'default'
    
    # Récupérer les limites pour ce rôle
    limits = transaction_limits.get(role, default_limits)
    
    return {
        'daily_limit': Decimal(str(limits.get('daily_limit', default_limits['daily_limit']))),
        'transaction_limit': Decimal(str(limits.get('transaction_limit', default_limits['transaction_limit']))),
    }


def check_transaction_amount_limits(user, amount):
    """
    Vérifie si le montant d'une transaction respecte les limites de l'utilisateur.
    
    Args:
        user (User): L'utilisateur qui effectue la transaction
        amount (Decimal): Le montant de la transaction
    
    Returns:
        bool: True si le montant est dans les limites, False sinon
    """
    # Si l'utilisateur est superutilisateur, pas de limites
    if user.is_superuser:
        return True
    
    # Récupérer les limites de l'utilisateur
    limits = get_user_transaction_limits(user)
    
    # Vérifier la limite par transaction
    if Decimal(str(amount)) > limits['transaction_limit']:
        return False
    
    # Vérifier la limite quotidienne
    today = timezone.now().date()
    daily_transactions = Transaction.objects.filter(
        created_by=user,
        date=today,
        status__in=['validated', 'pending']
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
    
    if (daily_transactions + Decimal(str(amount))) > limits['daily_limit']:
        return False
        
    return True


def check_validation_requirements(transaction):
    """
    Vérifie les exigences de validation pour une transaction en fonction de son montant.
    
    Args:
        transaction (Transaction): La transaction à vérifier
    
    Returns:
        dict: Informations sur les exigences de validation
    """
    # Récupérer les seuils et exigences depuis les paramètres
    thresholds = getattr(settings, 'TRANSACTION_THRESHOLDS', {
        'high_amount': 10000,
        'very_high_amount': 50000,
    })
    
    validators_required = getattr(settings, 'TRANSACTION_VALIDATORS_REQUIRED', {
        'default': 1,
        'high_amount': 2,
        'very_high_amount': 3,
    })
    
    # Déterminer le niveau d'importance
    amount = transaction.amount
    if amount >= Decimal(str(thresholds.get('very_high_amount', 50000))):
        importance = 'very_high_amount'
    elif amount >= Decimal(str(thresholds.get('high_amount', 10000))):
        importance = 'high_amount'
    else:
        importance = 'default'
    
    # Nombre de validateurs requis pour ce niveau
    required_validators = validators_required.get(importance, 1)
    
    # Nombre actuel de validations
    current_validations = transaction.validations.count() if hasattr(transaction, 'validations') else 0
    
    return {
        'importance': importance,
        'required_validators': required_validators,
        'current_validations': current_validations,
        'is_fully_validated': current_validations >= required_validators,
    }


def can_approve_transaction(user, transaction):
    """
    Vérifie si l'utilisateur peut approuver définitivement une transaction.
    Prend en compte les validations multiples si nécessaire.
    
    Args:
        user (User): L'utilisateur qui tente d'approuver
        transaction (Transaction): La transaction à approuver
    
    Returns:
        bool: True si l'utilisateur peut approuver, False sinon
    """
    # Si l'utilisateur a la permission d'approbation globale
    if user.has_perm('finances.approve_all_transactions'):
        return True
    
    # Vérifier si l'utilisateur peut valider la transaction
    if not can_validate_transaction(user, transaction):
        return False
    
    # Vérifier les exigences de validation
    validation_info = check_validation_requirements(transaction)
    
    # Si la transaction est de faible importance, une seule validation suffit
    if validation_info['importance'] == 'default':
        return True
    
    # Pour les transactions importantes, vérifier le nombre de validations
    # et si l'utilisateur a le bon niveau d'autorité
    user_groups = user.groups.values_list('name', flat=True)
    
    # Si c'est un admin finance, il peut toujours approuver
    if 'Finance Admin' in user_groups:
        return True
    
    # Un manager finance peut approuver les transactions à haute importance
    if validation_info['importance'] == 'high_amount' and 'Finance Manager' in user_groups:
        # Vérifier si le nombre de validations est suffisant
        return validation_info['current_validations'] >= validation_info['required_validators'] - 1
    
    # Pour les transactions très importantes, seul un admin peut approuver
    if validation_info['importance'] == 'very_high_amount':
        return False
    
    return False


def is_transaction_locked(transaction):
    """
    Vérifie si une transaction est verrouillée (ne peut plus être modifiée).
    
    Args:
        transaction (Transaction): La transaction à vérifier
    
    Returns:
        bool: True si la transaction est verrouillée, False sinon
    """
    # Si la transaction est déjà verrouillée
    if hasattr(transaction, 'is_locked') and transaction.is_locked:
        return True
    
    # Récupérer les paramètres de verrouillage
    lock_settings = getattr(settings, 'TRANSACTION_LOCK_SETTINGS', {
        'lock_after_days': 30,
        'hard_lock_after_days': 90,
    })
    
    # Vérifier si la transaction est assez ancienne pour être verrouillée
    today = timezone.now().date()
    transaction_date = transaction.date
    
    # Verrouillage dur après X jours, peu importe le statut
    days_since_transaction = (today - transaction_date).days
    if days_since_transaction >= lock_settings.get('hard_lock_after_days', 90):
        return True
    
    # Verrouillage des transactions validées ou rejetées après Y jours
    if transaction.status in ['validated', 'rejected'] and days_since_transaction >= lock_settings.get('lock_after_days', 30):
        return True
    
    return False


def check_fraud_indicators(transaction):
    """
    Vérifie les indicateurs potentiels de fraude dans une transaction.
    
    Args:
        transaction (Transaction): La transaction à vérifier
    
    Returns:
        dict: Résultats de l'analyse avec les indicateurs de risque
    """
    # Récupérer les paramètres de détection de fraude
    fraud_settings = getattr(settings, 'FRAUD_DETECTION_SETTINGS', {
        'enable': True,
        'flagged_transaction_types': ['expense'],
        'suspicious_amount_threshold': 10000,
    })
    
    # Si la détection de fraude est désactivée
    if not fraud_settings.get('enable', True):
        return {'risk_level': 'none', 'indicators': []}
    
    indicators = []
    risk_level = 'none'
    
    # Vérifier le type de transaction
    if transaction.type in fraud_settings.get('flagged_transaction_types', ['expense']):
        # Vérifier le montant
        if transaction.amount >= Decimal(str(fraud_settings.get('suspicious_amount_threshold', 10000))):
            indicators.append('high_amount')
            risk_level = 'medium'
        
        # Vérifier si la transaction a été créée et validée par la même personne
        if transaction.created_by == transaction.validated_by:
            indicators.append('same_person_validation')
            risk_level = 'high' if risk_level == 'medium' else 'medium'
        
        # Vérifier si la transaction a été créée récemment et pour une date antérieure
        today = timezone.now().date()
        if (today - transaction.date).days > 30 and (today - transaction.created_at.date()).days < 7:
            indicators.append('backdated_transaction')
            risk_level = 'high'
        
        # Vérifier si la transaction a été traitée en dehors des heures normales
        created_hour = transaction.created_at.hour
        if created_hour < 7 or created_hour > 19:
            indicators.append('unusual_time')
            risk_level = 'medium' if risk_level == 'none' else risk_level
    
    return {
        'risk_level': risk_level,
        'indicators': indicators
    }