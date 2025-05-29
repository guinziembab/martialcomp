from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User

from organizations.models import Organization, OrganizationMember, OrganizationRole


class Membership(models.Model):
    """Gestion des adhésions et renouvellements."""
    
    TYPE_CHOICES = [
        ('annual', _('Annuelle')),
        ('biannual', _('Semestrielle')),
        ('quarterly', _('Trimestrielle')),
        ('monthly', _('Mensuelle')),
        ('special', _('Spéciale')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('active', _('Active')),
        ('expired', _('Expirée')),
        ('canceled', _('Annulée')),
        ('suspended', _('Suspendue')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Espèces')),
        ('check', _('Chèque')),
        ('card', _('Carte bancaire')),
        ('transfer', _('Virement')),
        ('other', _('Autre')),
    ]
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    organization = models.ForeignKey(
        'organizations.Organization',  # Changed from 'competitions.Club' to 'organizations.Organization'
        on_delete=models.CASCADE,
        related_name='member_subscriptions',  # Changed from 'memberships' to avoid conflicts
        null=True,
        blank=True
    )
    membership_type = models.CharField(_("Type d'adhésion"), max_length=20, choices=TYPE_CHOICES)
    
    # Dates
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"))
    created_at = models.DateTimeField(_("Date de création"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Dernière mise à jour"), auto_now=True)
    
    # Paiement
    amount = models.DecimalField(_("Montant"), max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        _("Méthode de paiement"),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True
    )
    payment_date = models.DateField(_("Date de paiement"), null=True, blank=True)
    payment_reference = models.CharField(_("Référence de paiement"), max_length=50, blank=True)
    payment_validated = models.BooleanField(_("Paiement validé"), default=False)
    
    # Statut
    status = models.CharField(_("Statut"), max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_memberships',
        verbose_name=_("Créé par")
    )
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = _("Adhésion")
        verbose_name_plural = _("Adhésions")
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.get_membership_type_display()} ({self.start_date} à {self.end_date})"
    
    @property
    def is_active(self):
        """Vérifie si l'adhésion est active à la date actuelle."""
        from django.utils import timezone
        today = timezone.now().date()
        return self.status == 'active' and self.start_date <= today <= self.end_date


class License(models.Model):
    """Gestion des licences fédérales."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('active', _('Active')),
        ('expired', _('Expirée')),
        ('suspended', _('Suspendue')),
        ('canceled', _('Annulée')),
    ]
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='licenses'
    )
    organization = models.ForeignKey(  # Changed from 'federation' to 'organization'
        'organizations.Organization',  # Changed from 'competitions.Federation' to 'organizations.Organization'
        on_delete=models.CASCADE,
        related_name='issued_licenses',  # Changed from 'licenses' to avoid conflicts
        verbose_name=_("Fédération")
    )
    license_number = models.CharField(_("Numéro de licence"), max_length=50)
    issue_date = models.DateField(_("Date d'émission"))
    expiry_date = models.DateField(_("Date d'expiration"))
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    is_competition_valid = models.BooleanField(
        _("Valide pour la compétition"), 
        default=True
    )
    license_type = models.CharField(_("Type de licence"), max_length=50, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Licence")
        verbose_name_plural = _("Licences")
        unique_together = ['practitioner', 'license_number', 'organization']  # Changed 'federation' to 'organization'
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Licence {self.license_number} - {self.practitioner.full_name}"
    
    @property
    def is_valid(self):
        """Vérifie si la licence est valide à la date actuelle."""
        from django.utils import timezone
        return self.status == 'active' and self.expiry_date >= timezone.now().date()