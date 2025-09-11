from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
import uuid


class Invoice(models.Model):
    """
    Modèle représentant une facture émise par une entité (club, fédération) Ã  un destinataire.
    """
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('issued', _('Ã‰mise')),
        ('paid', _('Payée')),
        ('partially_paid', _('Partiellement payée')),
        ('overdue', _('En retard')),
        ('cancelled', _('Annulée')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=50, unique=True, blank=True, verbose_name=_('Numéro de facture'))
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise Ã  jour'))
    issued_date = models.DateField(default=timezone.now, verbose_name=_('Date d\'émission'))
    due_date = models.DateField(verbose_name=_('Date d\'échéance'))
    paid_date = models.DateField(null=True, blank=True, verbose_name=_('Date de paiement'))
    
    # Montants
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Sous-total HT'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Montant TVA'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Total TTC'))
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Montant payé'))
    
    # Information générale
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name=_('Statut'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    terms = models.TextField(blank=True, verbose_name=_('Conditions'))
    
    # Relations
    # Ã‰metteur de la facture (club, fédération, etc.)
    issuer_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, related_name='issued_invoices', verbose_name=_('Type d\'émetteur'))
    issuer_object_id = models.CharField(max_length=50, verbose_name=_('ID de l\'émetteur'))
    
    # Destinataire de la facture (membre, club, etc.)
    recipient_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE, related_name='received_invoices', verbose_name=_('Type de destinataire'))
    recipient_object_id = models.CharField(max_length=50, verbose_name=_('ID du destinataire'))
    
    # Entité liée Ã  la facture (compétition, adhésion, etc.)
    related_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_invoices', verbose_name=_('Type d\'entité liée'))
    related_object_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID de l\'entité liée'))
    
    # Utilisateur qui a créé la facture
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_invoices', verbose_name=_('Créé par'))
    
    # PDF document
    pdf_file = models.FileField(upload_to='finances/invoices/%Y/%m/', null=True, blank=True, verbose_name=_('Fichier PDF'))
    
    class Meta:
        app_label = 'finances'
        verbose_name = _('Facture')
        verbose_name_plural = _('Factures')
        ordering = ['-issued_date', '-number']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['issued_date']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.number} - {self.total} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Si c'est une nouvelle facture, générer un numéro unique
        if not self.number:
            year = timezone.now().year
            # Calculer le prochain numéro disponible
            last_invoice = Invoice.objects.filter(
                number__startswith=f"INV-{year}"
            ).order_by('-number').first()
            
            if last_invoice:
                try:
                    last_number = int(last_invoice.number.split('-')[-1])
                    next_number = last_number + 1
                except (IndexError, ValueError):
                    next_number = 1
            else:
                next_number = 1
                
            self.number = f"INV-{year}-{next_number:05d}"
        
        # Calculer/mettre Ã  jour les montants
        if not self.total:
            self.total = self.subtotal + self.tax_amount
        
        # Mettre Ã  jour le statut en fonction du paiement
        if self.status != 'cancelled':
            if self.amount_paid >= self.total:
                self.status = 'paid'
                if not self.paid_date:
                    self.paid_date = timezone.now().date()
            elif self.amount_paid > 0:
                self.status = 'partially_paid'
            elif self.status == 'issued' and self.due_date and self.due_date < timezone.now().date():
                self.status = 'overdue'
        
        super().save(*args, **kwargs)
    
    @property
    def is_paid(self):
        return self.status == 'paid'
    
    @property
    def is_overdue(self):
        return self.due_date < timezone.now().date() and self.status not in ['paid', 'cancelled']
    
    @property
    def balance_due(self):
        return self.total - self.amount_paid
    
    def issue(self):
        """
        Ã‰met la facture (passe du statut brouillon Ã  émise).
        """
        if self.status == 'draft':
            self.status = 'issued'
            self.save()
            return True
        return False
    
    def cancel(self):
        """
        Annule la facture.
        """
        if self.status != 'cancelled':
            self.status = 'cancelled'
            self.save()
            return True
        return False
    
    def register_payment(self, amount, payment_date=None):
        """
        Enregistre un paiement pour cette facture.
        """
        if self.status in ['cancelled']:
            return False
            
        self.amount_paid += amount
        
        if payment_date:
            self.paid_date = payment_date
        elif not self.paid_date and self.amount_paid >= self.total:
            self.paid_date = timezone.now().date()
            
        self.save()
        return True


class InvoiceItem(models.Model):
    """
    Représente une ligne de facturation dans une facture.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items', verbose_name=_('Facture'))
    
    description = models.CharField(max_length=255, verbose_name=_('Description'))
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1, verbose_name=_('Quantité'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Prix unitaire HT'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Taux de TVA (%)'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Montant TVA'))
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Sous-total HT'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_('Total TTC'))
    
    # Informations supplémentaires
    reference = models.CharField(max_length=50, blank=True, verbose_name=_('Référence'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))
    
    # Liens vers les entités (facultatif)
    item_content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Type d\'élément'))
    item_object_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID de l\'élément'))
    
    # Catégorie comptable
    category = models.ForeignKey('finances.AccountingCategory', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Catégorie comptable'))
    
    class Meta:
        app_label = 'finances'
        verbose_name = _('Ã‰lément de facture')
        verbose_name_plural = _('Ã‰léments de facture')
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"
    
    def save(self, *args, **kwargs):
        # Calculer les montants
        self.subtotal = self.quantity * self.unit_price
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total = self.subtotal + self.tax_amount
        
        # Sauvegarder l'élément
        super().save(*args, **kwargs)
        
        # Mettre Ã  jour les totaux de la facture
        invoice = self.invoice
        items = invoice.items.all()
        
        invoice.subtotal = sum(item.subtotal for item in items)
        invoice.tax_amount = sum(item.tax_amount for item in items)
        invoice.total = sum(item.total for item in items)
        invoice.save()
        
    def delete(self, *args, **kwargs):
        invoice = self.invoice
        super().delete(*args, **kwargs)
        
        # Recalculer les totaux de la facture
        items = invoice.items.all()
        invoice.subtotal = sum(item.subtotal for item in items)
        invoice.tax_amount = sum(item.tax_amount for item in items)
        invoice.total = sum(item.total for item in items)
        invoice.save()


