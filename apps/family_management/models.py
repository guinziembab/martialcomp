from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import uuid


class Family(models.Model):
    """
    Modèle principal pour représenter une famille dans MartialComp.
    Une famille regroupe plusieurs pratiquants et permet une gestion centralisée.
    """
    
    # Identifiant unique pour la famille
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Nom de famille ou nom personnalisé pour identifier la famille
    family_name = models.CharField(
        _("Nom de famille"), 
        max_length=100,
        help_text=_("Nom principal de la famille (ex: Famille Martin)")
    )
    
    # Description optionnelle de la famille
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description optionnelle de la famille")
    )
    
    # Responsable principal de la famille (généralement un parent)
    primary_responsible = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='managed_families',
        verbose_name=_("Responsable principal"),
        help_text=_("Parent ou tuteur responsable de la gestion familiale")
    )
    
    # Informations de contact et facturation centralisées
    billing_address = models.TextField(
        _("Adresse de facturation"),
        blank=True,
        help_text=_("Adresse principale pour la facturation familiale")
    )
    
    billing_phone = models.CharField(
        _("Téléphone de contact"),
        max_length=20,
        blank=True
    )
    
    billing_email = models.EmailField(
        _("Email de facturation"),
        blank=True,
        help_text=_("Email pour recevoir les factures et communications administratives")
    )
    
    # Paramètres de gestion familiale
    shared_calendar = models.BooleanField(
        _("Calendrier familial partagé"),
        default=True,
        help_text=_("Autoriser la vue consolidée du calendrier familial")
    )
    
    shared_notifications = models.BooleanField(
        _("Notifications partagées"),
        default=True,
        help_text=_("Centraliser les notifications au niveau familial")
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(_("Famille active"), default=True)
    
    # Organisation/tenant pour multi-tenant
    organization = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.CASCADE, 
        related_name='families',
        null=True, blank=True
    )
    
    class Meta:
        app_label = 'family_management'
        verbose_name = _("Famille")
        verbose_name_plural = _("Familles")
        ordering = ['family_name']
        
    def __str__(self):
        return f"{self.family_name}"
    
    def get_all_members(self):
        """Retourne tous les membres de la famille"""
        return self.members.filter(is_active=True)
    
    def get_active_members(self):
        """Alias pour get_all_members pour compatibilité"""
        return self.get_all_members()
    
    def get_total_practitioners(self):
        """Retourne le nombre total de pratiquants actifs dans la famille"""
        return len([member.practitioner for member in self.get_all_members() 
                   if member.practitioner and hasattr(member.practitioner, 'status') 
                   and member.practitioner.status == 'active'])
    
    def get_monthly_fees(self):
        """Calcule les frais mensuels estimés pour la famille"""
        # Calcul basique basé sur le nombre de membres actifs
        active_count = self.get_all_members().count()
        base_fee = 50  # Frais de base par membre
        return active_count * base_fee
    
    def get_practitioners(self):
        """Retourne tous les pratiquants de la famille"""
        return [member.practitioner for member in self.get_all_members() 
                if member.practitioner and member.practitioner.status == 'active']
    
    def get_total_pending_payments(self):
        """Calcule le total des paiements en attente pour la famille"""
        from django.db.models import Sum
        return self.payment_groups.filter(is_paid=False).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
    
    def has_upcoming_events(self):
        """Vérifie s'il y a des événements Ã  venir pour les membres de la famille"""
        from django.utils import timezone
        return FamilyEvent.objects.filter(
            family=self,
            start_date__gte=timezone.now()
        ).exists()


class FamilyRole(models.Model):
    """
    Définit les rÃ´les possibles au sein d'une famille
    """
    ROLE_CHOICES = [
        ('parent', _('Parent')),
        ('guardian', _('Tuteur légal')),
        ('child', _('Enfant')),
        ('spouse', _('Conjoint(e)')),
        ('sibling', _('Frère/SÅ“ur')),
        ('other', _('Autre relation'))
    ]
    
    name = models.CharField(
        _("Nom du rÃ´le"),
        max_length=50,
        choices=ROLE_CHOICES,
        unique=True
    )
    
    can_manage_family = models.BooleanField(
        _("Peut gérer la famille"),
        default=False,
        help_text=_("Autorise la gestion administrative de la famille")
    )
    
    can_view_all_data = models.BooleanField(
        _("Peut voir toutes les données"),
        default=True,
        help_text=_("Autorise la consultation des données de tous les membres")
    )
    
    can_register_members = models.BooleanField(
        _("Peut inscrire les membres"),
        default=False,
        help_text=_("Autorise l'inscription des membres aux compétitions/événements")
    )
    
    class Meta:
        app_label = 'family_management'
        verbose_name = _("RÃ´le familial")
        verbose_name_plural = _("RÃ´les familiaux")
        
    def __str__(self):
        return self.get_name_display()


class FamilyMember(models.Model):
    """
    Représente un membre d'une famille avec son rÃ´le et ses permissions
    """
    
    # Relations principales
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_("Famille")
    )
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='family_memberships',
        verbose_name=_("Pratiquant"),
        null=True, blank=True
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='family_memberships',
        verbose_name=_("Utilisateur"),
        null=True, blank=True
    )
    
    # RÃ´le dans la famille
    role = models.CharField(
        _("RÃ´le familial"),
        max_length=50,
        choices=FamilyRole.ROLE_CHOICES,
        default='child'
    )
    
    # Permissions spécifiques pour ce membre
    can_manage_others = models.BooleanField(
        _("Peut gérer les autres membres"),
        default=False
    )
    
    can_make_payments = models.BooleanField(
        _("Peut effectuer des paiements"),
        default=False
    )
    
    # Statut et métadonnées
    is_active = models.BooleanField(_("Membre actif"), default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # Paramètres de visibilité
    share_calendar = models.BooleanField(
        _("Partager le calendrier"),
        default=True,
        help_text=_("Afficher les événements de ce membre dans le calendrier familial")
    )
    
    receive_family_notifications = models.BooleanField(
        _("Recevoir les notifications familiales"),
        default=True
    )
    
    class Meta:
        app_label = 'family_management'
        verbose_name = _("Membre de famille")
        verbose_name_plural = _("Membres de famille")
        # Utilisation d'indexes au lieu de contraintes complexes pour éviter les problèmes SQLite
        indexes = [
            models.Index(fields=['family', 'practitioner'], name='family_practitioner_idx'),
            models.Index(fields=['family', 'user'], name='family_user_idx'),
        ]
        
    def __str__(self):
        if self.practitioner:
            return f"{self.practitioner.full_name} ({self.get_role_display()}) - {self.family.family_name}"
        return f"{self.user.get_full_name()} ({self.get_role_display()}) - {self.family.family_name}"
    
    def clean(self):
        """Validation personnalisée"""
        if not self.practitioner and not self.user:
            raise ValidationError(_("Un membre doit Ãªtre lié soit Ã  un pratiquant soit Ã  un utilisateur"))
        
        if self.practitioner and self.user:
            # Vérifier que l'utilisateur correspond au pratiquant
            if self.practitioner.user and self.practitioner.user != self.user:
                raise ValidationError(_("L'utilisateur sélectionné ne correspond pas au pratiquant"))
    
    def get_display_name(self):
        """Retourne le nom d'affichage du membre"""
        if self.practitioner:
            return self.practitioner.full_name
        return self.user.get_full_name() if self.user else "Membre inconnu"
    
    def has_permission(self, permission):
        """Vérifie si le membre a une permission spécifique"""
        role_permissions = {
            'parent': ['manage_family', 'view_all', 'register_members', 'make_payments'],
            'guardian': ['manage_family', 'view_all', 'register_members', 'make_payments'],
            'spouse': ['view_all', 'register_members'],
            'child': ['view_own'],
            'sibling': ['view_own'],
            'other': ['view_own']
        }
        
        base_permissions = role_permissions.get(self.role, ['view_own'])
        
        # Ajouter les permissions personnalisées
        if self.can_manage_others and 'manage_family' not in base_permissions:
            base_permissions.append('manage_family')
        
        if self.can_make_payments and 'make_payments' not in base_permissions:
            base_permissions.append('make_payments')
            
        return permission in base_permissions


class FamilyPaymentGroup(models.Model):
    """
    Regroupe plusieurs paiements/factures au niveau familial
    """
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='payment_groups',
        verbose_name=_("Famille")
    )
    
    group_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    description = models.CharField(
        _("Description"),
        max_length=200,
        help_text=_("Description du groupe de paiements")
    )
    
    total_amount = models.DecimalField(
        _("Montant total"),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(_("Payé"), default=False)
    
    class Meta:
        app_label = 'family_management'
        verbose_name = _("Groupe de paiement familial")
        verbose_name_plural = _("Groupes de paiements familiaux")
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.description} - {self.family.family_name} ({self.total_amount}â‚¬)"


class FamilyEvent(models.Model):
    """
    Ã‰vénements spécifiques Ã  une famille (réunions, sorties, etc.)
    """
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='family_events',
        verbose_name=_("Famille")
    )
    
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    
    start_date = models.DateTimeField(_("Date de début"))
    end_date = models.DateTimeField(_("Date de fin"), null=True, blank=True)
    
    location = models.CharField(_("Lieu"), max_length=200, blank=True)
    
    # Membres concernés par l'événement
    concerned_members = models.ManyToManyField(
        FamilyMember,
        related_name='family_events',
        verbose_name=_("Membres concernés"),
        blank=True
    )
    
    is_private = models.BooleanField(
        _("Ã‰vénement privé"),
        default=False,
        help_text=_("Visible uniquement par la famille")
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_family_events',
        verbose_name=_("Créé par")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'family_management'
        verbose_name = _("Ã‰vénement familial")
        verbose_name_plural = _("Ã‰vénements familiaux")
        ordering = ['start_date']
        
    def __str__(self):
        return f"{self.title} - {self.family.family_name}"
