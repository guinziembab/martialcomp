from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

from finances.models.accounts import AccountingCategory, FinancialAccount
from finances.models.transactions import Transaction
from finances.models.payments import PaymentMethod
from finances.models.invoices import Invoice, InvoiceItem


class CombatFee(models.Model):
    """
    Configure les frais de participation pour les compétitions de combat.
    Chaque frais est lié à une compétition et définit les montants pour chaque type de participant.
    """
    FEE_TYPES = [
        ('registration', _('Inscription')),                 # Frais d'inscription
        ('equipment_rental', _('Location d\'équipement')),  # Frais pour louer des équipements
        ('coach_pass', _('Pass coach')),                    # Frais pour l'accès des coachs
        ('team_registration', _('Inscription équipe')),     # Frais spécifiques aux équipes
        ('spectator', _('Spectateur')),                     # Billets spectateurs
        ('other', _('Autre')),                              # Autres frais
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relation avec la compétition
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, 
                                   related_name='combat_fees', verbose_name=_('Compétition'))
    
    # Description et tarification
    name = models.CharField(max_length=100, verbose_name=_('Nom du tarif'))
    fee_type = models.CharField(max_length=20, choices=FEE_TYPES, verbose_name=_('Type de frais'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    
    # Montant et période de validité
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Montant'))
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    is_early_bird = models.BooleanField(default=False, verbose_name=_('Tarif préférentiel anticipé'))
    
    # Période de validité
    start_date = models.DateTimeField(verbose_name=_('Date de début'))
    end_date = models.DateTimeField(verbose_name=_('Date de fin'))
    
    # Réductions possibles
    has_team_discount = models.BooleanField(default=False, verbose_name=_('Remise pour équipe'))
    team_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                              verbose_name=_('Pourcentage de remise équipe'))
    
    # Limites et restrictions
    max_participants = models.PositiveIntegerField(default=0, verbose_name=_('Limite de participants (0 = illimité)'))
    
    # Configuration comptable
    accounting_category = models.ForeignKey(AccountingCategory, on_delete=models.SET_NULL, 
                                           null=True, blank=True, related_name='combat_fees',
                                           verbose_name=_('Catégorie comptable'))
    account = models.ForeignKey(FinancialAccount, on_delete=models.SET_NULL, 
                               null=True, blank=True, related_name='combat_fees',
                               verbose_name=_('Compte financier'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  null=True, blank=True, related_name='created_combat_fees',
                                  verbose_name=_('Créé par'))
    
    class Meta:
        verbose_name = _('Frais de compétition combat')
        verbose_name_plural = _('Frais de compétition combat')
        ordering = ['competition', 'fee_type', '-is_early_bird']
        indexes = [
            models.Index(fields=['competition', 'fee_type']),
            models.Index(fields=['is_early_bird']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.amount} {self.currency} ({self.get_fee_type_display()})"
    
    @property
    def is_active(self):
        """Vérifie si le tarif est actuellement actif"""
        now = timezone.now()
        return now >= self.start_date and now <= self.end_date
    
    def calculate_total(self, quantity=1, is_team=False):
        """Calcule le montant total en fonction de la quantité et des remises éventuelles"""
        total = self.amount * quantity
        
        # Appliquer les remises équipe si applicable
        if is_team and self.has_team_discount and self.team_discount_percent > 0:
            discount = (total * self.team_discount_percent) / 100
            total -= discount
            
        return total


class CombatRegistrationPayment(models.Model):
    """
    Représente un paiement pour une ou plusieurs inscriptions à une compétition de combat.
    Ce modèle sert de lien entre les inscriptions, les frais et les transactions financières.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('confirmed', _('Confirmé')),
        ('cancelled', _('Annulé')),
        ('refunded', _('Remboursé')),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=50, unique=True, blank=True, null=True, 
                               verbose_name=_('Référence de paiement'))
    
    # Relation avec la compétition
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, 
                                   related_name='combat_payments', verbose_name=_('Compétition'))
    
    # Lien avec des inscriptions de combats spécifiques
    combats = models.ManyToManyField('Combat', blank=True, related_name='payments', 
                                    verbose_name=_('Combats associés'))
    
    # Pour les paiements d'équipe
    team = models.ForeignKey('CombatTeam', on_delete=models.SET_NULL, null=True, blank=True, 
                            related_name='payments', verbose_name=_('Équipe'))
    
    # Informations du payeur (peut être un participant, un club, etc.)
    payer_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                          null=True, blank=True, verbose_name=_('Type du payeur'))
    payer_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID du payeur'))
    payer = GenericForeignKey('payer_content_type', 'payer_id')
    
    # Informations de paiement
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Montant'))
    currency = models.CharField(max_length=3, default='EUR', verbose_name=_('Devise'))
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, 
                                      null=True, blank=True, verbose_name=_('Méthode de paiement'))
    
    # Relations avec les modèles financiers
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, 
                                   null=True, blank=True, verbose_name=_('Transaction financière'))
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, 
                               null=True, blank=True, verbose_name=_('Facture'))
    
    # Statut et dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('Statut'))
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Date de paiement'))
    due_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Date d\'échéance'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                    null=True, blank=True, related_name='processed_combat_payments',
                                    verbose_name=_('Traité par'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Paiement d\'inscription combat')
        verbose_name_plural = _('Paiements d\'inscription combat')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['payment_date']),
            models.Index(fields=['competition']),
        ]
    
    def __str__(self):
        return f"Paiement {self.reference} - {self.amount} {self.currency} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Générer une référence unique si elle n'existe pas
        if not self.reference:
            now = timezone.now()
            self.reference = f"CP-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
        # Première sauvegarde - pas encore d'ID
        is_new = self.pk is None
        
        super().save(*args, **kwargs)
        
        # Après la première sauvegarde, créer la facture associée
        if is_new and not self.invoice:
            self.create_invoice()
    
    def create_invoice(self):
        """Crée une facture associée à ce paiement"""
        if not self.invoice:
            # Déterminer le bénéficiaire (la fédération, le club, etc. qui organise la compétition)
            recipient_model = None
            recipient_id = None
            
            if hasattr(self.competition, 'federation') and self.competition.federation:
                recipient_model = ContentType.objects.get_for_model(self.competition.federation)
                recipient_id = str(self.competition.federation.id)
            elif hasattr(self.competition, 'club') and self.competition.club:
                recipient_model = ContentType.objects.get_for_model(self.competition.club)
                recipient_id = str(self.competition.club.id)
            
            # Créer la facture
            invoice = Invoice.objects.create(
                reference=f"INV-{self.reference}",
                issuer_content_type=recipient_model,
                issuer_id=recipient_id,
                recipient_content_type=self.payer_content_type,
                recipient_id=self.payer_id,
                amount=self.amount,
                currency=self.currency,
                issue_date=timezone.now(),
                due_date=self.due_date or (timezone.now() + timezone.timedelta(days=30)),
                status='pending' if self.status == 'pending' else 'paid',
                notes=f"Paiement pour participation à la compétition: {self.competition.nom}"
            )
            
            # Ajouter les éléments de facture pour chaque type de frais
            InvoiceItem.objects.create(
                invoice=invoice,
                description=f"Inscription à la compétition {self.competition.nom}",
                quantity=1,
                unit_price=self.amount,
                amount=self.amount,
            )
            
            # Mettre à jour la référence
            self.invoice = invoice
            self.save(update_fields=['invoice'])
            
            return invoice
    
    def confirm_payment(self, payment_method=None, transaction=None):
        """Confirme le paiement et met à jour le statut"""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.payment_date = timezone.now()
            
            if payment_method:
                self.payment_method = payment_method
                
            # Mettre à jour ou créer une transaction associée
            if transaction:
                self.transaction = transaction
            elif not self.transaction:
                # Créer une nouvelle transaction
                self.create_transaction()
                
            # Mettre à jour la facture
            if self.invoice:
                self.invoice.status = 'paid'
                self.invoice.payment_date = self.payment_date
                self.invoice.save()
                
            self.save()
            return True
        return False
    
    def create_transaction(self):
        """Crée une transaction financière pour ce paiement"""
        if not self.transaction:
            # Trouver la catégorie comptable appropriée
            category = None
            if hasattr(self.competition, 'combat_fees'):
                fee = self.competition.combat_fees.filter(fee_type='registration').first()
                if fee and fee.accounting_category:
                    category = fee.accounting_category
            
            # Créer la transaction
            transaction = Transaction.objects.create(
                type='income',
                amount=self.amount,
                currency=self.currency,
                date=timezone.now(),
                status='validated' if self.status == 'confirmed' else 'pending',
                description=f"Paiement pour inscription à la compétition {self.competition.nom}",
                invoice=self.invoice,
                payment_method=self.payment_method,
                category=category,
                # Liens génériques vers l'entité source
                source_content_type=self.payer_content_type,
                source_object_id=self.payer_id,
            )
            
            # Mettre à jour la référence
            self.transaction = transaction
            self.save(update_fields=['transaction'])
            
            return transaction
    
    def cancel_payment(self):
        """Annule le paiement"""
        if self.status in ['pending', 'confirmed']:
            self.status = 'cancelled'
            
            # Annuler la facture
            if self.invoice:
                self.invoice.status = 'cancelled'
                self.invoice.save()
                
            # Annuler la transaction
            if self.transaction:
                self.transaction.status = 'cancelled'
                self.transaction.save()
                
            self.save()
            return True
        return False
    
    def refund_payment(self):
        """Effectue un remboursement"""
        if self.status == 'confirmed':
            self.status = 'refunded'
            
            # Mettre à jour la facture
            if self.invoice:
                self.invoice.status = 'refunded'
                self.invoice.save()
                
            # Traiter la transaction
            if self.transaction:
                self.transaction.status = 'refunded'
                self.transaction.save()
                
                # Créer une transaction inverse (sortie d'argent)
                refund_transaction = Transaction.objects.create(
                    type='expense',
                    amount=self.amount,
                    currency=self.currency,
                    date=timezone.now(),
                    status='validated',
                    description=f"Remboursement pour inscription à la compétition {self.competition.nom}",
                    category=self.transaction.category,
                    payment_method=self.transaction.payment_method,
                    # Liens génériques vers l'entité destination
                    destination_content_type=self.payer_content_type,
                    destination_object_id=self.payer_id,
                )
                
            self.save()
            return True
        return False