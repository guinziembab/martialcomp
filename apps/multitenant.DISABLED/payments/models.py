"""
Modèles pour le système de paiement multi-tenant.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
import uuid
from decimal import Decimal

from apps.multitenant.models import Tenant


class TenantPayment(models.Model):
    """
    Modèle pour enregistrer les paiements d'abonnement des tenants.
    """
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('completed', _('Complété')),
        ('failed', _('Ã‰choué')),
        ('refunded', _('Remboursé')),
        ('cancelled', _('Annulé')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('card', _('Carte bancaire')),
        ('bank_transfer', _('Virement bancaire')),
        ('paypal', _('PayPal')),
        ('mobile_money', _('Mobile Money')),
        ('other', _('Autre')),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_("Tenant")
    )
    
    # Détails du paiement
    amount = models.DecimalField(
        _("Montant"),
        max_digits=10,
        decimal_places=2
    )
    currency = models.CharField(
        _("Devise"),
        max_length=3,
        default='EUR'
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        help_text=_("Description du paiement")
    )
    
    # Status et méthode
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(
        _("Méthode de paiement"),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    
    # Informations du provider
    provider = models.CharField(
        _("Fournisseur de paiement"),
        max_length=50,
        help_text=_("Ex: stripe, paystack, etc.")
    )
    provider_payment_id = models.CharField(
        _("ID de paiement du fournisseur"),
        max_length=255,
        unique=True,
        help_text=_("ID du paiement chez le fournisseur")
    )
    provider_metadata = models.JSONField(
        _("Métadonnées du fournisseur"),
        default=dict,
        blank=True
    )
    
    # Période de l'abonnement
    subscription_period_start = models.DateTimeField(
        _("Début de la période"),
        null=True,
        blank=True
    )
    subscription_period_end = models.DateTimeField(
        _("Fin de la période"),
        null=True,
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payments',
        verbose_name=_("Créé par")
    )
    
    # Informations additionnelles
    invoice_id = models.CharField(
        _("Numéro de facture"),
        max_length=100,
        blank=True,
        help_text=_("Référence de la facture associée")
    )
    payment_date = models.DateTimeField(
        _("Date du paiement"),
        null=True,
        blank=True
    )
    failure_reason = models.TextField(
        _("Raison de l'échec"),
        blank=True,
        help_text=_("Détails en cas d'échec du paiement")
    )
    
    class Meta:
        verbose_name = _("Paiement tenant")
        verbose_name_plural = _("Paiements tenant")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['provider_payment_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.amount} {self.currency} - {self.get_status_display()}"
    
    @property
    def is_successful(self):
        """Vérifie si le paiement est réussi."""
        return self.status == 'completed'
    
    @property
    def can_be_refunded(self):
        """Vérifie si le paiement peut Ãªtre remboursé."""
        return self.status == 'completed' and self.provider in ['stripe', 'paystack']
    
    def get_formatted_amount(self):
        """Retourne le montant formaté avec la devise."""
        currency_symbols = {
            'EUR': 'â‚¬',
            'USD': '$',
            'GBP': 'Â£',
            'JPY': 'Â¥',
            'CHF': 'CHF ',
            'CAD': 'CA$',
            'AUD': 'AU$',
        }
        symbol = currency_symbols.get(self.currency, self.currency + ' ')
        return f"{symbol}{self.amount}"


class LegacyTenantSubscription(models.Model):
    """
    Modèle pour gérer les abonnements actifs des tenants (ancien modèle).
    Ce modèle est conservé pour la compatibilité avec les anciens systèmes,
    mais les nouveaux abonnements devraient utiliser TenantSubscription dans multitenant.models.
    """
    
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('cancelled', _('Annulé')),
        ('expired', _('Expiré')),
        ('suspended', _('Suspendu')),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='legacy_subscription',
        verbose_name=_("Tenant")
    )
    
    # Plan et statut
    plan = models.CharField(
        _("Plan d'abonnement"),
        max_length=50,
        choices=Tenant.SUBSCRIPTION_PLAN_CHOICES
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Dates
    start_date = models.DateTimeField(_("Date de début"))
    end_date = models.DateTimeField(_("Date de fin"))
    cancelled_at = models.DateTimeField(
        _("Date d'annulation"),
        null=True,
        blank=True
    )
    next_billing_date = models.DateTimeField(
        _("Prochaine date de facturation"),
        null=True,
        blank=True
    )
    
    # Informations de paiement
    subscription_id = models.CharField(
        _("ID d'abonnement"),
        max_length=255,
        unique=True,
        help_text=_("ID de l'abonnement chez le fournisseur")
    )
    payment_provider = models.CharField(
        _("Fournisseur de paiement"),
        max_length=50
    )
    provider_metadata = models.JSONField(
        _("Métadonnées du fournisseur"),
        default=dict,
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    class Meta:
        verbose_name = _("Abonnement tenant (legacy)")
        verbose_name_plural = _("Abonnements tenant (legacy)")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.get_plan_display()} - {self.get_status_display()}"
    
    @property
    def is_active(self):
        """Vérifie si l'abonnement est actif."""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'active' and
            self.start_date <= now <= self.end_date
        )
    
    @property
    def days_remaining(self):
        """Retourne le nombre de jours restants dans l'abonnement."""
        from django.utils import timezone
        if not self.is_active:
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)
    
    def cancel(self, reason=None):
        """Annule l'abonnement."""
        from django.utils import timezone
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        if reason:
            if not self.provider_metadata:
                self.provider_metadata = {}
            self.provider_metadata['cancellation_reason'] = reason
        self.save()


class PaymentMethod(models.Model):
    """
    Méthodes de paiement enregistrées pour un tenant.
    """
    
    TYPE_CHOICES = [
        ('card', _('Carte bancaire')),
        ('bank_account', _('Compte bancaire')),
        ('paypal', _('PayPal')),
        ('mobile_money', _('Mobile Money')),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='payment_methods',
        verbose_name=_("Tenant")
    )
    
    # Type et détails
    type = models.CharField(
        _("Type"),
        max_length=20,
        choices=TYPE_CHOICES
    )
    is_default = models.BooleanField(
        _("Méthode par défaut"),
        default=False
    )
    
    # Informations masquées
    display_name = models.CharField(
        _("Nom d'affichage"),
        max_length=100,
        help_text=_("Ex: Visa se terminant par 4242")
    )
    provider_method_id = models.CharField(
        _("ID de la méthode chez le fournisseur"),
        max_length=255,
        unique=True
    )
    provider = models.CharField(
        _("Fournisseur"),
        max_length=50
    )
    provider_metadata = models.JSONField(
        _("Métadonnées du fournisseur"),
        default=dict,
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    class Meta:
        verbose_name = _("Méthode de paiement")
        verbose_name_plural = _("Méthodes de paiement")
        ordering = ['-is_default', '-created_at']
        unique_together = [['tenant', 'is_default']]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.display_name}"
    
    def save(self, *args, **kwargs):
        """S'assure qu'il n'y a qu'une seule méthode par défaut par tenant."""
        if self.is_default:
            # Désactiver toutes les autres méthodes par défaut pour ce tenant
            PaymentMethod.objects.filter(
                tenant=self.tenant,
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        super().save(*args, **kwargs)

