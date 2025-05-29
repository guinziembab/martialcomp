# -*- coding: utf-8 -*-
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from organizations.models import Organization
from competitions.models.club import Club
from competitions.models.practitioners import Practitioner


class Event(models.Model):
    """Modèle pour les événements."""
    
    TYPE_CHOICES = [
        ('competition', _('Compétition')),
        ('training', _('Entraînement')),
        ('seminar', _('Séminaire')),
        ('exam', _('Examen')),
        ('meeting', _('Réunion')),
        ('social', _('Social')),
        ('other', _('Autre')),
    ]
    
    VISIBILITY_CHOICES = [
        ('public', _('Public')),
        ('members', _('Membres uniquement')),
        ('private', _('Privé')),
    ]
    
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"))
    event_type = models.CharField(_("Type d'événement"), max_length=20, choices=TYPE_CHOICES)
    
    # Organisation
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name=_("Organisation")
    )
    
    # Dates et heures
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"))
    start_time = models.TimeField(_("Heure de début"), null=True, blank=True)
    end_time = models.TimeField(_("Heure de fin"), null=True, blank=True)
    all_day = models.BooleanField(_("Toute la journée"), default=False)
    
    # Lieu
    location = models.CharField(_("Lieu"), max_length=200, blank=True)
    address = models.CharField(_("Adresse"), max_length=300, blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=20, blank=True)
    
    # Paramètres
    visibility = models.CharField(_("Visibilité"), max_length=20, choices=VISIBILITY_CHOICES, default='members')
    is_public = models.BooleanField(_("Public"), default=False)
    max_participants = models.PositiveIntegerField(_("Nombre max de participants"), null=True, blank=True)
    registration_required = models.BooleanField(_("Inscription requise"), default=False)
    registration_deadline = models.DateTimeField(_("Date limite d'inscription"), null=True, blank=True)
    
    # Détails
    price = models.DecimalField(_("Prix"), max_digits=10, decimal_places=2, default=0)
    contact_person = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='organized_events',
        verbose_name=_("Personne de contact")
    )
    contact_email = models.EmailField(_("Email de contact"), blank=True)
    contact_phone = models.CharField(_("Téléphone de contact"), max_length=20, blank=True)
    
    # Attachements et média
    image = models.ImageField(_("Image"), upload_to='events/', null=True, blank=True)
    documents = models.JSONField(_("Documents"), default=list, blank=True)
    
    # Métadonnées
    is_cancelled = models.BooleanField(_("Annulé"), default=False)
    cancellation_reason = models.TextField(_("Raison d'annulation"), blank=True)
    is_archived = models.BooleanField(_("Archivé"), default=False)
    archived_at = models.DateTimeField(_("Archivé le"), null=True, blank=True)
    
    # Personnalisation
    color = models.CharField(_("Couleur"), max_length=7, default='#007bff')
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events',
        verbose_name=_("Créé par")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Événement")
        verbose_name_plural = _("Événements")
        ordering = ['start_date', 'start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
    
    @property
    def is_upcoming(self):
        """Vérifie si l'événement est à venir."""
        return self.start_date >= timezone.now().date()
    
    @property
    def is_past(self):
        """Vérifie si l'événement est passé."""
        return self.end_date < timezone.now().date()
    
    @property
    def is_ongoing(self):
        """Vérifie si l'événement est en cours."""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    @property
    def participants_count(self):
        """Nombre de participants inscrits."""
        return self.participants.count()
    
    @property
    def is_full(self):
        """Vérifie si l'événement est complet."""
        if self.max_participants:
            return self.participants_count >= self.max_participants
        return False
    
    @property
    def is_nearly_full(self):
        """Vérifie si l'événement est presque complet (80% de capacité)."""
        if self.max_participants:
            return self.participants_count >= (self.max_participants * 0.8)
        return False
    
    def is_user_registered(self, user):
        """Vérifie si un utilisateur est inscrit à cet événement."""
        if not user.is_authenticated:
            return False
        return self.participants.filter(user=user).exists()


class EventParticipant(models.Model):
    """Participants à un événement."""
    
    STATUS_CHOICES = [
        ('registered', _('Inscrit')),
        ('confirmed', _('Confirmé')),
        ('waitlist', _('Liste en attente')),
        ('cancelled', _('Annulé')),
    ]
    
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_("Événement")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_participations',
        verbose_name=_("Utilisateur")
    )
    
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='registered')
    
    # Détails de participation
    registered_at = models.DateTimeField(_("Inscrit le"), auto_now_add=True)
    confirmed_at = models.DateTimeField(_("Confirmé le"), null=True, blank=True)
    attended = models.BooleanField(_("A participé"), default=False)
    
    # Paiement
    payment_status = models.CharField(
        _("Statut de paiement"),
        max_length=20,
        choices=[
            ('pending', _('En attente')),
            ('paid', _('Payé')),
            ('refunded', _('Remboursé')),
        ],
        default='pending'
    )
    payment_date = models.DateTimeField(_("Date de paiement"), null=True, blank=True)
    payment_amount = models.DecimalField(_("Montant payé"), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Notes
    notes = models.TextField(_("Notes"), blank=True)
    
    class Meta:
        verbose_name = _("Participant à l'événement")
        verbose_name_plural = _("Participants aux événements")
        ordering = ['event', 'registered_at']
        unique_together = [['event', 'user']]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.event.title}"


class EventSurvey(models.Model):
    """Modèle pour les sondages liés aux événements."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='surveys',
        verbose_name=_("Événement")
    )
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    
    # Contrôle d'accès
    is_anonymous = models.BooleanField(_("Anonyme"), default=False)
    is_active = models.BooleanField(_("Actif"), default=True)
    
    # Timing
    start_date = models.DateTimeField(_("Date de début"), null=True, blank=True)
    end_date = models.DateTimeField(_("Date de fin"), null=True, blank=True)
    
    # Paramètres
    is_required = models.BooleanField(_("Obligatoire"), default=False)
    allow_multiple_submissions = models.BooleanField(_("Autoriser plusieurs soumissions"), default=False)
    
    # Métadonnées
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_surveys',
        verbose_name=_("Créé par")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Sondage d'événement")
        verbose_name_plural = _("Sondages d'événements")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.event.title}"
    
    @property
    def is_open(self):
        """Vérifie si le sondage est actuellement ouvert."""
        now = timezone.now()
        if self.start_date and self.end_date:
            return self.start_date <= now <= self.end_date
        if self.start_date:
            return self.start_date <= now
        if self.end_date:
            return now <= self.end_date
        return self.is_active


class SurveyQuestion(models.Model):
    """Questions du sondage."""
    
    TYPE_CHOICES = [
        ('text', _('Texte')),
        ('textarea', _('Zone de texte')),
        ('single_choice', _('Choix unique')),
        ('multiple_choice', _('Choix multiple')),
        ('rating', _('Notation')),
        ('scale', _('Échelle')),
        ('date', _('Date')),
    ]
    
    survey = models.ForeignKey(
        EventSurvey,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_("Sondage")
    )
    question_text = models.CharField(_("Question"), max_length=500)
    question_type = models.CharField(_("Type de question"), max_length=20, choices=TYPE_CHOICES)
    is_required = models.BooleanField(_("Obligatoire"), default=False)
    help_text = models.CharField(_("Texte d'aide"), max_length=500, blank=True)
    
    # Options pour les questions à choix
    choices = models.JSONField(_("Choix"), default=list, blank=True)
    
    # Options pour les notations et échelles
    min_value = models.IntegerField(_("Valeur minimale"), null=True, blank=True)
    max_value = models.IntegerField(_("Valeur maximale"), null=True, blank=True)
    
    order = models.PositiveIntegerField(_("Ordre"), default=0)
    
    class Meta:
        verbose_name = _("Question de sondage")
        verbose_name_plural = _("Questions de sondage")
        ordering = ['survey', 'order']
    
    def __str__(self):
        return f"{self.question_text[:50]}{'...' if len(self.question_text) > 50 else ''}"


class SurveyResponse(models.Model):
    """Réponses aux sondages."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(
        EventSurvey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_("Sondage")
    )
    participant = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_responses',
        verbose_name=_("Participant")
    )
    
    # Pour les réponses anonymes ou identifiées sans compte
    respondent_name = models.CharField(_("Nom du répondant"), max_length=200, blank=True)
    respondent_email = models.EmailField(_("Email du répondant"), blank=True)
    
    submitted_at = models.DateTimeField(_("Soumis le"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_("Adresse IP"), blank=True, null=True)
    
    # Métadonnées
    completion_time = models.DurationField(_("Temps de complétion"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Réponse au sondage")
        verbose_name_plural = _("Réponses aux sondages")
        ordering = ['-submitted_at']
    
    def __str__(self):
        if self.participant:
            return f"Réponse de {self.participant.get_full_name()} - {self.survey.title}"
        elif self.respondent_name:
            return f"Réponse de {self.respondent_name} - {self.survey.title}"
        else:
            return f"Réponse anonyme - {self.survey.title}"


class QuestionResponse(models.Model):
    """Réponses individuelles aux questions du sondage."""
    
    response = models.ForeignKey(
        SurveyResponse,
        on_delete=models.CASCADE,
        related_name='question_responses',
        verbose_name=_("Réponse au sondage")
    )
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_("Question")
    )
    
    # Différents types de réponses
    text_response = models.TextField(_("Réponse texte"), blank=True)
    choice_response = models.JSONField(_("Réponse à choix"), default=list, blank=True)
    numeric_response = models.IntegerField(_("Réponse numérique"), null=True, blank=True)
    date_response = models.DateField(_("Réponse date"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Réponse à une question")
        verbose_name_plural = _("Réponses aux questions")
    
    def __str__(self):
        return f"Réponse à {self.question}"


# Note: EventReminder class is now defined in event_planning.py to avoid model conflicts