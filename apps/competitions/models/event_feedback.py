# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from . import Event


class EventFeedback(models.Model):
    """
    Modèle pour stocker les retours d'expérience (feedback) des participants sur les événements.
    """
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='event_feedbacks',
        verbose_name=_("Ã‰vénement")
    )
    
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_feedbacks',
        verbose_name=_("Soumis par")
    )
    
    # Date de soumission
    submitted_at = models.DateTimeField(_("Date de soumission"), auto_now_add=True)
    
    # Ã‰valuations numériques
    overall_satisfaction = models.PositiveSmallIntegerField(_("Satisfaction générale"), choices=[(i, str(i)) for i in range(1, 6)])
    organization_rating = models.PositiveSmallIntegerField(_("Organisation"), choices=[(i, str(i)) for i in range(1, 6)])
    content_quality = models.PositiveSmallIntegerField(_("Qualité du contenu"), choices=[(i, str(i)) for i in range(1, 6)])
    location_rating = models.PositiveSmallIntegerField(_("Lieu"), choices=[(i, str(i)) for i in range(1, 6)])
    value_for_money = models.PositiveSmallIntegerField(_("Rapport qualité-prix"), choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    
    # Recommandation
    RECOMMENDATION_CHOICES = [
        ('yes', _("Oui, sans hésitation")),
        ('maybe', _("Peut-Ãªtre")),
        ('no', _("Non"))
    ]
    would_recommend = models.CharField(_("Recommandation"), max_length=10, choices=RECOMMENDATION_CHOICES)
    
    # Champs de commentaires
    highlights = models.TextField(_("Points forts"), blank=True)
    improvements = models.TextField(_("Points Ã  améliorer"), blank=True)
    additional_comments = models.TextField(_("Commentaires additionnels"), blank=True)
    
    # Paramètres supplémentaires
    allow_testimonial = models.BooleanField(_("Autoriser comme témoignage"), default=False)
    
    # Champs spécifiques au type d'événement (optionnels)
    competition_fairness = models.PositiveSmallIntegerField(_("Ã‰quité de la compétition"), choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    instructor_knowledge = models.PositiveSmallIntegerField(_("Connaissance de l'instructeur"), choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    material_usefulness = models.PositiveSmallIntegerField(_("Utilité du matériel"), choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    exam_difficulty = models.PositiveSmallIntegerField(_("Difficulté de l'examen"), choices=[(i, str(i)) for i in range(1, 6)], null=True, blank=True)
    
    # Champ pour stocker des données supplémentaires (au format JSON)
    extra_data = models.JSONField(_("Données supplémentaires"), default=dict, blank=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Feedback d'événement")
        verbose_name_plural = _("Feedbacks d'événements")
        ordering = ['-submitted_at']
        unique_together = ['event', 'submitted_by']  # Un seul feedback par utilisateur et par événement
    
    def __str__(self):
        return f"{self.submitted_by.get_full_name() or self.submitted_by.username} - {self.event.title} ({self.submitted_at.strftime('%d/%m/%Y')})"
    
    @property
    def average_rating(self):
        """Calcule la note moyenne de toutes les évaluations numériques."""
        ratings = [
            self.overall_satisfaction,
            self.organization_rating,
            self.content_quality,
            self.location_rating
        ]
        
        # Ajouter les évaluations optionnelles si elles sont renseignées
        if self.value_for_money:
            ratings.append(self.value_for_money)
        if self.competition_fairness:
            ratings.append(self.competition_fairness)
        if self.instructor_knowledge:
            ratings.append(self.instructor_knowledge)
        if self.material_usefulness:
            ratings.append(self.material_usefulness)
        if self.exam_difficulty:
            ratings.append(self.exam_difficulty)
        
        return sum(ratings) / len(ratings) if ratings else 0


