from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole


class AffiliationRequest(models.Model):
    """Demande d'affiliation d'un club Ã  une fédération."""
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('cancelled', _('Annulée')),
    ]
    
    requesting_organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='sent_affiliation_requests',
        verbose_name=_('Organisation demandeuse'),
    )
    target_organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='received_affiliation_requests',
        verbose_name=_("Organisation cible")
    )
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    notes = models.TextField(_("Notes"), blank=True)
    response_message = models.TextField(_("Message de réponse"), blank=True)
    
    def __str__(self):
        return f"{self.requesting_organization.name} - {self.target_organization.name} ({self.get_status_display()})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Demande d'affiliation")
        verbose_name_plural = _("Demandes d'affiliation")
        ordering = ['-created_at']


