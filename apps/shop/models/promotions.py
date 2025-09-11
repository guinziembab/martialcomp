from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class Coupon(models.Model):
    """
    Coupons de réduction pour les achats.
    """
    # Types de coupons
    PERCENTAGE = 'percentage'
    FIXED_AMOUNT = 'fixed'
    FREE_SHIPPING = 'free_shipping'
    
    TYPE_CHOICES = [
        (PERCENTAGE, _('Pourcentage')),
        (FIXED_AMOUNT, _('Montant fixe')),
        (FREE_SHIPPING, _('Livraison gratuite')),
    ]
    
    code = models.CharField(_("Code"), max_length=30, unique=True)
    description = models.CharField(_("Description"), max_length=200, blank=True)
    type = models.CharField(_("Type"), max_length=20, choices=TYPE_CHOICES, default=PERCENTAGE)
    
    # Valeur de la réduction (pourcentage ou montant fixe selon le type)
    value = models.DecimalField(
        _("Valeur"), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Limites d'utilisation
    min_purchase_amount = models.DecimalField(
        _("Montant d'achat minimum"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    max_discount_amount = models.DecimalField(
        _("Montant de remise maximum"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Limiter le montant maximum de la remise (uniquement pour le type pourcentage)")
    )
    usage_limit = models.PositiveIntegerField(
        _("Limite d'utilisation"),
        null=True,
        blank=True,
        help_text=_("Nombre maximum d'utilisations autorisées")
    )
    usage_count = models.PositiveIntegerField(_("Nombre d'utilisations"), default=0)
    
    # Restrictions
    is_for_first_order = models.BooleanField(
        _("Première commande uniquement"),
        default=False,
        help_text=_("Applicable uniquement pour la première commande d'un utilisateur")
    )
    
    # Validité
    is_active = models.BooleanField(_("Actif"), default=True)
    start_date = models.DateTimeField(_("Date de début"), default=timezone.now)
    end_date = models.DateTimeField(_("Date de fin"), null=True, blank=True)
    
    # Relations
    applicable_products = models.ManyToManyField(
        'shop.Product',
        blank=True,
        related_name='applicable_coupons',
        verbose_name=_("Produits applicables")
    )
    applicable_categories = models.ManyToManyField(
        'shop.Category',
        blank=True,
        related_name='applicable_coupons',
        verbose_name=_("Catégories applicables")
    )
    
    # Dates
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")
    
    def __str__(self):
        return f"{self.code} - {self.get_type_display()}"
    
    @property
    def is_valid(self):
        """
        Vérifie si le coupon est valide en fonction de la date et des limites d'utilisation.
        """
        now = timezone.now()
        
        # Vérifier si le coupon est actif
        if not self.is_active:
            return False
        
        # Vérifier les dates de validité
        if now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        
        # Vérifier les limites d'utilisation
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        
        return True
    
    def get_discount_amount(self, cart_total):
        """
        Calcule le montant de la remise en fonction du type de coupon et du total du panier.
        """
        if not self.is_valid:
            return Decimal('0.00')
        
        # Vérifier le montant minimum d'achat
        if self.min_purchase_amount and cart_total < self.min_purchase_amount:
            return Decimal('0.00')
        
        # Calculer la remise selon le type
        if self.type == self.PERCENTAGE:
            discount = cart_total * (self.value / Decimal('100'))
            # Appliquer la limite maximum si définie
            if self.max_discount_amount and discount > self.max_discount_amount:
                return self.max_discount_amount
            return discount
        elif self.type == self.FIXED_AMOUNT:
            # La remise ne peut pas dépasser le total du panier
            return min(self.value, cart_total)
        
        # Pour le type FREE_SHIPPING, la logique est gérée ailleurs
        return Decimal('0.00')


class Promotion(models.Model):
    """
    Promotions temporaires sur des produits ou catégories.
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    # Type de remise
    discount_type = models.CharField(
        _("Type de remise"),
        max_length=20,
        choices=[
            ('percentage', _('Pourcentage')),
            ('fixed', _('Montant fixe')),
        ],
        default='percentage'
    )
    discount_value = models.DecimalField(_("Valeur de la remise"), max_digits=10, decimal_places=2)
    
    # Dates de validité
    start_date = models.DateTimeField(_("Date de début"), default=timezone.now)
    end_date = models.DateTimeField(_("Date de fin"))
    is_active = models.BooleanField(_("Active"), default=True)
    
    # Ã‰léments concernés par la promotion
    products = models.ManyToManyField(
        'shop.Product',
        blank=True,
        related_name='promotions',
        verbose_name=_("Produits en promotion")
    )
    categories = models.ManyToManyField(
        'shop.Category',
        blank=True,
        related_name='promotions',
        verbose_name=_("Catégories en promotion")
    )
    brands = models.ManyToManyField(
        'shop.Brand',
        blank=True,
        related_name='promotions',
        verbose_name=_("Marques en promotion")
    )
    
    # Options supplémentaires
    banner_image = models.ImageField(
        _("Image bannière"),
        upload_to='shop/promotions/',
        blank=True,
        null=True
    )
    highlight_color = models.CharField(_("Couleur de surbrillance"), max_length=7, blank=True)
    priority = models.PositiveIntegerField(_("Priorité"), default=0)
    
    # Dates
    created_at = models.DateTimeField(_("Créée le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mise Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
        ordering = ['-start_date', 'name']
    
    def __str__(self):
        return self.name
    
    @property
    def is_valid(self):
        """
        Vérifie si la promotion est active et dans sa période de validité.
        """
        now = timezone.now()
        return (
            self.is_active and 
            now >= self.start_date and 
            now <= self.end_date
        )
    
    def get_discount_amount(self, price):
        """
        Calcule le montant de la remise en fonction du type et de la valeur.
        """
        if self.discount_type == 'percentage':
            return price * (self.discount_value / Decimal('100'))
        else:  # fixed amount
            return min(self.discount_value, price)  # La remise ne peut pas dépasser le prix
    
    def get_discounted_price(self, price):
        """
        Calcule le prix après application de la remise.
        """
        discount = self.get_discount_amount(price)
        return max(price - discount, Decimal('0.00'))  # Le prix ne peut pas Ãªtre négatif


