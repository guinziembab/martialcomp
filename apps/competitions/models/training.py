# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class TrainingSlot(models.Model):
    """Créneaux d'entraÃ®nement récurrents."""
    
    LEVEL_CHOICES = [
        ('beginner', _('Débutant')),
        ('intermediate', _('Intermédiaire')),
        ('advanced', _('Avancé')),
        ('all', _('Tous niveaux')),
    ]
    
    DAY_CHOICES = [
        (0, _('Lundi')),
        (1, _('Mardi')),
        (2, _('Mercredi')),
        (3, _('Jeudi')),
        (4, _('Vendredi')),
        (5, _('Samedi')),
        (6, _('Dimanche')),
    ]
    
    club = models.ForeignKey(
        'competitions.Club',
        on_delete=models.CASCADE,
        related_name='training_slots',
        verbose_name=_("Club")
    )
    
    discipline = models.ForeignKey(
        'competitions.Discipline',
        on_delete=models.CASCADE,
        related_name='training_slots',
        verbose_name=_("Discipline")
    )
    
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    day_of_week = models.IntegerField(_("Jour de la semaine"), choices=DAY_CHOICES)
    start_time = models.TimeField(_("Heure de début"))
    end_time = models.TimeField(_("Heure de fin"))
    
    level = models.CharField(_("Niveau"), max_length=20, choices=LEVEL_CHOICES, default='all')
    
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_slots',
        verbose_name=_("Instructeur")
    )
    
    location = models.CharField(_("Lieu"), max_length=200, blank=True)
    max_participants = models.PositiveIntegerField(_("Nombre max de participants"), default=20)
    
    is_active = models.BooleanField(_("Actif"), default=True)
    
    # Période de validité
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Créneau d'entraÃ®nement")
        verbose_name_plural = _("Créneaux d'entraÃ®nement")
        ordering = ['day_of_week', 'start_time']
        unique_together = [['club', 'day_of_week', 'start_time', 'location']]
    
    def __str__(self):
        return f"{self.name} - {self.get_day_of_week_display()} {self.start_time}"
    
    @property
    def duration(self):
        """Durée de l'entraÃ®nement en minutes."""
        start = timezone.datetime.combine(timezone.now().date(), self.start_time)
        end = timezone.datetime.combine(timezone.now().date(), self.end_time)
        return (end - start).seconds // 60


class TrainingSession(models.Model):
    """Session d'entraÃ®nement spécifique."""
    
    training_slot = models.ForeignKey(
        TrainingSlot,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_("Créneau")
    )
    
    date = models.DateField(_("Date"))
    
    # Peut Ãªtre différent du créneau habituel
    actual_instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='training_sessions',
        verbose_name=_("Instructeur réel")
    )
    
    # Modifications éventuelles
    actual_start_time = models.TimeField(_("Heure de début réelle"), null=True, blank=True)
    actual_end_time = models.TimeField(_("Heure de fin réelle"), null=True, blank=True)
    actual_location = models.CharField(_("Lieu réel"), max_length=200, blank=True)
    
    is_cancelled = models.BooleanField(_("Annulé"), default=False)
    cancellation_reason = models.TextField(_("Raison d'annulation"), blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Session d'entraÃ®nement")
        verbose_name_plural = _("Sessions d'entraÃ®nement")
        ordering = ['-date', 'training_slot__start_time']
        unique_together = [['training_slot', 'date']]
    
    def __str__(self):
        return f"{self.training_slot.name} - {self.date}"
    
    @property
    def instructor(self):
        """Retourne l'instructeur réel ou celui du créneau."""
        return self.actual_instructor or self.training_slot.instructor
    
    @property
    def start_time(self):
        """Retourne l'heure de début réelle ou celle du créneau."""
        return self.actual_start_time or self.training_slot.start_time
    
    @property
    def end_time(self):
        """Retourne l'heure de fin réelle ou celle du créneau."""
        return self.actual_end_time or self.training_slot.end_time
    
    @property
    def location(self):
        """Retourne le lieu réel ou celui du créneau."""
        return self.actual_location or self.training_slot.location


class TrainingReservation(models.Model):
    """Réservation d'un pratiquant pour un entraÃ®nement."""
    
    STATUS_CHOICES = [
        ('confirmed', _("Confirmé")),
        ('waitlist', _("Liste en attente")),
        ('cancelled', _("Annulé")),
    ]
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='training_reservations',
        verbose_name=_("Pratiquant")
    )
    
    training_slot = models.ForeignKey(
        TrainingSlot,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name=_("Créneau")
    )
    
    date = models.DateField(_("Date"))
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='confirmed')
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Réservation d'entraÃ®nement")
        verbose_name_plural = _("Réservations d'entraÃ®nement")
        ordering = ['-date', 'training_slot__start_time']
        unique_together = [['practitioner', 'training_slot', 'date']]
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.training_slot.name} - {self.date}"


class Attendance(models.Model):
    """Présence aux sessions d'entraÃ®nement."""
    
    STATUS_CHOICES = [
        ('present', _('Présent')),
        ('absent', _('Absent')),
        ('excused', _('Excusé')),
        ('late', _('En retard')),
    ]
    
    session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_("Session")
    )
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name=_("Pratiquant")
    )
    
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES)
    
    arrival_time = models.TimeField(_("Heure d'arrivée"), null=True, blank=True)
    departure_time = models.TimeField(_("Heure de départ"), null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recorded_attendances',
        verbose_name=_("Enregistré par")
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Présence")
        verbose_name_plural = _("Présences")
        ordering = ['-session__date', 'practitioner__last_name']
        unique_together = [['session', 'practitioner']]
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.session} - {self.get_status_display()}"


class TrainingProgram(models.Model):
    """Programme d'entraÃ®nement structuré."""
    
    LEVEL_CHOICES = [
        ('beginner', _('Débutant')),
        ('intermediate', _('Intermédiaire')),
        ('advanced', _('Avancé')),
    ]
    
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"))
    
    disciplines = models.ManyToManyField(
        'competitions.Discipline',
        related_name='training_programs',
        verbose_name=_("Disciplines")
    )
    
    level = models.CharField(_("Niveau"), max_length=20, choices=LEVEL_CHOICES)
    
    duration_weeks = models.PositiveIntegerField(_("Durée (semaines)"))
    sessions_per_week = models.PositiveIntegerField(_("Sessions par semaine"))
    
    objectives = models.TextField(_("Objectifs"))
    prerequisites = models.TextField(_("Prérequis"), blank=True)
    
    is_active = models.BooleanField(_("Actif"), default=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_training_programs',
        verbose_name=_("Créé par")
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Programme d'entraÃ®nement")
        verbose_name_plural = _("Programmes d'entraÃ®nement")
        ordering = ['level', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.get_level_display()}"


class TrainingModule(models.Model):
    """Module d'un programme d'entraÃ®nement."""
    
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name=_("Programme")
    )
    
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"))
    
    order = models.PositiveIntegerField(_("Ordre"))
    duration_weeks = models.PositiveIntegerField(_("Durée (semaines)"))
    
    objectives = models.TextField(_("Objectifs"))
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Module de programme")
        verbose_name_plural = _("Modules de programme")
        ordering = ['program', 'order']
    
    def __str__(self):
        return f"{self.program.name} - {self.name}"


class TrainingExercise(models.Model):
    """Exercice d'un module d'entraÃ®nement."""
    
    module = models.ForeignKey(
        TrainingModule,
        on_delete=models.CASCADE,
        related_name='exercises',
        verbose_name=_("Module")
    )
    
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"))
    
    order = models.PositiveIntegerField(_("Ordre"))
    
    duration_minutes = models.PositiveIntegerField(_("Durée (minutes)"))
    repetitions = models.PositiveIntegerField(_("Répétitions"), null=True, blank=True)
    sets = models.PositiveIntegerField(_("Séries"), null=True, blank=True)
    
    video_url = models.URLField(_("URL vidéo"), blank=True)
    image = models.ImageField(_("Image"), upload_to='training/exercises/', null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Exercice")
        verbose_name_plural = _("Exercices")
        ordering = ['module', 'order']
    
    def __str__(self):
        return f"{self.module.name} - {self.name}"


class PractitionerProgress(models.Model):
    """Progression d'un pratiquant dans un exercice."""
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='exercise_progress',
        verbose_name=_("Pratiquant")
    )
    
    exercise = models.ForeignKey(
        TrainingExercise,
        on_delete=models.CASCADE,
        related_name='practitioner_progress',
        verbose_name=_("Exercice")
    )
    
    completed = models.BooleanField(_("Complété"), default=False)
    completed_date = models.DateTimeField(_("Date de complétion"), null=True, blank=True)
    
    performance_rating = models.IntegerField(
        _("Note de performance"),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Progression d'exercice")
        verbose_name_plural = _("Progressions d'exercices")
        unique_together = [['practitioner', 'exercise']]
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.exercise.name}"


class ProgramEnrollment(models.Model):
    """Inscription d'un pratiquant Ã  un programme d'entraÃ®nement"""
    
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('paused', _('En pause')),
        ('completed', _('Terminé')),
        ('cancelled', _('Annulé'))
    ]
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='program_enrollments',
        verbose_name=_("Pratiquant")
    )
    
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name=_("Programme")
    )
    
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"), null=True, blank=True)
    
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    progress = models.FloatField(
        _("Progression"),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )  # 0 Ã  100
    
    notes = models.TextField(_("Notes"), blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Inscription au programme")
        verbose_name_plural = _("Inscriptions aux programmes")
        unique_together = [['practitioner', 'program', 'start_date']]
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.program.name} ({self.get_status_display()})"
    
    def calculate_progress(self):
        """Calcule la progression basée sur les présences et les objectifs atteints"""
        total_modules = self.program.modules.count()
        if total_modules == 0:
            return 0.0
            
        completed_exercises = PractitionerProgress.objects.filter(
            practitioner=self.practitioner,
            exercise__module__program=self.program,
            completed=True
        ).count()
        
        total_exercises = TrainingExercise.objects.filter(
            module__program=self.program
        ).count()
        
        if total_exercises > 0:
            self.progress = (completed_exercises / total_exercises) * 100
            self.save()
        
        return self.progress
    
    def mark_completed(self):
        """Marque l'inscription comme terminée"""
        self.status = 'completed'
        self.end_date = timezone.now().date()
        self.progress = 100.0
        self.save()


class PersonalGoal(models.Model):
    """Objectif personnel d'un pratiquant"""
    
    GOAL_TYPES = [
        ('competition', _('Compétition')),
        ('grade', _('Grade')),
        ('performance', _('Performance')),
        ('attendance', _('Présence')),
        ('skill', _('Compétence')),
        ('fitness', _('Forme physique')),
        ('custom', _('Personnalisé'))
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En cours')),
        ('achieved', _('Atteint')),
        ('failed', _('Non atteint')),
        ('cancelled', _('Annulé'))
    ]
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='personal_goals',
        verbose_name=_("Pratiquant")
    )
    
    goal_type = models.CharField(
        _("Type d'objectif"),
        max_length=20,
        choices=GOAL_TYPES
    )
    
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"))
    
    target_date = models.DateField(_("Date cible"))
    
    # Métriques spécifiques selon le type
    target_value = models.CharField(_("Valeur cible"), max_length=100, blank=True)
    current_value = models.CharField(_("Valeur actuelle"), max_length=100, blank=True)
    
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    achievement_date = models.DateField(_("Date de réalisation"), null=True, blank=True)
    
    notes = models.TextField(_("Notes"), blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Objectif personnel")
        verbose_name_plural = _("Objectifs personnels")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.title}"
    
    def check_achievement(self):
        """Vérifie si l'objectif a été atteint"""
        if self.status in ['achieved', 'failed', 'cancelled']:
            return self.status
            
        # Logique de vérification selon le type d'objectif
        if self.goal_type == 'attendance':
            # Vérifier le taux de présence
            recent_sessions = TrainingSession.objects.filter(
                date__gte=self.created_at.date(),
                training_slot__club=self.practitioner.club
            ).count()
            
            attended_sessions = Attendance.objects.filter(
                practitioner=self.practitioner,
                session__date__gte=self.created_at.date(),
                status='present'
            ).count()
            
            if recent_sessions > 0:
                attendance_rate = (attended_sessions / recent_sessions) * 100
                self.current_value = f"{attendance_rate:.1f}%"
                
                try:
                    target_rate = float(self.target_value.rstrip('%'))
                    if attendance_rate >= target_rate:
                        self.mark_achieved()
                except ValueError:
                    pass
        
        elif self.goal_type == 'grade':
            # Vérifier l'obtention du grade
            current_grade = self.practitioner.practitioner_grades.filter(
                grade__name=self.target_value,
                obtained_date__gte=self.created_at.date()
            ).exists()
            
            if current_grade:
                self.mark_achieved()
        
        self.save()
        return self.status
    
    def mark_achieved(self):
        """Marque l'objectif comme atteint"""
        self.status = 'achieved'
        self.achievement_date = timezone.now().date()
        self.save()
    
    def mark_failed(self):
        """Marque l'objectif comme non atteint"""
        self.status = 'failed'
        self.save()


class AbsenceDeclaration(models.Model):
    """Déclaration d'absence par un pratiquant ou parent."""

    DECLARATION_TYPE_CHOICES = [
        ('absence', _('Absence')),
        ('late', _('Retard')),
        ('early_leave', _('Départ anticipé')),
    ]

    REASON_CATEGORY_CHOICES = [
        ('health', _('Santé/Maladie')),
        ('school', _('École/Travail')),
        ('family', _('Famille')),
        ('vacation', _('Vacances')),
        ('other', _('Autre')),
    ]

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('acknowledged', _('Pris en compte')),
        ('rejected', _('Refusé')),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='absence_declarations',
        verbose_name=_("Pratiquant")
    )

    declaration_type = models.CharField(
        _("Type de déclaration"),
        max_length=20,
        choices=DECLARATION_TYPE_CHOICES,
        default='absence'
    )

    # Date spécifique ou plage de dates
    date = models.DateField(_("Date"))
    date_end = models.DateField(_("Date de fin"), null=True, blank=True)

    # Créneau concerné (optionnel si absence toute la journée)
    training_slot = models.ForeignKey(
        TrainingSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='absence_declarations',
        verbose_name=_("Créneau d'entraînement")
    )

    # Raison
    reason = models.TextField(_("Commentaire"), blank=True)
    reason_category = models.CharField(
        _("Catégorie de raison"),
        max_length=20,
        choices=REASON_CATEGORY_CHOICES,
        null=True,
        blank=True
    )

    # Qui a déclaré (peut être parent ou pratiquant)
    declared_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='declared_absences',
        verbose_name=_("Déclaré par")
    )
    declared_at = models.DateTimeField(_("Déclaré le"), auto_now_add=True)

    # Statut de validation
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Validation par l'instructeur
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_absences',
        verbose_name=_("Validé par")
    )
    acknowledged_at = models.DateTimeField(_("Validé le"), null=True, blank=True)
    instructor_note = models.TextField(_("Note de l'instructeur"), blank=True)

    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Déclaration d'absence")
        verbose_name_plural = _("Déclarations d'absence")
        ordering = ['-date', '-declared_at']

    def __str__(self):
        return f"{self.practitioner.full_name} - {self.get_declaration_type_display()} - {self.date}"

    def acknowledge(self, user, note=''):
        """Valide la déclaration."""
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.instructor_note = note
        self.save()

    def reject(self, user, note=''):
        """Refuse la déclaration."""
        self.status = 'rejected'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.instructor_note = note
        self.save()

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_acknowledged(self):
        return self.status == 'acknowledged'

    @property
    def is_multi_day(self):
        """Vérifie si c'est une absence sur plusieurs jours."""
        return self.date_end is not None and self.date_end > self.date

    def get_dates(self):
        """Retourne la liste des dates concernées."""
        from datetime import timedelta
        if not self.is_multi_day:
            return [self.date]

        dates = []
        current = self.date
        while current <= self.date_end:
            dates.append(current)
            current += timedelta(days=1)
        return dates

