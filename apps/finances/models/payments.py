from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class PaymentMethod(models.Model):
    """
    Modèle représentant les différentes méthodes de paiement acceptées.
    Chaque méthode peut avoir des configurations spécifiques pour les intégrations.
    """
    TYPE_CHOICES = [
        ('cash', _('Espèces')),
        ('card', _('Carte bancaire')),
        ('transfer', _('Virement bancaire')),
        ('check', _('Chèque')),
        ('direct_debit', _('Prélèvement automatique')),
        ('paypal', _('PayPal')),
        ('stripe', _('Stripe')),
        ('other', _('Autre')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_('Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Frais associés
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Frais fixe'))
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Frais pourcentage (%)'))
    
    # Configuration pour intégrations tierces
    api_key = models.CharField(max_length=255, blank=True, verbose_name=_('Clé API (chiffrée)'))
    api_secret = models.CharField(max_length=255, blank=True, verbose_name=_('Secret API (chiffré)'))
    config = models.JSONField(default=dict, blank=True, verbose_name=_('Configuration'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise Ã  jour'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    
    # Relations
    organization_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Type d\'organisation'))
    organization_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID de l\'organisation'))
    
    class Meta:
        app_label = 'finances'
        verbose_name = _('Méthode de paiement')
        verbose_name_plural = _('Méthodes de paiement')
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
    def calculate_fee(self, amount):
        """
        Calcule les frais pour un montant donné en utilisant les paramètres définis.
        """
        percentage_fee = (amount * self.fee_percentage) / 100
        total_fee = self.fee_fixed + percentage_fee
        return round(total_fee, 2)
    
    def get_total_with_fees(self, amount):
        """
        Retourne le montant total incluant les frais.
        """
        return amount + self.calculate_fee(amount)


class PaymentAttempt(models.Model):
    """
    Enregistre les tentatives de paiement pour un suivi détaillé.
    """
    STATUS_CHOICES = [
        ('initiated', _('Initiée')),
        ('processing', _('En cours')),
        ('succeeded', _('Réussie')),
        ('failed', _('Ã‰chouée')),
        ('cancelled', _('Annulée')),
        ('refunded', _('Remboursée')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey('finances.Transaction', on_delete=models.CASCADE, related_name='payment_attempts', verbose_name=_('Transaction'))
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, verbose_name=_('Méthode de paiement'))
    
    # Information de suivi
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Montant'))
    fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Montant des frais'))
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    
    # Dates
    initiated_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date d\'initiation'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise Ã  jour'))
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Date de complétion'))
    
    # Statut
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated', verbose_name=_('Statut'))
    error_code = models.CharField(max_length=50, blank=True, verbose_name=_('Code d\'erreur'))
    error_message = models.TextField(blank=True, verbose_name=_('Message d\'erreur'))
    
    # Information externe
    provider_reference = models.CharField(max_length=255, blank=True, verbose_name=_('Référence externe'))
    provider_response = models.JSONField(default=dict, blank=True, verbose_name=_('Réponse du fournisseur'))
    
    # Sécurité
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('Adresse IP'))
    user_agent = models.TextField(blank=True, verbose_name=_('User Agent'))

    # Émetteur (qui paie) et receveur (qui encaisse)
    payer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_attempts_made', verbose_name=_('Émetteur'))
    payee_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_attempt_payee_ct', verbose_name=_('Type du bénéficiaire'))
    payee_object_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID du bénéficiaire'))
    
    
    class Meta:
        app_label = 'finances'
        verbose_name = _('Tentative de paiement')
        verbose_name_plural = _('Tentatives de paiement')
        ordering = ['-initiated_at']
        
    def __str__(self):
        return f"{self.transaction} - {self.get_status_display()} - {self.amount} {self.currency}"
    
    def mark_as_succeeded(self, provider_reference=None, provider_response=None):
        """
        Marque une tentative comme réussie et met Ã  jour les informations associées.
        """
        self.status = 'succeeded'
        self.completed_at = models.functions.Now()
        
        if provider_reference:
            self.provider_reference = provider_reference
        
        if provider_response:
            self.provider_response = provider_response
            
        self.save()
        
        # Mettre Ã  jour la transaction associée
        if self.transaction and self.transaction.status == 'pending':
            self.transaction.status = 'validated'
            self.transaction.date_validated = models.functions.Now()
            self.transaction.save()
            
        return True
    
    def mark_as_failed(self, error_code=None, error_message=None, provider_response=None):
        """
        Marque une tentative comme échouée et enregistre les informations d'erreur.
        """
        self.status = 'failed'
        self.completed_at = models.functions.Now()
        
        if error_code:
            self.error_code = error_code
            
        if error_message:
            self.error_message = error_message
            
        if provider_response:
            self.provider_response = provider_response
            
        self.save()
        return True
        
    def mark_as_refunded(self, provider_reference=None, provider_response=None):
        """
        Marque une tentative comme remboursée.
        """
        if self.status != 'succeeded':
            return False
            
        self.status = 'refunded'
        
        if provider_reference:
            self.provider_reference = provider_reference
            
        if provider_response:
            self.provider_response = provider_response
            
        self.save()
        
        # Mettre Ã  jour la transaction associée
        if self.transaction and self.transaction.status == 'validated':
            self.transaction.status = 'refunded'
            self.transaction.save()
            
        return True


