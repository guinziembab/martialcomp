"""
Intégration du module finances avec l'architecture multi-tenant.
"""
from django.db import connection
from django.utils.functional import SimpleLazyObject
from django.core.exceptions import ImproperlyConfigured
from decimal import Decimal
from typing import Dict, Any, Optional, List
import logging

from apps.multitenant.models import Tenant, TenantFeature
from apps.multitenant.utils import get_tenant_from_request
from apps.finances.models.accounts import Account, AccountType
from apps.finances.models.transactions import Transaction, TransactionType

logger = logging.getLogger('finances.tenant')


def get_tenant_account_config(tenant: Tenant) -> Dict[str, Any]:
    """
    Récupère la configuration financière spécifique au tenant.
    """
    # Configuration par défaut
    default_config = {
        # Pourcentage de commission par plan
        'commission_rates': {
            'essentials': Decimal('0.05'),  # 5%
            'masters': Decimal('0.04'),     # 4%
            'champion': Decimal('0.03'),    # 3%
        },
        # Paramètres de facturation
        'invoice_prefix': tenant.schema_name.upper()[:3],
        'payment_terms_days': 30,
        'default_currency': tenant.currency or 'EUR',
        # Paramètres fiscaux par région
        'tax_rates': {
            'EUROPE': Decimal('0.20'),      # 20% VAT (Europe)
            'NORTH_AMERICA': Decimal('0.0'), # No VAT (depends on state)
            'SOUTH_AMERICA': Decimal('0.18'), # ~18% common in South America
            'ASIA': Decimal('0.10'),        # 10% common in many Asian countries
            'OCEANIA': Decimal('0.15'),     # ~15% common (e.g., 15% in NZ, 10% in AU)
            'AFRICA': Decimal('0.15'),      # ~15% common (varies greatly by country)
        },
        # Limites financières
        'transaction_limits': {
            'essentials': {
                'daily_limit': Decimal('5000'),
                'single_transaction_limit': Decimal('1000'),
            },
            'masters': {
                'daily_limit': Decimal('10000'),
                'single_transaction_limit': Decimal('2000'),
            },
            'champion': {
                'daily_limit': Decimal('25000'),
                'single_transaction_limit': Decimal('5000'),
            },
        },
    }
    
    # Récupérer la configuration personnalisée si elle existe
    try:
        finance_feature = TenantFeature.objects.get(
            tenant=tenant,
            feature_code='financial_settings'
        )
        if finance_feature.config:
            import json
            custom_config = json.loads(finance_feature.config)
            
            # Fusionner les configurations
            for key, value in custom_config.items():
                if isinstance(value, dict) and key in default_config:
                    default_config[key].update(value)
                else:
                    default_config[key] = value
    except TenantFeature.DoesNotExist:
        pass
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Erreur dans la configuration financière du tenant {tenant.name}: {e}")
    
    return default_config


class TenantFinanceManager:
    """
    Gestionnaire des finances spécifiques Ã  un tenant.
    """
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.config = get_tenant_account_config(tenant)
    
    def initialize_accounts(self) -> bool:
        """
        Initialise les comptes par défaut pour un nouveau tenant.
        """
        try:
            # Définir le schéma du tenant
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO {self.tenant.schema_name}')
            
            # Vérifier si les comptes existent déjÃ 
            if Account.objects.filter(default_account=True).exists():
                logger.info(f"Les comptes pour le tenant {self.tenant.name} existent déjÃ ")
                return True
            
            # Créer les comptes par défaut
            accounts_to_create = [
                # Comptes de revenus
                {
                    'name': 'Revenus des compétitions',
                    'code': 'REV-COMP',
                    'type': AccountType.REVENUE,
                    'currency': self.config['default_currency'],
                    'is_active': True,
                    'default_account': True,
                },
                {
                    'name': 'Revenus des licences',
                    'code': 'REV-LIC',
                    'type': AccountType.REVENUE,
                    'currency': self.config['default_currency'],
                    'is_active': True,
                    'default_account': True,
                },
                {
                    'name': 'Revenus des grades',
                    'code': 'REV-GRADE',
                    'type': AccountType.REVENUE,
                    'currency': self.config['default_currency'],
                    'is_active': True,
                    'default_account': True,
                },
                # Comptes de dépenses
                {
                    'name': 'Frais de plateforme',
                    'code': 'EXP-PLAT',
                    'type': AccountType.EXPENSE,
                    'currency': self.config['default_currency'],
                    'is_active': True,
                    'default_account': True,
                },
                {
                    'name': 'Commissions bancaires',
                    'code': 'EXP-BANK',
                    'type': AccountType.EXPENSE,
                    'currency': self.config['default_currency'],
                    'is_active': True,
                    'default_account': True,
                },
                # Comptes d'actifs
                {
                    'name': 'Compte principal',
                    'code': 'ASSET-MAIN',
                    'type': AccountType.ASSET,
                    'currency': self.config['default_currency'],
                    'is_active': True,
                    'default_account': True,
                },
                # Comptes de passifs
                {
                    'name': 'TVA collectée',
                    'code': 'LIAB-VAT',
                    'type': AccountType.LIABILITY,
                    'currency': self.config['default_currency'],
                    'is_active': True,
                    'default_account': True,
                },
            ]
            
            # Créer les comptes
            for account_data in accounts_to_create:
                Account.objects.create(**account_data)
            
            logger.info(f"Comptes initialisés pour le tenant {self.tenant.name}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des comptes pour {self.tenant.name}: {e}")
            return False
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des comptes du tenant.
        """
        # Définir le schéma du tenant
        with connection.cursor() as cursor:
            cursor.execute(f'SET search_path TO {self.tenant.schema_name}')
        
        # Récupérer les soldes par type de compte
        summary = {
            'revenue': Account.objects.filter(type=AccountType.REVENUE).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
            
            'expense': Account.objects.filter(type=AccountType.EXPENSE).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
            
            'asset': Account.objects.filter(type=AccountType.ASSET).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
            
            'liability': Account.objects.filter(type=AccountType.LIABILITY).aggregate(
                total=Sum('balance')
            )['total'] or Decimal('0'),
        }
        
        # Calculer les totaux
        summary['net_income'] = summary['revenue'] - summary['expense']
        summary['net_worth'] = summary['asset'] - summary['liability']
        
        # Ajouter les informations de facturation
        from apps.finances.models.invoices import Invoice
        from django.db.models import Count, Sum
        
        invoice_stats = Invoice.objects.aggregate(
            total_count=Count('id'),
            unpaid_count=Count('id', filter=Q(status='unpaid')),
            total_amount=Sum('total_amount'),
            unpaid_amount=Sum('total_amount', filter=Q(status='unpaid')),
        )
        
        summary.update(invoice_stats)
        
        return summary
    
    def calculate_platform_fee(self, amount: Decimal) -> Decimal:
        """
        Calcule les frais de plateforme en fonction du plan du tenant.
        """
        rate = self.config['commission_rates'].get(
            self.tenant.subscription_plan,
            Decimal('0.05')  # Taux par défaut si plan inconnu
        )
        
        return (amount * rate).quantize(Decimal('0.01'))
    
    def record_platform_fee(self, source_transaction: Transaction) -> Optional[Transaction]:
        """
        Enregistre les frais de plateforme pour une transaction.
        """
        try:
            # Définir le schéma du tenant
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO {self.tenant.schema_name}')
            
            # Calculer les frais
            fee_amount = self.calculate_platform_fee(source_transaction.amount)
            
            if fee_amount == Decimal('0'):
                return None
            
            # Trouver les comptes
            try:
                expense_account = Account.objects.get(code='EXP-PLAT', default_account=True)
                asset_account = Account.objects.get(code='ASSET-MAIN', default_account=True)
            except Account.DoesNotExist:
                logger.error(f"Comptes par défaut manquants pour {self.tenant.name}")
                return None
            
            # Créer la transaction
            fee_transaction = Transaction.objects.create(
                description=f"Frais de plateforme pour {source_transaction.reference}",
                transaction_type=TransactionType.PLATFORM_FEE,
                amount=fee_amount,
                currency=source_transaction.currency,
                from_account=asset_account,
                to_account=expense_account,
                reference=f"FEE-{source_transaction.reference}",
                related_transaction=source_transaction,
                metadata={
                    'source_transaction_id': str(source_transaction.id),
                    'fee_rate': str(self.config['commission_rates'].get(self.tenant.subscription_plan)),
                    'plan': self.tenant.subscription_plan,
                }
            )
            
            return fee_transaction
        
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des frais pour {self.tenant.name}: {e}")
            return None


# Middleware pour l'intégration finances-tenant
class TenantFinanceMiddleware:
    """
    Middleware qui lie les finances au contexte tenant.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ajouter le gestionnaire finances au contexte tenant
        if hasattr(request, 'tenant') and request.tenant:
            request.tenant_finance = SimpleLazyObject(
                lambda: TenantFinanceManager(request.tenant)
            )
        
        response = self.get_response(request)
        return response


# Utilitaire pour l'intégration dans les vues
def tenant_finance_required(view_func):
    """
    Décorateur qui s'assure qu'un gestionnaire de finances tenant est disponible.
    """
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            raise ImproperlyConfigured("Tenant context required")
        
        if not hasattr(request, 'tenant_finance'):
            request.tenant_finance = TenantFinanceManager(request.tenant)
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


# Initialisation des comptes pour les nouveaux tenants
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Tenant)
def initialize_tenant_finances(sender, instance, created, **kwargs):
    """
    Initialise les finances pour un nouveau tenant.
    """
    if created:
        manager = TenantFinanceManager(instance)
        manager.initialize_accounts()

