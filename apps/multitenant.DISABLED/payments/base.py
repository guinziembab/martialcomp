"""
Base payment provider interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
from django.utils.translation import gettext_lazy as _


class PaymentProviderError(Exception):
    """Base exception for payment provider errors"""
    pass


class PaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    All payment integrations should inherit from this class.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the payment provider with configuration.
        
        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate the configuration for this provider.
        Raises PaymentProviderError if configuration is invalid.
        """
        pass
    
    @abstractmethod
    def create_customer(self, tenant_data: Dict[str, Any]) -> str:
        """
        Create a customer account for a tenant.
        
        Args:
            tenant_data: Dictionary containing tenant information
            
        Returns:
            Customer ID from the payment provider
        """
        pass
    
    @abstractmethod
    def create_subscription(self, customer_id: str, plan_id: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a subscription for a customer.
        
        Args:
            customer_id: Provider's customer ID
            plan_id: Plan identifier
            metadata: Optional metadata for the subscription
            
        Returns:
            Subscription details dictionary
        """
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id: str, 
                          immediate: bool = False) -> Dict[str, Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Provider's subscription ID
            immediate: Whether to cancel immediately or at period end
            
        Returns:
            Cancellation confirmation details
        """
        pass
    
    @abstractmethod
    def process_payment(self, amount: Decimal, currency: str, 
                       customer_id: str, description: str = "",
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a one-time payment.
        
        Args:
            amount: Payment amount
            currency: ISO currency code
            customer_id: Provider's customer ID
            description: Payment description
            metadata: Optional metadata for the payment
            
        Returns:
            Payment result dictionary
        """
        pass
    
    @abstractmethod
    def create_checkout_session(self, items: list, success_url: str, 
                              cancel_url: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a checkout session for user payment.
        
        Args:
            items: List of items to purchase
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled
            metadata: Optional metadata for the session
            
        Returns:
            Checkout session URL
        """
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle webhook events from the payment provider.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature for verification
            
        Returns:
            Processed event data
        """
        pass
    
    def get_customer_portal_url(self, customer_id: str, return_url: str) -> str:
        """
        Get URL for customer billing portal (if supported).
        
        Args:
            customer_id: Provider's customer ID
            return_url: URL to return to after portal session
            
        Returns:
            Portal URL or raises NotImplementedError
        """
        raise NotImplementedError(_("Customer portal not supported by this provider"))
    
    def update_subscription(self, subscription_id: str, 
                          plan_id: Optional[str] = None,
                          quantity: Optional[int] = None) -> Dict[str, Any]:
        """
        Update an existing subscription.
        
        Args:
            subscription_id: Provider's subscription ID
            plan_id: New plan ID (if changing plan)
            quantity: New quantity (if changing quantity)
            
        Returns:
            Updated subscription details
        """
        raise NotImplementedError(_("Subscription updates not supported by this provider"))
    
    def get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a subscription.
        
        Args:
            subscription_id: Provider's subscription ID
            
        Returns:
            Subscription details dictionary
        """
        raise NotImplementedError(_("Subscription details not available"))
    
    def list_payment_methods(self, customer_id: str) -> list:
        """
        List payment methods for a customer.
        
        Args:
            customer_id: Provider's customer ID
            
        Returns:
            List of payment methods
        """
        raise NotImplementedError(_("Payment method listing not supported"))


class PaymentProviderFactory:
    """Factory class for creating payment provider instances"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register a payment provider class.
        
        Args:
            name: Provider name (e.g., 'stripe', 'paypal')
            provider_class: Provider class inheriting from PaymentProvider
        """
        if not issubclass(provider_class, PaymentProvider):
            raise ValueError(f"{provider_class} must inherit from PaymentProvider")
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(cls, name: str, config: Dict[str, Any]) -> PaymentProvider:
        """
        Create a payment provider instance.
        
        Args:
            name: Provider name
            config: Provider configuration
            
        Returns:
            PaymentProvider instance
            
        Raises:
            ValueError: If provider is not registered
        """
        if name not in cls._providers:
            raise ValueError(f"Unknown payment provider: {name}")
        
        provider_class = cls._providers[name]
        return provider_class(config)