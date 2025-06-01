from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal
import uuid


class Cart(models.Model):
    """
    Panier d'achat pour les utilisateurs.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True,
        verbose_name=_("Utilisateur")
    )
    session_id = models.CharField(_("ID de session"), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Si le panier est converti en commande, nous gardons la référence
    converted_to_order = models.BooleanField(_("Converti en commande"), default=False)
    order = models.ForeignKey(
        'shop.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='originating_cart',
        verbose_name=_("Commande résultante")
    )
    
    class Meta:
        verbose_name = _("Panier")
        verbose_name_plural = _("Paniers")
    
    def __str__(self):
        if self.user:
            return f"Panier de {self.user.username} ({self.id})"
        return f"Panier anonyme ({self.session_id})"
    
    def get_subtotal(self):
        """Calcule le sous-total du panier sans frais supplémentaires."""
        return sum(item.line_total for item in self.items.all())
        
    @property
    def subtotal(self):
        """Property pour le sous-total du panier."""
        return self.get_subtotal()
    
    @property
    def total_quantity(self):
        """Retourne le nombre total d'articles dans le panier."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def is_empty(self):
        """Vérifie si le panier est vide."""
        return self.items.count() == 0
    
    def add_item(self, product, quantity=1, variation=None):
        """
        Ajoute un article au panier ou met à jour sa quantité si déjà présent.
        """
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            variation=variation,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
            
        self.updated_at = models.DateTimeField.auto_now
        self.save()
        
        return cart_item
    
    def update_item_quantity(self, cart_item_id, quantity):
        """
        Met à jour la quantité d'un article du panier.
        """
        try:
            cart_item = self.items.get(id=cart_item_id)
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()
                
            self.updated_at = models.DateTimeField.auto_now
            self.save()
            
            return True
        except CartItem.DoesNotExist:
            return False
    
    def clear(self):
        """
        Vide le panier.
        """
        self.items.all().delete()
        self.updated_at = models.DateTimeField.auto_now
        self.save()
        
    def get_total_price(self):
        """
        Calcule le prix total du panier (sous-total + frais éventuels).
        """
        return self.get_subtotal()
        
    def get_discount(self):
        """
        Calcule le montant total des remises appliquées.
        """
        # À implémenter avec le système de promotions
        return Decimal('0.00')


class CartItem(models.Model):
    """
    Article dans le panier d'achat.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("Panier")
    )
    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_("Produit")
    )
    variation = models.ForeignKey(
        'shop.ProductVariation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items',
        verbose_name=_("Variation")
    )
    quantity = models.PositiveIntegerField(_("Quantité"), default=1)
    added_at = models.DateTimeField(_("Ajouté le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Prix au moment de l'ajout (pour référence si le prix change)
    price_at_addition = models.DecimalField(
        _("Prix au moment de l'ajout"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _("Article du panier")
        verbose_name_plural = _("Articles du panier")
        unique_together = ['cart', 'product', 'variation']
    
    def __str__(self):
        variation_str = f" ({self.variation})" if self.variation else ""
        return f"{self.quantity} x {self.product.name}{variation_str}"
    
    def save(self, *args, **kwargs):
        # Enregistrer le prix actuel au moment de l'ajout
        if not self.pk and not self.price_at_addition:
            if self.variation:
                self.price_at_addition = self.variation.price
            else:
                self.price_at_addition = self.product.current_price
        
        super().save(*args, **kwargs)
    
    def get_unit_price(self):
        """
        Retourne le prix unitaire actuel.
        """
        if self.variation:
            return self.variation.price
        return self.product.current_price
        
    @property
    def unit_price(self):
        """
        Property pour le prix unitaire.
        """
        return self.get_unit_price()
    
    def get_total_price(self):
        """
        Calcule le total pour cette ligne du panier.
        """
        return self.get_unit_price() * self.quantity
        
    @property
    def line_total(self):
        """
        Calcule le total pour cette ligne du panier.
        """
        return self.get_total_price()