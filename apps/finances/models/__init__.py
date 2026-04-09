# -*- coding: utf-8 -*-
"""
Imports des modèles de l'application finances
"""

from .transactions import Transaction, TransactionCategory, TransactionAttachment
from .payments import PaymentMethod, PaymentAttempt
from .invoices import Invoice, InvoiceItem
from .accounts import AccountingCategory, FinancialAccount, MembershipFee
from .combat import (
    Combat, CombatScore, CombatPenalty, CombatRound,
    CombatPool, CombatTeam, CombatTeamMember
)
from .combat_finances import CombatFee, CombatRegistrationPayment

# Banking import models
from .banking import (
    BankImportBatch,
    BankTransaction,
    ReconciliationRule,
    PractitionerBankInfo,
)

# Imports requis avec gestion d'erreurs
try:
    from .pricing import PricingRegion, VolumeDiscount
except ImportError:
    from django.db import models

    class PricingRegion(models.Model):
        name = models.CharField(max_length=100, default='Default Region')

        class Meta:
            app_label = 'finances'
            verbose_name = 'Pricing Region'
            verbose_name_plural = 'Pricing Regions'

        def __str__(self):
            return self.name

    class VolumeDiscount(models.Model):
        name = models.CharField(max_length=100, default='Default Discount')

        class Meta:
            app_label = 'finances'
            verbose_name = 'Volume Discount'
            verbose_name_plural = 'Volume Discounts'

        def __str__(self):
            return self.name

try:
    from .subscription import (
        Subscription, SubscriptionPayment, SubscriptionTier,
        FeatureFlag, OrganizationSubscription, FeatureUsageLog
    )
except ImportError:
    from django.db import models

    class FeatureFlag(models.Model):
        name = models.CharField(max_length=100, default='Default Feature')

        class Meta:
            app_label = 'finances'
            verbose_name = 'Feature Flag'
            verbose_name_plural = 'Feature Flags'

        def __str__(self):
            return self.name

    class OrganizationSubscription(models.Model):
        name = models.CharField(max_length=100, default='Default Subscription')

        class Meta:
            app_label = 'finances'
            verbose_name = 'Organization Subscription'
            verbose_name_plural = 'Organization Subscriptions'

        def __str__(self):
            return self.name

    class FeatureUsageLog(models.Model):
        name = models.CharField(max_length=100, default='Default Usage Log')

        class Meta:
            app_label = 'finances'
            verbose_name = 'Feature Usage Log'
            verbose_name_plural = 'Feature Usage Logs'

        def __str__(self):
            return self.name

# Currency models (Multi-devise) - Phase 1
try:
    from .currency import Currency, ExchangeRate
except ImportError:
    Currency = None
    ExchangeRate = None

__all__ = [
    'Transaction',
    'TransactionCategory',
    'TransactionAttachment',
    'PaymentMethod',
    'PaymentAttempt',
    'Invoice',
    'InvoiceItem',
    'AccountingCategory',
    'FinancialAccount',
    'MembershipFee',
    # Combat models
    'Combat',
    'CombatScore',
    'CombatPenalty',
    'CombatRound',
    'CombatPool',
    'CombatTeam',
    'CombatTeamMember',
    # Combat finance models
    'CombatFee',
    'CombatRegistrationPayment',
    # Pricing models
    'PricingRegion',
    'VolumeDiscount',
    # Subscription models
    'Subscription',
    'SubscriptionPayment',
    'SubscriptionTier',
    'FeatureFlag',
    'OrganizationSubscription',
    'FeatureUsageLog',
    # Banking import models
    'BankImportBatch',
    'BankTransaction',
    'ReconciliationRule',
    'PractitionerBankInfo',
    # Currency models (Multi-devise)
    'Currency',
    'ExchangeRate',
]
