"""
Service de paiement pour la gestion des abonnements et fonctionnalités Ã  l'usage
"""
from django.utils import timezone
from decimal import Decimal
import logging
from typing import Dict, Any, Optional, List, Tuple

from django.conf import settings
from django.apps import apps
from ..models import (
    Tenant, SubscriptionTier, TenantSubscription,
    PayPerUseFeature, FeatureUsage, PromotionCode
)
from .models import LegacyTenantSubscription
from .base import PaymentProviderFactory, PaymentProviderError

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service pour gérer les paiements, abonnements et facturation des fonctionnalités Ã  l'usage.
    """
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.provider = self._get_payment_provider()
    
    def _get_payment_provider(self):
        """
        Sélectionne le fournisseur de paiement approprié en fonction de la région du tenant.
        """
        # Mapping des régions vers les fournisseurs de paiement
        region_mapping = getattr(settings, 'PAYMENT_REGION_MAPPING', {
            'africa': 'paystack',
            'europe_west': 'stripe',
            'europe_east': 'stripe',
            'north_america': 'stripe',
            'south_america': 'mercadopago',
            'central_america': 'mercadopago',
            'asia_se': 'stripe',
            'asia_other': 'alipay',
            'middle_east': 'stripe',
            'oceania': 'stripe',
        })
        
        # Sélection du fournisseur basée sur la région ou le fournisseur spécifié du tenant
        if self.tenant.payment_provider:
            provider_name = self.tenant.payment_provider
        else:
            provider_name = region_mapping.get(self.tenant.continent, 'stripe')
        
        # Récupération de la configuration du fournisseur
        provider_config = getattr(settings, 'PAYMENT_PROVIDERS', {}).get(provider_name)
        if not provider_config:
            logger.warning(f"Configuration introuvable pour le fournisseur: {provider_name}, utilisation de Stripe par défaut")
            provider_name = 'stripe'
            provider_config = getattr(settings, 'PAYMENT_PROVIDERS', {}).get('stripe', {})
        
        return PaymentProviderFactory.create_provider(provider_name, provider_config)
    
    def create_subscription(self, tier_id, billing_cycle):
        """
        Crée un abonnement pour le tenant au niveau spécifié.
        
        Args:
            tier_id: ID du niveau d'abonnement
            billing_cycle: Cycle de facturation ('monthly' ou 'annually')
            
        Returns:
            TenantSubscription: L'abonnement créé
        """
        try:
            tier = SubscriptionTier.objects.get(id=tier_id, is_active=True)
            price = tier.price_annually if billing_cycle == 'annually' else tier.price_monthly
            
            # Vérifier si un abonnement actif existe déjÃ 
            active_subscription = TenantSubscription.objects.filter(
                tenant=self.tenant,
                status='active',
                end_date__gt=timezone.now()
            ).first()
            
            if active_subscription:
                # Annuler l'abonnement existant Ã  la fin de la période
                self.cancel_subscription(active_subscription.id, immediate=False)
            
            # Créer ou récupérer le client
            if not self.tenant.payment_config.get('customer_id'):
                customer_id = self.provider.create_customer({
                    'email': self.tenant.owner.email,
                    'name': self.tenant.name,
                    'tenant_id': str(self.tenant.id),
                })
                
                # Enregistrer l'ID client
                self.tenant.payment_config['customer_id'] = customer_id
                self.tenant.save(update_fields=['payment_config'])
            else:
                customer_id = self.tenant.payment_config['customer_id']
            
            # Créer l'abonnement chez le fournisseur de paiement
            provider_subscription = self.provider.create_subscription(
                customer_id=customer_id,
                plan_id=f"{tier.name.lower()}_{billing_cycle}",
                metadata={
                    'tenant_id': str(self.tenant.id),
                    'tenant_name': self.tenant.name,
                    'tier_id': tier_id,
                    'billing_cycle': billing_cycle,
                },
                price_amount=float(price)
            )
            
            # Calculer date de fin
            start_date = timezone.now()
            if billing_cycle == 'annually':
                end_date = start_date + timezone.timedelta(days=365)
            else:
                end_date = start_date + timezone.timedelta(days=30)
            
            # Créer l'abonnement dans notre base de données
            subscription = TenantSubscription.objects.create(
                tenant=self.tenant,
                tier=tier,
                billing_cycle=billing_cycle,
                status='active',
                start_date=start_date,
                end_date=end_date,
                auto_renew=True,
                payment_provider_subscription_id=provider_subscription.get('id')
            )
            
            # Mettre Ã  jour le tenant
            self.tenant.subscription_plan = tier.name.lower()
            self.tenant.is_trial = False
            self.tenant.subscription_start_date = start_date
            self.tenant.subscription_end_date = end_date
            self.tenant.save()
            
            return subscription
            
        except SubscriptionTier.DoesNotExist:
            raise ValueError(f"Niveau d'abonnement inexistant ou inactif: {tier_id}")
        except PaymentProviderError as e:
            logger.error(f"Erreur lors de la création de l'abonnement: {str(e)}")
            raise
    
    def cancel_subscription(self, subscription_id, immediate=False):
        """
        Annule un abonnement.
        
        Args:
            subscription_id: ID de l'abonnement Ã  annuler
            immediate: Annuler immédiatement ou Ã  la fin de la période
            
        Returns:
            dict: Résultat de l'annulation
        """
        try:
            subscription = TenantSubscription.objects.get(id=subscription_id, tenant=self.tenant)
            
            # Annuler l'abonnement chez le fournisseur de paiement
            if subscription.payment_provider_subscription_id:
                try:
                    self.provider.cancel_subscription(
                        subscription.payment_provider_subscription_id,
                        immediate=immediate
                    )
                except PaymentProviderError as e:
                    logger.error(f"Erreur lors de l'annulation de l'abonnement chez le fournisseur: {str(e)}")
            
            # Mettre Ã  jour notre base de données
            if immediate:
                subscription.status = 'canceled'
                subscription.end_date = timezone.now()
            else:
                subscription.status = 'active'  # Reste actif jusqu'Ã  la date de fin
                subscription.auto_renew = False
            
            subscription.save()
            
            return {'success': True, 'status': subscription.status}
            
        except TenantSubscription.DoesNotExist:
            raise ValueError(f"Abonnement introuvable: {subscription_id}")
    
    def process_pay_per_use_charges(self, billing_cycle_end_date=None):
        """
        Traite les frais d'utilisation des fonctionnalités Ã  l'usage.
        
        Args:
            billing_cycle_end_date: Date de fin du cycle de facturation (optionnel)
            
        Returns:
            dict: Résumé des frais facturés
        """
        if billing_cycle_end_date is None:
            billing_cycle_end_date = timezone.now()
        
        # Récupérer toutes les utilisations non facturées pour ce tenant
        unbilled_usages = FeatureUsage.objects.filter(
            tenant=self.tenant,
            billed=False,
            usage_date__lt=billing_cycle_end_date
        ).select_related('feature')
        
        total_charge = Decimal('0.00')
        usage_details = []
        
        # Calculer les frais
        for usage in unbilled_usages:
            feature = usage.feature
            charge = usage.quantity * feature.price_per_unit
            total_charge += charge
            usage_details.append({
                'feature_name': feature.name,
                'quantity': usage.quantity,
                'unit_price': float(feature.price_per_unit),
                'total': float(charge)
            })
            
            # Marquer comme facturé
            usage.billed = True
            usage.save()
        
        # Traiter le paiement avec le fournisseur
        if total_charge > 0:
            customer_id = self.tenant.payment_config.get('customer_id')
            if not customer_id:
                logger.error(f"Pas d'ID client pour le tenant {self.tenant.id}")
                return {
                    'success': False,
                    'error': 'No customer ID found',
                    'total_charge': float(total_charge),
                    'details': usage_details
                }
            
            try:
                invoice = self.provider.create_invoice(
                    customer_id=customer_id,
                    amount=float(total_charge),
                    currency=self.tenant.currency or 'EUR',
                    description=f"Frais d'utilisation - {self.tenant.name}",
                    items=usage_details
                )
                
                return {
                    'success': True,
                    'total_charge': float(total_charge),
                    'invoice_id': invoice.get('id'),
                    'details': usage_details
                }
            except PaymentProviderError as e:
                logger.error(f"Erreur lors de la création de la facture: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'total_charge': float(total_charge),
                    'details': usage_details
                }
        
        return {
            'success': True,
            'total_charge': 0,
            'details': []
        }
    
    def apply_promotion_code(self, code, tier_id, billing_cycle):
        """
        Applique un code promotionnel Ã  un abonnement.
        
        Args:
            code: Code promotionnel
            tier_id: ID du niveau d'abonnement
            billing_cycle: Cycle de facturation
            
        Returns:
            dict: Détails du prix avec réduction
        """
        try:
            # Vérifier si le code existe et est valide
            promotion = PromotionCode.objects.get(
                code=code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now()
            )
            
            # Vérifier si le nombre maximal d'utilisations est atteint
            if promotion.max_uses and promotion.current_uses >= promotion.max_uses:
                return {
                    'valid': False,
                    'reason': 'Code promotionnel a atteint son nombre maximum d\'utilisations'
                }
            
            # Récupérer le niveau d'abonnement
            tier = SubscriptionTier.objects.get(id=tier_id, is_active=True)
            
            # Calculer le prix en fonction du cycle de facturation
            original_price = tier.price_annually if billing_cycle == 'annually' else tier.price_monthly
            discounted_price = original_price
            
            # Appliquer la réduction
            if promotion.discount_type == 'percentage':
                discounted_price = original_price * (1 - promotion.discount_value / 100)
            elif promotion.discount_type == 'fixed':
                discounted_price = max(original_price - promotion.discount_value, Decimal('0.00'))
            # Pour 'free_months', la logique sera gérée lors de la création de l'abonnement
            
            return {
                'valid': True,
                'original_price': float(original_price),
                'discounted_price': float(discounted_price),
                'discount_type': promotion.discount_type,
                'discount_value': float(promotion.discount_value),
                'description': promotion.description
            }
            
        except PromotionCode.DoesNotExist:
            return {'valid': False, 'reason': 'Code promotionnel invalide ou expiré'}
        except SubscriptionTier.DoesNotExist:
            return {'valid': False, 'reason': 'Niveau d\'abonnement invalide'}


def check_feature_availability(tenant, feature_key):
    """
    Vérifie si une fonctionnalité spécifique est disponible pour un tenant en fonction de son abonnement.
    
    Args:
        tenant: Objet tenant
        feature_key: Identifiant de la fonctionnalité
        
    Returns:
        tuple: (is_available, reason)
    """
    try:
        # Récupérer l'abonnement actif
        subscription = TenantSubscription.objects.get(
            tenant=tenant,
            status='active',
            end_date__gte=timezone.now()
        )
        
        # Vérifier si la fonctionnalité est incluse dans le niveau d'abonnement
        tier_features = subscription.tier.features
        if feature_key in tier_features and tier_features[feature_key]:
            return True, None
        
        # Si non incluse dans l'abonnement, vérifier si c'est une fonctionnalité Ã  l'usage
        try:
            PayPerUseFeature.objects.get(name=feature_key, is_active=True)
            return True, "pay_per_use"
        except PayPerUseFeature.DoesNotExist:
            return False, "Fonctionnalité non disponible dans votre abonnement actuel"
            
    except TenantSubscription.DoesNotExist:
        return False, "Aucun abonnement actif"


def record_feature_usage(tenant, feature_key, quantity=1):
    """
    Enregistre l'utilisation d'une fonctionnalité Ã  l'usage.
    
    Args:
        tenant: Objet tenant
        feature_key: Identifiant de la fonctionnalité
        quantity: Quantité d'utilisation Ã  enregistrer
        
    Returns:
        bool: Statut de succès
    """
    try:
        feature = PayPerUseFeature.objects.get(name=feature_key, is_active=True)
        
        # Enregistrer l'utilisation
        FeatureUsage.objects.create(
            tenant=tenant,
            feature=feature,
            quantity=quantity,
            usage_date=timezone.now()
        )
        
        return True
    except PayPerUseFeature.DoesNotExist:
        return False
