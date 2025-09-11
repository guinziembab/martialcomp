# competitions/models/judge.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole

User = get_user_model()

# Constantes pour les niveaux de qualification
QUALIFICATION_LEVELS = [
    ('novice', _('Novice')),
    ('regional', _('Régional')),
    ('national', _('National')),
    ('international', _('International')),
]

class Judge(models.Model):
    """
    Modèle pour le profil juge d'un pratiquant.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='judge_profile',
        verbose_name=_("Utilisateur"),
        null=True,
        blank=True
    )
    practitioner = models.OneToOneField(
        'Practitioner', 
        on_delete=models.CASCADE, 
        related_name='judge',
        verbose_name=_("Pratiquant")
    )
    qualification_level = models.CharField(
        _("Niveau de qualification"), 
        max_length=20, 
        choices=QUALIFICATION_LEVELS, 
        default='novice'
    )
    years_experience = models.PositiveSmallIntegerField(
        _("Années d'expérience"), 
        default=0
    )
    # Alias pour maintenir la compatibilité avec experience_years
    @property
    def experience_years(self):
        return self.years_experience
    
    @experience_years.setter
    def experience_years(self, value):
        self.years_experience = value
        
    is_technical_judge = models.BooleanField(
        _("Juge technique"), 
        default=True
    )
    is_combat_referee = models.BooleanField(
        _("Arbitre de combat"), 
        default=False
    )
    notes = models.TextField(
        _("Notes"), 
        blank=True
    )
    certification_number = models.CharField(
        _("Numéro de certification"), 
        max_length=100, 
        blank=True
    )
    certified_since = models.DateField(
        _("Certifié depuis"), 
        null=True, 
        blank=True
    )
    organization = models.ForeignKey('organizations.Organization', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certified_judges',  # Changed from 'judges' to avoid conflicts
        verbose_name=_("Fédération certifiante")
    )
    active = models.BooleanField(
        _("Actif"), 
        default=True
    )
    created_at = models.DateTimeField(
        _("Créé le"), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Mis Ã  jour le"), 
        auto_now=True
    )
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.get_qualification_level_display()}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Juge")
        verbose_name_plural = _("Juges")
        ordering = ['-qualification_level', '-years_experience']
    
    @property
    def full_name(self):
        return self.practitioner.full_name
    
    @property
    def current_assignments(self):
        """Retourne les affectations actuelles du juge."""
        today = timezone.now().date()
        return JudgeAssignment.objects.filter(
            registration__practitioner=self.practitioner,
            category__competition__start_date__lte=today,
            category__competition__end_date__gte=today
        )
    
    @property
    def upcoming_assignments(self):
        """Retourne les affectations Ã  venir du juge."""
        today = timezone.now().date()
        return JudgeAssignment.objects.filter(
            registration__practitioner=self.practitioner,
            category__competition__start_date__gt=today
        )
    
    @property
    def past_assignments(self):
        """Retourne les affectations passées du juge."""
        today = timezone.now().date()
        return JudgeAssignment.objects.filter(
            registration__practitioner=self.practitioner,
            category__competition__end_date__lt=today
        )


class JudgeTechnicalApplication(models.Model):
    """
    Modèle pour les candidatures de juges techniques.
    Stocke les informations des candidatures avant validation.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='technical_judge_applications',
        verbose_name=_("Utilisateur")
    )
    first_name = models.CharField(_("Prénom"), max_length=100)
    last_name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Téléphone"), max_length=20, blank=True, null=True)
    
    # Qualifications
    qualification_level = models.CharField(
        _("Niveau de qualification"),
        max_length=20,
        choices=QUALIFICATION_LEVELS,
        default='novice'
    )
    experience_years = models.PositiveIntegerField(_("Années d'expérience"), default=0)
    qualifications = models.TextField(_("Qualifications"), blank=True)
    certifications = models.TextField(_("Certifications"), blank=True)
    
    # Relations avec les disciplines (si applicable)
    disciplines = models.ManyToManyField(
        'Discipline', 
        related_name='judge_technical_applications',
        verbose_name=_("Disciplines")
    )
    
    # Documents
    resume = models.FileField(_("CV"), upload_to='judges/resumes/', blank=True, null=True)
    certification_document = models.FileField(
        _("Document de certification"), 
        upload_to='judges/certifications/', 
        blank=True, 
        null=True
    )
    
    # Autres informations
    message = models.TextField(_("Message"), blank=True)
    agree_to_terms = models.BooleanField(_("Accepte les conditions"), default=False)
    
    # Suivi de candidature
    application_date = models.DateTimeField(_("Date de candidature"), auto_now_add=True)
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=[
            ('pending', _('En attente')),
            ('approved', _('Approuvée')),
            ('rejected', _('Rejetée')),
        ],
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_judge_applications',
        verbose_name=_("Examiné par")
    )
    reviewed_at = models.DateTimeField(_("Date d'examen"), null=True, blank=True)
    notes_internal = models.TextField(_("Notes internes"), blank=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Candidature de juge technique")
        verbose_name_plural = _("Candidatures de juges techniques")
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"
    
    def approve(self, reviewer=None):
        """
        Approuve la candidature et crée un profil de juge.
        
        Args:
            reviewer: L'utilisateur qui approuve la candidature
        
        Returns:
            Judge: Le profil de juge créé
        """
        from ..models import Practitioner
        
        with models.transaction.atomic():
            # Mettre Ã  jour le statut de la candidature
            self.status = 'approved'
            self.reviewed_by = reviewer
            self.reviewed_at = timezone.now()
            self.save()
            
            # Vérifier si un Practitioner existe déjÃ  pour cet utilisateur
            practitioner, created = Practitioner.objects.get_or_create(
                user=self.user,
                defaults={
                    'first_name': self.first_name,
                    'last_name': self.last_name,
                    'email': self.email,
                }
            )
            
            # Créer ou mettre Ã  jour le profil de juge
            judge, created = Judge.objects.update_or_create(
                practitioner=practitioner,
                defaults={
                    'user': self.user,
                    'qualification_level': self.qualification_level,
                    'years_experience': self.experience_years,
                    'is_technical_judge': True,
                    'notes': self.qualifications,
                    'active': True,
                }
            )
            
            # Associer les disciplines
            if self.disciplines.exists():
                if hasattr(practitioner, 'disciplines'):
                    for discipline in self.disciplines.all():
                        practitioner.disciplines.add(discipline)
            
            return judge
    
    def reject(self, reviewer=None, notes=None):
        """
        Rejette la candidature.
        
        Args:
            reviewer: L'utilisateur qui rejette la candidature
            notes: Commentaires expliquant le rejet
        """
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.notes_internal = notes
        self.save()


class JudgeQualification(models.Model):
    """
    Modèle pour les qualifications spécifiques des juges.
    """
    QUALIFICATION_TYPES = [
        ('technical_judge', _('Juge Technique')),
        ('combat_referee', _('Arbitre Combat')),
        ('chief_judge', _('Juge en Chef')),
        ('timekeeper', _('Chronométreur')),
    ]
    
    practitioner = models.ForeignKey(
        'Practitioner', 
        on_delete=models.CASCADE, 
        related_name='qualifications',
        verbose_name=_("Pratiquant")
    )
    qualification_type = models.CharField(
        _("Type de qualification"), 
        max_length=20, 
        choices=QUALIFICATION_TYPES
    )
    level = models.CharField(
        _("Niveau"), 
        max_length=20, 
        choices=QUALIFICATION_LEVELS
    )
    discipline = models.ForeignKey(
        'Discipline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='judge_qualifications',
        verbose_name=_("Discipline")
    )
    certified_date = models.DateField(
        _("Date de certification"), 
        null=True, 
        blank=True
    )
    expiry_date = models.DateField(
        _("Date d'expiration"), 
        null=True, 
        blank=True
    )
    certificate_number = models.CharField(
        _("Numéro de certificat"), 
        max_length=100, 
        blank=True
    )
    issuing_organization = models.ForeignKey(
        'organizations.Organization', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_qualifications',
        verbose_name=_("Fédération émettrice")
    )
    notes = models.TextField(
        _("Notes"), 
        blank=True
    )
    created_at = models.DateTimeField(
        _("Créé le"), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Mis Ã  jour le"), 
        auto_now=True
    )
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.get_qualification_type_display()} ({self.get_level_display()})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Qualification de juge")
        verbose_name_plural = _("Qualifications de juge")
        unique_together = ('practitioner', 'qualification_type', 'discipline')
        ordering = ['practitioner', 'qualification_type']  # Removed 'federation' from ordering
    
    @property
    def is_valid(self):
        """Vérifie si la qualification est encore valide."""
        if not self.expiry_date:
            return True
        return self.expiry_date >= timezone.now().date()


class JudgeAssignment(models.Model):
    """
    Modèle pour les affectations des juges/arbitres aux catégories de compétition.
    """
    ASSIGNMENT_TYPES = [
        ('technical_judge', _('Juge Technique')),
        ('combat_referee', _('Arbitre Combat')),
        ('chief_judge', _('Juge en Chef')),
        ('timekeeper', _('Chronométreur')),
        ('scorekeeper', _('Marqueur')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('confirmed', _('Confirmé')),
        ('declined', _('Refusé')),
        ('completed', _('Terminé')),
    ]
    
    registration = models.ForeignKey(
        'CompetitionRegistration', 
        on_delete=models.CASCADE, 
        related_name='judge_assignments',
        verbose_name=_("Inscription")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='judge_assignments',
        verbose_name=_("Utilisateur"),
        null=True, 
        blank=True
    )
    # Relation directe pour les juges en chef
    chief_judge = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='chief_judge_assignments',
        verbose_name=_("Juge en chef"),
        null=True, 
        blank=True
    )
    category = models.ForeignKey(
        'CompetitionCategory', 
        on_delete=models.CASCADE, 
        related_name='judge_assignments',
        verbose_name=_("Catégorie")
    )
    assignment_type = models.CharField(
        _("Type d'affectation"), 
        max_length=20, 
        choices=ASSIGNMENT_TYPES
    )
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default='pending'
    )
    start_time = models.DateTimeField(
        _("Heure de début"), 
        null=True, 
        blank=True
    )
    end_time = models.DateTimeField(
        _("Heure de fin"), 
        null=True, 
        blank=True
    )
    tatami = models.PositiveSmallIntegerField(
        _("Tatami"), 
        null=True, 
        blank=True
    )
    notes = models.TextField(
        _("Notes"), 
        blank=True
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='judge_assignments_made',
        verbose_name=_("Assigné par")
    )
    created_at = models.DateTimeField(
        _("Créé le"), 
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Mis Ã  jour le"), 
        auto_now=True
    )
    
    def __str__(self):
        return f"{self.registration.practitioner.full_name} - {self.category.name} ({self.get_assignment_type_display()})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Affectation de juge")
        verbose_name_plural = _("Affectations de juge")
        unique_together = ('registration', 'category', 'assignment_type')
        ordering = ['category__competition', 'category', 'assignment_type']
    
    def save(self, *args, **kwargs):
        # Si c'est un juge en chef, mettre Ã  jour le champ correspondant
        if self.assignment_type == 'chief_judge' and not self.chief_judge:
            self.chief_judge = self.user
            
        # Si la relation user n'est pas définie mais que la registration a un user associé
        if not self.user and hasattr(self.registration, 'practitioner') and hasattr(self.registration.practitioner, 'user'):
            self.user = self.registration.practitioner.user
            
        super().save(*args, **kwargs)
    
    @property
    def competition(self):
        """Retourne la compétition associée Ã  cette affectation."""
        return self.category.competition
    
    @property
    def judge_name(self):
        """Retourne le nom du juge."""
        return self.registration.practitioner.full_name
    
    @property
    def is_active(self):
        """Vérifie si l'affectation est active (en cours)."""
        now = timezone.now()
        if self.start_time and self.end_time:
            return self.start_time <= now <= self.end_time
        return False


