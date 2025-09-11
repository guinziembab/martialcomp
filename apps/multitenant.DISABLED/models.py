from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid


class Tenant(models.Model):
    """
    Modèle représentant un tenant (organisation) dans l'architecture multi-tenant.
    Chaque tenant a son propre schéma PostgreSQL et son propre domaine.
    """
    
    CONTINENT_CHOICES = [
        ('africa', _('Afrique')),
        ('asia_se', _('Asie du Sud-Est')),
        ('asia_other', _('Asie (autres)')),
        ('south_america', _('Amérique du Sud')),
        ('central_america', _('Amérique Centrale')),
        ('europe_east', _('Europe de l\'Est')),
        ('europe_west', _('Europe de l\'Ouest')),
        ('north_america', _('Amérique du Nord')),
        ('oceania', _('Océanie')),
        ('middle_east', _('Moyen-Orient')),
    ]
    
    SUBSCRIPTION_PLAN_CHOICES = [
        ('essentials', _('Dojo Essentials')),
        ('masters', _('Master\'s Circle')),
        ('champion', _('Grand Champion Suite')),
        ('trial', _('Essai Gratuit')),
    ]
    
    PAYMENT_PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('stripe_connect', 'Stripe Connect'),
        ('paystack', 'Paystack'),
        ('mercado_pago', 'Mercado Pago'),
        ('alipay', 'Alipay'),
        ('paytm', 'Paytm'),
        ('custom', 'Custom Provider'),
    ]
    
    # Identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Nom de l'organisation"), max_length=255)
    slug = models.SlugField(
        _("Identifiant"),
        max_length=50,
        unique=True,
        validators=[
            MinLengthValidator(3),
            RegexValidator(
                regex='^[a-z0-9-]+$',
                message='Seuls les lettres minuscules, chiffres et tirets sont autorisés.'
            )
        ]
    )
    
    # Configuration technique
    schema_name = models.CharField(
        _("Nom du schéma PostgreSQL"),
        max_length=63,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-z][a-z0-9_]*$',
                message='Le nom du schéma doit commencer par une lettre et contenir uniquement des lettres minuscules, chiffres et underscores.'
            )
        ]
    )
    
    # Domaine
    domain = models.CharField(
        _("Domaine principal"),
        max_length=253,
        unique=True,
        help_text="Ex: club1.martialcomp.com"
    )
    
    # Localisation et facturation
    continent = models.CharField(
        _("Continent"),
        max_length=20,
        choices=CONTINENT_CHOICES,
        help_text="Détermine la grille tarifaire applicable"
    )
    country = models.CharField(_("Pays"), max_length=2)  # Code ISO
    timezone = models.CharField(_("Fuseau horaire"), max_length=50, default='UTC')
    currency = models.CharField(_("Devise"), max_length=3, default='EUR')
    language = models.CharField(_("Langue"), max_length=10, default='fr')
    
    # Abonnement
    subscription_plan = models.CharField(
        _("Plan d'abonnement"),
        max_length=20,
        choices=SUBSCRIPTION_PLAN_CHOICES,
        default='trial'
    )
    subscription_start_date = models.DateTimeField(_("Début d'abonnement"), null=True, blank=True)
    subscription_end_date = models.DateTimeField(_("Fin d'abonnement"), null=True, blank=True)
    is_trial = models.BooleanField(_("En période d'essai"), default=True)
    trial_end_date = models.DateTimeField(_("Fin de l'essai"), null=True, blank=True)
    
    # Configuration paiement
    payment_provider = models.CharField(
        _("Fournisseur de paiement"),
        max_length=20,
        choices=PAYMENT_PROVIDER_CHOICES,
        default='stripe'
    )
    payment_config = models.JSONField(
        _("Configuration paiement"),
        default=dict,
        help_text="Configuration spécifique au fournisseur de paiement (clés API, etc.)"
    )
    stripe_account_id = models.CharField(
        _("ID Compte Stripe Connect"),
        max_length=255,
        blank=True,
        help_text="Pour les organisations utilisant Stripe Connect"
    )
    
    # Limites du plan
    max_users = models.PositiveIntegerField(_("Nombre max d'utilisateurs"), default=100)
    max_disciplines = models.PositiveIntegerField(_("Nombre max de disciplines"), default=2)
    features_config = models.JSONField(
        _("Configuration des fonctionnalités"),
        default=dict,
        help_text="Fonctionnalités activées/désactivées selon le plan"
    )
    
    # Statut et métadonnées
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)
    activated_at = models.DateTimeField(_("Date d'activation"), null=True, blank=True)
    deactivated_at = models.DateTimeField(_("Date de désactivation"), null=True, blank=True)
    
    # Relations
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_tenants',
        verbose_name=_("Propriétaire")
    )
    
    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Tenant")
        verbose_name_plural = _("Tenants")
        ordering = ['name']
        indexes = [
            models.Index(fields=['domain']),
            models.Index(fields=['schema_name']),
            models.Index(fields=['is_active', 'subscription_end_date']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.domain})"
    
    @property
    def is_subscription_active(self):
        """Vérifie si l'abonnement est actif"""
        from django.utils import timezone
        now = timezone.now()
        
        if self.is_trial and self.trial_end_date:
            return now < self.trial_end_date
        
        if self.subscription_end_date:
            return now < self.subscription_end_date
        
        return False
    
    def get_price_for_plan(self, plan=None):
        """Retourne le prix pour un plan donné selon le continent"""
        if plan is None:
            plan = self.subscription_plan
        
        PRICING_MATRIX = {
            'africa': {'essentials': 2.99, 'masters': 5.99, 'champion': 9.99},
            'asia_se': {'essentials': 4.99, 'masters': 9.99, 'champion': 14.99},
            'asia_other': {'essentials': 6.99, 'masters': 12.99, 'champion': 19.99},
            'south_america': {'essentials': 5.99, 'masters': 11.99, 'champion': 17.99},
            'central_america': {'essentials': 4.99, 'masters': 9.99, 'champion': 14.99},
            'europe_east': {'essentials': 6.99, 'masters': 12.99, 'champion': 19.99},
            'europe_west': {'essentials': 9.99, 'masters': 19.99, 'champion': 29.99},
            'north_america': {'essentials': 9.99, 'masters': 19.99, 'champion': 29.99},
            'oceania': {'essentials': 9.99, 'masters': 19.99, 'champion': 29.99},
            'middle_east': {'essentials': 7.99, 'masters': 15.99, 'champion': 23.99},
        }
        
        return PRICING_MATRIX.get(self.continent, {}).get(plan, 0)
    
    def get_available_features(self):
        """Retourne les fonctionnalités disponibles selon le plan"""
        FEATURES_MATRIX = {
            'essentials': {
                'max_members': 100,
                'max_disciplines': 2,
                'competitions': False,
                'advanced_reporting': False,
                'api_access': False,
                'mobile_app': False,
            },
            'masters': {
                'max_members': 300,
                'max_disciplines': 5,
                'competitions': True,
                'advanced_reporting': True,
                'api_access': False,
                'mobile_app': False,
            },
            'champion': {
                'max_members': None,  # Illimité
                'max_disciplines': None,  # Illimité
                'competitions': True,
                'advanced_reporting': True,
                'api_access': True,
                'mobile_app': True,
            },
        }
        
        return FEATURES_MATRIX.get(self.subscription_plan, {})


class Domain(models.Model):
    """
    Domaines supplémentaires pour un tenant.
    Permet Ã  une organisation d'avoir plusieurs domaines pointant vers le mÃªme tenant.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='domains'
    )
    domain = models.CharField(_("Domaine"), max_length=253, unique=True)
    is_primary = models.BooleanField(_("Domaine principal"), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Domaine")
        verbose_name_plural = _("Domaines")
        ordering = ['-is_primary', 'domain']
    
    def __str__(self):
        return self.domain


class TenantFeature(models.Model):
    """
    Gestion des fonctionnalités activées/désactivées par tenant.
    Permet une personnalisation fine au-delÃ  des plans standards.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='custom_features'
    )
    feature_code = models.CharField(
        _("Code de la fonctionnalité"),
        max_length=50,
        help_text="Ex: advanced_reporting, api_access, mobile_app"
    )
    is_enabled = models.BooleanField(_("Activé"), default=True)
    enabled_until = models.DateTimeField(
        _("Activé jusqu'Ã "),
        null=True,
        blank=True,
        help_text="Pour les fonctionnalités temporaires"
    )
    metadata = models.JSONField(
        _("Métadonnées"),
        default=dict,
        help_text="Configuration spécifique Ã  la fonctionnalité"
    )
    
    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Fonctionnalité tenant")
        verbose_name_plural = _("Fonctionnalités tenant")
        unique_together = ['tenant', 'feature_code']
        ordering = ['feature_code']
    
    def __str__(self):
        return f"{self.tenant.name} - {self.feature_code}"


# Modèles pour le système de tarification
class SubscriptionTier(models.Model):
    """
    Représente un niveau d'abonnement avec ses caractéristiques et son prix.
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"))
    price_monthly = models.DecimalField(_("Prix mensuel"), max_digits=10, decimal_places=2)
    price_annually = models.DecimalField(_("Prix annuel"), max_digits=10, decimal_places=2)
    max_users = models.PositiveIntegerField(_("Nombre max d'utilisateurs"))
    max_competitions = models.PositiveIntegerField(_("Nombre max de compétitions"))
    max_storage_gb = models.PositiveIntegerField(_("Stockage max (GB)"))
    features = models.JSONField(_("Fonctionnalités"), default=dict)
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)

    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Niveau d'abonnement")
        verbose_name_plural = _("Niveaux d'abonnement")
        ordering = ['price_monthly']

    def __str__(self):
        return self.name


class TenantSubscription(models.Model):
    """
    Représente l'abonnement d'un tenant Ã  un niveau spécifique.
    """
    BILLING_CYCLE_CHOICES = [
        ('monthly', _('Mensuel')),
        ('annually', _('Annuel')),
    ]
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('past_due', _('En retard de paiement')),
        ('canceled', _('Annulé')),
        ('trialing', _('En période d\'essai')),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='subscriptions')
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT, related_name='tenant_subscriptions')
    billing_cycle = models.CharField(_("Cycle de facturation"), max_length=10, choices=BILLING_CYCLE_CHOICES)
    status = models.CharField(_("Statut"), max_length=10, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField(_("Date de début"))
    end_date = models.DateTimeField(_("Date de fin"))
    auto_renew = models.BooleanField(_("Renouvellement automatique"), default=True)
    payment_provider_subscription_id = models.CharField(_("ID d'abonnement fournisseur"), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)

    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Abonnement tenant")
        verbose_name_plural = _("Abonnements tenant")
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.tenant.name} - {self.tier.name} ({self.get_billing_cycle_display()})"

    @property
    def is_active(self):
        """Vérifie si l'abonnement est actif"""
        now = timezone.now()
        return self.status == 'active' and now < self.end_date


class PayPerUseFeature(models.Model):
    """
    Fonctionnalités disponibles en paiement Ã  l'usage.
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"))
    price_per_unit = models.DecimalField(_("Prix par unité"), max_digits=10, decimal_places=2)
    unit_label = models.CharField(_("Libellé de l'unité"), max_length=50)  # ex: "par participant", "par Go"
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)

    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Fonctionnalité Ã  l'usage")
        verbose_name_plural = _("Fonctionnalités Ã  l'usage")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.price_per_unit} â‚¬ {self.unit_label})"


class FeatureUsage(models.Model):
    """
    Enregistre l'utilisation des fonctionnalités Ã  l'usage.
    """
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='feature_usages')
    feature = models.ForeignKey(PayPerUseFeature, on_delete=models.PROTECT, related_name='usages')
    quantity = models.PositiveIntegerField(_("Quantité"))
    usage_date = models.DateTimeField(_("Date d'utilisation"))
    billed = models.BooleanField(_("Facturé"), default=False)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)

    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Utilisation de fonctionnalité")
        verbose_name_plural = _("Utilisations de fonctionnalités")
        ordering = ['-usage_date']

    def __str__(self):
        return f"{self.tenant.name} - {self.feature.name} ({self.quantity})"


class PromotionCode(models.Model):
    """
    Codes promotionnels pour des réductions sur les abonnements.
    """
    TYPE_CHOICES = [
        ('percentage', _('Pourcentage de réduction')),
        ('fixed', _('Montant fixe de réduction')),
        ('free_months', _('Mois gratuits')),
    ]
    
    code = models.CharField(_("Code"), max_length=50, unique=True)
    description = models.TextField(_("Description"))
    discount_type = models.CharField(_("Type de réduction"), max_length=20, choices=TYPE_CHOICES)
    discount_value = models.DecimalField(_("Valeur de la réduction"), max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField(_("Valide Ã  partir de"))
    valid_until = models.DateTimeField(_("Valide jusqu'Ã "))
    max_uses = models.PositiveIntegerField(_("Nombre max d'utilisations"), null=True, blank=True)
    current_uses = models.PositiveIntegerField(_("Utilisations actuelles"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Date de modification"), auto_now=True)

    class Meta:
        app_label = 'multitenant'
        verbose_name = _("Code promotionnel")
        verbose_name_plural = _("Codes promotionnels")
        ordering = ['-valid_until']

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    @property
    def is_valid(self):
        """Vérifie si le code est valide"""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True

