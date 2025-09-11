from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class JudgeTraining(models.Model):
    """Formation pour les juges"""
    
    TRAINING_TYPE_CHOICES = [
        ('initial', _('Formation initiale')),
        ('continuous', _('Formation continue')),
        ('specialization', _('Spécialisation')),
        ('refresher', _('Recyclage')),
    ]
    
    LEVEL_CHOICES = [
        ('regional', _('Régional')),
        ('national', _('National')),  
        ('international', _('International')),
    ]
    
    STATUS_CHOICES = [
        ('planned', _('Planifié')),
        ('open', _('Inscriptions ouvertes')),
        ('closed', _('Inscriptions fermées')),
        ('ongoing', _('En cours')),
        ('completed', _('Terminé')),
        ('cancelled', _('Annulé')),
    ]
    
    title = models.CharField(_("Titre"), max_length=200)
    name = models.CharField(_("Nom de la formation"), max_length=200)  # Gardé pour compatibilité
    description = models.TextField(_("Description"))
    training_type = models.CharField(_("Type de formation"), max_length=20, choices=TRAINING_TYPE_CHOICES)
    level = models.CharField(_("Niveau"), max_length=20, choices=LEVEL_CHOICES)
    
    # Dates
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"))
    registration_deadline = models.DateField(_("Date limite d'inscription"))
    
    # Lieu et capacité
    location = models.CharField(_("Lieu"), max_length=200)
    max_participants = models.PositiveIntegerField(_("Nombre max de participants"))
    
    # Formateur
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taught_trainings',
        verbose_name=_("Formateur")
    )
    
    # Disciplines concernées
    disciplines = models.ManyToManyField(
        'competitions.Discipline',
        related_name='judge_trainings',
        verbose_name=_("Disciplines")
    )
    
    # Statut
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='planned')
    
    # Durée
    duration_hours = models.PositiveIntegerField(_("Durée (heures)"))
    
    # Federation associée
    federation = models.ForeignKey(
        'competitions.Federation',
        on_delete=models.CASCADE,
        related_name='judge_trainings',
        verbose_name=_("Fédération"),
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Formation de juge")
        verbose_name_plural = _("Formations de juges")
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title or self.name
    
    @property
    def is_open_for_registration(self):
        """Vérifie si les inscriptions sont ouvertes"""
        from django.utils import timezone
        return (
            self.status == 'open' and 
            self.registration_deadline >= timezone.now().date()
        )
    
    @property
    def participants_count(self):
        """Nombre de participants inscrits"""
        return self.registrations.count()


class JudgeTrainingRegistration(models.Model):
    """Inscription d'un juge Ã  une formation"""
    judge = models.ForeignKey('competitions.Judge', on_delete=models.CASCADE, related_name='training_registrations')
    training = models.ForeignKey(JudgeTraining, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Inscription Ã  une formation")
        verbose_name_plural = _("Inscriptions aux formations")
        unique_together = ['judge', 'training']
    
    def __str__(self):
        return f"{self.judge} - {self.training}"

