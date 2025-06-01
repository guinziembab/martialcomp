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
    address = models.TextField(_("Adresse"), blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=20, blank=True)
    
    # Logo et médias
    logo = models.ImageField(_("Logo"), upload_to='organizations/logos/', null=True, blank=True)
    
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
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
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
            # Utiliser le nom ou une chaîne par défaut si le nom est vide
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
        
        super().save(*args, **kwargs)
    
    def get_affiliated_organizations(self, include_inactive=False):
        """Retourne les organisations affiliées à cette organisation."""
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
        """Retourne le rôle d'un utilisateur dans l'organisation."""
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
            
        try:
            membership = self.members.get(user=user, is_active=True)
            return (membership.can_manage_competitions or 
                   membership.role in ['owner', 'admin'])
        except OrganizationMember.DoesNotExist:
            return False

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
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"), null=True, blank=True)
    certification_number = models.CharField(_("Numéro de certification"), max_length=100, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    # Statut
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Affiliation")
        verbose_name_plural = _("Affiliations")
        unique_together = [['parent_organization', 'child_organization']]
        indexes = [
            models.Index(fields=['parent_organization', 'is_active']),
            models.Index(fields=['child_organization', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.child_organization.name} → {self.parent_organization.name} ({self.get_affiliation_type_display()})"
    
    def clean(self):
        # Empêcher l'auto-affiliation
        if self.parent_organization == self.child_organization:
            raise ValidationError(_("Une organisation ne peut pas s'affilier à elle-même."))
        
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

class OrganizationRole(models.TextChoices):
    OWNER = 'owner', _('Propriétaire')
    ADMIN = 'admin', _('Administrateur')
    MANAGER = 'manager', _('Gestionnaire')
    MEMBER = 'member', _('Membre')
    COACH = 'coach', _('Entraîneur')
    JUDGE = 'judge', _('Juge')

class OrganizationMember(models.Model):
    """
    Relation entre un utilisateur et une organisation, avec un rôle spécifique
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
        _("Rôle"),
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
    
    # Statut
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
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
    
    def save(self, *args, **kwargs):
        # Définir automatiquement les permissions selon le rôle
        if self.role == OrganizationRole.OWNER or self.role == OrganizationRole.ADMIN:
            self.can_manage_members = True
            self.can_edit_organization = True
            self.can_manage_competitions = True
        elif self.role == OrganizationRole.MANAGER:
            self.can_manage_members = True
            self.can_manage_competitions = True
            
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Vérifie si l'adhésion est expirée."""
        from django.utils import timezone
        if not self.end_date:
            return False
        
        return self.end_date < timezone.now().date()