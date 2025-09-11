from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole

# Modèle amélioré pour l'inscription des pratiquants Ã  une compétition
class CompetitionRegistration(models.Model):
    # Utilisation de références avant (forward references) avec des chaÃ®nes
    practitioner = models.ForeignKey('competitions.Practitioner', on_delete=models.CASCADE, related_name='registrations')
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, related_name='registrations')
    
    # RÃ´les dans la compétition (multiple)
    roles = models.ManyToManyField('competitions.CompetitionRole', related_name='registrations', blank=True)
    is_competitor = models.BooleanField(_("Participant"), default=False)
    is_technical_judge = models.BooleanField(_("Juge Technique"), default=False)
    is_combat_referee = models.BooleanField(_("Arbitre Combat"), default=False)
    is_volunteer = models.BooleanField(_("Bénévole"), default=False)
    is_coach = models.BooleanField(_("Coach"), default=False)
    
    # Sélection des types de compétitions pour ce pratiquant
    competition_types = models.ManyToManyField('competitions.CompetitionType', related_name='registrations', blank=True)
    
    # Catégories par type de compétition
    categories = models.ManyToManyField('competitions.CompetitionCategory', related_name='registrations', blank=True)
    
    # Autres informations
    registration_date = models.DateTimeField(_("Date d'inscription"), auto_now_add=True)
    status = models.CharField(_("Statut"), max_length=20, choices=[
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
    ], default='pending')
    
    # Commentaires et notes spécifiques
    notes = models.TextField(_("Notes"), blank=True)
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.competition.title}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Inscription Ã  une compétition")
        verbose_name_plural = _("Inscriptions aux compétitions")
        unique_together = ('practitioner', 'competition')

# Modèle pour les affectations des juges/arbitres aux catégories
# Renommé pour éviter le conflit avec le modèle dans judges.py
class JudgeCompetitionAssignment(models.Model):
    registration = models.ForeignKey('competitions.CompetitionRegistration', on_delete=models.CASCADE, related_name='assignments')
    category = models.ForeignKey('competitions.CompetitionCategory', on_delete=models.CASCADE, related_name='competition_judge_assignments')
    assignment_type = models.CharField(_("Type d'affectation"), max_length=20, choices=[
        ('technical_judge', _('Juge Technique')),
        ('combat_referee', _('Arbitre Combat')),
        ('chief_judge', _('Juge en Chef')),
        ('timekeeper', _('Chronométreur')),
    ])
    
    def __str__(self):
        return f"{self.registration.practitioner.full_name} - {self.category.name} ({self.get_assignment_type_display()})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Affectation de juge Ã  une compétition")
        verbose_name_plural = _("Affectations de juge aux compétitions")
        unique_together = ('registration', 'category', 'assignment_type')
        # Ajout d'un nom de table personnalisé pour éviter des conflits potentiels
        db_table = 'competitions_judge_competition_assignment'


