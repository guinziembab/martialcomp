"""
Modèles de finances spécifiques Ã  l'architecture multi-tenant.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal
from datetime import datetime, date
import uuid

try:
    from apps.multitenant.models import TenantAwareModel
except ImportError:  # Multi-tenant désactivé
    from django.db import models
    class TenantAwareModel(models.Model):
        class Meta:
            abstract = True
from apps.finances.models.accounts import Account
from apps.finances.models.invoices import Invoice


class TenantFinancialSetting(TenantAwareModel):
    """
    Paramètres financiers spécifiques Ã  un tenant.
    """
    # Informations fiscales
    vat_number = models.CharField(
        _("Numéro de TVA"),
        max_length=100,
        blank=True,
        help_text=_("Numéro de TVA pour les factures")
    )
    
    tax_id = models.CharField(
        _("Numéro fiscal"),
        max_length=100,
        blank=True,
        help_text=_("Identifiant fiscal de l'organisation")
    )
    
    tax_rate = models.DecimalField(
        _("Taux de TVA"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.20'),
        help_text=_("Taux de TVA standard (0.20 = 20%)")
    )
    
    # Paramètres de facturation
    invoice_prefix = models.CharField(
        _("Préfixe des factures"),
        max_length=10,
        blank=True,
        help_text=_("Préfixe ajouté aux numéros des factures")
    )
    
    invoice_footer = models.TextField(
        _("Pied de page des factures"),
        blank=True,
        help_text=_("Texte Ã  inclure en bas des factures")
    )
    
    payment_terms_days = models.PositiveIntegerField(
        _("Délai de paiement (jours)"),
        default=30,
        help_text=_("Nombre de jours accordés pour le paiement")
    )
    
    # Comptes par défaut
    revenue_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_revenue_settings',
        verbose_name=_("Compte de revenus par défaut")
    )
    
    expense_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenant_expense_settings',
        verbose_name=_("Compte de dépenses par défaut")
    )
    
    # Limites financières
    transaction_daily_limit = models.DecimalField(
        _("Limite quotidienne de transactions"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Limite totale des transactions par jour")
    )
    
    single_transaction_limit = models.DecimalField(
        _("Limite par transaction"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Montant maximum pour une transaction unique")
    )
    
    # Configuration d'automatisation
    auto_send_invoices = models.BooleanField(
        _("Envoi automatique des factures"),
        default=True,
        help_text=_("Envoyer automatiquement les nouvelles factures par email")
    )
    
    auto_send_payment_reminders = models.BooleanField(
        _("Envoi automatique des rappels de paiement"),
        default=True,
        help_text=_("Envoyer automatiquement des rappels pour les factures en retard")
    )
    
    auto_apply_platform_fees = models.BooleanField(
        _("Appliquer automatiquement les frais de plateforme"),
        default=True,
        help_text=_("Calculer et enregistrer automatiquement les frais de plateforme")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _("Dernière mise Ã  jour"),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Paramètres financiers")
        verbose_name_plural = _("Paramètres financiers")
        indexes = [
            models.Index(fields=['tenant']),
        ]
    
    def __str__(self):
        return f"Paramètres financiers pour {self.tenant.name}"
    
    def get_tax_rate(self) -> Decimal:
        """
        Obtient le taux de TVA applicable.
        """
        if hasattr(self.tenant, 'country') and self.tenant.country:
            # Logique spécifique par pays pourrait Ãªtre implémentée ici
            pass
        
        return self.tax_rate
    
    def get_next_invoice_number(self) -> str:
        """
        Génère le prochain numéro de facture avec préfixe.
        """
        from django.db.models import Max
        
        prefix = self.invoice_prefix or self.tenant.schema_name[:3].upper()
        year = datetime.now().year
        
        # Trouver le dernier numéro de facture pour ce préfixe et cette année
        last_invoice = Invoice.objects.filter(
            reference__startswith=f"{prefix}-{year}-"
        ).aggregate(Max('reference'))
        
        last_ref = last_invoice.get('reference__max')
        if last_ref:
            try:
                # Extraire le numéro de séquence
                sequence = int(last_ref.split('-')[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1
        
        # Formatage: PREFIX-YEAR-SEQUENCE (ex: ABC-2023-00001)
        return f"{prefix}-{year}-{sequence:05d}"


class TenantBillingCycle(TenantAwareModel):
    """
    Cycle de facturation pour un tenant.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        _("Nom du cycle"),
        max_length=100,
        help_text=_("Nom descriptif du cycle (ex: Janvier 2023)")
    )
    
    start_date = models.DateField(
        _("Date de début")
    )
    
    end_date = models.DateField(
        _("Date de fin")
    )
    
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=[
            ('pending', _("En attente")),
            ('active', _("Actif")),
            ('closed', _("ClÃ´turé")),
            ('cancelled', _("Annulé")),
        ],
        default='pending'
    )
    
    invoice_date = models.DateField(
        _("Date de facturation"),
        null=True,
        blank=True,
        help_text=_("Date Ã  laquelle les factures seront générées")
    )
    
    invoice_due_date = models.DateField(
        _("Date d'échéance"),
        null=True,
        blank=True,
        help_text=_("Date limite de paiement")
    )
    
    notes = models.TextField(
        _("Notes"),
        blank=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _("Dernière mise Ã  jour"),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Cycle de facturation")
        verbose_name_plural = _("Cycles de facturation")
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'start_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def is_current(self) -> bool:
        """
        Vérifie si ce cycle est le cycle actuel.
        """
        today = date.today()
        return self.start_date <= today <= self.end_date
    
    def get_total_revenue(self) -> Decimal:
        """
        Calcule le revenu total pour ce cycle.
        """
        from apps.finances.models.transactions import Transaction
        from django.db.models import Sum
        
        total = Transaction.objects.filter(
            tenant=self.tenant,
            transaction_type='REVENUE',
            transaction_date__gte=self.start_date,
            transaction_date__lte=self.end_date
        ).aggregate(Sum('amount'))
        
        return total['amount__sum'] or Decimal('0')
    
    def get_total_expenses(self) -> Decimal:
        """
        Calcule les dépenses totales pour ce cycle.
        """
        from apps.finances.models.transactions import Transaction
        from django.db.models import Sum
        
        total = Transaction.objects.filter(
            tenant=self.tenant,
            transaction_type='EXPENSE',
            transaction_date__gte=self.start_date,
            transaction_date__lte=self.end_date
        ).aggregate(Sum('amount'))
        
        return total['amount__sum'] or Decimal('0')
    
    def get_net_income(self) -> Decimal:
        """
        Calcule le revenu net pour ce cycle.
        """
        return self.get_total_revenue() - self.get_total_expenses()


class TenantInvoiceTemplate(TenantAwareModel):
    """
    Modèle de facture personnalisé pour un tenant.
    """
    name = models.CharField(
        _("Nom du modèle"),
        max_length=100
    )
    
    description = models.TextField(
        _("Description"),
        blank=True
    )
    
    is_default = models.BooleanField(
        _("Modèle par défaut"),
        default=False
    )
    
    # Contenu HTML du modèle
    header_html = models.TextField(
        _("HTML d'en-tÃªte"),
        blank=True,
        help_text=_("Contenu HTML personnalisé pour l'en-tÃªte de la facture")
    )
    
    footer_html = models.TextField(
        _("HTML de pied de page"),
        blank=True,
        help_text=_("Contenu HTML personnalisé pour le pied de page de la facture")
    )
    
    # Personnalisation visuelle
    primary_color = models.CharField(
        _("Couleur primaire"),
        max_length=7,
        default="#0066cc",
        help_text=_("Code hexadécimal de la couleur primaire (#RRGGBB)")
    )
    
    secondary_color = models.CharField(
        _("Couleur secondaire"),
        max_length=7,
        default="#000000",
        help_text=_("Code hexadécimal de la couleur secondaire (#RRGGBB)")
    )
    
    # Logo personnalisé
    logo = models.ImageField(
        _("Logo"),
        upload_to="tenants/invoices/logos/",
        null=True,
        blank=True,
        help_text=_("Logo Ã  afficher sur les factures")
    )
    
    # CSS personnalisé
    custom_css = models.TextField(
        _("CSS personnalisé"),
        blank=True,
        help_text=_("CSS personnalisé pour le modèle de facture")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(
        _("Date de création"),
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        _("Dernière mise Ã  jour"),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _("Modèle de facture")
        verbose_name_plural = _("Modèles de facture")
        unique_together = [('tenant', 'name')]
        indexes = [
            models.Index(fields=['tenant', 'is_default']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def save(self, *args, **kwargs):
        """
        Assurez-vous qu'il n'y a qu'un seul modèle par défaut.
        """
        if self.is_default:
            # Désactiver les autres modèles par défaut pour ce tenant
            TenantInvoiceTemplate.objects.filter(
                tenant=self.tenant,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)

