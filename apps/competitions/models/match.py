from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole

class Match(models.Model):
    """Modèle pour les matchs dans une compétition."""
    competition = models.ForeignKey('Competition', on_delete=models.CASCADE, related_name='matches')
    name = models.CharField(_("Nom"), max_length=255)
    date_match = models.DateField(_("Date du match"))
    start_time = models.DateTimeField(_("Heure de début"), null=True, blank=True)
    end_time = models.DateTimeField(_("Heure de fin"), null=True, blank=True)
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=[
            ('pending', _('En attente')),
            ('in_progress', _('En cours')),
            ('completed', _('Terminé')),
            ('cancelled', _('Annulé')),
        ],
        default='pending'
    )
    participants = models.ManyToManyField('Practitioner', related_name='matches', blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.competition.title})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Match")
        verbose_name_plural = _("Matches")
        ordering = ['date_match', 'start_time']


