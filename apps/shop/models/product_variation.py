from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class AttributeType(models.Model):
    """
    Types d'attributs pour les variations de produits (ex: Taille, Couleur).
    """
    name = models.CharField(_("Nom"), max_length=50)
    display_name = models.CharField(_("Nom d'affichage"), max_length=50)
    description = models.TextField(_("Description"), blank=True)
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Type d'attribut")
        verbose_name_plural = _("Types d'attributs")
    
    def __str__(self):
        return self.display_name


class AttributeValue(models.Model):
    """
    Valeurs possibles pour chaque type d'attribut (ex: S, M, L pour Taille).
    """
    attribute_type = models.ForeignKey(
        AttributeType,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_("Type d'attribut")
    )
    value = models.CharField(_("Valeur"), max_length=50)
    display_value = models.CharField(_("Valeur d'affichage"), max_length=50)
    color_code = models.CharField(_("Code couleur (hex)"), max_length=7, blank=True)
    order = models.PositiveIntegerField(_("Ordre"), default=0)
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Valeur d'attribut")
        verbose_name_plural = _("Valeurs d'attributs")
        ordering = ['attribute_type', 'order', 'value']
        unique_together = ['attribute_type', 'value']
    
    def __str__(self):
        return f"{self.attribute_type}: {self.display_value}"


class ProductVariation(models.Model):
    """
    Variation d'un produit (ex: T-shirt bleu taille L).
    """
    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.CASCADE,
        related_name='variations',
        verbose_name=_("Produit")
    )
    sku = models.CharField(_("Référence (SKU)"), max_length=50, unique=True)
    price_adjustment = models.DecimalField(
        _("Ajustement de prix"),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_("Montant ajouté/soustrait au prix de base du produit")
    )
    stock_quantity = models.PositiveIntegerField(_("Quantité en stock"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)
    attributes = models.ManyToManyField(
        AttributeValue,
        through='ProductAttributeValue',
        related_name='product_variations',
        verbose_name=_("Attributs")
    )
    image = models.ImageField(
        _("Image spécifique"), 
        upload_to='shop/variations/', 
        blank=True, 
        null=True
    )
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Variation de produit")
        verbose_name_plural = _("Variations de produits")
    
    def __str__(self):
        attrs = ", ".join([str(attr) for attr in self.productattributevalue_set.all()])
        return f"{self.product.name} - {attrs}"
    
    @property
    def price(self):
        """Calcule le prix final avec l'ajustement."""
        base_price = self.product.current_price
        return base_price + self.price_adjustment
    
    @property
    def is_in_stock(self):
        """Vérifie si cette variation est en stock."""
        return self.stock_quantity > 0


class ProductAttributeValue(models.Model):
    """
    Table de liaison entre ProductVariation et AttributeValue.
    """
    product_variation = models.ForeignKey(
        ProductVariation,
        on_delete=models.CASCADE,
        verbose_name=_("Variation de produit")
    )
    attribute_value = models.ForeignKey(
        AttributeValue,
        on_delete=models.CASCADE,
        verbose_name=_("Valeur d'attribut")
    )
    
    class Meta:
        app_label = 'shop'
        verbose_name = _("Attribut de variation")
        verbose_name_plural = _("Attributs de variations")
        unique_together = ['product_variation', 'attribute_value']
    
    def __str__(self):
        return f"{self.attribute_value.attribute_type.display_name}: {self.attribute_value.display_value}"


