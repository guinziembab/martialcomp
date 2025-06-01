from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class Brand(models.Model):
    """
    Marques de produits d'arts martiaux.
    """
    name = models.CharField(_("Nom"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True)
    description = models.TextField(_("Description"), blank=True)
    website = models.URLField(_("Site web"), blank=True)
    logo = models.ImageField(_("Logo"), upload_to='shop/brands/', blank=True, null=True)
    is_premium = models.BooleanField(_("Marque premium"), default=False)
    is_featured = models.BooleanField(_("Mise en avant"), default=False)
    country_origin = models.CharField(_("Pays d'origine"), max_length=100, blank=True)
    year_established = models.PositiveIntegerField(_("Année de création"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Marque")
        verbose_name_plural = _("Marques")
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Générer le slug automatiquement si non fourni
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Supplier(models.Model):
    """
    Fournisseurs d'équipements.
    """
    name = models.CharField(_("Nom"), max_length=100)
    code = models.CharField(_("Code fournisseur"), max_length=20, unique=True)
    contact_name = models.CharField(_("Nom du contact"), max_length=100, blank=True)
    contact_email = models.EmailField(_("Email du contact"), blank=True)
    contact_phone = models.CharField(_("Téléphone du contact"), max_length=20, blank=True)
    
    address = models.CharField(_("Adresse"), max_length=255, blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    zip_code = models.CharField(_("Code postal"), max_length=20, blank=True)
    country = models.CharField(_("Pays"), max_length=100, blank=True)
    
    website = models.URLField(_("Site web"), blank=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    payment_terms = models.CharField(_("Conditions de paiement"), max_length=100, blank=True)
    delivery_terms = models.CharField(_("Conditions de livraison"), max_length=100, blank=True)
    minimum_order = models.DecimalField(
        _("Commande minimum"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    lead_time_days = models.PositiveIntegerField(
        _("Délai de livraison (jours)"),
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Fournisseur")
        verbose_name_plural = _("Fournisseurs")
        ordering = ['name']
    
    def __str__(self):
        return self.name