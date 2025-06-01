from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


class TransactionCategory(models.Model):
    """
    Catégories pour les transactions financières.
    """
    TYPE_CHOICES = [
        ('income', _('Revenu')),
        ('expense', _('Dépense')),
        ('both', _('Les deux')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='both', verbose_name=_('Type applicable'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Hiérarchie des catégories
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children', verbose_name=_('Catégorie parente'))
    
    # État
    active = models.BooleanField(default=True, verbose_name=_('Actif'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    class Meta:
        verbose_name = _('Catégorie de transaction')
        verbose_name_plural = _('Catégories de transactions')
        ordering = ['name']
        indexes = [
            models.Index(fields=['transaction_type']),
            models.Index(fields=['active']),
        ]
        
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_descendants(self):
        """
        Retourne toutes les catégories descendantes de cette catégorie.
        """
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Transaction(models.Model):
    """
    Modèle central pour tout mouvement financier dans le système.
    Chaque transaction représente un flux d'argent entrant ou sortant.
    """
    TYPE_CHOICES = [
        ('income', _('Revenu')),
        ('expense', _('Dépense')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('validated', _('Validée')),
        ('rejected', _('Rejetée')),
        ('refunded', _('Remboursée')),
        ('cancelled', _('Annulée')),
    ]
    
    # Identificateurs
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    # Informations de base
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_('Type'))
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Montant'))
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    
    # Date de la transaction (peut être différente de la date de création)
    date = models.DateField(default=timezone.now, verbose_name=_('Date de la transaction'))
    
    # Dates
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_updated = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    date_validated = models.DateTimeField(null=True, blank=True, verbose_name=_('Date de validation'))
    
    # Statut et catégorisation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('Statut'))
    category = models.ForeignKey(TransactionCategory, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Catégorie'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Relations avec d'autres modèles (à activer lorsque ces modèles seront créés)
    # Notez que ces relations utiliseront des chaînes pour éviter les dépendances circulaires
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_transactions', verbose_name=_('Créé par'))
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_transactions', verbose_name=_('Mis à jour par'))
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='validated_transactions', verbose_name=_('Validé par'))
    payment_method = models.ForeignKey('finances.PaymentMethod', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Méthode de paiement'))
    financial_account = models.ForeignKey('finances.FinancialAccount', on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Compte financier'))
    invoice = models.ForeignKey('finances.Invoice', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Facture associée'))
    
    # Liens vers entités du système
    source_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_transactions', verbose_name=_('Type d\'entité source'))
    source_object_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID de l\'entité source'))
    
    destination_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True, related_name='destination_transactions', verbose_name=_('Type d\'entité destination'))
    destination_object_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID de l\'entité destination'))
    
    # Documents associés
    receipt_file = models.FileField(upload_to='finances/receipts/%Y/%m/', null=True, blank=True, verbose_name=_('Reçu'))
    
    # Métadonnées
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Métadonnées'))
    
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-date_created']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['type']),
            models.Index(fields=['date_created']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} {self.currency} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Générer une référence unique si elle n'existe pas
        if not self.reference:
            now = timezone.now()
            self.reference = f"TR-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
        # Mettre à jour la date de validation si le statut change à 'validated'
        if self.status == 'validated' and not self.date_validated:
            self.date_validated = timezone.now()
            
        super().save(*args, **kwargs)
    
    @property
    def is_income(self):
        return self.type == 'income'
    
    @property
    def is_expense(self):
        return self.type == 'expense'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_validated(self):
        return self.status == 'validated'
    
    # Alias pour la compatibilité avec les vues existantes
    @property
    def created_at(self):
        """Alias pour date_created pour la compatibilité avec les vues."""
        return self.date_created
    
    @property
    def updated_at(self):
        """Alias pour date_updated pour la compatibilité avec les vues."""
        return self.date_updated
    
    def validate(self, user=None):
        """Valide une transaction en attente."""
        if self.status == 'pending':
            self.status = 'validated'
            self.date_validated = timezone.now()
            if user:
                self.validated_by = user
            self.save()
            return True
        return False
    
    def reject(self, user=None):
        """Rejette une transaction en attente."""
        if self.status == 'pending':
            self.status = 'rejected'
            if user:
                self.validated_by = user
            self.save()
            return True
        return False
    
    def cancel(self, user=None):
        """Annule une transaction."""
        if self.status in ['pending', 'validated']:
            self.status = 'cancelled'
            if user:
                self.validated_by = user
            self.save()
            return True
        return False
    
    def refund(self, user=None):
        """Marque une transaction comme remboursée."""
        if self.status == 'validated':
            self.status = 'refunded'
            if user:
                self.validated_by = user
            self.save()
            return True
        return False


class TransactionAttachment(models.Model):
    """
    Pièces jointes pour les transactions (factures, reçus, etc.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='attachments', verbose_name=_('Transaction'))
    
    # Fichier et métadonnées
    file = models.FileField(upload_to='finances/attachments/%Y/%m/', verbose_name=_('Fichier'))
    filename = models.CharField(max_length=255, verbose_name=_('Nom du fichier'))
    file_type = models.CharField(max_length=50, blank=True, verbose_name=_('Type de fichier'))
    file_size = models.PositiveIntegerField(default=0, verbose_name=_('Taille du fichier'))
    
    # Description
    description = models.CharField(max_length=255, blank=True, verbose_name=_('Description'))
    
    # Métadonnées
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_attachments', verbose_name=_('Téléchargé par'))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de téléchargement'))
    
    class Meta:
        verbose_name = _('Pièce jointe de transaction')
        verbose_name_plural = _('Pièces jointes de transactions')
        ordering = ['-uploaded_at']
        
    def __str__(self):
        return f"{self.filename} ({self.transaction.reference})"
    
    def save(self, *args, **kwargs):
        # Si le nom de fichier n'est pas défini, l'extraire du fichier
        if not self.filename and self.file:
            self.filename = self.file.name.split('/')[-1]
            
        # Déterminer le type de fichier à partir de l'extension
        if self.file and not self.file_type:
            extension = self.filename.split('.')[-1].lower()
            if extension in ['jpg', 'jpeg', 'png', 'gif']:
                self.file_type = 'image'
            elif extension in ['pdf']:
                self.file_type = 'pdf'
            elif extension in ['doc', 'docx']:
                self.file_type = 'document'
            elif extension in ['xls', 'xlsx', 'csv']:
                self.file_type = 'spreadsheet'
            else:
                self.file_type = 'other'
                
        # Enregistrer la taille du fichier
        if self.file and not self.file_size and hasattr(self.file, 'size'):
            self.file_size = self.file.size
            
        super().save(*args, **kwargs)