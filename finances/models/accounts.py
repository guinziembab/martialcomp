from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
import uuid


class AccountingCategory(models.Model):
    """
    Catégories comptables pour classer les transactions et faciliter les rapports financiers.
    """
    TYPE_CHOICES = [
        ('income', _('Revenu')),
        ('expense', _('Dépense')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_('Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    code = models.CharField(max_length=20, blank=True, verbose_name=_('Code comptable'))
    
    # Hiérarchie des catégories
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories', verbose_name=_('Catégorie parente'))
    
    # Organisation associée (optionnel, pour les catégories spécifiques)
    organization_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Type d\'organisation'))
    organization_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID de l\'organisation'))
    organization = GenericForeignKey('organization_content_type', 'organization_id')
    
    # Métadonnées
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_system = models.BooleanField(default=False, verbose_name=_('Catégorie système'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    class Meta:
        verbose_name = _('Catégorie comptable')
        verbose_name_plural = _('Catégories comptables')
        ordering = ['name']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['is_active']),
        ]
        
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_name(self):
        """Retourne le nom complet avec la hiérarchie des parents."""
        if self.parent:
            return f"{self.parent.full_name} > {self.name}"
        return self.name
    
    @property
    def is_income_category(self):
        """Vérifie si c'est une catégorie de revenus."""
        return self.type == 'income'
    
    @property
    def is_expense_category(self):
        """Vérifie si c'est une catégorie de dépenses."""
        return self.type == 'expense'


class FinancialAccount(models.Model):
    """
    Représente un compte financier (bancaire ou caisse) pour une entité.
    """
    TYPE_CHOICES = [
        ('checking', _('Compte courant')),
        ('savings', _('Compte d\'épargne')),
        ('cash', _('Caisse')),
        ('credit', _('Carte de crédit')),
        ('other', _('Autre')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_('Type'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Informations financières
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('Solde d\'ouverture'))
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('Solde actuel'))
    reconciled_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_('Solde rapproché'))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    last_reconciled = models.DateTimeField(null=True, blank=True, verbose_name=_('Dernière réconciliation'))
    
    # Propriétaire du compte
    owner_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('Type de propriétaire'))
    owner_id = models.CharField(max_length=50, verbose_name=_('ID du propriétaire'))
    owner = GenericForeignKey('owner_content_type', 'owner_id')
    
    # Informations bancaires (si applicable)
    bank_name = models.CharField(max_length=100, blank=True, verbose_name=_('Nom de la banque'))
    account_number = models.CharField(max_length=50, blank=True, verbose_name=_('Numéro de compte'))
    iban = models.CharField(max_length=34, blank=True, verbose_name=_('IBAN'))
    bic = models.CharField(max_length=11, blank=True, verbose_name=_('BIC/SWIFT'))
    
    # État
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_default = models.BooleanField(default=False, verbose_name=_('Compte par défaut'))
    
    class Meta:
        verbose_name = _('Compte financier')
        verbose_name_plural = _('Comptes financiers')
        ordering = ['-is_default', 'name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.current_balance} {self.currency})"
    
    def save(self, *args, **kwargs):
        # Si c'est un nouveau compte, initialiser le solde courant avec le solde d'ouverture
        if not self.pk:
            self.current_balance = self.opening_balance
            
        # Si c'est marqué comme compte par défaut, désactiver ce flag pour les autres comptes du même propriétaire
        if self.is_default and self.owner_content_type and self.owner_id:
            FinancialAccount.objects.filter(
                owner_content_type=self.owner_content_type,
                owner_id=self.owner_id,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
            
        super().save(*args, **kwargs)
    
    def update_balance(self, amount, transaction_type):
        """
        Met à jour le solde du compte basé sur une transaction.
        
        Parameters:
        - amount: le montant à ajouter ou soustraire
        - transaction_type: 'income' ou 'expense'
        """
        if transaction_type == 'income':
            self.current_balance += amount
        elif transaction_type == 'expense':
            self.current_balance -= amount
        
        self.save(update_fields=['current_balance', 'updated_at'])
    
    def reconcile(self):
        """
        Marque le compte comme réconcilié avec le solde actuel.
        """
        self.reconciled_balance = self.current_balance
        self.last_reconciled = timezone.now()
        self.save(update_fields=['reconciled_balance', 'last_reconciled', 'updated_at'])
        return True


class MembershipFee(models.Model):
    """
    Configuration des cotisations pour différents types de membres.
    """
    PERIOD_CHOICES = [
        ('yearly', _('Annuelle')),
        ('seasonal', _('Saisonnière')),
        ('semester', _('Semestrielle')),
        ('quarterly', _('Trimestrielle')),
        ('monthly', _('Mensuelle')),
        ('one_time', _('Unique')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Organisation qui définit cette cotisation
    organization_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('Type d\'organisation'))
    organization_id = models.CharField(max_length=50, verbose_name=_('ID de l\'organisation'))
    organization = GenericForeignKey('organization_content_type', 'organization_id')
    
    # Configuration de la cotisation
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Montant'))
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default='yearly', verbose_name=_('Période'))
    
    # Délais et périodes
    start_date = models.DateField(verbose_name=_('Date de début'))
    end_date = models.DateField(verbose_name=_('Date de fin'))
    grace_period_days = models.PositiveIntegerField(default=30, verbose_name=_('Période de grâce (jours)'))
    
    # Paramètres supplémentaires
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_prorated = models.BooleanField(default=False, verbose_name=_('Au prorata'))
    member_type = models.CharField(max_length=50, blank=True, verbose_name=_('Type de membre'))
    age_min = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Âge minimum'))
    age_max = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Âge maximum'))
    
    # Catégorie comptable pour cette cotisation
    accounting_category = models.ForeignKey(AccountingCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Catégorie comptable'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    class Meta:
        verbose_name = _('Cotisation')
        verbose_name_plural = _('Cotisations')
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date']),
        ]
        
    def __str__(self):
        return f"{self.name} - {self.amount} {self.currency} ({self.get_period_display()})"
    
    @property
    def is_current(self):
        """Vérifie si cette configuration de cotisation est actuellement valide."""
        today = timezone.now().date()
        return self.is_active and self.start_date <= today <= self.end_date
    
    def calculate_prorated_amount(self, join_date):
        """
        Calcule le montant au prorata en fonction de la date d'adhésion.
        """
        if not self.is_prorated:
            return self.amount
            
        # Date de fin de la période courante
        period_end = self.end_date
        
        # Nombre total de jours dans la période
        total_days = (period_end - self.start_date).days
        
        # Nombre de jours restants
        days_remaining = (period_end - join_date).days
        
        # Si la date d'adhésion est après la date de fin ou avant la date de début
        if days_remaining <= 0 or total_days <= 0:
            return 0
            
        # Calcul du montant au prorata
        prorated_amount = (self.amount * days_remaining) / total_days
        
        # Arrondir à 2 décimales
        return round(prorated_amount, 2)