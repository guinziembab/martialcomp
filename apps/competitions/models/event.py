# -*- coding: utf-8 -*-
import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from apps.organizations.models import Organization
from . import Club
from . import Practitioner


# ============================================================================
# CHOIX POUR LES ÉVÉNEMENTS RÉCURRENTS
# ============================================================================

class EventFormat(models.TextChoices):
    """Format de l'événement"""
    IN_PERSON = 'in_person', _('En présentiel')
    ONLINE = 'online', _('En ligne (visio)')
    HYBRID = 'hybrid', _('Hybride (présentiel + visio)')


class RecurrenceFrequency(models.TextChoices):
    """Fréquence de récurrence"""
    DAILY = 'daily', _('Quotidien')
    WEEKLY = 'weekly', _('Hebdomadaire')
    BIWEEKLY = 'biweekly', _('Toutes les 2 semaines')
    MONTHLY = 'monthly', _('Mensuel')
    YEARLY = 'yearly', _('Annuel')


class Weekday(models.TextChoices):
    """Jours de la semaine"""
    MONDAY = 'MO', _('Lundi')
    TUESDAY = 'TU', _('Mardi')
    WEDNESDAY = 'WE', _('Mercredi')
    THURSDAY = 'TH', _('Jeudi')
    FRIDAY = 'FR', _('Vendredi')
    SATURDAY = 'SA', _('Samedi')
    SUNDAY = 'SU', _('Dimanche')


class OccurrenceStatus(models.TextChoices):
    """Statut d'une occurrence"""
    PLANNED = 'planned', _('Planifié')
    CONFIRMED = 'confirmed', _('Confirmé')
    IN_PROGRESS = 'in_progress', _('En cours')
    COMPLETED = 'completed', _('Terminé')
    CANCELLED = 'cancelled', _('Annulé')
    POSTPONED = 'postponed', _('Reporté')


class AttendanceStatus(models.TextChoices):
    """Statut de présence"""
    REGISTERED = 'registered', _('Inscrit')
    CONFIRMED = 'confirmed', _('Confirmé')
    PRESENT = 'present', _('Présent')
    ABSENT = 'absent', _('Absent')
    EXCUSED = 'excused', _('Excusé')
    LATE = 'late', _('En retard')


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

    # =========================================================================
    # CHAMPS DE RÉCURRENCE
    # =========================================================================
    is_recurring = models.BooleanField(_("Événement récurrent"), default=False)
    recurrence_frequency = models.CharField(
        _("Fréquence de récurrence"),
        max_length=20,
        choices=RecurrenceFrequency.choices,
        null=True,
        blank=True
    )
    recurrence_interval = models.PositiveSmallIntegerField(
        _("Intervalle de récurrence"),
        default=1,
        help_text=_("Ex: tous les 2 jours, toutes les 3 semaines...")
    )
    recurrence_days = models.JSONField(
        _("Jours de récurrence"),
        null=True,
        blank=True,
        help_text=_("Liste des jours: ['MO', 'WE', 'FR']")
    )
    recurrence_day_of_month = models.PositiveSmallIntegerField(
        _("Jour du mois"),
        null=True,
        blank=True,
        help_text=_("Pour récurrence mensuelle: 1-31")
    )
    recurrence_week_of_month = models.SmallIntegerField(
        _("Semaine du mois"),
        null=True,
        blank=True,
        help_text=_("1=première, 2=deuxième, -1=dernière")
    )
    recurrence_end_type = models.CharField(
        _("Type de fin de récurrence"),
        max_length=20,
        choices=[
            ('never', _('Jamais')),
            ('after', _('Après N occurrences')),
            ('on_date', _('À une date précise')),
        ],
        default='never'
    )
    recurrence_end_after = models.PositiveIntegerField(
        _("Nombre d'occurrences"),
        null=True,
        blank=True,
        help_text=_("Fin après N occurrences")
    )
    recurrence_end_date = models.DateField(
        _("Date de fin de récurrence"),
        null=True,
        blank=True
    )
    recurrence_rule = models.TextField(
        _("Règle RRULE iCalendar"),
        blank=True,
        help_text=_("Règle RRULE générée automatiquement")
    )

    # =========================================================================
    # CHAMPS VISIO / EN LIGNE
    # =========================================================================
    event_format = models.CharField(
        _("Format de l'événement"),
        max_length=20,
        choices=EventFormat.choices,
        default=EventFormat.IN_PERSON
    )
    online_url = models.URLField(
        _("URL de la visioconférence"),
        max_length=500,
        blank=True
    )
    online_platform = models.CharField(
        _("Plateforme"),
        max_length=50,
        blank=True,
        help_text=_("Ex: Zoom, Teams, Google Meet...")
    )
    online_meeting_id = models.CharField(
        _("ID de réunion"),
        max_length=100,
        blank=True
    )
    online_password = models.CharField(
        _("Mot de passe de la réunion"),
        max_length=100,
        blank=True
    )

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
        app_label = 'competitions'
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

    # =========================================================================
    # MÉTHODES DE RÉCURRENCE
    # =========================================================================

    def generate_rrule(self):
        """Génère une règle RRULE iCalendar à partir des paramètres."""
        if not self.is_recurring or not self.recurrence_frequency:
            self.recurrence_rule = ''
            return ''

        freq_map = {
            'daily': 'DAILY',
            'weekly': 'WEEKLY',
            'biweekly': 'WEEKLY',
            'monthly': 'MONTHLY',
            'yearly': 'YEARLY',
        }

        parts = [f"FREQ={freq_map.get(self.recurrence_frequency, 'WEEKLY')}"]

        interval = self.recurrence_interval or 1
        if self.recurrence_frequency == 'biweekly':
            interval = 2
        if interval > 1:
            parts.append(f"INTERVAL={interval}")

        if self.recurrence_frequency in ['weekly', 'biweekly'] and self.recurrence_days:
            days = ','.join(self.recurrence_days)
            parts.append(f"BYDAY={days}")

        if self.recurrence_frequency == 'monthly':
            if self.recurrence_week_of_month and self.recurrence_days:
                week = self.recurrence_week_of_month
                day = self.recurrence_days[0] if self.recurrence_days else 'MO'
                parts.append(f"BYDAY={week}{day}")
            elif self.recurrence_day_of_month:
                parts.append(f"BYMONTHDAY={self.recurrence_day_of_month}")

        if self.recurrence_end_type == 'after' and self.recurrence_end_after:
            parts.append(f"COUNT={self.recurrence_end_after}")
        elif self.recurrence_end_type == 'on_date' and self.recurrence_end_date:
            end_date = self.recurrence_end_date.strftime('%Y%m%d')
            parts.append(f"UNTIL={end_date}")

        self.recurrence_rule = ';'.join(parts)
        return self.recurrence_rule

    def generate_occurrences(self, months_ahead=6, save=True):
        """Génère les occurrences pour les N prochains mois."""
        if not self.is_recurring:
            return []

        try:
            from dateutil.rrule import rrulestr
            from dateutil.relativedelta import relativedelta
            from datetime import datetime as dt_datetime
        except ImportError:
            return self._generate_occurrences_simple(months_ahead, save)

        if not self.recurrence_rule:
            self.generate_rrule()
            if save:
                self.save(update_fields=['recurrence_rule'])

        if not self.recurrence_rule:
            return []

        start_dt = dt_datetime.combine(
            self.start_date,
            self.start_time or dt_datetime.min.time()
        )

        end_gen = timezone.now() + relativedelta(months=months_ahead)

        if self.start_time and self.end_time:
            duration = dt_datetime.combine(dt_datetime.min, self.end_time) - dt_datetime.combine(dt_datetime.min, self.start_time)
        else:
            duration = timedelta(hours=1)

        try:
            rrule_full = f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}\nRRULE:{self.recurrence_rule}"
            rule = rrulestr(rrule_full)
            dates = list(rule.between(timezone.now(), end_gen, inc=True))
        except Exception:
            return self._generate_occurrences_simple(months_ahead, save)

        occurrences = []

        for occ_date in dates:
            existing = self.occurrences.filter(start_datetime__date=occ_date.date()).first()

            if existing:
                occurrences.append(existing)
                continue

            end_dt = occ_date + duration

            occurrence = EventOccurrence(
                event=self,
                start_datetime=occ_date,
                end_datetime=end_dt,
                status=OccurrenceStatus.PLANNED
            )

            if save:
                occurrence.save()

            occurrences.append(occurrence)

        return occurrences

    def _generate_occurrences_simple(self, months_ahead=6, save=True):
        """Génération simplifiée sans python-dateutil."""
        from datetime import datetime as dt_datetime
        from dateutil.relativedelta import relativedelta

        if not self.is_recurring or not self.recurrence_frequency:
            return []

        occurrences = []
        today = timezone.now().date()
        end_gen = today + relativedelta(months=months_ahead)

        if self.start_time and self.end_time:
            duration = dt_datetime.combine(dt_datetime.min, self.end_time) - dt_datetime.combine(dt_datetime.min, self.start_time)
        else:
            duration = timedelta(hours=1)

        day_map = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
        current_date = max(self.start_date, today)

        if self.recurrence_frequency == 'daily':
            interval_days = self.recurrence_interval or 1
        elif self.recurrence_frequency in ['weekly', 'biweekly']:
            interval_days = 7 * (2 if self.recurrence_frequency == 'biweekly' else (self.recurrence_interval or 1))
        else:
            interval_days = 30

        if self.recurrence_frequency in ['weekly', 'biweekly'] and self.recurrence_days:
            week_start = current_date - timedelta(days=current_date.weekday())

            while week_start <= end_gen:
                for day_code in self.recurrence_days:
                    day_offset = day_map.get(day_code, 0)
                    occ_date = week_start + timedelta(days=day_offset)

                    if occ_date >= today and occ_date <= end_gen:
                        if (self.recurrence_end_type == 'after' and
                            self.recurrence_end_after and
                            len(occurrences) >= self.recurrence_end_after):
                            break

                        if (self.recurrence_end_type == 'on_date' and
                            self.recurrence_end_date and
                            occ_date > self.recurrence_end_date):
                            break

                        existing = self.occurrences.filter(start_datetime__date=occ_date).first()

                        if existing:
                            occurrences.append(existing)
                        else:
                            start_dt = dt_datetime.combine(occ_date, self.start_time or dt_datetime.min.time())
                            if timezone.is_naive(start_dt):
                                start_dt = timezone.make_aware(start_dt)

                            occurrence = EventOccurrence(
                                event=self,
                                start_datetime=start_dt,
                                end_datetime=start_dt + duration,
                                status=OccurrenceStatus.PLANNED
                            )
                            if save:
                                occurrence.save()
                            occurrences.append(occurrence)

                week_start += timedelta(days=interval_days)
        else:
            while current_date <= end_gen:
                if (self.recurrence_end_type == 'after' and
                    self.recurrence_end_after and
                    len(occurrences) >= self.recurrence_end_after):
                    break

                if (self.recurrence_end_type == 'on_date' and
                    self.recurrence_end_date and
                    current_date > self.recurrence_end_date):
                    break

                existing = self.occurrences.filter(start_datetime__date=current_date).first()

                if existing:
                    occurrences.append(existing)
                else:
                    start_dt = dt_datetime.combine(current_date, self.start_time or dt_datetime.min.time())
                    if timezone.is_naive(start_dt):
                        start_dt = timezone.make_aware(start_dt)

                    occurrence = EventOccurrence(
                        event=self,
                        start_datetime=start_dt,
                        end_datetime=start_dt + duration,
                        status=OccurrenceStatus.PLANNED
                    )
                    if save:
                        occurrence.save()
                    occurrences.append(occurrence)

                current_date += timedelta(days=interval_days)

        return occurrences

    def get_next_occurrence(self):
        """Retourne la prochaine occurrence à venir."""
        return self.occurrences.filter(
            start_datetime__gte=timezone.now(),
            status__in=[OccurrenceStatus.PLANNED, OccurrenceStatus.CONFIRMED]
        ).order_by('start_datetime').first()

    def get_upcoming_occurrences(self, limit=10):
        """Retourne les prochaines occurrences."""
        return self.occurrences.filter(
            start_datetime__gte=timezone.now()
        ).exclude(
            status=OccurrenceStatus.CANCELLED
        ).order_by('start_datetime')[:limit]

    @property
    def is_online(self):
        """Vérifie si événement est en ligne."""
        return self.event_format in [EventFormat.ONLINE, EventFormat.HYBRID]

    @property
    def is_hybrid(self):
        """Vérifie si événement est hybride."""
        return self.event_format == EventFormat.HYBRID


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

    # User optionnel pour permettre les inscriptions publiques (guests)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='event_participations',
        verbose_name=_("Utilisateur"),
        null=True,
        blank=True
    )

    # Lien vers le pratiquant (pour inscription par club manager)
    practitioner = models.ForeignKey(
        Practitioner,
        on_delete=models.CASCADE,
        related_name='event_participations',
        verbose_name=_("Pratiquant"),
        null=True,
        blank=True
    )

    # Rôle du participant
    role = models.CharField(
        _("Rôle"),
        max_length=30,
        default='participant',
        blank=True
    )

    # Champs pour les inscriptions publiques (guests sans compte)
    is_guest = models.BooleanField(_("Invité (sans compte)"), default=False)
    guest_first_name = models.CharField(_("Prénom"), max_length=100, blank=True)
    guest_last_name = models.CharField(_("Nom"), max_length=100, blank=True)
    guest_email = models.EmailField(_("Email"), blank=True)
    guest_phone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    guest_club = models.CharField(_("Club/Organisation"), max_length=200, blank=True)
    guest_grade = models.CharField(_("Grade/Niveau"), max_length=100, blank=True)

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
        app_label = 'competitions'
        verbose_name = _("Participant à l'événement")
        verbose_name_plural = _("Participants aux événements")
        ordering = ['event', 'registered_at']
    def __str__(self):
        if self.user:
            return f"{self.user.get_full_name()} - {self.event.title}"
        return f"{self.guest_first_name} {self.guest_last_name} (invité) - {self.event.title}"

    @property
    def display_name(self):
        """Retourne le nom à afficher selon le type de participant."""
        if self.user:
            return self.user.get_full_name() or self.user.username
        return f"{self.guest_first_name} {self.guest_last_name}".strip() or "Invité"

    @property
    def display_email(self):
        """Retourne l'email à afficher selon le type de participant."""
        if self.user:
            return self.user.email
        return self.guest_email


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
        app_label = 'competitions'
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
        app_label = 'competitions'
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
        app_label = 'competitions'
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
        app_label = 'competitions'
        verbose_name = _("Réponse à une question")
        verbose_name_plural = _("Réponses aux questions")
    
    def __str__(self):
        return f"Réponse à {self.question}"


# Note: EventReminder class is now defined in event_planning.py to avoid model conflicts


# ============================================================================
# MODÈLES POUR LES ÉVÉNEMENTS RÉCURRENTS
# ============================================================================

class EventOccurrence(models.Model):
    """
    Instance spécifique d'un événement récurrent.
    Chaque occurrence représente une date/heure particulière d'un événement récurrent.
    """

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='occurrences',
        verbose_name=_("Événement parent")
    )

    # Dates/heures de l'occurrence
    start_datetime = models.DateTimeField(_("Date et heure de début"))
    end_datetime = models.DateTimeField(_("Date et heure de fin"))

    # Statut de l'occurrence
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=OccurrenceStatus.choices,
        default=OccurrenceStatus.PLANNED
    )

    # Modifications spécifiques à cette occurrence
    is_exception = models.BooleanField(
        _("Exception"),
        default=False,
        help_text=_("Cette occurrence a été modifiée individuellement")
    )
    override_location = models.CharField(
        _("Lieu (remplacement)"),
        max_length=255,
        blank=True
    )
    override_online_url = models.URLField(
        _("URL visio (remplacement)"),
        max_length=500,
        blank=True
    )
    override_max_participants = models.PositiveIntegerField(
        _("Max participants (remplacement)"),
        null=True,
        blank=True
    )

    # Notes et annulation
    notes = models.TextField(_("Notes"), blank=True)
    cancellation_reason = models.TextField(_("Raison d'annulation"), blank=True)
    cancelled_at = models.DateTimeField(_("Annulé le"), null=True, blank=True)
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_occurrences',
        verbose_name=_("Annulé par")
    )

    # Statistiques
    attendees_count = models.PositiveIntegerField(_("Nombre de présents"), default=0)

    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Occurrence d'événement")
        verbose_name_plural = _("Occurrences d'événements")
        ordering = ['start_datetime']
        indexes = [
            models.Index(fields=['event', 'start_datetime']),
            models.Index(fields=['status']),
            models.Index(fields=['start_datetime']),
        ]

    def __str__(self):
        return f"{self.event.title} - {self.start_datetime.strftime('%d/%m/%Y %H:%M')}"

    @property
    def is_past(self):
        """Vérifie si l'occurrence est passée."""
        return self.end_datetime < timezone.now()

    @property
    def is_upcoming(self):
        """Vérifie si l'occurrence est à venir."""
        return self.start_datetime > timezone.now()

    @property
    def is_ongoing(self):
        """Vérifie si l'occurrence est en cours."""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime

    @property
    def is_cancelled(self):
        """Vérifie si l'occurrence est annulée."""
        return self.status == OccurrenceStatus.CANCELLED

    @property
    def effective_location(self):
        """Retourne le lieu effectif (override ou parent)."""
        return self.override_location or self.event.location

    @property
    def effective_online_url(self):
        """Retourne l'URL visio effective (override ou parent)."""
        return self.override_online_url or self.event.online_url

    @property
    def effective_max_participants(self):
        """Retourne le max participants effectif (override ou parent)."""
        return self.override_max_participants or self.event.max_participants

    @property
    def duration(self):
        """Retourne la durée de l'occurrence."""
        return self.end_datetime - self.start_datetime

    def cancel(self, reason='', cancelled_by=None):
        """Annule cette occurrence."""
        self.status = OccurrenceStatus.CANCELLED
        self.cancellation_reason = reason
        self.cancelled_at = timezone.now()
        self.cancelled_by = cancelled_by
        self.save()

    def confirm(self):
        """Confirme cette occurrence."""
        if self.status == OccurrenceStatus.PLANNED:
            self.status = OccurrenceStatus.CONFIRMED
            self.save()

    def complete(self):
        """Marque cette occurrence comme terminée."""
        if self.status in [OccurrenceStatus.PLANNED, OccurrenceStatus.CONFIRMED, OccurrenceStatus.IN_PROGRESS]:
            self.status = OccurrenceStatus.COMPLETED
            self.save()

    def update_attendees_count(self):
        """Met à jour le compteur de présents."""
        self.attendees_count = self.attendances.filter(
            status=AttendanceStatus.PRESENT
        ).count()
        self.save(update_fields=['attendees_count'])


class EventOccurrenceAttendance(models.Model):
    """
    Présence d'un participant à une occurrence spécifique.
    Permet de tracker qui était présent à chaque séance d'un cours récurrent.
    """

    occurrence = models.ForeignKey(
        EventOccurrence,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_("Occurrence")
    )
    participant = models.ForeignKey(
        'EventParticipant',
        on_delete=models.CASCADE,
        related_name='occurrence_attendances',
        verbose_name=_("Participant")
    )

    # Statut de présence
    status = models.CharField(
        _("Statut de présence"),
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.REGISTERED
    )

    # Pointage
    check_in_time = models.DateTimeField(_("Heure de pointage"), null=True, blank=True)
    check_in_method = models.CharField(
        _("Méthode de pointage"),
        max_length=20,
        choices=[
            ('manual', _('Manuel')),
            ('qr_code', _('QR Code')),
            ('nfc', _('NFC')),
            ('auto', _('Automatique')),
        ],
        blank=True
    )
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_in_attendances',
        verbose_name=_("Pointé par")
    )

    # Notes
    notes = models.TextField(_("Notes"), blank=True)
    excuse_reason = models.TextField(_("Raison d'excuse"), blank=True)

    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Présence à une occurrence")
        verbose_name_plural = _("Présences aux occurrences")
        ordering = ['occurrence', 'participant']
        unique_together = ['occurrence', 'participant']
        indexes = [
            models.Index(fields=['occurrence', 'status']),
            models.Index(fields=['participant', 'status']),
        ]

    def __str__(self):
        return f"{self.participant.display_name} - {self.occurrence}"

    @property
    def is_present(self):
        """Vérifie si le participant était présent."""
        return self.status == AttendanceStatus.PRESENT

    @property
    def is_absent(self):
        """Vérifie si le participant était absent."""
        return self.status == AttendanceStatus.ABSENT

    @property
    def is_excused(self):
        """Vérifie si le participant était excusé."""
        return self.status == AttendanceStatus.EXCUSED

    def mark_present(self, method='manual', checked_by=None):
        """Marque le participant comme présent."""
        self.status = AttendanceStatus.PRESENT
        self.check_in_time = timezone.now()
        self.check_in_method = method
        self.checked_in_by = checked_by
        self.save()
        self.occurrence.update_attendees_count()

    def mark_absent(self):
        """Marque le participant comme absent."""
        self.status = AttendanceStatus.ABSENT
        self.save()
        self.occurrence.update_attendees_count()

    def mark_excused(self, reason=''):
        """Marque le participant comme excusé."""
        self.status = AttendanceStatus.EXCUSED
        self.excuse_reason = reason
        self.save()
        self.occurrence.update_attendees_count()

    def mark_late(self, method='manual', checked_by=None):
        """Marque le participant comme en retard."""
        self.status = AttendanceStatus.LATE
        self.check_in_time = timezone.now()
        self.check_in_method = method
        self.checked_in_by = checked_by
        self.save()
        self.occurrence.update_attendees_count()
