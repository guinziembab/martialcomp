from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.text import slugify

User = get_user_model()

class OrganizationType(models.TextChoices):
    GLOBAL_BODY = 'global_body', _('Organisation internationale multidisciplinaire')
    INTERNATIONAL_FEDERATION = 'international_federation', _('Fédération internationale')
    NATIONAL_FEDERATION = 'national_federation', _('Fédération nationale')
    REGIONAL_BODY = 'regional_body', _('Organisation régionale')
    CLUB = 'club', _('Club/Association')
    ACADEMY = 'academy', _('Académie')
    OTHER = 'other', _('Autre')

class AffiliationType(models.TextChoices):
    MEMBER = 'member', _('Membre')
    PARTNER = 'partner', _('Partenaire')
    TECHNICAL = 'technical', _('Affiliation technique')
    ADMINISTRATIVE = 'administrative', _('Affiliation administrative')


class AffiliationStatus(models.TextChoices):
    """Statut d'approbation pour une affiliation"""
    PENDING = 'pending', _('En attente')
    APPROVED = 'approved', _('Approuve')
    REJECTED = 'rejected', _('Refuse')


class AffiliationInitiator(models.TextChoices):
    """Qui a initie la demande d'affiliation"""
    PARENT = 'parent', _('Federation (invitation)')
    CHILD = 'child', _('Club (demande)')

class Organization(models.Model):
    """
    Modèle générique pour toutes les organisations (fédérations, clubs, etc.)
    """
    name = models.CharField(_("Nom"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, unique=True, blank=True)
    short_name = models.CharField(_("Nom court"), max_length=50, blank=True)
    organization_type = models.CharField(
        _("Type d'organisation"),
        max_length=30,
        choices=OrganizationType.choices
    )
    disciplines = models.ManyToManyField(
        'competitions.Discipline', 
        related_name='organization_list',  # Changé pour éviter les conflits
        blank=True,
        verbose_name=_("Disciplines")
    )
    description = models.TextField(_("Description"), blank=True)
    
    # Informations de contact
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    website = models.URLField(_("Site web"), blank=True)
    
    # Localisation
    country = models.CharField(_("Pays"), max_length=100, blank=True)
    pricing_tier = models.CharField(
        _("Tier tarifaire"),
        max_length=10,
        choices=[('mature', _('Marché mature')), ('emergent', _('Marché émergent'))],
        default='mature',
        blank=True,
        help_text=_("Déterminé automatiquement à partir du pays")
    )
    address = models.TextField(_("Adresse"), blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=20, blank=True)
    
    # Logo et médias
    logo = models.ImageField(_("Logo"), upload_to='organizations/logos/', null=True, blank=True)
    banner = models.ImageField(
        _("Bannière"),
        upload_to='organizations/banners/',
        null=True,
        blank=True,
        help_text=_("Dimensions recommandées: 1920x600px. Max 5 Mo.")
    )

    # Couleurs du thème
    primary_color = models.CharField(
        _("Couleur principale"),
        max_length=7,
        default='#8b5cf6',
        help_text=_("Code couleur hexadécimal (ex: #8b5cf6)")
    )
    secondary_color = models.CharField(
        _("Couleur secondaire"),
        max_length=7,
        default='#a78bfa',
        help_text=_("Code couleur hexadécimal (ex: #a78bfa)")
    )
    accent_color = models.CharField(
        _("Couleur d'accent"),
        max_length=7,
        default='#d4af37',
        help_text=_("Code couleur hexadécimal (ex: #d4af37)")
    )

    # Relations avec anciens modèles (pour la migration)
    old_federation_id = models.PositiveIntegerField(_("ID de l'ancienne fédération"), null=True, blank=True)
    old_club_id = models.PositiveIntegerField(_("ID de l'ancien club"), null=True, blank=True)
    
    # Relations
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_organizations',
        verbose_name=_("Créé par")
    )
    
    # Métadonnées
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    # Champ JSON pour stocker les métadonnées du site (contenu personnalisé, etc.)
    metadata = models.JSONField(
        _("Métadonnées du site"),
        default=dict,
        blank=True,
        help_text=_("Stocke le contenu personnalisé du site public")
    )

    class Meta:
        app_label = 'organizations'
        verbose_name = _("Organisation")
        verbose_name_plural = _("Organisations")
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization_type']),
            models.Index(fields=['country', 'city']),
            models.Index(fields=['old_federation_id']),
            models.Index(fields=['old_club_id']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_organization_type_display()})"
    
    def save(self, *args, **kwargs):
        # Générer un slug unique si non défini ou vide
        if not self.slug:
            # Utiliser le nom ou une chaÃ®ne par défaut si le nom est vide
            base_slug = slugify(self.name) if self.name else 'organization'
            
            # S'assurer que le slug n'est jamais vide
            if not base_slug:
                base_slug = 'organization'
            
            # Vérifier l'unicité du slug
            counter = 1
            self.slug = base_slug
            
            # Exclure l'enregistrement actuel lors de la vérification d'unicité
            slug_qs = Organization.objects.filter(slug=self.slug)
            if self.pk:
                slug_qs = slug_qs.exclude(pk=self.pk)
                
            while slug_qs.exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1
                slug_qs = Organization.objects.filter(slug=self.slug)
                if self.pk:
                    slug_qs = slug_qs.exclude(pk=self.pk)
                
        # Si short_name n'est pas défini, utiliser les premiers caractères de name
        if not self.short_name and self.name:
            self.short_name = self.name[:50]

        # Auto-déterminer le pricing_tier à partir du pays
        if self.country:
            from apps.finances.pricing_tiers import get_market_tier_for_country
            self.pricing_tier = get_market_tier_for_country(self.country)

        super().save(*args, **kwargs)
    
    def get_affiliated_organizations(self, include_inactive=False):
        """Retourne les organisations affiliées Ã  cette organisation."""
        child_affiliations = self.child_affiliations.all()
        if not include_inactive:
            child_affiliations = child_affiliations.filter(is_active=True)
        
        return Organization.objects.filter(
            parent_affiliations__in=child_affiliations
        ).distinct()
    
    def get_parent_organizations(self, include_inactive=False):
        """Retourne les organisations parentes auxquelles cette organisation est affiliée."""
        parent_affiliations = self.parent_affiliations.all()
        if not include_inactive:
            parent_affiliations = parent_affiliations.filter(is_active=True)
        
        return Organization.objects.filter(
            child_affiliations__in=parent_affiliations
        ).distinct()
    
    def get_active_members(self):
        """Retourne les membres actifs de l'organisation."""
        return self.members.filter(is_active=True).select_related('user')
    
    def is_user_member(self, user):
        """Vérifie si un utilisateur est membre de l'organisation."""
        if not user or not user.is_authenticated:
            return False
        return self.members.filter(user=user, is_active=True).exists()
    
    def get_user_role(self, user):
        """Retourne le rÃ´le d'un utilisateur dans l'organisation."""
        if not user or not user.is_authenticated:
            return None
        
        try:
            membership = self.members.get(user=user, is_active=True)
            return membership.role
        except OrganizationMember.DoesNotExist:
            return None
    
    def can_user_edit(self, user):
        """Vérifie si un utilisateur peut éditer l'organisation."""
        if not user or not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
            
        try:
            membership = self.members.get(user=user, is_active=True)
            return (membership.can_edit_organization or 
                   membership.role in ['owner', 'admin'])
        except OrganizationMember.DoesNotExist:
            return False
    
    def can_user_manage_members(self, user):
        """Vérifie si un utilisateur peut gérer les membres de l'organisation."""
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
            
        try:
            membership = self.members.get(user=user, is_active=True)
            return (membership.can_manage_members or 
                   membership.role in ['owner', 'admin'])
        except OrganizationMember.DoesNotExist:
            return False
            
    def can_user_manage_competitions(self, user):
        """Vérifie si un utilisateur peut gérer les compétitions de l'organisation."""
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
    
    def get_website_url(self):
        """Retourne l'URL du site public de l'organisation."""
        if self.organization_type == 'national_federation':
            return f"https://fed-{self.slug}.martialcomp.com"
        else:
            return f"https://{self.slug}.martialcomp.com"
    
    def get_admin_site_url(self):
        """Retourne l'URL de gestion du site de l'organisation."""
        if self.organization_type == 'national_federation':
            return f"https://fed-{self.slug}.martialcomp.com/admin/site/"
        else:
            return f"https://{self.slug}.martialcomp.com/admin/site/"
    
    def get_qr_site_url(self):
        """Retourne l'URL des codes QR du site de l'organisation."""
        if self.organization_type == 'national_federation':
            return f"https://fed-{self.slug}.martialcomp.com/qr/"
        else:
            return f"https://{self.slug}.martialcomp.com/qr/"
    
    def has_website_template(self):
        """Vérifie si l'organisation a un template de site web."""
        # Pour l'instant, on considère que toutes les organisations actives ont un template
        # Cette méthode peut être étendue pour vérifier l'existence réelle du template
        return self.is_active and self.slug
            
        try:
            membership = self.members.get(user=user, is_active=True)
            return (membership.can_manage_competitions or 
                   membership.role in ['owner', 'admin'])
        except OrganizationMember.DoesNotExist:
            return False

class SportSeason(models.Model):
    """
    Représente une saison sportive (ex: 2024-2025) pour une organisation.
    Les fédérations définissent leurs saisons, les clubs s'y conforment via les affiliations.
    """
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='seasons',
        verbose_name=_("Organisation")
    )
    name = models.CharField(
        _("Nom de la saison"),
        max_length=20,
        help_text=_("Ex: 2024-2025")
    )
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"))
    renewal_reminder_days = models.PositiveIntegerField(
        _("Jours avant rappel"),
        default=30,
        help_text=_("Nombre de jours avant la fin de saison pour envoyer les rappels de renouvellement")
    )
    is_current = models.BooleanField(
        _("Saison courante"),
        default=False,
        help_text=_("Marquer comme saison active")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Saison sportive")
        verbose_name_plural = _("Saisons sportives")
        unique_together = ['organization', 'name']
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['organization', 'is_current']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError(_("La date de début doit être antérieure à la date de fin."))

    def save(self, *args, **kwargs):
        # Si cette saison est marquée comme courante, désactiver les autres
        if self.is_current:
            SportSeason.objects.filter(
                organization=self.organization,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """Vérifie si on est actuellement dans cette saison."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date

    @property
    def days_remaining(self):
        """Nombre de jours restants dans la saison."""
        from django.utils import timezone
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    @property
    def is_renewal_period(self):
        """Vérifie si on est dans la période de renouvellement."""
        return 0 < self.days_remaining <= self.renewal_reminder_days


class AffiliationFeeConfiguration(models.Model):
    """
    Configuration des tarifs d'affiliation par type et par saison.
    Permet de définir des prix différents selon le type d'affiliation.
    """
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='affiliation_fees',
        verbose_name=_("Organisation")
    )
    season = models.ForeignKey(
        SportSeason,
        on_delete=models.CASCADE,
        related_name='fee_configurations',
        verbose_name=_("Saison")
    )
    affiliation_type = models.CharField(
        _("Type d'affiliation"),
        max_length=30,
        choices=AffiliationType.choices
    )
    amount = models.DecimalField(
        _("Montant"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Montant HT de l'affiliation")
    )
    tax_rate = models.DecimalField(
        _("Taux de TVA"),
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text=_("Taux de TVA en pourcentage (ex: 20.00)")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description des avantages inclus")
    )
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Configuration tarif affiliation")
        verbose_name_plural = _("Configurations tarifs affiliation")
        unique_together = ['organization', 'season', 'affiliation_type']
        ordering = ['season', 'affiliation_type']

    def __str__(self):
        return f"{self.organization.name} - {self.season.name} - {self.get_affiliation_type_display()}: {self.amount}€"

    @property
    def amount_with_tax(self):
        """Calcule le montant TTC."""
        from decimal import Decimal
        return self.amount * (1 + self.tax_rate / Decimal('100'))


class AffiliationPeriodStatus(models.TextChoices):
    """Statut d'une période d'affiliation"""
    PENDING_PAYMENT = 'pending_payment', _('En attente de paiement')
    ACTIVE = 'active', _('Active')
    EXPIRED = 'expired', _('Expirée')
    CANCELLED = 'cancelled', _('Annulée')


class AffiliationPeriod(models.Model):
    """
    Représente une période d'affiliation pour une saison donnée.
    Permet de garder l'historique complet des affiliations par saison.
    """
    affiliation = models.ForeignKey(
        'Affiliation',
        on_delete=models.CASCADE,
        related_name='periods',
        verbose_name=_("Affiliation")
    )
    season = models.ForeignKey(
        SportSeason,
        on_delete=models.PROTECT,
        related_name='affiliation_periods',
        verbose_name=_("Saison")
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=AffiliationPeriodStatus.choices,
        default=AffiliationPeriodStatus.PENDING_PAYMENT
    )
    invoice = models.ForeignKey(
        'finances.Invoice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='affiliation_periods',
        verbose_name=_("Facture")
    )
    amount = models.DecimalField(
        _("Montant"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Montant de l'affiliation pour cette période")
    )
    paid_amount = models.DecimalField(
        _("Montant payé"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    payment_date = models.DateTimeField(
        _("Date de paiement"),
        null=True,
        blank=True
    )
    renewed_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewals',
        verbose_name=_("Renouvelé depuis")
    )
    notes = models.TextField(_("Notes"), blank=True)
    last_reminder_sent = models.DateTimeField(
        _("Dernier rappel envoyé"),
        null=True,
        blank=True,
        help_text=_("Date du dernier rappel de renouvellement envoyé")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Période d'affiliation")
        verbose_name_plural = _("Périodes d'affiliation")
        unique_together = ['affiliation', 'season']
        ordering = ['-season__start_date']
        indexes = [
            models.Index(fields=['affiliation', 'status']),
            models.Index(fields=['season', 'status']),
        ]

    def __str__(self):
        return f"{self.affiliation} - {self.season.name} ({self.get_status_display()})"

    @property
    def is_paid(self):
        """Vérifie si la période est entièrement payée."""
        return self.paid_amount >= self.amount

    @property
    def remaining_amount(self):
        """Montant restant à payer."""
        return max(self.amount - self.paid_amount, 0)

    @property
    def payment_percentage(self):
        """Pourcentage payé."""
        if self.amount == 0:
            return 100
        return min(int((self.paid_amount / self.amount) * 100), 100)


class AffiliationRenewalRequestStatus(models.TextChoices):
    """Statut d'une demande de renouvellement"""
    PENDING = 'pending', _('En attente')
    APPROVED = 'approved', _('Approuvée')
    REJECTED = 'rejected', _('Refusée')


class AffiliationRenewalRequest(models.Model):
    """
    Demande de renouvellement d'affiliation initiée par le club.
    Le club demande à renouveler son affiliation pour une nouvelle saison.
    """
    affiliation = models.ForeignKey(
        'Affiliation',
        on_delete=models.CASCADE,
        related_name='renewal_requests',
        verbose_name=_("Affiliation")
    )
    from_period = models.ForeignKey(
        AffiliationPeriod,
        on_delete=models.PROTECT,
        related_name='renewal_requests_from',
        verbose_name=_("Période précédente")
    )
    to_season = models.ForeignKey(
        SportSeason,
        on_delete=models.PROTECT,
        related_name='renewal_requests',
        verbose_name=_("Nouvelle saison")
    )
    requested_at = models.DateTimeField(_("Demandé le"), auto_now_add=True)
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='affiliation_renewal_requests',
        verbose_name=_("Demandé par")
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=AffiliationRenewalRequestStatus.choices,
        default=AffiliationRenewalRequestStatus.PENDING
    )
    processed_at = models.DateTimeField(
        _("Traité le"),
        null=True,
        blank=True
    )
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_renewal_requests',
        verbose_name=_("Traité par")
    )
    rejection_reason = models.TextField(
        _("Motif de refus"),
        blank=True
    )
    created_period = models.ForeignKey(
        AffiliationPeriod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_from_request',
        verbose_name=_("Période créée")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Demande de renouvellement")
        verbose_name_plural = _("Demandes de renouvellement")
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['affiliation', 'status']),
            models.Index(fields=['to_season', 'status']),
        ]

    def __str__(self):
        return f"{self.affiliation.child_organization.name} -> {self.to_season.name} ({self.get_status_display()})"


class Affiliation(models.Model):
    """
    Relation d'affiliation entre deux organisations
    """
    parent_organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='child_affiliations',
        verbose_name=_("Organisation parente")
    )
    child_organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='parent_affiliations',
        verbose_name=_("Organisation affiliée")
    )
    affiliation_type = models.CharField(
        _("Type d'affiliation"),
        max_length=30,
        choices=AffiliationType.choices,
        default=AffiliationType.MEMBER
    )
    
    # Informations d'affiliation
    start_date = models.DateField(_("Date de debut"), null=True, blank=True)
    end_date = models.DateField(_("Date de fin"), null=True, blank=True)
    certification_number = models.CharField(
        _("Numero de certification"), max_length=100, blank=True
    )
    notes = models.TextField(_("Notes"), blank=True)

    # Lien vers la période courante (pour accès rapide)
    current_period = models.ForeignKey(
        'AffiliationPeriod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name=_("Période courante")
    )

    # Systeme d'approbation bidirectionnelle
    initiated_by = models.CharField(
        _("Initie par"),
        max_length=10,
        choices=AffiliationInitiator.choices,
        default=AffiliationInitiator.PARENT
    )
    parent_status = models.CharField(
        _("Statut cote federation"),
        max_length=10,
        choices=AffiliationStatus.choices,
        default=AffiliationStatus.PENDING
    )
    child_status = models.CharField(
        _("Statut cote club"),
        max_length=10,
        choices=AffiliationStatus.choices,
        default=AffiliationStatus.PENDING
    )
    parent_approved_at = models.DateTimeField(_("Approuve par federation le"), null=True, blank=True)
    child_approved_at = models.DateTimeField(_("Approuve par club le"), null=True, blank=True)
    parent_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='federation_approvals',
        verbose_name=_("Approuve par (federation)")
    )
    child_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='club_approvals',
        verbose_name=_("Approuve par (club)")
    )

    # Statut global (actif seulement si les deux parties ont approuve)
    is_active = models.BooleanField(_("Actif"), default=False)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Affiliation")
        verbose_name_plural = _("Affiliations")
        unique_together = [['parent_organization', 'child_organization']]
        indexes = [
            models.Index(fields=['parent_organization', 'is_active']),
            models.Index(fields=['child_organization', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.child_organization.name} â†’ {self.parent_organization.name} ({self.get_affiliation_type_display()})"
    
    def clean(self):
        # EmpÃªcher l'auto-affiliation
        if self.parent_organization == self.child_organization:
            raise ValidationError(_("Une organisation ne peut pas s'affilier Ã  elle-mÃªme."))
        
        # Vérifier les affiliations circulaires (A->B->A)
        if Affiliation.objects.filter(
            parent_organization=self.child_organization,
            child_organization=self.parent_organization
        ).exists():
            raise ValidationError(_("Affiliation circulaire détectée. Veuillez vérifier les relations."))
    
    @property
    def is_expired(self):
        """Vérifie si l'affiliation est expirée."""
        from django.utils import timezone
        if not self.end_date:
            return False
        return self.end_date < timezone.now().date()

    @property
    def is_season_active(self):
        """Vérifie si l'affiliation est active pour la saison en cours."""
        if not self.current_period:
            return False
        return self.current_period.status == AffiliationPeriodStatus.ACTIVE

    @property
    def expires_soon(self):
        """Vérifie si l'affiliation expire bientôt (dans la période de rappel)."""
        if not self.current_period or not self.current_period.season:
            return False
        return self.current_period.season.is_renewal_period

    @property
    def days_until_expiry(self):
        """Nombre de jours avant expiration de la période courante."""
        if not self.current_period or not self.current_period.season:
            return None
        return self.current_period.season.days_remaining

    def get_period_for_season(self, season):
        """Récupère la période d'affiliation pour une saison donnée."""
        return self.periods.filter(season=season).first()

    def get_active_period(self):
        """Récupère la période active actuelle."""
        return self.periods.filter(status=AffiliationPeriodStatus.ACTIVE).first()


class OrganizationRole(models.TextChoices):
    OWNER = 'owner', _('Propriétaire')
    ADMIN = 'admin', _('Administrateur')
    MANAGER = 'manager', _('Gestionnaire')
    TREASURER = 'treasurer', _('Trésorier')
    ACCOUNTANT = 'accountant', _('Comptable')
    MEMBER = 'member', _('Membre')
    COACH = 'coach', _('Entraîneur')
    JUDGE = 'judge', _('Juge')


class MembershipStatus(models.TextChoices):
    """Statut de validation d'un rôle de membre"""
    PENDING = 'pending', _('En attente de validation')
    APPROVED = 'approved', _('Approuvé')
    REJECTED = 'rejected', _('Refusé')

class OrganizationMember(models.Model):
    """
    Relation entre un utilisateur et une organisation, avec un rÃ´le spécifique
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='organization_memberships',
        verbose_name=_("Utilisateur")
    )
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='members',
        verbose_name=_("Organisation")
    )
    role = models.CharField(
        _("RÃ´le"),
        max_length=30,
        choices=OrganizationRole.choices,
        default=OrganizationRole.MEMBER
    )
    
    # Informations supplémentaires
    title = models.CharField(_("Titre"), max_length=100, blank=True)
    join_date = models.DateField(_("Date d'adhésion"), auto_now_add=True)
    end_date = models.DateField(_("Date de fin"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Permissions spécifiques
    can_manage_members = models.BooleanField(_("Peut gérer les membres"), default=False)
    can_edit_organization = models.BooleanField(_("Peut modifier l'organisation"), default=False)
    can_manage_competitions = models.BooleanField(_("Peut gérer les compétitions"), default=False)

    # Statut de validation du rôle (workflow d'approbation)
    membership_status = models.CharField(
        _("Statut de validation"),
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.APPROVED,
        help_text=_("Statut de validation du rôle par un administrateur")
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_memberships',
        verbose_name=_("Approuvé par")
    )
    approved_at = models.DateTimeField(_("Approuvé le"), null=True, blank=True)
    rejection_reason = models.TextField(_("Motif de refus"), blank=True)

    # Lien avec le pratiquant (pour faciliter la navigation)
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organization_roles',
        verbose_name=_("Pratiquant associé")
    )

    # Rôles additionnels (cumul de rôles)
    additional_roles = models.JSONField(
        _("Rôles additionnels"),
        default=list,
        blank=True,
        help_text=_("Liste de codes de rôles supplémentaires, ex: ['treasurer', 'coach']")
    )

    # Statut
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Membre d'organisation")
        verbose_name_plural = _("Membres d'organisations")
        unique_together = [['user', 'organization']]
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['organization', 'role', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.get_role_display()})"
    
    @property
    def all_roles(self):
        """Retourne la liste de tous les rôles (principal + additionnels)."""
        roles = [self.role]
        if self.additional_roles:
            roles.extend(r for r in self.additional_roles if r != self.role)
        return roles

    def has_role(self, role_code):
        """Vérifie si le membre possède un rôle (principal ou additionnel)."""
        return role_code == self.role or (self.additional_roles and role_code in self.additional_roles)

    def save(self, *args, **kwargs):
        # Calculer les permissions en cumulant rôle principal + rôles additionnels
        all_roles = self.all_roles
        self.can_manage_members = any(
            r in ('owner', 'admin', 'manager') for r in all_roles
        )
        self.can_edit_organization = any(
            r in ('owner', 'admin') for r in all_roles
        )
        self.can_manage_competitions = any(
            r in ('owner', 'admin', 'manager') for r in all_roles
        )
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Vérifie si l'adhésion est expirée."""
        from django.utils import timezone
        if not self.end_date:
            return False
        return self.end_date < timezone.now().date()

    @property
    def is_pending(self):
        """Vérifie si le rôle est en attente de validation."""
        return self.membership_status == MembershipStatus.PENDING

    @property
    def is_approved(self):
        """Vérifie si le rôle est approuvé."""
        return self.membership_status == MembershipStatus.APPROVED

    @property
    def is_rejected(self):
        """Vérifie si le rôle est refusé."""
        return self.membership_status == MembershipStatus.REJECTED

    @property
    def has_dashboard_access(self):
        """Vérifie si le membre peut accéder à son dashboard de rôle."""
        return self.is_active and self.is_approved and not self.is_expired

    def approve(self, approved_by_user):
        """Approuve le rôle d'un membre."""
        from django.utils import timezone
        self.membership_status = MembershipStatus.APPROVED
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = ''
        self.save(update_fields=['membership_status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])

    def reject(self, rejected_by_user, reason=''):
        """Refuse le rôle d'un membre."""
        from django.utils import timezone
        self.membership_status = MembershipStatus.REJECTED
        self.approved_by = rejected_by_user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['membership_status', 'approved_by', 'approved_at', 'rejection_reason', 'updated_at'])

    @classmethod
    def get_role_dashboard_url(cls, role):
        """Retourne l'URL du dashboard associé à un rôle."""
        from django.urls import reverse
        role_dashboards = {
            OrganizationRole.OWNER: 'competitions:dashboard:club',
            OrganizationRole.ADMIN: 'competitions:dashboard:club',
            OrganizationRole.MANAGER: 'competitions:dashboard:manager',
            OrganizationRole.TREASURER: 'finances:dashboard',
            OrganizationRole.ACCOUNTANT: 'finances:dashboard',
            OrganizationRole.COACH: 'competitions:dashboard:coach',
            OrganizationRole.JUDGE: 'competitions:dashboard:judge_technical',
            OrganizationRole.MEMBER: 'competitions:dashboard:participant',
        }
        url_name = role_dashboards.get(role, 'competitions:dashboard:participant')
        try:
            return reverse(url_name)
        except Exception:
            return reverse('competitions:dashboard')

    def get_dashboard_url(self):
        """Retourne l'URL du dashboard pour ce membre."""
        return self.get_role_dashboard_url(self.role)


class OrganizationGalleryImage(models.Model):
    """
    Images de galerie pour les organisations.
    Maximum 10 images par organisation, avec descriptions.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='gallery_images',
        verbose_name=_("Organisation")
    )
    image = models.ImageField(
        _("Image"),
        upload_to='organizations/gallery/',
        help_text=_("Formats acceptés: JPG, PNG, WebP. Max 5 Mo.")
    )
    description = models.CharField(
        _("Description"),
        max_length=255,
        blank=True,
        help_text=_("Description courte de l'image")
    )
    alt_text = models.CharField(
        _("Texte alternatif"),
        max_length=255,
        blank=True,
        help_text=_("Pour l'accessibilité")
    )
    order = models.PositiveIntegerField(
        _("Ordre d'affichage"),
        default=0
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'organizations'
        verbose_name = _("Image de galerie")
        verbose_name_plural = _("Images de galerie")
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['organization', 'order']),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.description or f'Image {self.id}'}"

    def save(self, *args, **kwargs):
        # Vérifier le nombre maximum d'images (10)
        if not self.pk:  # Nouvelle image
            count = OrganizationGalleryImage.objects.filter(
                organization=self.organization
            ).count()
            if count >= 10:
                raise ValidationError(
                    _("Maximum 10 images autorisées par organisation.")
                )
        super().save(*args, **kwargs)


class OrganizationVideoLink(models.Model):
    """
    Liens vidéos YouTube pour les organisations.
    Maximum 10 vidéos par organisation.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='video_links',
        verbose_name=_("Organisation")
    )
    youtube_url = models.URLField(
        _("URL YouTube"),
        help_text=_("URL complète de la vidéo YouTube")
    )
    title = models.CharField(
        _("Titre"),
        max_length=255,
        help_text=_("Titre de la vidéo")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description de la vidéo")
    )
    thumbnail_url = models.URLField(
        _("URL de la miniature"),
        blank=True,
        help_text=_("Générée automatiquement depuis YouTube")
    )
    video_id = models.CharField(
        _("ID YouTube"),
        max_length=20,
        blank=True,
        help_text=_("Extrait automatiquement de l'URL")
    )
    order = models.PositiveIntegerField(
        _("Ordre d'affichage"),
        default=0
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'organizations'
        verbose_name = _("Lien vidéo")
        verbose_name_plural = _("Liens vidéos")
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'order']),
            models.Index(fields=['organization', 'is_active']),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.title}"

    def extract_video_id(self):
        """Extrait l'ID vidéo depuis l'URL YouTube."""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/shorts\/([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, self.youtube_url)
            if match:
                return match.group(1)
        return ''

    def get_thumbnail_url(self):
        """Génère l'URL de la miniature YouTube."""
        if self.video_id:
            return f"https://img.youtube.com/vi/{self.video_id}/hqdefault.jpg"
        return ''

    def get_embed_url(self):
        """Retourne l'URL d'embed pour l'iframe."""
        if self.video_id:
            return f"https://www.youtube.com/embed/{self.video_id}"
        return ''

    def save(self, *args, **kwargs):
        # Extraire l'ID vidéo et générer la miniature
        self.video_id = self.extract_video_id()
        if self.video_id and not self.thumbnail_url:
            self.thumbnail_url = self.get_thumbnail_url()

        # Vérifier le nombre maximum de vidéos (10)
        if not self.pk:
            count = OrganizationVideoLink.objects.filter(
                organization=self.organization
            ).count()
            if count >= 10:
                raise ValidationError(
                    _("Maximum 10 vidéos autorisées par organisation.")
                )
        super().save(*args, **kwargs)


class OrganizationNews(models.Model):
    """
    Modèle pour les actualités/news des organisations (fédérations, clubs).
    Permet de publier des articles sur le site public de l'organisation.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='news_articles',
        verbose_name=_("Organisation")
    )
    title = models.CharField(
        _("Titre"),
        max_length=255,
        help_text=_("Titre de l'actualité")
    )
    slug = models.SlugField(
        _("Slug"),
        max_length=255,
        blank=True,
        help_text=_("URL-friendly version du titre (généré automatiquement)")
    )
    excerpt = models.CharField(
        _("Résumé"),
        max_length=500,
        blank=True,
        help_text=_("Court résumé affiché dans les listes (optionnel)")
    )
    content = models.TextField(
        _("Contenu"),
        help_text=_("Contenu complet de l'actualité (supporte le HTML)")
    )
    image = models.ImageField(
        _("Image principale"),
        upload_to='organizations/news/',
        null=True,
        blank=True,
        help_text=_("Image d'illustration (recommandé: 800x400px)")
    )

    # Statut de publication
    is_published = models.BooleanField(
        _("Publié"),
        default=False,
        help_text=_("Cocher pour rendre l'article visible sur le site")
    )
    is_featured = models.BooleanField(
        _("À la une"),
        default=False,
        help_text=_("Afficher en priorité sur la page d'accueil")
    )

    # Dates
    published_at = models.DateTimeField(
        _("Date de publication"),
        null=True,
        blank=True,
        help_text=_("Date de publication (peut être dans le futur)")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    # Auteur
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organization_news',
        verbose_name=_("Auteur")
    )

    class Meta:
        app_label = 'organizations'
        verbose_name = _("Actualité")
        verbose_name_plural = _("Actualités")
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'is_published', '-published_at']),
            models.Index(fields=['organization', 'is_featured']),
        ]
        unique_together = [['organization', 'slug']]

    def __str__(self):
        return f"{self.organization.name} - {self.title}"

    def save(self, *args, **kwargs):
        # Générer le slug automatiquement
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = base_slug
            # Assurer l'unicité du slug pour cette organisation
            counter = 1
            while OrganizationNews.objects.filter(
                organization=self.organization,
                slug=self.slug
            ).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        # Définir la date de publication si publié
        if self.is_published and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()

        super().save(*args, **kwargs)

    def get_excerpt(self):
        """Retourne le résumé ou tronque le contenu."""
        if self.excerpt:
            return self.excerpt
        # Supprimer les tags HTML et tronquer
        import re
        text = re.sub(r'<[^>]+>', '', self.content)
        if len(text) > 200:
            return text[:197] + '...'
        return text

    @classmethod
    def get_published_for_organization(cls, organization, limit=10):
        """Retourne les actualités publiées pour une organisation."""
        from django.utils import timezone
        return cls.objects.filter(
            organization=organization,
            is_published=True,
            published_at__lte=timezone.now()
        ).order_by('-published_at')[:limit]
