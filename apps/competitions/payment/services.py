from django.db import models
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from datetime import datetime
import logging

from .models import (
    OrganizationPaymentCapability, RegionalPaymentConfig, CountryPaymentConfig,
    PaymentGatewayConfig, Transaction, PaymentAttempt, ManualPaymentTracking,
    PaymentWebhook, PaymentRefund, PaymentError
)

logger = logging.getLogger(__name__)


class PaymentCapabilityService:
    """Service pour configurer les capacités de paiement des organisations"""
    
    @staticmethod
    def evaluate_organization_capabilities(organization, answers=None):
        """
        Ã‰value les capacités de paiement d'une organisation en fonction 
        de ses réponses Ã  un questionnaire ou de ses attributs
        
        Args:
            organization: Instance de l'organisation
            answers: Réponses au questionnaire de capacité (optionnel)
            
        Returns:
            OrganizationPaymentCapability: Objet de capacité mis Ã  jour
        """
        capability, created = OrganizationPaymentCapability.objects.get_or_create(
            organization=organization
        )
        
        # Si des réponses au questionnaire sont fournies
        if answers:
            # Déterminer le niveau de capacité en fonction des réponses
            if answers.get('has_merchant_account') == True:
                capability.capability_level = 'FULL'
            elif answers.get('has_bank_account') == True and answers.get('can_use_payment_links') == True:
                capability.capability_level = 'BASIC'
            elif answers.get('has_mobile_money') == True or answers.get('has_digital_wallet') == True:
                capability.capability_level = 'MINIMAL'
            else:
                capability.capability_level = 'NONE'
            
            # Enregistrer les informations spécifiques
            capability.has_bank_account = answers.get('has_bank_account', False)
            if answers.get('bank_account_info'):
                capability.bank_account_info = answers.get('bank_account_info')
                
            capability.has_mobile_money = answers.get('has_mobile_money', False)
            if answers.get('mobile_money_info'):
                capability.mobile_money_info = answers.get('mobile_money_info')
                
            capability.has_financial_partner = answers.get('has_financial_partner', False)
            if answers.get('financial_partner_info'):
                capability.financial_partner_info = answers.get('financial_partner_info')
            
            # Collecter les méthodes disponibles
            collection_methods = []
            
            if answers.get('can_accept_card_payments'):
                collection_methods.append('CARD')
            if answers.get('can_accept_bank_transfers'):
                collection_methods.append('BANK_TRANSFER')
            if answers.get('can_accept_mobile_money'):
                if answers.get('mobile_money_providers'):
                    collection_methods.extend(answers.get('mobile_money_providers'))
            if answers.get('can_accept_manual_payments'):
                collection_methods.append('MANUAL')
                
            capability.collection_methods = collection_methods
            capability.setup_completed = True
            capability.save()
        
        # Si pas de réponses, essayer de déterminer automatiquement
        else:
            # Vérifier si l'organisation a déjÃ  configuré des passerelles de paiement
            has_gateways = PaymentGatewayConfig.objects.filter(
                organization=organization,
                is_active=True
            ).exists()
            
            if has_gateways:
                capability.capability_level = 'FULL'
            else:
                # Par défaut, supposons un niveau minimal de capacité
                capability.capability_level = 'MINIMAL'
                
                # Suggérer des méthodes en fonction de la région/pays
                try:
                    country_config = CountryPaymentConfig.objects.get(country_code=organization.country)
                    
                    # Récupérer les solutions alternatives pour ce pays
                    alt_solutions = country_config.alternative_payment_solutions
                    if alt_solutions:
                        # Vérifier s'il y a des solutions de mobile money disponibles
                        for solution in alt_solutions:
                            if solution.get('type') in ['MOBILE_MONEY', 'DIGITAL_WALLET']:
                                capability.has_mobile_money = True
                                capability.mobile_money_info = {
                                    'suggested_provider': solution.get('provider'),
                                    'setup_instructions': solution.get('setup_instructions')
                                }
                                break
                    
                    # Suggérer des méthodes de collecte en fonction du pays
                    capability.collection_methods = [
                        method for method in country_config.primary_payment_methods 
                        if method in ['MANUAL', 'BANK_TRANSFER'] or 'PERSONAL' in method
                    ]
                    
                except CountryPaymentConfig.DoesNotExist:
                    # Si pas de configuration pays, utiliser des valeurs par défaut sécurisées
                    capability.collection_methods = ['MANUAL', 'BANK_TRANSFER']
            
            capability.setup_completed = False
            capability.save()
        
        return capability
    
    @staticmethod
    def setup_payment_solution(organization):
        """
        Configure les solutions de paiement adaptées aux capacités de l'organisation
        
        Args:
            organization: Instance de l'organisation
            
        Returns:
            dict: Informations sur la configuration effectuée
        """
        # Récupérer les capacités de l'organisation
        try:
            capability = OrganizationPaymentCapability.objects.get(organization=organization)
        except OrganizationPaymentCapability.DoesNotExist:
            # Si les capacités n'ont pas été évaluées, le faire maintenant
            capability = PaymentCapabilityService.evaluate_organization_capabilities(organization)
        
        # Récupérer la région et le pays
        region = organization.region
        country = organization.country
        
        result = {
            'setup_status': 'SUCCESS',
            'capability_level': capability.capability_level,
            'configured_methods': []
        }
        
        # Configurer en fonction du niveau de capacité
        if capability.capability_level == 'FULL':
            # Configuration complète
            result.update(PaymentCapabilityService._setup_full_merchant_integration(organization, capability))
            
        elif capability.capability_level == 'BASIC':
            # Configuration simplifiée
            if capability.has_bank_account:
                result.update(PaymentCapabilityService._setup_payment_links_solution(organization, capability))
            elif capability.has_mobile_money:
                result.update(PaymentCapabilityService._setup_mobile_money_solution(organization, capability))
            else:
                result.update(PaymentCapabilityService._setup_basic_solution_by_region(organization, region, country))
                
        elif capability.capability_level == 'MINIMAL':
            # Configuration minimale
            if capability.has_mobile_money:
                result.update(PaymentCapabilityService._setup_mobile_money_minimal(organization, capability))
            elif capability.has_financial_partner:
                result.update(PaymentCapabilityService._setup_financial_partner_integration(organization, capability))
            else:
                result.update(PaymentCapabilityService._setup_minimal_solution_by_region(organization, region, country))
                
        else:  # NONE
            # Configuration manuelle
            result.update(PaymentCapabilityService._setup_manual_payment_tracking(organization, capability))
        
        return result
    
    @staticmethod
    def _setup_full_merchant_integration(organization, capability):
        """Configuration complète pour organisations avec compte marchand"""
        # Activer toutes les passerelles supportées
        enabled_methods = []
        
        # Récupérer les méthodes disponibles pour ce pays
        try:
            country_config = CountryPaymentConfig.objects.get(country_code=organization.country)
            available_methods = country_config.primary_payment_methods
        except CountryPaymentConfig.DoesNotExist:
            # Utiliser les méthodes de la région par défaut
            try:
                regional_config = RegionalPaymentConfig.objects.get(region=organization.region)
                available_methods = regional_config.enabled_payment_methods
            except RegionalPaymentConfig.DoesNotExist:
                # Méthodes par défaut si aucune configuration trouvée
                available_methods = ['CARD', 'BANK_TRANSFER']
        
        # Configurer chaque méthode
        for method in available_methods:
            if method in capability.collection_methods:
                config = PaymentGatewayConfig.objects.update_or_create(
                    organization=organization,
                    provider=method,
                    defaults={
                        'is_active': True,
                        'is_default': (method == available_methods[0]),
                        'region': organization.region,
                        'country': organization.country,
                        'config_data': {
                            'setup_type': 'FULL_MERCHANT',
                            'setup_date': datetime.now().isoformat()
                        }
                    }
                )[0]
                
                enabled_methods.append({
                    'method': method,
                    'is_default': config.is_default
                })
        
        # Mettre Ã  jour l'organisation
        organization.has_merchant_account = True
        organization.merchant_validation_status = 'VERIFIED'
        organization.enabled_payment_methods = [m['method'] for m in enabled_methods]
        organization.save()
        
        return {
            'setup_type': 'FULL_MERCHANT',
            'configured_methods': enabled_methods
        }
    
    @staticmethod
    def _setup_mobile_money_solution(organization, capability):
        """Configuration pour organisations utilisant des solutions de mobile money"""
        enabled_methods = []
        
        # Récupérer les informations de mobile money
        mobile_info = capability.mobile_money_info
        provider = mobile_info.get('provider')
        phone_number = mobile_info.get('phone_number')
        
        if not provider or not phone_number:
            return {
                'setup_status': 'ERROR',
                'error_message': 'Informations de mobile money incomplètes',
                'configured_methods': []
            }
        
        # Créer une configuration pour cette méthode
        personal_provider = f"{provider}_PERSONAL"
        config = PaymentGatewayConfig.objects.update_or_create(
            organization=organization,
            provider=personal_provider,
            defaults={
                'is_active': True,
                'is_default': True,
                'region': organization.region,
                'country': organization.country,
                'config_data': {
                    'setup_type': 'MOBILE_MONEY_PERSONAL',
                    'phone_number': phone_number,
                    'provider': provider,
                    'setup_date': datetime.now().isoformat()
                }
            }
        )[0]
        
        enabled_methods.append({
            'method': personal_provider,
            'is_default': True,
            'display_name': f"{provider.replace('_', ' ')} ({phone_number})",
            'instructions': f"Les paiements seront envoyés directement Ã  votre compte {provider.replace('_', ' ')} associé au numéro {phone_number}"
        })
        
        # Ajouter également une option de paiement manuel/virement si disponible
        if capability.has_bank_account:
            bank_info = capability.bank_account_info
            
            config = PaymentGatewayConfig.objects.update_or_create(
                organization=organization,
                provider='BANK_TRANSFER',
                defaults={
                    'is_active': True,
                    'is_default': False,
                    'region': organization.region,
                    'country': organization.country,
                    'config_data': {
                        'setup_type': 'MANUAL_INSTRUCTIONS',
                        'bank_name': bank_info.get('bank_name'),
                        'account_name': bank_info.get('account_name'),
                        'account_number': bank_info.get('account_number'),
                        'setup_date': datetime.now().isoformat()
                    }
                }
            )[0]
            
            enabled_methods.append({
                'method': 'BANK_TRANSFER',
                'is_default': False,
                'display_name': f"Virement bancaire ({bank_info.get('bank_name')})",
                'instructions': f"Les paiements seront effectués par virement bancaire sur le compte {bank_info.get('account_name')} Ã  {bank_info.get('bank_name')}"
            })
        
        # Mettre Ã  jour l'organisation
        organization.has_merchant_account = False
        organization.enabled_payment_methods = [m['method'] for m in enabled_methods]
        organization.save()
        
        return {
            'setup_type': 'MOBILE_MONEY_PERSONAL',
            'configured_methods': enabled_methods
        }
    
    @staticmethod
    def _setup_manual_payment_tracking(organization, capability):
        """Configuration pour organisations utilisant uniquement des paiements manuels"""
        enabled_methods = []
        
        # Configurer le suivi manuel des paiements
        config = PaymentGatewayConfig.objects.update_or_create(
            organization=organization,
            provider='MANUAL',
            defaults={
                'is_active': True,
                'is_default': True,
                'region': organization.region,
                'country': organization.country,
                'config_data': {
                    'setup_type': 'MANUAL_TRACKING',
                    'setup_date': datetime.now().isoformat(),
                    'payment_instructions': "Les paiements seront suivis manuellement par l'organisation"
                }
            }
        )[0]
        
        enabled_methods.append({
            'method': 'MANUAL',
            'is_default': True,
            'display_name': "Paiement manuel (suivi)",
            'instructions': "Les paiements seront suivis manuellement par l'organisation"
        })
        
        # Ajouter également une option de virement si l'organisation a un compte bancaire
        if capability.has_bank_account:
            bank_info = capability.bank_account_info
            
            config = PaymentGatewayConfig.objects.update_or_create(
                organization=organization,
                provider='BANK_TRANSFER',
                defaults={
                    'is_active': True,
                    'is_default': False,
                    'region': organization.region,
                    'country': organization.country,
                    'config_data': {
                        'setup_type': 'MANUAL_INSTRUCTIONS',
                        'bank_name': bank_info.get('bank_name'),
                        'account_name': bank_info.get('account_name'),
                        'account_number': bank_info.get('account_number'),
                        'setup_date': datetime.now().isoformat()
                    }
                }
            )[0]
            
            enabled_methods.append({
                'method': 'BANK_TRANSFER',
                'is_default': False,
                'display_name': f"Virement bancaire ({bank_info.get('bank_name')})",
                'instructions': f"Les paiements seront effectués par virement bancaire sur le compte {bank_info.get('account_name')} Ã  {bank_info.get('bank_name')}"
            })
        
        # Mettre Ã  jour l'organisation
        organization.has_merchant_account = False
        organization.enabled_payment_methods = [m['method'] for m in enabled_methods]
        organization.save()
        
        return {
            'setup_type': 'MANUAL_TRACKING',
            'configured_methods': enabled_methods
        }
    
    @staticmethod
    def _setup_payment_links_solution(organization, capability):
        """Configuration pour organisations avec compte bancaire mais sans compte marchand"""
        # Implémentation pour les liens de paiement
        return {
            'setup_type': 'PAYMENT_LINKS',
            'configured_methods': []
        }
    
    @staticmethod
    def _setup_basic_solution_by_region(organization, region, country):
        """Configuration basique selon la région"""
        # Implémentation pour solutions basiques par région
        return {
            'setup_type': 'BASIC_REGIONAL',
            'configured_methods': []
        }
    
    @staticmethod
    def _setup_mobile_money_minimal(organization, capability):
        """Configuration minimale pour mobile money"""
        # Implémentation pour mobile money minimal
        return {
            'setup_type': 'MOBILE_MONEY_MINIMAL',
            'configured_methods': []
        }
    
    @staticmethod
    def _setup_financial_partner_integration(organization, capability):
        """Configuration pour partenaires financiers"""
        # Implémentation pour partenaires financiers
        return {
            'setup_type': 'FINANCIAL_PARTNER',
            'configured_methods': []
        }
    
    @staticmethod
    def _setup_minimal_solution_by_region(organization, region, country):
        """Configuration minimale selon la région"""
        # Implémentation pour solutions minimales par région
        return {
            'setup_type': 'MINIMAL_REGIONAL',
            'configured_methods': []
        }


class PaymentGatewaySelector:
    """Service pour sélectionner la passerelle de paiement appropriée"""
    
    @staticmethod
    def get_gateway_for_organization(organization, payment_method=None, user_country=None):
        """
        Sélectionne la passerelle de paiement appropriée en fonction de l'organisation,
        de la méthode de paiement et du pays de l'utilisateur
        
        Args:
            organization: Instance de l'organisation
            payment_method: Méthode de paiement demandée (optionnel)
            user_country: Code ISO du pays de l'utilisateur (optionnel)
            
        Returns:
            PaymentGatewayConfig: Configuration de la passerelle Ã  utiliser
        """
        # Si l'organisation a une configuration de passerelle spécifique
        if organization.has_merchant_account and organization.merchant_validation_status == 'VERIFIED':
            # Récupérer les passerelles configurées pour cette organisation
            gateway_configs = PaymentGatewayConfig.objects.filter(
                organization=organization,
                is_active=True
            )
            
            # Si une méthode de paiement est spécifiée, filtrer par méthode
            if payment_method and gateway_configs.filter(provider=payment_method).exists():
                return gateway_configs.get(provider=payment_method)
            
            # Sinon, utiliser la passerelle par défaut de l'organisation
            if gateway_configs.filter(is_default=True).exists():
                return gateway_configs.get(is_default=True)
                
            # Si aucune passerelle par défaut, prendre la première disponible
            if gateway_configs.exists():
                return gateway_configs.first()
        
        # Si pas de configuration spécifique Ã  l'organisation, utiliser la configuration régionale
        country_code = organization.country
        region_code = organization.region
        
        # Récupérer la configuration régionale
        try:
            regional_config = RegionalPaymentConfig.objects.get(region=region_code)
        except RegionalPaymentConfig.DoesNotExist:
            # Utiliser une configuration par défaut en cas d'erreur
            regional_config = RegionalPaymentConfig.objects.get(region='EUROPE_WEST')
        
        # Récupérer la configuration du pays
        try:
            country_config = CountryPaymentConfig.objects.get(country_code=country_code)
        except CountryPaymentConfig.DoesNotExist:
            # Utiliser les informations de la région si le pays n'est pas configuré
            country_config = None
        
        # Déterminer les méthodes de paiement disponibles
        available_methods = regional_config.enabled_payment_methods
        if country_config:
            primary_methods = country_config.primary_payment_methods
            if primary_methods:
                available_methods = primary_methods
        
        # Si une méthode spécifique est demandée, vérifier si elle est disponible
        if payment_method and payment_method in available_methods:
            method_to_use = payment_method
        else:
            # Utiliser la première méthode disponible
            method_to_use = available_methods[0] if available_methods else 'CARD'
        
        # Récupérer ou créer la configuration de passerelle globale
        gateway_config, _ = PaymentGatewayConfig.objects.get_or_create(
            provider=method_to_use,
            region=region_code,
            country=country_code,
            defaults={
                'is_active': True,
                'is_default': False
            }
        )
        
        return gateway_config


class RegionalPricingService:
    """Service pour gérer les tarifs adaptés Ã  chaque région"""
    
    @staticmethod
    def get_price_for_region(product_type, region, tier=None):
        """
        Calcule le prix adapté pour une région et un type de produit
        
        Args:
            product_type (str): Type de produit (subscription, module, etc.)
            region (str): Code de région (AFRICA_WEST, EUROPE_WEST, etc.)
            tier (str, optional): Niveau de service (club, pro, fed)
            
        Returns:
            tuple: (prix, devise)
        """
        try:
            # Récupérer la configuration régionale
            regional_config = RegionalPaymentConfig.objects.get(region=region)
            
            # Récupérer les tarifs de base (en EUR)
            base_prices = {
                'subscription': {
                    'club': 29,
                    'pro': 89,
                    'fed': 199
                },
                'module': {
                    'comp': 39,
                    'gest': 29
                }
            }
            
            # Appliquer la réduction selon le niveau de tarification de la région
            discount_multiplier = 1.0
            if regional_config.pricing_tier == 'TIER_1':
                discount_multiplier = 0.8  # 20% de réduction
            elif regional_config.pricing_tier == 'TIER_2':
                discount_multiplier = 0.5  # 50% de réduction
            elif regional_config.pricing_tier == 'TIER_3':
                discount_multiplier = 0.3  # 70% de réduction
            elif regional_config.pricing_tier == 'CUSTOM':
                # Récupérer le multiplicateur personnalisé dans les données de configuration
                discount_multiplier = regional_config.config_data.get('discount_multiplier', 1.0)
            
            # Calculer le prix avec la réduction
            if product_type in base_prices and tier in base_prices[product_type]:
                base_price = base_prices[product_type][tier]
                discounted_price = base_price * discount_multiplier
                
                # Arrondir selon les règles de la devise
                currency = regional_config.default_currency
                if currency in ['JPY', 'KRW', 'IDR', 'VND']:
                    # Arrondir aux 100 ou 1000 les plus proches pour ces devises
                    discounted_price = round(discounted_price / 100) * 100
                else:
                    # Arrondir Ã  deux décimales pour les autres devises
                    discounted_price = round(discounted_price, 2)
                
                return discounted_price, currency
        
        except RegionalPaymentConfig.DoesNotExist:
            pass
        
        # Valeurs par défaut en cas d'erreur
        return 29, "EUR"
    
    @staticmethod
    def convert_price(amount, from_currency, to_currency):
        """
        Convertit un montant d'une devise Ã  une autre
        
        Args:
            amount (float): Montant Ã  convertir
            from_currency (str): Code ISO de la devise source
            to_currency (str): Code ISO de la devise cible
            
        Returns:
            float: Montant converti
        """
        if from_currency == to_currency:
            return amount
        
        # Utiliser un service de taux de change (Ã  implémenter)
        # Pour l'instant, retourner le montant original
        return amount


class PaymentProcessingService:
    """Service pour traiter les paiements"""
    
    @staticmethod
    def process_payment(organization, amount, currency, payment_method, user_data, metadata=None):
        """
        Traite un paiement pour une organisation
        
        Args:
            organization: Instance de l'organisation
            amount: Montant Ã  payer
            currency: Devise du paiement
            payment_method: Méthode de paiement choisie
            user_data: Données de l'utilisateur (email, téléphone, etc.)
            metadata: Métadonnées supplémentaires
            
        Returns:
            dict: Résultat du traitement du paiement
        """
        # Sélectionner la passerelle appropriée
        gateway_config = PaymentGatewaySelector.get_gateway_for_organization(
            organization, 
            payment_method=payment_method,
            user_country=user_data.get('country')
        )
        
        # Créer une transaction
        transaction = Transaction.objects.create(
            organization=organization,
            amount=amount,
            currency=currency,
            description=f"Paiement Ã  {organization.name}",
            created_by=user_data.get('user')
        )
        
        # Créer une tentative de paiement
        payment_attempt = PaymentAttempt.objects.create(
            transaction=transaction,
            organization=organization,
            gateway_config=gateway_config,
            amount=amount,
            currency=currency,
            payment_method=payment_method
        )
        
        # Enrichir les métadonnées
        full_metadata = {
            'payment_attempt_id': payment_attempt.id,
            'organization_id': organization.id,
            'user_id': user_data.get('user_id'),
            'email': user_data.get('email'),
            'phone_number': user_data.get('phone_number')
        }
        
        if metadata:
            full_metadata.update(metadata)
        
        # Mettre Ã  jour les métadonnées de la tentative de paiement
        payment_attempt.metadata = full_metadata
        payment_attempt.save()
        
        # Initier le paiement via la passerelle appropriée
        try:
            # Ici, on appellerait la passerelle de paiement appropriée
            # Pour l'instant, on simule un succès
            result = {
                'success': True,
                'gateway_transaction_id': f"TXN_{payment_attempt.id}",
                'redirect_url': f"/payment/redirect/{payment_attempt.id}/",
                'payment_instructions': f"Paiement de {amount} {currency} Ã  {organization.name}"
            }
            
            # Mettre Ã  jour la tentative de paiement
            payment_attempt.gateway_transaction_id = result['gateway_transaction_id']
            payment_attempt.gateway_response = result
            payment_attempt.status = 'PROCESSING'
            payment_attempt.save()
            
            return {
                'success': True,
                'payment_attempt_id': payment_attempt.id,
                'payment_data': result
            }
            
        except Exception as e:
            # Enregistrer l'erreur
            PaymentError.objects.create(
                organization=organization,
                payment_attempt=payment_attempt,
                error_type='PAYMENT_PROCESSING_ERROR',
                error_message=str(e),
                metadata=full_metadata
            )
            
            payment_attempt.status = 'FAILED'
            payment_attempt.gateway_response = {'error': str(e)}
            payment_attempt.save()
            
            return {
                'success': False,
                'error': str(e),
                'payment_attempt_id': payment_attempt.id
            }
    
    @staticmethod
    def handle_webhook(provider, event_type, payload, headers=None):
        """
        Traite un webhook de paiement
        
        Args:
            provider: Nom du fournisseur (STRIPE, PAYPAL, etc.)
            event_type: Type d'événement
            payload: Données du webhook
            headers: En-tÃªtes HTTP (optionnel)
            
        Returns:
            dict: Résultat du traitement
        """
        # Créer un enregistrement du webhook
        webhook = PaymentWebhook.objects.create(
            provider=provider,
            event_type=event_type,
            payload=payload,
            headers=headers or {}
        )
        
        try:
            # Traiter selon le type d'événement
            if event_type == 'payment.succeeded':
                result = PaymentProcessingService._handle_payment_success(webhook, payload)
            elif event_type == 'payment.failed':
                result = PaymentProcessingService._handle_payment_failure(webhook, payload)
            elif event_type == 'payment.refunded':
                result = PaymentProcessingService._handle_payment_refund(webhook, payload)
            else:
                result = {'status': 'IGNORED', 'message': f'Event type {event_type} not handled'}
            
            webhook.processing_status = 'PROCESSED'
            webhook.processing_notes = str(result)
            webhook.processed_at = timezone.now()
            webhook.save()
            
            return result
            
        except Exception as e:
            webhook.processing_status = 'FAILED'
            webhook.processing_notes = str(e)
            webhook.save()
            
            return {'status': 'ERROR', 'message': str(e)}
    
    @staticmethod
    def _handle_payment_success(webhook, payload):
        """Traite un paiement réussi"""
        # Implémentation pour paiement réussi
        return {'status': 'SUCCESS', 'message': 'Payment processed successfully'}
    
    @staticmethod
    def _handle_payment_failure(webhook, payload):
        """Traite un échec de paiement"""
        # Implémentation pour échec de paiement
        return {'status': 'FAILED', 'message': 'Payment failed'}
    
    @staticmethod
    def _handle_payment_refund(webhook, payload):
        """Traite un remboursement"""
        # Implémentation pour remboursement
        return {'status': 'REFUNDED', 'message': 'Payment refunded'} 
