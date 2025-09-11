from typing import Dict, Type, Any
from django.conf import settings
from .base import AbstractPaymentGateway
from .gateways import (
    StripeGateway, PayPalGateway, OrangeMoneyGateway, MPesaGateway,
    AlipayGateway, WeChatPayGateway, FawryGateway, STCPayGateway
)


class PaymentGatewayFactory:
    """
    Factory pour créer la passerelle de paiement appropriée
    selon la configuration de l'organisation.
    """
    
    # Mapping des passerelles disponibles
    GATEWAYS = {
        'stripe': StripeGateway,
        'paypal': PayPalGateway,
        'orange_money': OrangeMoneyGateway,
        'm_pesa': MPesaGateway,
        'alipay': AlipayGateway,
        'wechat_pay': WeChatPayGateway,
        'fawry': FawryGateway,
        'stc_pay': STCPayGateway,
    }
    
    @classmethod
    def get_gateway(cls, organization) -> AbstractPaymentGateway:
        """
        Retourne la passerelle de paiement pour l'organisation.
        
        Args:
            organization: L'organisation pour laquelle créer la passerelle
            
        Returns:
            AbstractPaymentGateway: La passerelle configurée
        """
        # Récupérer la configuration de paiement de l'organisation
        payment_config = getattr(organization, 'payment_config', {})
        gateway_name = payment_config.get('gateway', 'stripe')
        
        # Récupérer la classe de passerelle
        gateway_class = cls.GATEWAYS.get(gateway_name)
        
        if not gateway_class:
            # Fallback vers Stripe si la passerelle n'existe pas
            gateway_class = StripeGateway
        
        # Créer et retourner l'instance
        return gateway_class(organization)
    
    @classmethod
    def get_available_gateways(cls) -> Dict[str, Type[AbstractPaymentGateway]]:
        """Retourne toutes les passerelles disponibles."""
        return cls.GATEWAYS.copy()
    
    @classmethod
    def register_gateway(cls, name: str, gateway_class: Type[AbstractPaymentGateway]):
        """Enregistre une nouvelle passerelle."""
        cls.GATEWAYS[name] = gateway_class
    
    @classmethod
    def get_gateway_info(cls, gateway_name: str) -> Dict[str, Any]:
        """Retourne les informations sur une passerelle."""
        gateway_class = cls.GATEWAYS.get(gateway_name)
        if not gateway_class:
            return {}
        
        return {
            'name': gateway_name,
            'display_name': gateway_class.get_display_name(),
            'description': gateway_class.get_description(),
            'supported_currencies': gateway_class.get_supported_currencies(),
            'supported_regions': gateway_class.get_supported_regions(),
            'features': gateway_class.get_features(),
        } 
