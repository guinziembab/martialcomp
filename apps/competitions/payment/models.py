from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import json

User = get_user_model()


class OrganizationPaymentCapability(models.Model):
    """Définit les capacités financières d'une organisation"""
    
    organization = models.OneToOneField('organizations.Organization', on_delete=models.CASCADE, related_name='payment_capability')
    
    # Niveau de capacité financière
    CAPABILITY_LEVELS = [
        ('FULL', _('Compte marchand complet - Gestion autonome')),
        ('BASIC', _('Compte basique - Solutions simplifiées')),
        ('MINIMAL', _('Capacité minimale - Solutions alternatives')),
        ('NONE', _('Aucune capacité - Mode manuel'))
    ]
    capability_level = models.CharField(max_length=10, choices=CAPABILITY_LEVELS, default='NONE')
    
    # Options de collecte des paiements
    collection_methods = models.JSONField(default=list)
    
    # Informations sur le compte bancaire (pour virements manuels ou automatiques)
    has_bank_account = models.BooleanField(default=False)
    bank_account_info = models.JSONField(default=dict, blank=True)
    
    # Pour les solutions de paiement mobile sans compte marchand
    has_mobile_money = models.BooleanField(default=False)
    mobile_money_info = models.JSONField(default=dict, blank=True)
    
    # Pour les organisations avec partenaires financiers locaux
    has_financial_partner = models.BooleanField(default=False)
    financial_partner_info = models.JSONField(default=dict, blank=True)
    
    # Date de dernière mise Ã  jour
    last_updated = models.DateTimeField(auto_now=True)
    setup_completed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _("Capacité de paiement")
        verbose_name_plural = _("Capacités de paiement")


class RegionalPaymentConfig(models.Model):
    """Configuration des paiements par région"""
    
    REGION_CHOICES = [
        ('AFRICA_NORTH', _('Afrique du Nord')),
        ('AFRICA_WEST', _('Afrique de l\'Ouest')),
        ('AFRICA_EAST', _('Afrique de l\'Est')),
        ('AFRICA_CENTRAL', _('Afrique Centrale')),
        ('AFRICA_SOUTH', _('Afrique Australe')),
        ('AMERICAS_NORTH', _('Amérique du Nord')),
        ('AMERICAS_CENTRAL', _('Amérique Centrale')),
        ('AMERICAS_SOUTH', _('Amérique du Sud')),
        ('ASIA_EAST', _('Asie de l\'Est')),
        ('ASIA_SOUTH', _('Asie du Sud')),
        ('ASIA_SOUTHEAST', _('Asie du Sud-Est')),
        ('ASIA_CENTRAL', _('Asie Centrale')),
        ('EUROPE_WEST', _('Europe de l\'Ouest')),
        ('EUROPE_EAST', _('Europe de l\'Est')),
        ('EUROPE_NORTH', _('Europe du Nord')),
        ('EUROPE_SOUTH', _('Europe du Sud')),
        ('MIDDLE_EAST', _('Moyen-Orient')),
        ('OCEANIA', _('Océanie')),
    ]
    
    region = models.CharField(max_length=30, choices=REGION_CHOICES, unique=True)
    
    # Devises acceptées par région
    default_currency = models.CharField(max_length=3, help_text=_("Code ISO de la devise par défaut (ex: EUR, USD)"))
    available_currencies = models.JSONField(default=list, help_text=_("Liste des codes ISO des devises disponibles"))
    
    # Méthodes de paiement activées pour cette région
    enabled_payment_methods = models.JSONField(default=list)
    
    # Solutions alternatives pour organisations sans compte marchand
    alternative_payment_solutions = models.JSONField(default=dict)
    
    # Tarification spécifique Ã  la région
    pricing_tier = models.CharField(max_length=20, choices=[
        ('STANDARD', _('Standard')),
        ('TIER_1', _('Tier 1 - Réduction 20%')),
        ('TIER_2', _('Tier 2 - Réduction 50%')),
        ('TIER_3', _('Tier 3 - Réduction 70%')),
        ('CUSTOM', _('Personnalisé')),
    ], default='STANDARD')
    
    # Frais de transaction supplémentaires spécifiques Ã  la région
    transaction_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fixed_transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Paramètres avancés pour cette région
    config_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Configuration régionale de paiement")
        verbose_name_plural = _("Configurations régionales de paiement")


class CountryPaymentConfig(models.Model):
    """Configuration des paiements par pays"""
    
    country_code = models.CharField(max_length=2, help_text=_("Code ISO du pays (ex: FR, US)"), unique=True)
    country_name = models.CharField(max_length=100)
    region = models.ForeignKey(RegionalPaymentConfig, on_delete=models.CASCADE, related_name='countries')
    
    # Devises
    default_currency = models.CharField(max_length=3, help_text=_("Code ISO de la devise par défaut du pays"))
    
    # Méthodes de paiement prioritaires pour ce pays
    primary_payment_methods = models.JSONField(default=list)
    secondary_payment_methods = models.JSONField(default=list)
    
    # Solutions alternatives pour organisations sans compte marchand
    alternative_payment_solutions = models.JSONField(default=list)
    
    # Paramètres fiscaux
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    requires_tax_id = models.BooleanField(default=False)
    tax_id_format = models.CharField(max_length=50, blank=True, null=True, help_text=_("Format du numéro d'identification fiscale"))
    
    # Paramètres avancés pour ce pays
    config_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Configuration de paiement par pays")
        verbose_name_plural = _("Configurations de paiement par pays")


class PaymentGatewayConfig(models.Model):
    """Configuration des passerelles de paiement"""
    
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='payment_gateways')
    
    # Informations de base
    provider = models.CharField(max_length=50, help_text=_("Nom du fournisseur (ex: STRIPE, PAYPAL, ORANGE_MONEY)"))
    display_name = models.CharField(max_length=100, blank=True)
    
    # Statut
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    # Région et pays
    region = models.CharField(max_length=30, choices=RegionalPaymentConfig.REGION_CHOICES)
    country = models.CharField(max_length=2)
    
    # Configuration spécifique
    config_data = models.JSONField(default=dict, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Configuration de passerelle de paiement")
        verbose_name_plural = _("Configurations de passerelles de paiement")
        unique_together = ('organization', 'provider')


class Transaction(models.Model):
    """Transaction de paiement"""
    
    # Identifiant unique
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Organisation et utilisateur
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, related_name='transactions')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_transactions')
    
    # Informations de paiement
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    description = models.TextField(blank=True)
    
    # Statut
    STATUS_CHOICES = [
        ('PENDING', _('En attente')),
        ('PROCESSING', _('En cours de traitement')),
        ('COMPLETED', _('Terminé')),
        ('FAILED', _('Ã‰choué')),
        ('CANCELLED', _('Annulé')),
        ('REFUNDED', _('Remboursé')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-created_at']


class PaymentAttempt(models.Model):
    """Tentative de paiement"""
    
    # Relations
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='payment_attempts')
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    gateway_config = models.ForeignKey(PaymentGatewayConfig, on_delete=models.SET_NULL, null=True)
    
    # Informations de paiement
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    payment_method = models.CharField(max_length=50)
    
    # Statut
    STATUS_CHOICES = [
        ('INITIATED', _('Initié')),
        ('PROCESSING', _('En cours de traitement')),
        ('SUCCESS', _('Succès')),
        ('FAILED', _('Ã‰choué')),
        ('CANCELLED', _('Annulé')),
        ('EXPIRED', _('Expiré')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INITIATED')
    
    # Données de la passerelle
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Tentative de paiement")
        verbose_name_plural = _("Tentatives de paiement")
        ordering = ['-created_at']


class ManualPaymentTracking(models.Model):
    """Suivi des paiements manuels ou semi-manuels"""
    
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    
    # Information sur le paiement
    payment_method = models.CharField(max_length=50)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Statut de vérification
    VERIFICATION_STATUS = [
        ('PENDING', _('En attente de vérification')),
        ('VERIFIED', _('Vérifié par l\'organisation')),
        ('REJECTED', _('Rejeté - Paiement non reçu')),
        ('DISPUTED', _('Contesté'))
    ]
    verification_status = models.CharField(max_length=10, choices=VERIFICATION_STATUS, default='PENDING')
    
    # Preuve de paiement
    proof_of_payment = models.FileField(upload_to='payment_proofs/', null=True, blank=True)
    proof_notes = models.TextField(blank=True)
    
    # Dates
    claimed_payment_date = models.DateTimeField(null=True, blank=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Personne ayant vérifié
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = _("Suivi de paiement manuel")
        verbose_name_plural = _("Suivis de paiements manuels")


class PaymentWebhook(models.Model):
    """Webhooks de paiement"""
    
    # Relations
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    payment_attempt = models.ForeignKey(PaymentAttempt, on_delete=models.CASCADE, null=True, blank=True)
    
    # Informations du webhook
    provider = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    webhook_id = models.CharField(max_length=100, blank=True)
    
    # Données reçues
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)
    
    # Statut de traitement
    PROCESSING_STATUS = [
        ('PENDING', _('En attente')),
        ('PROCESSED', _('Traité')),
        ('FAILED', _('Ã‰choué')),
        ('IGNORED', _('Ignoré'))
    ]
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='PENDING')
    
    # Métadonnées
    processing_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Webhook de paiement")
        verbose_name_plural = _("Webhooks de paiement")
        ordering = ['-created_at']


class PaymentRefund(models.Model):
    """Remboursements de paiement"""
    
    # Relations
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='refunds')
    payment_attempt = models.ForeignKey(PaymentAttempt, on_delete=models.CASCADE, related_name='refunds')
    
    # Informations de remboursement
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    reason = models.TextField(blank=True)
    
    # Statut
    STATUS_CHOICES = [
        ('PENDING', _('En attente')),
        ('PROCESSING', _('En cours de traitement')),
        ('COMPLETED', _('Terminé')),
        ('FAILED', _('Ã‰choué')),
        ('CANCELLED', _('Annulé')),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Données de la passerelle
    gateway_refund_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Remboursement")
        verbose_name_plural = _("Remboursements")
        ordering = ['-created_at']


class PaymentError(models.Model):
    """Erreurs de paiement"""
    
    # Relations
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, null=True, blank=True)
    payment_attempt = models.ForeignKey(PaymentAttempt, on_delete=models.CASCADE, null=True, blank=True)
    
    # Informations d'erreur
    error_type = models.CharField(max_length=100)
    error_message = models.TextField()
    error_code = models.CharField(max_length=50, blank=True)
    
    # Contexte
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Erreur de paiement")
        verbose_name_plural = _("Erreurs de paiement")
        ordering = ['-created_at'] 
