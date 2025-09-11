from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Product(models.Model):
    """
    Modèle principal de produit pour la boutique.
    """
    # Choix pour le niveau de pratique
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    PROFESSIONAL = 'professional'
    ALL_LEVELS = 'all'
    
    LEVEL_CHOICES = [
        (BEGINNER, _('Débutant')),
        (INTERMEDIATE, _('Intermédiaire')),
        (ADVANCED, _('Avancé')),
        (PROFESSIONAL, _('Professionnel')),
        (ALL_LEVELS, _('Tous niveaux')),
    ]
    
    # Informations de base
    name = models.CharField(_("Nom"), max_length=150)
    slug = models.SlugField(_("Slug"), max_length=200, unique=True)
    description = models.TextField(_("Description"))
    short_description = models.CharField(_("Description courte"), max_length=255, blank=True)
    
    # Catégorisation
    categories = models.ManyToManyField(
        'shop.Category', 
        related_name='products',
        verbose_name=_("Catégories")
    )
    
    # Pour la compatibilité avec le code existant
    @property
    def category(self):
        """Retourne la catégorie principale du produit."""
        return self.categories.first()
    
    # Associations
    disciplines = models.ManyToManyField(
        'competitions.Discipline', 
        blank=True,
        related_name='related_products',
        verbose_name=_("Disciplines associées")
    )
    
    # Prix et stocks
    price = models.DecimalField(
        _("Prix"), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    sale_price = models.DecimalField(
        _("Prix promotionnel"), 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock_quantity = models.PositiveIntegerField(_("Quantité en stock"), default=0)
    low_stock_threshold = models.PositiveIntegerField(_("Seuil de stock bas"), default=5)
    
    # Caractéristiques spécifiques
    brand = models.CharField(
        _("Marque"), 
        max_length=100, 
        blank=True,
        help_text=_("Nom de la marque du produit (ex: Nike, Adidas, Venum)")
    )
    supplier = models.CharField(
        _("Fournisseur"), 
        max_length=100, 
        blank=True,
        help_text=_("Nom du fournisseur ou distributeur")
    )
    sku = models.CharField(_("Référence (SKU)"), max_length=50, unique=True)
    barcode = models.CharField(_("Code-barres"), max_length=50, blank=True)
    practice_level = models.CharField(
        _("Niveau de pratique"),
        max_length=20,
        choices=LEVEL_CHOICES,
        default=ALL_LEVELS
    )
    
    # Certifications et homologation
    is_certified = models.BooleanField(_("Produit homologué"), default=False)
    certification_details = models.TextField(_("Détails d'homologation"), blank=True)
    certificate_file = models.FileField(
        _("Certificat d'homologation"),
        upload_to='shop/certificates/',
        blank=True,
        null=True
    )
    
    # Dimensions et poids pour l'expédition
    weight = models.DecimalField(
        _("Poids (kg)"), 
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    length = models.DecimalField(
        _("Longueur (cm)"), 
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    width = models.DecimalField(
        _("Largeur (cm)"), 
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    height = models.DecimalField(
        _("Hauteur (cm)"), 
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Métadonnées et SEO
    meta_title = models.CharField(_("Meta titre"), max_length=200, blank=True)
    meta_description = models.TextField(_("Meta description"), blank=True)
    tags = models.CharField(_("Tags"), max_length=255, blank=True)
    
    # Statuts et contrÃ´le
    is_active = models.BooleanField(_("Actif"), default=True)
    is_featured = models.BooleanField(_("Mis en avant"), default=False)
    is_new = models.BooleanField(_("Nouveau produit"), default=True)
    tax_rate = models.DecimalField(
        _("Taux de TVA (%)"), 
        max_digits=5, 
        decimal_places=2, 
        default=20.0
    )
    
    # Dates
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Produit")
        verbose_name_plural = _("Produits")
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Générer le slug automatiquement si non fourni
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    @property
    def current_price(self):
        """Retourne le prix actuel (promotion ou normal)."""
        return self.sale_price if self.sale_price else self.price
    
    @property
    def has_discount(self):
        """Indique si le produit a une promotion active."""
        return bool(self.sale_price and self.sale_price < self.price)
    
    @property
    def discount_percentage(self):
        """Calcule le pourcentage de réduction."""
        if self.has_discount:
            return int(100 - (self.sale_price * 100 / self.price))
        return 0
    
    @property
    def is_in_stock(self):
        """Vérifie si le produit est en stock."""
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Vérifie si le stock est bas."""
        return 0 < self.stock_quantity <= self.low_stock_threshold


class ProductImage(models.Model):
    """
    Images de produit.
    """
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name=_("Produit")
    )
    image = models.ImageField(_("Image"), upload_to='shop/products/')
    alt_text = models.CharField(_("Texte alternatif"), max_length=100, blank=True)
    is_main = models.BooleanField(_("Image principale"), default=False)
    order = models.PositiveIntegerField(_("Ordre"), default=0)
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Image produit")
        verbose_name_plural = _("Images produits")
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.product.name} ({self.id})"
    
    def save(self, *args, **kwargs):
        # Si cette image est définie comme principale, s'assurer que les autres ne le sont pas
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        
        # Si c'est la seule image, la définir comme principale
        if not ProductImage.objects.filter(product=self.product).exists():
            self.is_main = True
            
        super().save(*args, **kwargs)


