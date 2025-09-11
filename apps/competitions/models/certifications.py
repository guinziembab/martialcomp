from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole

class JudgeCertification(models.Model):
    """Modèle pour les certifications de juges délivrées par les organisations."""
    
    LEVEL_CHOICES = [
        ('regional', _('Régional')),
        ('national', _('National')),
        ('international', _('International')),
    ]
    
    # Relations - Ajout de null=True pour faciliter la migration
    organization = models.ForeignKey('organizations.Organization',  
        on_delete=models.CASCADE, 
        related_name='judge_certifications',
        verbose_name=_("Organisation")
    )
    discipline = models.ForeignKey(
        'Discipline', 
        on_delete=models.CASCADE, 
        related_name='certifications',
        verbose_name=_("Discipline"),
        null=True,  # Permettre temporairement des valeurs nulles pour la migration
        blank=True
    )
    
    # Informations générales
    title = models.CharField(_("Titre"), max_length=100)
    code = models.CharField(_("Code"), max_length=20, blank=True, null=True)  # Permettre null pour faciliter la migration
    level = models.CharField(_("Niveau"), max_length=20, choices=LEVEL_CHOICES, default='regional')
    description = models.TextField(_("Description"), blank=True)
    requirements = models.TextField(_("Prérequis"), blank=True)
    
    # Champs anciens qui pourraient encore exister dans la base de données
    # Les conserver avec null=True pour permettre la migration
    certification_type = models.CharField(max_length=50, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    examiner = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='examiner_certifications')
    max_participants = models.PositiveIntegerField(null=True, blank=True)
    registration_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    
    # Validité
    validity_period = models.PositiveIntegerField(
        _("Durée de validité (mois)"), 
        default=36,
        help_text=_("Durée de validité de la certification en mois"),
        null=True  # Permettre temporairement des valeurs nulles
    )
    
    # Métadonnées
    is_active = models.BooleanField(_("Active"), default=True, null=True)  # Permettre temporairement des valeurs nulles
    created_at = models.DateTimeField(_("Créée le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mise Ã  jour le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Certification de juge")
        verbose_name_plural = _("Certifications de juge")
        ordering = ['organization', 'level', 'title']  # Corrigé de 'federation' Ã  'organization'
        # Supprimer temporairement la contrainte unique_together
        # unique_together = ['organization', 'code']  # Serait 'organization' au lieu de 'federation'
    
    def __str__(self):
        return f"{self.title} - {self.get_organization_name()} ({self.get_level_display()})"
    
    def get_organization_name(self):
        """Récupérer le nom de l'organisation de manière sécurisée."""
        try:
            return self.organization.name if self.organization else "N/A"
        except:
            return "N/A"
    
    def active_certifications_count(self):
        """Nombre de certifications actives délivrées."""
        return self.registrations.filter(status='approved').count()


class CertificationRegistration(models.Model):
    """Modèle pour les inscriptions aux examens de certification."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('completed', _('Complétée')),
    ]
    
    # Relations - Ajout de null=True pour faciliter la migration
    certification = models.ForeignKey(
        JudgeCertification, 
        on_delete=models.CASCADE, 
        related_name='registrations',
        verbose_name=_("Certification")
    )
    user = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='certification_registrations',
        verbose_name=_("Utilisateur"),
        null=True,  # Permettre temporairement des valeurs nulles
        blank=True
    )
    
    # Conserver temporairement les anciens champs pour la migration
    practitioner = models.ForeignKey('Practitioner', on_delete=models.SET_NULL, null=True, blank=True, related_name='cert_registrations')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    examiner_feedback = models.TextField(null=True, blank=True)
    
    # Données d'inscription
    registration_date = models.DateTimeField(_("Date d'inscription"), auto_now_add=True)
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(_("Notes"), blank=True)
    
    # Métadonnées
    reviewed_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='reviewed_certification_registrations',
        verbose_name=_("Examiné par")
    )
    reviewed_at = models.DateTimeField(_("Examiné le"), null=True, blank=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Inscription Ã  une certification")
        verbose_name_plural = _("Inscriptions aux certifications")
        ordering = ['-registration_date']
        # Supprimer temporairement la contrainte unique_together
        # unique_together = ['certification', 'user']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.get_certification_title()}"
        elif self.practitioner:
            return f"{self.practitioner} - {self.get_certification_title()}"
        return f"Registration {self.id}"
    
    def get_certification_title(self):
        """Récupérer le titre de la certification de manière sécurisée."""
        try:
            return self.certification.title if self.certification else "N/A"
        except:
            return "N/A"
    
    def approve(self, reviewer):
        """Approuve l'inscription."""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject(self, reviewer, notes=None):
        """Rejette l'inscription."""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()


class Exam(models.Model):
    """Modèle pour les examens de grade et certification organisés par les fédérations."""
    
    EXAM_TYPE_CHOICES = [
        ('grade', _('Examen de grade')),
        ('certification', _('Examen de certification')),
        ('recertification', _('Examen de recertification')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('published', _('Publié')),
        ('ongoing', _('En cours')),
        ('completed', _('Terminé')),
        ('cancelled', _('Annulé'))
    ]
    
    # Relations
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='exams',
        verbose_name=_("Organisation")
    )
    discipline = models.ForeignKey(
        'Discipline',
        on_delete=models.CASCADE,
        related_name='exams',
        verbose_name=_("Discipline")
    )
    
    # Informations générales
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    exam_type = models.CharField(_("Type d'examen"), max_length=20, choices=EXAM_TYPE_CHOICES, default='grade')
    
    # Date et lieu
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"), null=True, blank=True)
    start_time = models.TimeField(_("Heure de début"), null=True, blank=True)
    end_time = models.TimeField(_("Heure de fin"), null=True, blank=True)
    location = models.CharField(_("Lieu"), max_length=255)
    address = models.TextField(_("Adresse complète"), blank=True)
    
    # Gestion des inscriptions
    registration_start = models.DateField(_("Début des inscriptions"))
    registration_end = models.DateField(_("Fin des inscriptions"))
    max_participants = models.PositiveIntegerField(_("Nombre maximum de participants"), default=50)
    registration_fee = models.DecimalField(_("Frais d'inscription"), max_digits=8, decimal_places=2, default=0)
    
    # Examinateurs
    chief_examiner = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chief_examiner_exams',
        verbose_name=_("Examinateur principal")
    )
    examiners = models.ManyToManyField(
        'auth.User',
        related_name='examiner_exams',
        blank=True,
        verbose_name=_("Examinateurs")
    )
    
    # Prérequis et règles
    requirements = models.TextField(_("Prérequis"), blank=True)
    rules = models.TextField(_("Règlement"), blank=True)
    materials_needed = models.TextField(_("Matériel nécessaire"), blank=True)
    
    # Statut et métadonnées
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exams',
        verbose_name=_("Créé par")
    )
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Examen")
        verbose_name_plural = _("Examens")
        ordering = ['-start_date', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.start_date}"
    
    @property
    def is_registration_open(self):
        """Vérifie si les inscriptions sont ouvertes."""
        from django.utils import timezone
        today = timezone.now().date()
        return (self.registration_start <= today <= self.registration_end and 
                self.status == 'published')
    
    @property
    def participants_count(self):
        """Nombre de participants inscrits."""
        return self.registrations.filter(status='approved').count()
    
    @property
    def available_spots(self):
        """Nombre de places disponibles."""
        return max(0, self.max_participants - self.participants_count)
    
    def can_register(self, user):
        """Vérifie si un utilisateur peut s'inscrire."""
        if not self.is_registration_open:
            return False, _("Les inscriptions ne sont pas ouvertes")
        
        if self.available_spots <= 0:
            return False, _("Plus de places disponibles")
            
        if self.registrations.filter(user=user).exists():
            return False, _("Vous êtes déjà inscrit à cet examen")
            
        return True, _("Inscription possible")


class ExamRegistration(models.Model):
    """Inscription à un examen."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('completed', _('Terminée')),
        ('absent', _('Absent')),
    ]
    
    # Relations
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name=_("Examen")
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='exam_registrations',
        verbose_name=_("Utilisateur")
    )
    
    # Informations d'inscription
    registration_date = models.DateTimeField(_("Date d'inscription"), auto_now_add=True)
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(_("Notes de l'inscription"), blank=True)
    
    # Résultats
    score = models.DecimalField(_("Note"), max_digits=5, decimal_places=2, null=True, blank=True)
    grade_obtained = models.CharField(_("Grade obtenu"), max_length=50, blank=True)
    passed = models.BooleanField(_("Réussi"), null=True, blank=True)
    examiner_feedback = models.TextField(_("Commentaires de l'examinateur"), blank=True)
    
    # Métadonnées
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_exam_registrations',
        verbose_name=_("Évalué par")
    )
    reviewed_at = models.DateTimeField(_("Évalué le"), null=True, blank=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Inscription à un examen")
        verbose_name_plural = _("Inscriptions aux examens")
        unique_together = ['exam', 'user']
        ordering = ['-registration_date']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.exam.title}"
    
    def approve(self, reviewer):
        """Approuve l'inscription."""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()
    
    def reject(self, reviewer, notes=None):
        """Rejette l'inscription."""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if notes:
            self.notes = notes
        self.save()
    
    def complete_with_results(self, reviewer, score=None, grade=None, passed=None, feedback=""):
        """Termine l'inscription avec les résultats."""
        self.status = 'completed'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        if score is not None:
            self.score = score
        if grade:
            self.grade_obtained = grade
        if passed is not None:
            self.passed = passed
        if feedback:
            self.examiner_feedback = feedback
        self.save()


