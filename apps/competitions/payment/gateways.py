import stripe
import requests
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.http import HttpRequest
from .base import AbstractPaymentGateway


class StripeGateway(AbstractPaymentGateway):
    """Passerelle Stripe pour l'Europe et l'Amérique du Nord."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'api_key': self.organization.stripe_api_key,
            'webhook_secret': self.organization.stripe_webhook_secret,
            'supported_currencies': ['EUR', 'USD', 'GBP', 'CAD'],
            'minimum_amount': '0.50',
            'maximum_amount': '999999.99',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        stripe.api_key = self.config['api_key']
        
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe utilise les centimes
                currency=currency.lower(),
                description=description,
                metadata={
                    'organization_id': str(self.organization.id),
                    'customer_email': customer_data.get('email'),
                }
            )
            
            return {
                'payment_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'status': payment_intent.status,
            }
        except stripe.error.StripeError as e:
            raise Exception(f"Erreur Stripe: {str(e)}")
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.config['webhook_secret']
            )
            
            if event['type'] == 'payment_intent.succeeded':
                return {
                    'payment_id': event['data']['object']['id'],
                    'status': 'succeeded',
                    'amount': event['data']['object']['amount'] / 100,
                }
            elif event['type'] == 'payment_intent.payment_failed':
                return {
                    'payment_id': event['data']['object']['id'],
                    'status': 'failed',
                }
                
        except Exception as e:
            raise Exception(f"Erreur webhook Stripe: {str(e)}")
    
    def get_payment_status(self, payment_id: str) -> str:
        stripe.api_key = self.config['api_key']
        payment_intent = stripe.PaymentIntent.retrieve(payment_id)
        return payment_intent.status
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        stripe.api_key = self.config['api_key']
        
        try:
            if amount:
                refund = stripe.Refund.create(
                    payment_intent=payment_id,
                    amount=int(amount * 100)
                )
            else:
                refund = stripe.Refund.create(payment_intent=payment_id)
            
            return refund.status == 'succeeded'
        except stripe.error.StripeError:
            return False
    
    def get_gateway_name(self) -> str:
        return 'stripe'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'Stripe'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement par carte bancaire (Europe, Amérique du Nord)'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['EUR', 'USD', 'GBP', 'CAD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['Europe', 'North America']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['Cartes bancaires', 'Apple Pay', 'Google Pay', 'SEPA']


class PayPalGateway(AbstractPaymentGateway):
    """Passerelle PayPal pour l'international."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'client_id': self.organization.paypal_client_id,
            'client_secret': self.organization.paypal_client_secret,
            'mode': self.organization.paypal_mode,  # 'sandbox' ou 'live'
            'supported_currencies': ['USD', 'EUR', 'GBP', 'CAD', 'AUD'],
            'minimum_amount': '1.00',
            'maximum_amount': '999999.99',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation PayPal
        return {
            'payment_id': f'paypal_{self.organization.id}_{amount}',
            'redirect_url': f'https://www.paypal.com/pay/{self.organization.id}',
            'status': 'pending',
        }
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        # Traitement webhook PayPal
        return {'status': 'processed'}
    
    def get_payment_status(self, payment_id: str) -> str:
        return 'succeeded'
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        return True
    
    def get_gateway_name(self) -> str:
        return 'paypal'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'PayPal'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement PayPal international'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['Global']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['PayPal', 'Cartes bancaires', 'Comptes PayPal']


class OrangeMoneyGateway(AbstractPaymentGateway):
    """Passerelle Orange Money pour l'Afrique de l'Ouest."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'merchant_id': self.organization.orange_money_merchant_id,
            'api_key': self.organization.orange_money_api_key,
            'supported_currencies': ['XOF', 'EUR', 'USD'],
            'minimum_amount': '100',
            'maximum_amount': '500000',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation Orange Money
        return {
            'payment_id': f'orange_{self.organization.id}_{amount}',
            'redirect_url': f'https://orange-money.com/pay/{self.organization.id}',
            'status': 'pending',
        }
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        return {'status': 'processed'}
    
    def get_payment_status(self, payment_id: str) -> str:
        return 'succeeded'
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        return True
    
    def get_gateway_name(self) -> str:
        return 'orange_money'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'Orange Money'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement mobile Orange Money (Afrique de l\'Ouest)'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['XOF', 'EUR', 'USD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['West Africa']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['Mobile Money', 'Orange Money', 'Transfert d\'argent']


class MPesaGateway(AbstractPaymentGateway):
    """Passerelle M-Pesa pour l'Afrique de l'Est."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'consumer_key': self.organization.mpesa_consumer_key,
            'consumer_secret': self.organization.mpesa_consumer_secret,
            'business_shortcode': self.organization.mpesa_business_shortcode,
            'supported_currencies': ['KES', 'USD'],
            'minimum_amount': '10',
            'maximum_amount': '70000',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation M-Pesa
        return {
            'payment_id': f'mpesa_{self.organization.id}_{amount}',
            'redirect_url': f'https://mpesa.com/pay/{self.organization.id}',
            'status': 'pending',
        }
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        return {'status': 'processed'}
    
    def get_payment_status(self, payment_id: str) -> str:
        return 'succeeded'
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        return True
    
    def get_gateway_name(self) -> str:
        return 'm_pesa'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'M-Pesa'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement mobile M-Pesa (Afrique de l\'Est)'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['KES', 'USD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['East Africa']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['Mobile Money', 'M-Pesa', 'Transfert d\'argent']


class AlipayGateway(AbstractPaymentGateway):
    """Passerelle Alipay pour la Chine."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'app_id': self.organization.alipay_app_id,
            'private_key': self.organization.alipay_private_key,
            'public_key': self.organization.alipay_public_key,
            'supported_currencies': ['CNY', 'USD'],
            'minimum_amount': '0.01',
            'maximum_amount': '999999.99',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation Alipay
        return {
            'payment_id': f'alipay_{self.organization.id}_{amount}',
            'redirect_url': f'https://alipay.com/pay/{self.organization.id}',
            'status': 'pending',
        }
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        return {'status': 'processed'}
    
    def get_payment_status(self, payment_id: str) -> str:
        return 'succeeded'
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        return True
    
    def get_gateway_name(self) -> str:
        return 'alipay'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'Alipay'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement Alipay (Chine)'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['CNY', 'USD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['China']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['Alipay', 'QR Code', 'Mobile Payment']


class WeChatPayGateway(AbstractPaymentGateway):
    """Passerelle WeChat Pay pour la Chine."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'app_id': self.organization.wechat_app_id,
            'mch_id': self.organization.wechat_mch_id,
            'api_key': self.organization.wechat_api_key,
            'supported_currencies': ['CNY', 'USD'],
            'minimum_amount': '0.01',
            'maximum_amount': '999999.99',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation WeChat Pay
        return {
            'payment_id': f'wechat_{self.organization.id}_{amount}',
            'redirect_url': f'https://wechat.com/pay/{self.organization.id}',
            'status': 'pending',
        }
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        return {'status': 'processed'}
    
    def get_payment_status(self, payment_id: str) -> str:
        return 'succeeded'
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        return True
    
    def get_gateway_name(self) -> str:
        return 'wechat_pay'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'WeChat Pay'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement WeChat Pay (Chine)'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['CNY', 'USD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['China']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['WeChat Pay', 'QR Code', 'Mobile Payment']


class FawryGateway(AbstractPaymentGateway):
    """Passerelle Fawry pour l'Ã‰gypte."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'merchant_code': self.organization.fawry_merchant_code,
            'security_key': self.organization.fawry_security_key,
            'supported_currencies': ['EGP', 'USD'],
            'minimum_amount': '1',
            'maximum_amount': '50000',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation Fawry
        return {
            'payment_id': f'fawry_{self.organization.id}_{amount}',
            'redirect_url': f'https://fawry.com/pay/{self.organization.id}',
            'status': 'pending',
        }
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        return {'status': 'processed'}
    
    def get_payment_status(self, payment_id: str) -> str:
        return 'succeeded'
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        return True
    
    def get_gateway_name(self) -> str:
        return 'fawry'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'Fawry'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement Fawry (Ã‰gypte)'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['EGP', 'USD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['Egypt']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['Fawry', 'Cash on Delivery', 'Mobile Payment']


class STCPayGateway(AbstractPaymentGateway):
    """Passerelle STC Pay pour l'Arabie Saoudite."""
    
    def _get_organization_config(self) -> Dict[str, Any]:
        return {
            'enabled': True,
            'merchant_id': self.organization.stc_merchant_id,
            'api_key': self.organization.stc_api_key,
            'supported_currencies': ['SAR', 'USD'],
            'minimum_amount': '1',
            'maximum_amount': '100000',
        }
    
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implémentation STC Pay
        return {
            'payment_id': f'stc_{self.organization.id}_{amount}',
            'redirect_url': f'https://stcpay.com/pay/{self.organization.id}',
            'status': 'pending',
        }
    
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        return {'status': 'processed'}
    
    def get_payment_status(self, payment_id: str) -> str:
        return 'succeeded'
    
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        return True
    
    def get_gateway_name(self) -> str:
        return 'stc_pay'
    
    @classmethod
    def get_display_name(cls) -> str:
        return 'STC Pay'
    
    @classmethod
    def get_description(cls) -> str:
        return 'Paiement STC Pay (Arabie Saoudite)'
    
    @classmethod
    def get_supported_currencies(cls) -> List[str]:
        return ['SAR', 'USD']
    
    @classmethod
    def get_supported_regions(cls) -> List[str]:
        return ['Saudi Arabia']
    
    @classmethod
    def get_features(cls) -> List[str]:
        return ['STC Pay', 'Mobile Payment', 'Digital Wallet'] 
