from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from apps.competitions.models import Organization
from . import PricingRegion, VolumeDiscount
from decimal import Decimal
from django.utils import timezone


def get_default_currency():
    """Retourne le code de la devise par défaut (EUR)"""
    return 'EUR'

class Subscription(models.Model):
    """Souscription avec nouveau modèle tarifaire par membre"""

    STATUS_CHOICES = [
        ('ACTIVE', _('Active')),
        ('EXPIRED', _('Expirée')),
        ('CANCELLED', _('Annulée')),
        ('PENDING', _('En attente')),
        ('TRIAL', _('Essai')),
    ]

    PAYMENT_METHODS = [
        ('CARD', _('Carte bancaire')),
        ('WIRE_TRANSFER', _('Virement')),
        ('SEPA', _('Prélèvement SEPA')),
        ('WALLET', _('Portefeuille')),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    region = models.ForeignKey(
        PricingRegion, on_delete=models.PROTECT,
        null=True, blank=True
    )
    
    # Informations de facturation
    member_count = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Nombre de membres facturés'
    )
    base_price_per_member = models.DecimalField(max_digits=6, decimal_places=2)
    volume_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_price_per_member = models.DecimalField(max_digits=6, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Période de facturation
    start_date = models.DateField()
    end_date = models.DateField()
    billing_cycle = models.CharField(max_length=20, default='ANNUAL', choices=[
        ('ANNUAL', _('Annuel')),
        ('MONTHLY', _('Mensuel')),
    ])
    
    # Statut et paiement
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    is_first_payment = models.BooleanField(default=True, help_text='Premier paiement pour calculer les commissions')
    
    # Informations de paiement échelonné
    installment_count = models.IntegerField(default=1, help_text='Nombre de versements')
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Multi-devise (Phase 2)
    currency = models.ForeignKey(
        'finances.Currency',
        on_delete=models.PROTECT,
        verbose_name=_("Devise"),
        default=get_default_currency,
        help_text=_("Devise utilisée pour cette souscription")
    )
    total_amount_eur = models.DecimalField(
        _("Montant total (EUR)"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Montant converti en EUR pour consolidation comptable")
    )
    exchange_rate_used = models.DecimalField(
        _("Taux de change utilisé"),
        max_digits=18,
        decimal_places=8,
        null=True,
        blank=True,
        help_text=_("Taux de change au moment de la transaction")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Souscription'
        verbose_name_plural = 'Souscriptions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.organization.name} - {self.member_count} membres - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        """Calcule automatiquement les prix lors de la sauvegarde"""
        if not self.pk or self._state.adding:
            self.calculate_pricing()
        super().save(*args, **kwargs)
    
    def calculate_pricing(self):
        """Calcule la tarification selon la région et le volume"""
        # Prix de base selon la région
        self.base_price_per_member = self.region.base_price_per_member

        # Réduction volume
        volume_discount = VolumeDiscount.get_discount_for_members(self.member_count)
        self.volume_discount_percentage = volume_discount

        # Prix final par membre
        discount_amount = self.base_price_per_member * (volume_discount / 100)
        self.final_price_per_member = self.base_price_per_member - discount_amount

        # Montant total
        self.total_amount = self.final_price_per_member * self.member_count

        # Montant par versement si échelonné
        if self.installment_count > 1:
            self.installment_amount = self.total_amount / self.installment_count

        # Calcul du montant en EUR si devise différente (Phase 2 Multi-devise)
        self._calculate_eur_amount()

    def _calculate_eur_amount(self):
        """
        Calcule le montant total en EUR pour consolidation comptable.
        Utilise le taux de change actuel si devise différente de EUR.
        """
        try:
            currency_code = self.currency_id if self.currency_id else 'EUR'

            if currency_code == 'EUR':
                # Pas de conversion nécessaire
                self.total_amount_eur = self.total_amount
                self.exchange_rate_used = Decimal('1.0')
            else:
                # Conversion vers EUR
                from .currency import ExchangeRate
                try:
                    rate = ExchangeRate.get_current_rate(currency_code, 'EUR')
                    self.exchange_rate_used = rate
                    self.total_amount_eur = self.total_amount * rate
                except ValueError:
                    # Pas de taux disponible, garder les valeurs null
                    self.total_amount_eur = None
                    self.exchange_rate_used = None
        except Exception:
            # En cas d'erreur (ex: Currency non encore migrée), ignorer
            pass

    def get_discount_savings(self):
        """Retourne les économies réalisées grâce à la réduction volume"""
        original_total = self.base_price_per_member * self.member_count
        return original_total - self.total_amount

    def get_formatted_total(self, include_symbol=True):
        """
        Retourne le montant total formaté selon la devise.

        Args:
            include_symbol: Inclure le symbole de la devise

        Returns:
            str: Montant formaté (ex: "1 234,56 €" ou "655 FCFA")
        """
        try:
            if self.currency:
                return self.currency.format_amount(self.total_amount, include_symbol)
        except Exception:
            pass
        # Fallback: formatage simple
        return f"{self.total_amount:.2f} EUR"

    def get_formatted_total_eur(self):
        """Retourne le montant en EUR formaté pour les rapports consolidés"""
        if self.total_amount_eur:
            return f"{self.total_amount_eur:.2f} €"
        return "N/A"

    def is_referral_eligible(self):
        """Vérifie si cette souscription est éligible pour une commission de parrainage"""
        return self.is_first_payment and self.status == 'ACTIVE'
    
    def create_referral_commission(self, referring_organization, percentage=7.00):
        """Crée une commission de parrainage"""
        from . import ReferralCommission
        
        commission_amount = self.total_amount * (percentage / 100)
        
        return ReferralCommission.objects.create(
            referring_organization=referring_organization,
            referred_organization=self.organization,
            initial_subscription=self,
            amount=commission_amount,
            percentage=percentage
        )
    
    @classmethod
    def create_subscription(cls, organization, region, member_count, start_date, 
                          payment_method='CARD', installment_count=1):
        """Crée une nouvelle souscription avec calcul automatique"""
        from datetime import date, timedelta
        
        # Calculer la date de fin (1 an par défaut)
        end_date = start_date + timedelta(days=365)
        
        subscription = cls(
            organization=organization,
            region=region,
            member_count=member_count,
            start_date=start_date,
            end_date=end_date,
            payment_method=payment_method,
            installment_count=installment_count
        )
        
        subscription.save()
        return subscription

class SubscriptionPayment(models.Model):
    """Paiements pour les souscriptions"""

    STATUS_CHOICES = [
        ('PENDING', _('En attente')),
        ('COMPLETED', _('Complété')),
        ('FAILED', _('Échoué')),
        ('REFUNDED', _('Remboursé')),
    ]
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    installment_number = models.IntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Informations de paiement
    payment_reference = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = 'Paiement souscription'
        verbose_name_plural = 'Paiements souscription'
        ordering = ['subscription', 'installment_number']
    
    def __str__(self):
        return f"Paiement {self.installment_number}/{self.subscription.installment_count} - {self.amount}â‚¬"
    
    def process_payment(self):
        """Traite le paiement et déclenche les commissions si nécessaire"""
        if self.status == 'PENDING':
            self.status = 'COMPLETED'
            self.payment_date = timezone.now()
            self.save()
            
            # Si c'est le premier paiement, vérifier les commissions de parrainage
            if self.subscription.is_referral_eligible():
                self.process_referral_commissions()
            
            return True
        return False
    
    def process_referral_commissions(self):
        """Traite les commissions de parrainage pour ce paiement"""
        from . import ReferralCommission
        
        # Chercher les commissions en attente pour cette organisation
        pending_commissions = ReferralCommission.objects.filter(
            referred_organization=self.subscription.organization,
            status='PENDING'
        )
        
        for commission in pending_commissions:
            commission.process_commission()


class SubscriptionTier(models.Model):
    """
    Modèle pour définir les différents niveaux d'abonnement et leurs fonctionnalités.
    """
    TIER_CHOICES = [
        ('free', _('Gratuit')),
        ('premium', _('Premium')),
        # Anciens tiers (désactivés, conservés pour compatibilité migration)
        ('dojo_essentials', _('Dojo Essentials')),
        ('masters_circle', _('Master\'s Circle')),
        ('grand_champion', _('Grand Champion Suite')),
    ]
    
    name = models.CharField(
        _("Nom du package"), 
        max_length=50, 
        choices=TIER_CHOICES, 
        unique=True
    )
    display_name = models.CharField(_("Nom d'affichage"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    # Limites du package
    max_members = models.IntegerField(_("Nombre maximum de membres"), default=100)
    max_disciplines = models.IntegerField(_("Nombre maximum de disciplines"), default=2)
    max_clubs = models.IntegerField(_("Nombre maximum de clubs"), default=1)
    max_storage_mb = models.IntegerField(_("Stockage maximum (MB)"), default=100)
    
    # Prix
    monthly_price = models.DecimalField(
        _("Prix mensuel"), 
        max_digits=6, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    yearly_price = models.DecimalField(
        _("Prix annuel"), 
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    
    # Métadonnées
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Modifié le"), auto_now=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = _("Niveau d'abonnement")
        verbose_name_plural = _("Niveaux d'abonnement")
        ordering = ['monthly_price']
    
    def __str__(self):
        return self.display_name


class FeatureFlag(models.Model):
    """
    Modèle pour contrÃ´ler l'accès aux fonctionnalités par niveau d'abonnement.
    """
    COMPLEXITY_CHOICES = [
        ('basic', _('Basique')),
        ('intermediate', _('Intermédiaire')),
        ('advanced', _('Avancé')),
        ('critical', _('Critique')),
    ]
    
    MODULE_CHOICES = [
        ('core', _('Core')),
        ('practitioner_management', _('Gestion Pratiquants')),
        ('organization_management', _('Gestion Organisations')),
        ('disciplines_training', _('Disciplines & Formation')),
        ('competitions', _('Compétitions')),
        ('scoring_system', _('Système de Notation')),
        ('combat_system', _('Système de Combat')),
        ('financial', _('Financier')),
        ('ecommerce', _('E-commerce')),
        ('communications', _('Communications')),
        ('documents_ged', _('Documents & GED')),
        ('family_management', _('Gestion Familiale')),
        ('events_planning', _('Ã‰vénements & Planning')),
        ('qr_mobile', _('QR Code & Mobile')),
        ('analytics_reporting', _('Analytics & Reporting')),
    ]
    
    name = models.CharField(_("Nom de la fonctionnalité"), max_length=100, unique=True)
    display_name = models.CharField(_("Nom d'affichage"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    
    module = models.CharField(
        _("Module"), 
        max_length=50, 
        choices=MODULE_CHOICES
    )
    complexity = models.CharField(
        _("Complexité"), 
        max_length=20, 
        choices=COMPLEXITY_CHOICES,
        default='basic'
    )
    
    # Relations avec les tiers d'abonnement
    subscription_tiers = models.ManyToManyField(
        SubscriptionTier,
        verbose_name=_("Niveaux d'abonnement"),
        help_text=_("Niveaux d'abonnement qui ont accès Ã  cette fonctionnalité")
    )
    
    # Configuration technique
    view_names = models.TextField(
        _("Noms des vues"),
        help_text=_("Noms des vues séparés par des virgules"),
        blank=True
    )
    url_patterns = models.TextField(
        _("Patterns d'URLs"),
        help_text=_("Patterns d'URLs séparés par des virgules"),
        blank=True
    )
    model_names = models.TextField(
        _("Noms des modèles"),
        help_text=_("Noms des modèles séparés par des virgules"),
        blank=True
    )
    
    # Ã‰tat
    is_active = models.BooleanField(_("Actif"), default=True)
    is_always_enabled = models.BooleanField(
        _("Toujours activé"), 
        default=False,
        help_text=_("Fonctionnalité critique qui ne peut pas Ãªtre désactivée")
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Modifié le"), auto_now=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = _("Feature Flag")
        verbose_name_plural = _("Feature Flags")
        ordering = ['module', 'name']
    
    def __str__(self):
        return f"{self.display_name} ({self.module})"
    
    def get_view_names_list(self):
        """Retourne la liste des noms de vues."""
        if self.view_names:
            return [name.strip() for name in self.view_names.split(',')]
        return []
    
    def get_url_patterns_list(self):
        """Retourne la liste des patterns d'URLs."""
        if self.url_patterns:
            return [pattern.strip() for pattern in self.url_patterns.split(',')]
        return []
    
    def get_model_names_list(self):
        """Retourne la liste des noms de modèles."""
        if self.model_names:
            return [name.strip() for name in self.model_names.split(',')]
        return []


class OrganizationSubscription(models.Model):
    """
    Modèle pour gérer les abonnements des organisations avec contrÃ´le de fonctionnalités.
    """
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('trial', _('Période d\'essai')),
        ('expired', _('Expiré')),
        ('suspended', _('Suspendu')),
        ('cancelled', _('Annulé')),
    ]
    
    organization = models.OneToOneField(
        'competitions.Club',  # Référence vers l'organisation/club
        on_delete=models.CASCADE,
        related_name='feature_subscription'
    )
    subscription_tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.PROTECT,
        verbose_name=_("Niveau d'abonnement")
    )
    
    # Dates
    start_date = models.DateTimeField(_("Date de début"))
    end_date = models.DateTimeField(_("Date de fin"))
    trial_end_date = models.DateTimeField(_("Fin de la période d'essai"), null=True, blank=True)
    
    # Ã‰tat
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default='trial'
    )
    
    # Compteurs d'utilisation
    current_members_count = models.IntegerField(_("Nombre de membres actuels"), default=0)
    current_disciplines_count = models.IntegerField(_("Nombre de disciplines actuelles"), default=0)
    current_clubs_count = models.IntegerField(_("Nombre de clubs actuels"), default=1)
    current_storage_mb = models.IntegerField(_("Stockage utilisé (MB)"), default=0)
    
    # Stripe
    stripe_customer_id = models.CharField(
        _("Stripe Customer ID"), max_length=255,
        null=True, blank=True, db_index=True,
        help_text="cus_...",
    )
    stripe_subscription_id = models.CharField(
        _("Stripe Subscription ID"), max_length=255,
        null=True, blank=True, db_index=True,
        help_text="sub_...",
    )
    stripe_price_id = models.CharField(
        _("Stripe Price ID"), max_length=255,
        null=True, blank=True,
        help_text="price_...",
    )

    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Modifié le"), auto_now=True)

    class Meta:
        app_label = 'finances'
        verbose_name = _("Abonnement organisation")
        verbose_name_plural = _("Abonnements organisations")
    
    def __str__(self):
        return f"{self.organization.name} - {self.subscription_tier.display_name}"
    
    @property
    def is_active(self):
        """Vérifie si l'abonnement est actif."""
        from django.utils import timezone
        return (
            self.status in ['active', 'trial'] and 
            self.end_date > timezone.now()
        )
    
    @property
    def is_trial(self):
        """Vérifie si l'organisation est en période d'essai."""
        from django.utils import timezone
        return (
            self.status == 'trial' and
            self.trial_end_date and
            self.trial_end_date > timezone.now()
        )
    
    def has_feature(self, feature_name):
        """Toutes les fonctionnalites sont disponibles pour tous les plans."""
        return self.is_active

    def check_limits(self):
        """Verifie la limite de membres (seule limite active)."""
        limits_exceeded = []
        if self.current_members_count > self.subscription_tier.max_members:
            limits_exceeded.append('members')
        return limits_exceeded

    def can_add_member(self):
        """Verifie si on peut ajouter un membre (blocage dur a 10 en Free)."""
        return (
            self.current_members_count
            < self.subscription_tier.max_members
        )

    @property
    def effective_pricing(self):
        """Retourne le pricing effectif selon le pays."""
        from apps.finances.pricing_tiers import (
            get_market_tier_for_country, PRICING,
            FREE_TIER_MAX_MEMBERS
        )
        from decimal import Decimal
        tier_name = self.subscription_tier.name
        if tier_name == 'free':
            return {
                'tier': 'free',
                'max_members': FREE_TIER_MAX_MEMBERS,
                'yearly_per_member': Decimal('0.00'),
                'monthly_per_member': Decimal('0.00'),
            }
        org = self.organization
        country = ''
        if hasattr(org, 'organization') and org.organization:
            country = getattr(org.organization, 'country', '')
        elif hasattr(org, 'country'):
            country = org.country or ''
        market_tier = get_market_tier_for_country(country)
        pricing = PRICING[market_tier]
        return {
            'tier': 'premium',
            'market_tier': market_tier,
            'max_members': self.subscription_tier.max_members,
            'yearly_per_member': pricing['yearly_per_member'],
            'monthly_per_member': pricing['monthly_per_member'],
        }

    def update_usage_counters(self):
        """Met Ã  jour les compteurs d'utilisation."""
        # Compter les membres actifs
        from apps.competitions.models import Practitioner
        self.current_members_count = Practitioner.objects.filter(
            club=self.organization,
            is_active=True
        ).count()
        
        # Compter les disciplines
        self.current_disciplines_count = self.organization.disciplines.count()
        
        # Compter le stockage utilisé (approximatif)
        # TODO: Implémenter le calcul exact du stockage
        
        self.save()


class FeatureUsageLog(models.Model):
    """
    Modèle pour tracker l'utilisation des fonctionnalités.
    """
    organization = models.ForeignKey(
        'competitions.Club',
        on_delete=models.CASCADE,
        related_name='feature_usage_logs'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feature_flag = models.ForeignKey(FeatureFlag, on_delete=models.CASCADE)
    
    # Informations sur l'utilisation
    view_name = models.CharField(_("Nom de la vue"), max_length=100)
    url_path = models.CharField(_("Chemin de l'URL"), max_length=255)
    
    # Métadonnées
    timestamp = models.DateTimeField(_("Horodatage"), auto_now_add=True)
    session_key = models.CharField(_("Clé de session"), max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField(_("Adresse IP"), null=True, blank=True)
    
    class Meta:
        app_label = 'finances'
        verbose_name = _("Log d'utilisation de fonctionnalité")
        verbose_name_plural = _("Logs d'utilisation de fonctionnalités")
        indexes = [
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['feature_flag', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.organization.name} - {self.feature_flag.name} - {self.timestamp}" 



