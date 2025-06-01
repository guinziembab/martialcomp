from django.db import models
from django.utils.translation import gettext_lazy as _

from organizations.models import Organization, OrganizationMember, OrganizationRole


class MedicalRecord(models.Model):
    """Dossier médical complet du pratiquant."""
    
    practitioner = models.OneToOneField(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='medical_record'
    )
    last_visit_date = models.DateField(_("Date de dernière visite"), null=True, blank=True)
    doctor_name = models.CharField(_("Médecin"), max_length=100, blank=True)
    doctor_contact = models.CharField(_("Contact du médecin"), max_length=50, blank=True)
    blood_type = models.CharField(_("Groupe sanguin"), max_length=5, blank=True)
    allergies = models.TextField(_("Allergies"), blank=True)
    chronic_conditions = models.TextField(_("Conditions chroniques"), blank=True)
    current_medications = models.TextField(_("Médicaments actuels"), blank=True)
    previous_injuries = models.TextField(_("Blessures antérieures"), blank=True)
    restrictions = models.TextField(_("Restrictions"), blank=True)
    emergency_protocols = models.TextField(_("Protocoles d'urgence"), blank=True)
    confidential_notes = models.TextField(_("Notes confidentielles"), blank=True)
    
    class Meta:
        verbose_name = _("Dossier médical")
        verbose_name_plural = _("Dossiers médicaux")
    
    def __str__(self):
        return f"Dossier médical de {self.practitioner.full_name}"


class MedicalCertificate(models.Model):
    """Suivi des certificats médicaux."""
    
    STATUS_CHOICES = [
        ('valid', _('Valide')),
        ('expired', _('Expiré')),
        ('pending', _('En attente de vérification')),
        ('rejected', _('Rejeté')),
    ]
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='medical_certificates'
    )
    issue_date = models.DateField(_("Date d'émission"))
    expiry_date = models.DateField(_("Date d'expiration"))
    doctor_name = models.CharField(_("Médecin"), max_length=100)
    certificate_file = models.FileField(
        _("Fichier du certificat"),
        upload_to='practitioners/medical_certificates/',
        null=True,
        blank=True
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='valid'
    )
    is_competition_valid = models.BooleanField(
        _("Valide pour la compétition"), 
        default=True,
        help_text=_("Indique si le certificat autorise explicitement la compétition.")
    )
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Certificat médical")
        verbose_name_plural = _("Certificats médicaux")
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Certificat médical de {self.practitioner.full_name} ({self.issue_date})"
    
    @property
    def is_valid(self):
        """Vérifie si le certificat est valide à la date actuelle."""
        from django.utils import timezone
        return self.status == 'valid' and self.expiry_date >= timezone.now().date()