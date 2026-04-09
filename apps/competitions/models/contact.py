from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactSubmission(models.Model):
    """Stocke les soumissions du formulaire de contact."""

    SUBJECT_CHOICES = [
        ('information', _("Demande d'information")),
        ('partnership', _("Partenariat")),
        ('federation', _("Federation")),
        ('club', _("Club / Ecole")),
        ('support', _("Support technique")),
        ('other', _("Autre")),
    ]

    name = models.CharField(_("Nom complet"), max_length=150)
    email = models.EmailField(_("Email"))
    organization = models.CharField(
        _("Organisation"),
        max_length=200,
        blank=True,
        help_text=_("Nom de votre club, ecole ou federation")
    )
    subject = models.CharField(
        _("Sujet"),
        max_length=50,
        choices=SUBJECT_CHOICES,
        default='information'
    )
    message = models.TextField(_("Message"))
    created_at = models.DateTimeField(_("Date de creation"), auto_now_add=True)
    is_read = models.BooleanField(_("Lu"), default=False)
    read_at = models.DateTimeField(_("Lu le"), null=True, blank=True)
    responded = models.BooleanField(_("Repondu"), default=False)
    responded_at = models.DateTimeField(_("Repondu le"), null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Message de contact")
        verbose_name_plural = _("Messages de contact")

    def __str__(self):
        return f"{self.name} - {self.get_subject_display()} ({self.created_at:%d/%m/%Y})"
