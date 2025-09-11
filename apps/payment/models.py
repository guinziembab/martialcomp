from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import uuid

User = get_user_model()

class SubscriptionPlan(models.Model):
    """Plan d'abonnement avec période d'essai"""
    PLAN_TYPES = [
        ('trial', 'Essai gratuit'),
        ('basic', 'Basique'),
        ('premium', 'Premium'),
        ('enterprise', 'Entreprise'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nom du plan")
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='basic')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix mensuel")
    trial_days = models.IntegerField(default=30, verbose_name="Jours d'essai")
    description = models.TextField(blank=True, verbose_name="Description")
    features = models.JSONField(default=list, verbose_name="Fonctionnalités")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'payment'
        verbose_name = "Plan d'abonnement"
        verbose_name_plural = "Plans d'abonnement"
    
    def __str__(self):
        return f"{self.name} - {self.get_plan_type_display()}"

class OrganizationSubscription(models.Model):
    """Abonnement d'une organisation"""
    STATUS_CHOICES = [
        ('trial', 'Essai'),
        ('active', 'Actif'),
        ('expired', 'Expiré'),
        ('cancelled', 'Annulé'),
        ('suspended', 'Suspendu'),
    ]
    
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, verbose_name="Organisation")
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, verbose_name="Plan")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    trial_start = models.DateTimeField(auto_now_add=True, verbose_name="Début de l'essai")
    trial_end = models.DateTimeField(verbose_name="Fin de l'essai")
    subscription_start = models.DateTimeField(null=True, blank=True, verbose_name="Début de l'abonnement")
    subscription_end = models.DateTimeField(null=True, blank=True, verbose_name="Fin de l'abonnement")
    auto_renew = models.BooleanField(default=True, verbose_name="Renouvellement automatique")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'payment'
        verbose_name = "Abonnement d'organisation"
        verbose_name_plural = "Abonnements d'organisations"
    
    def __str__(self):
        return f"{self.organization.name} - {self.plan.name}"
    
    def save(self, *args, **kwargs):
        if not self.trial_end:
            self.trial_end = self.trial_start + timedelta(days=self.plan.trial_days)
        super().save(*args, **kwargs)
    
    @property
    def is_trial_active(self):
        """Vérifie si l'essai est encore actif"""
        return self.status == 'trial' and timezone.now() <= self.trial_end
    
    @property
    def is_active(self):
        """Vérifie si l'abonnement est actif"""
        if self.status == 'trial':
            return self.is_trial_active
        elif self.status == 'active':
            return self.subscription_end is None or timezone.now() <= self.subscription_end
        return False
    
    @property
    def days_remaining(self):
        """Jours restants avant expiration"""
        if self.status == 'trial':
            if self.is_trial_active:
                return (self.trial_end - timezone.now()).days
        elif self.status == 'active' and self.subscription_end:
            return (self.subscription_end - timezone.now()).days
        return 0

class PaymentMethod(models.Model):
    """Méthodes de paiement"""
    METHOD_TYPES = [
        ('card', 'Carte bancaire'),
        ('paypal', 'PayPal'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Virement bancaire'),
    ]
    
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, verbose_name="Organisation")
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES, verbose_name="Type de méthode")
    is_default = models.BooleanField(default=False, verbose_name="Méthode par défaut")
    payment_data = models.JSONField(default=dict, verbose_name="Données de paiement")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'payment'
        verbose_name = "Méthode de paiement"
        verbose_name_plural = "Méthodes de paiement"
    
    def __str__(self):
        return f"{self.organization.name} - {self.get_method_type_display()}"

class Payment(models.Model):
    """Transactions de paiement"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Ã‰choué'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]
    
    subscription = models.ForeignKey(OrganizationSubscription, on_delete=models.CASCADE, verbose_name="Abonnement")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, verbose_name="Méthode de paiement")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant")
    currency = models.CharField(max_length=3, default='EUR', verbose_name="Devise")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, unique=True, verbose_name="ID de transaction")
    gateway_response = models.JSONField(default=dict, verbose_name="Réponse de la passerelle")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'payment'
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
    
    def __str__(self):
        return f"{self.subscription.organization.name} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4())
        super().save(*args, **kwargs)

class PaymentWebhook(models.Model):
    """Webhooks de paiement"""
    webhook_id = models.CharField(max_length=100, unique=True, verbose_name="ID du webhook")
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, verbose_name="Paiement")
    event_type = models.CharField(max_length=50, verbose_name="Type d'événement")
    payload = models.JSONField(verbose_name="Données reçues")
    processed = models.BooleanField(default=False, verbose_name="Traité")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'payment'
        verbose_name = "Webhook de paiement"
        verbose_name_plural = "Webhooks de paiement"
    
    def __str__(self):
        return f"{self.event_type} - {self.payment.transaction_id}"

class Refund(models.Model):
    """Remboursements"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
        ('completed', 'Terminé'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, verbose_name="Paiement")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Montant remboursé")
    reason = models.TextField(verbose_name="Raison du remboursement")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    refund_id = models.CharField(max_length=100, unique=True, verbose_name="ID de remboursement")
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name="Traité le")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'payment'
        verbose_name = "Remboursement"
        verbose_name_plural = "Remboursements"
    
    def __str__(self):
        return f"Remboursement {self.refund_id} - {self.amount}"

class PaymentError(models.Model):
    """Erreurs de paiement"""
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, verbose_name="Paiement")
    error_code = models.CharField(max_length=50, verbose_name="Code d'erreur")
    error_message = models.TextField(verbose_name="Message d'erreur")
    error_data = models.JSONField(default=dict, verbose_name="Données d'erreur")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'payment'
        verbose_name = "Erreur de paiement"
        verbose_name_plural = "Erreurs de paiement"
    
    def __str__(self):
        return f"{self.error_code} - {self.payment.transaction_id}"


