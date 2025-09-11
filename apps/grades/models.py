from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator



class GradeCategory(models.Model):
    """Catégorie de grades (Débutant, Intermédiaire, Avancé, Expert, etc.)."""
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    discipline = models.ForeignKey(
        'competitions.Discipline',
        on_delete=models.CASCADE,
        related_name='grade_categories',
        verbose_name=_("Discipline")
    )
    order = models.PositiveSmallIntegerField(_("Ordre d'affichage"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)

    class Meta:
        app_label = 'grades'
        verbose_name = _("Catégorie de grade")
        verbose_name_plural = _("Catégories de grade")
        ordering = ['discipline', 'order', 'name']
        unique_together = ['name', 'discipline']

    def __str__(self):
        return f"{self.name} ({self.discipline.name})"


class Grade(models.Model):
    """Définition des grades disponibles par discipline."""
    name = models.CharField(_("Nom"), max_length=100)
    discipline = models.ForeignKey(
        'competitions.Discipline',
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name=_("Discipline")
    )
    category = models.ForeignKey(
        GradeCategory,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name=_("Catégorie"),
        null=True,
        blank=True
    )
    color = models.CharField(_("Couleur"), max_length=50, blank=True)
    color_code = models.CharField(_("Code couleur"), max_length=7, blank=True, help_text=_("Code hexadécimal de la couleur (ex: #FFFFFF)"))
    level = models.PositiveSmallIntegerField(_("Niveau"), default=0, help_text=_("Ordre numérique du grade dans la hiérarchie"))
    min_age = models.PositiveSmallIntegerField(_("Ã‚ge minimum"), default=0, help_text=_("Ã‚ge minimum requis pour ce grade"))
    min_time_in_previous_grade = models.PositiveSmallIntegerField(
        _("Temps minimum dans le grade précédent (mois)"), 
        default=0, 
        help_text=_("Temps minimum requis dans le grade précédent (en mois)")
    )
    requirements_text = models.TextField(_("Exigences"), blank=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    is_dan_grade = models.BooleanField(_("Grade dan/dang"), default=False, help_text=_("S'agit-il d'un grade dan/dang (ceinture noire)"))
    order = models.PositiveSmallIntegerField(_("Ordre d'affichage"), default=0)
    
    class Meta:
        verbose_name = _("Grade")
        verbose_name_plural = _("Grades")
        ordering = ['discipline', 'level', 'name']
        unique_together = ['name', 'discipline']

    def __str__(self):
        return f"{self.name} ({self.discipline.name})"
    
    @property
    def is_black_belt(self):
        """Détermine si le grade est une ceinture noire ou équivalent."""
        return self.is_dan_grade or ("noir" in self.name.lower()) or ("dang" in self.name.lower()) or ("dan" in self.name.lower())
    
    @property
    def next_grade(self):
        """Retourne le grade suivant dans la hiérarchie, s'il existe."""
        return Grade.objects.filter(
            discipline=self.discipline,
            level__gt=self.level,
            is_active=True
        ).order_by('level').first()
    
    @property
    def previous_grade(self):
        """Retourne le grade précédent dans la hiérarchie, s'il existe."""
        return Grade.objects.filter(
            discipline=self.discipline,
            level__lt=self.level,
            is_active=True
        ).order_by('-level').first()


class PractitionerGrade(models.Model):
    """Historique des grades obtenus par un pratiquant."""
    practitioner = models.ForeignKey(
        'competitions.Practitioner',  # Ajout des guillemets ici
        on_delete=models.CASCADE, 
        related_name='grade_history',
        verbose_name=_("Pratiquant")
    )
    grade = models.ForeignKey(
        Grade, 
        on_delete=models.CASCADE, 
        related_name='practitioners',
        verbose_name=_("Grade")
    )
    discipline = models.ForeignKey(
        'competitions.Discipline',  # Ajout des guillemets ici aussi si nécessaire
        on_delete=models.CASCADE, 
        related_name='practitioner_grades',
        verbose_name=_("Discipline")
    )
    date_obtained = models.DateField(_("Date d'obtention"), default=timezone.now)
    date_expiry = models.DateField(_("Date d'expiration"), null=True, blank=True)
    awarded_by = models.CharField(_("Décerné par"), max_length=100, blank=True)
    location = models.CharField(_("Lieu d'obtention"), max_length=100, blank=True)
    certificate_number = models.CharField(_("Numéro de certificat"), max_length=50, blank=True)
    certificate_file = models.FileField(_("Certificat"), upload_to='grades/certificates/', null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    is_current = models.BooleanField(_("Grade actuel"), default=True, help_text=_("Indique si c'est le grade actuel du pratiquant pour cette discipline"))
    
    class Meta:
        verbose_name = _("Grade de pratiquant")
        verbose_name_plural = _("Grades des pratiquants")
        ordering = ['-date_obtained']
        indexes = [
            models.Index(fields=['practitioner', 'discipline', 'is_current']),
            models.Index(fields=['grade', 'date_obtained']),
        ]

    def __str__(self):
        return f"{self.practitioner.full_name} - {self.grade.name} ({self.discipline.name}) - {self.date_obtained}"
    
    def save(self, *args, **kwargs):
        # Si ce grade est défini comme courant, désactiver les autres grades courants pour ce pratiquant et cette discipline
        if self.is_current:
            PractitionerGrade.objects.filter(
                practitioner=self.practitioner,
                discipline=self.discipline,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
            
        # Enregistrer la discipline du grade
        if not self.discipline_id:
            self.discipline = self.grade.discipline
            
        super().save(*args, **kwargs)


class GradeRequirement(models.Model):
    """Exigences spécifiques pour obtenir un grade."""
    grade = models.ForeignKey(
        Grade, 
        on_delete=models.CASCADE, 
        related_name='grade_requirements',  # Modification ici
        verbose_name=_("Grade")
    )
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    is_mandatory = models.BooleanField(_("Obligatoire"), default=True)
    min_age = models.PositiveSmallIntegerField(_("Ã‚ge minimum"), default=0)
    min_time_in_previous_grade = models.PositiveSmallIntegerField(
        _("Temps minimum dans le grade précédent (mois)"), 
        default=0
    )
    required_points = models.PositiveSmallIntegerField(_("Points requis"), default=0)
    order = models.PositiveSmallIntegerField(_("Ordre d'affichage"), default=0)
    
    class Meta:
        verbose_name = _("Exigence de grade")
        verbose_name_plural = _("Exigences de grade")
        ordering = ['grade', 'order']
        
    def __str__(self):
        return f"{self.name} ({self.grade.name})"


class GradeExam(models.Model):
    """Sessions d'examens de passage de grade."""
    STATUS_CHOICES = [
        ('scheduled', _('Planifié')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('cancelled', _('Annulé')),
    ]
    
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    date = models.DateField(_("Date"))
    location = models.CharField(_("Lieu"), max_length=200)
    discipline = models.ForeignKey(
        'competitions.Discipline', 
        on_delete=models.CASCADE, 
        related_name='grade_exams',
        verbose_name=_("Discipline")
    )
    available_grades = models.ManyToManyField(
        Grade, 
        related_name='exams',
        verbose_name=_("Grades disponibles")
    )
    max_participants = models.PositiveSmallIntegerField(_("Nombre maximum de participants"), validators=[MinValueValidator(1)], default=50)
    registration_deadline = models.DateField(_("Date limite d'inscription"))
    examiners = models.CharField(_("Examinateurs"), max_length=200, blank=True)
    fee = models.DecimalField(_("Frais d'inscription"), max_digits=10, decimal_places=2, default=0)
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Examen de passage de grade")
        verbose_name_plural = _("Examens de passage de grade")
        ordering = ['-date']
        
    def __str__(self):
        return f"{self.title} - {self.date}"
    
    @property
    def is_registration_open(self):
        """Vérifie si l'inscription est encore ouverte."""
        today = timezone.now().date()
        return (
            today <= self.registration_deadline and 
            self.status in ['scheduled', 'in_progress'] and
            self.count_registered() < self.max_participants
        )
    
    def count_registered(self):
        """Compte le nombre de pratiquants inscrits Ã  cet examen."""
        return self.registrations.count()


class GradeExamRegistration(models.Model):
    """Inscriptions aux examens de passage de grade."""
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('passed', _('Réussi')),
        ('failed', _('Ã‰choué')),
        ('absent', _('Absent')),
    ]
    
    exam = models.ForeignKey(
        GradeExam, 
        on_delete=models.CASCADE, 
        related_name='registrations',
        verbose_name=_("Examen")
    )
    practitioner = models.ForeignKey(
        'competitions.Practitioner', 
        on_delete=models.CASCADE, 
        related_name='grade_exam_registrations',
        verbose_name=_("Pratiquant")
    )
    target_grade = models.ForeignKey(
        Grade, 
        on_delete=models.CASCADE, 
        related_name='exam_registrations',
        verbose_name=_("Grade visé")
    )
    registration_date = models.DateTimeField(_("Date d'inscription"), auto_now_add=True)
    payment_confirmed = models.BooleanField(_("Paiement confirmé"), default=False)
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='pending')
    score = models.DecimalField(_("Score"), max_digits=5, decimal_places=2, null=True, blank=True)
    examiner_notes = models.TextField(_("Notes de l'examinateur"), blank=True)
    certificate_issued = models.BooleanField(_("Certificat émis"), default=False)
    certificate_number = models.CharField(_("Numéro de certificat"), max_length=50, blank=True)
    
    class Meta:
        verbose_name = _("Inscription Ã  un examen de grade")
        verbose_name_plural = _("Inscriptions aux examens de grade")
        unique_together = ['exam', 'practitioner']
        ordering = ['exam', 'registration_date']
        
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.target_grade.name} ({self.exam.title})"
    
# Dans grades/models.py
class GradingSystem(models.Model):
    """Système de graduation pour une discipline."""
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    discipline = models.ForeignKey(
        'competitions.Discipline',
        on_delete=models.CASCADE, 
        related_name='grading_systems',
        verbose_name=_("Discipline")
    )
    # Ajoutez d'autres champs selon vos besoins
    
    class Meta:
        verbose_name = _("Système de graduation")
        verbose_name_plural = _("Systèmes de graduation")
        
    def __str__(self):
        return f"{self.name} ({self.discipline.name})"
    
class GradeActionLog(models.Model):
    """Journal des actions effectuées sur les grades des pratiquants."""
    ACTION_TYPES = [
        ('add', _('Ajout')),
        ('update', _('Modification')),
        ('delete', _('Suppression')),
        ('set_current', _('Définition comme grade actuel')),
        ('revoke', _('Retrait')),
    ]
    
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='grade_action_logs',
        verbose_name=_("Pratiquant")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='grade_actions',
        verbose_name=_("Utilisateur")
    )
    action_type = models.CharField(
        _("Type d'action"),
        max_length=20,
        choices=ACTION_TYPES
    )
    grade = models.ForeignKey(
        'Grade',
        on_delete=models.SET_NULL,
        null=True,
        related_name='action_logs',
        verbose_name=_("Grade")
    )
    notes = models.TextField(_("Notes"), blank=True)
    timestamp = models.DateTimeField(_("Horodatage"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Journal d'action sur grade")
        verbose_name_plural = _("Journal des actions sur grades")
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_action_type_display()} - {self.practitioner.full_name} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

