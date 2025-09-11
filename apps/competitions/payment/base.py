from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.urls import reverse


class AbstractPaymentGateway(ABC):
    """
    Classe abstraite pour les passerelles de paiement.
    Chaque organisation peut avoir sa propre implémentation.
    """
    
    def __init__(self, organization):
        self.organization = organization
        self.config = self._get_organization_config()
    
    @abstractmethod
    def _get_organization_config(self) -> Dict[str, Any]:
        """Récupère la configuration spécifique Ã  l'organisation."""
        pass
    
    @abstractmethod
    def create_payment(self, amount: Decimal, currency: str, 
                      description: str, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un paiement et retourne les données nécessaires."""
        pass
    
    @abstractmethod
    def process_webhook(self, request: HttpRequest) -> Dict[str, Any]:
        """Traite les webhooks de la passerelle de paiement."""
        pass
    
    @abstractmethod
    def get_payment_status(self, payment_id: str) -> str:
        """Récupère le statut d'un paiement."""
        pass
    
    @abstractmethod
    def refund_payment(self, payment_id: str, amount: Optional[Decimal] = None) -> bool:
        """Effectue un remboursement."""
        pass
    
    def get_success_url(self) -> str:
        """URL de succès après paiement."""
        return reverse('competitions:payment:success')
    
    def get_cancel_url(self) -> str:
        """URL d'annulation."""
        return reverse('competitions:payment:cancel')
    
    def get_webhook_url(self) -> str:
        """URL de webhook."""
        return reverse('competitions:payment:webhook', kwargs={'gateway': self.get_gateway_name()})
    
    @abstractmethod
    def get_gateway_name(self) -> str:
        """Retourne le nom de la passerelle."""
        pass
    
    def is_enabled(self) -> bool:
        """Vérifie si la passerelle est activée pour cette organisation."""
        return self.config.get('enabled', False)
    
    def get_supported_currencies(self) -> list:
        """Retourne les devises supportées."""
        return self.config.get('supported_currencies', ['EUR', 'USD'])
    
    def get_minimum_amount(self) -> Decimal:
        """Retourne le montant minimum."""
        return Decimal(self.config.get('minimum_amount', '0.01'))
    
    def get_maximum_amount(self) -> Decimal:
        """Retourne le montant maximum."""
        return Decimal(self.config.get('maximum_amount', '999999.99')) 
