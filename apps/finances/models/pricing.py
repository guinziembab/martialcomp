from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from apps.competitions.models import Organization
from decimal import Decimal
from django.utils import timezone

class PricingRegion(models.Model):
    """Régions géographiques avec tarification spécifique"""
    
    REGION_CHOICES = [
        ('mature', _('Marchés matures')),
        ('emergent', _('Marchés émergents')),
        # Anciennes régions (désactivées, conservées pour compatibilité)
        ('africa', _('Afrique')),
        ('southeast_asia', _('Asie du Sud-Est')),
        ('south_central_america', _('Amérique du Sud/Centrale')),
        ('eastern_europe', _('Europe de l\'Est')),
        ('western_europe_north_america_oceania', _('Europe de l\'Ouest/Amérique du Nord/Océanie')),
        ('middle_east', _('Moyen-Orient')),
    ]
    
    name = models.CharField(max_length=100, choices=REGION_CHOICES, unique=True)
    base_price_per_member = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        help_text='Prix de base par membre (facturation annuelle)'
    )
    monthly_price_per_member = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Prix mensuel par membre'
    )
    currency = models.CharField(max_length=3, default='EUR')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Région tarifaire'
        verbose_name_plural = 'Régions tarifaires'
    
    def __str__(self):
        return f"{self.get_name_display()} - {self.base_price_per_member}â‚¬"
    
    @classmethod
    def get_default_pricing(cls):
        """Retourne la tarification par defaut (2 tiers)"""
        return {
            'mature': {
                'yearly': Decimal('9.99'),
                'monthly': Decimal('0.99'),
            },
            'emergent': {
                'yearly': Decimal('4.99'),
                'monthly': Decimal('0.49'),
            },
        }

class VolumeDiscount(models.Model):
    """Dégressivité par nombre de membres"""
    
    member_range_start = models.IntegerField(help_text='Nombre minimum de membres')
    member_range_end = models.IntegerField(help_text='Nombre maximum de membres (0 = illimité)')
    discount_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Pourcentage de réduction'
    )
    description = models.CharField(max_length=200, blank=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Réduction volume'
        verbose_name_plural = 'Réductions volume'
        ordering = ['member_range_start']
    
    def __str__(self):
        end = self.member_range_end if self.member_range_end > 0 else '+'
        return f"{self.member_range_start}-{end} membres: -{self.discount_percentage}%"
    
    @classmethod
    def get_discount_for_members(cls, member_count):
        """Retourne la réduction applicable pour un nombre de membres"""
        discount = cls.objects.filter(
            member_range_start__lte=member_count,
            member_range_end__gte=member_count
        ).first()
        
        if not discount:
            # Chercher la réduction avec member_range_end = 0 (illimité)
            discount = cls.objects.filter(
                member_range_start__lte=member_count,
                member_range_end=0
            ).first()
        
        return discount.discount_percentage if discount else Decimal('0')

class Wallet(models.Model):
    """Portefeuille virtuel pour les organisations"""
    
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Portefeuille'
        verbose_name_plural = 'Portefeuilles'
    
    def __str__(self):
        return f"Portefeuille {self.organization.name}: {self.balance}â‚¬"
    
    def credit(self, amount, description=""):
        """Crédite le portefeuille"""
        self.balance += amount
        self.save()
        
        # Créer une transaction
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='CREDIT',
            description=description
        )
    
    def debit(self, amount, description=""):
        """Débite le portefeuille"""
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            
            # Créer une transaction
            WalletTransaction.objects.create(
                wallet=self,
                amount=-amount,
                transaction_type='DEBIT',
                description=description
            )
            return True
        return False

class WalletTransaction(models.Model):
    """Transactions du portefeuille"""

    TRANSACTION_TYPES = [
        ('CREDIT', _('Crédit')),
        ('DEBIT', _('Débit')),
        ('COMMISSION', _('Commission')),
        ('REFUND', _('Remboursement')),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='wallet_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Transaction de portefeuille'
        verbose_name_plural = 'Transactions de portefeuille'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} {self.amount}â‚¬ - {self.wallet.organization.name}"

class ReferralCommission(models.Model):
    """Commission de parrainage pour les fédérations"""

    STATUS_CHOICES = [
        ('PENDING', _('En attente')),
        ('PROCESSED', _('Traité')),
        ('CANCELLED', _('Annulé')),
    ]
    
    referring_organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        related_name='referrals_made',
        help_text='Fédération qui a parrainé'
    )
    referred_organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE,
        related_name='referral_source',
        help_text='Club parrainé'
    )
    initial_subscription = models.ForeignKey(
        'finances.Subscription', 
        on_delete=models.CASCADE,
        related_name='referral_commission'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=7.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Commission de parrainage'
        verbose_name_plural = 'Commissions de parrainage'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commission {self.amount}â‚¬ - {self.referring_organization.name} â†’ {self.referred_organization.name}"
    
    def process_commission(self):
        """Traite la commission en créditant le portefeuille de la fédération"""
        if self.status == 'PENDING':
            wallet, created = Wallet.objects.get_or_create(organization=self.referring_organization)
            wallet.credit(self.amount, f"Commission parrainage: {self.referred_organization.name}")
            
            self.status = 'PROCESSED'
            self.processed_at = timezone.now()
            self.save()
            
            return True
        return False

class TemporaryAccess(models.Model):
    """Accès temporaire pour utilisateurs non-abonnés"""

    ACCESS_TYPES = [
        ('competitor_essential', _('Compétiteur Essential')),
        ('live_results', _('Résultats Live')),
        ('guest_judge', _('Juge invité')),
        ('event_shop', _('Boutique événement')),
    ]
    
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    event = models.ForeignKey('competitions.Event', on_delete=models.CASCADE)
    access_type = models.CharField(max_length=30, choices=ACCESS_TYPES)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    payment = models.ForeignKey('finances.PaymentAttempt', null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Accès temporaire'
        verbose_name_plural = 'Accès temporaires'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_access_type_display()} - {self.user.username} - {self.event.name}"
    
    @property
    def is_valid(self):
        """Vérifie si l'accès est encore valide"""
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until
    
    def get_price(self):
        """Retourne le prix selon le type d'accès"""
        prices = {
            'competitor_essential': Decimal('15.00'),
            'live_results': Decimal('3.99'),
            'guest_judge': Decimal('0.00'),
            'event_shop': Decimal('0.00'),
        }
        return prices.get(self.access_type, Decimal('0.00')) 



