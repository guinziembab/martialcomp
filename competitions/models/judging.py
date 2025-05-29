from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator

from organizations.models import Organization, OrganizationMember, OrganizationRole
from competitions.models import Competition, CompetitionCategory
from competitions.models.user import User
from competitions.models.federation import Federation

class JudgeProfile(models.Model):
    """Profil de juge pour un utilisateur."""
    
    QUALIFICATION_LEVELS = [
        ('novice', _('Novice')),
        ('regional', _('Régional')),
        ('national', _('National')),
        ('international', _('International')),
    ]
    
    JUDGE_TYPES = [
        ('technical', _('Juge Technique')),
        ('combat', _('Arbitre Combat')),
        ('chief', _('Juge en Chef')),
        ('assistant', _('Assistant/Chronométreur')),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='judge_profile',
        verbose_name=_("Utilisateur"),
    )
    
    qualification_level = models.CharField(
        _("Niveau de qualification"), 
        max_length=20, 
        choices=QUALIFICATION_LEVELS, 
        default='novice'
    )
    judge_types = models.CharField(
        _("Types de juge"), 
        max_length=255, 
        default='technical',
        help_text=_("Types séparés par des virgules: technical,combat,chief,assistant")
    )
    
    license_number = models.CharField(
        _("Numéro de licence"), 
        max_length=50, 
        blank=True
    )
    experience_years = models.PositiveSmallIntegerField(
        _("Années d'expérience"), 
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    certifying_organization = models.ForeignKey('organizations.Organization',  
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='certified_judges',
        verbose_name=_("Fédération certificatrice")
    )
    certification_date = models.DateField(
        _("Date de certification"), 
        null=True, 
        blank=True
    )
    certification_expiry = models.DateField(
        _("Date d'expiration de certification"), 
        null=True, 
        blank=True
    )
    
    is_active = models.BooleanField(
        _("Actif"), 
        default=True
    )
    is_training = models.BooleanField(
        _("En formation"), 
        default=False,
        help_text=_("Les notes des juges en formation ne sont pas comptabilisées")
    )
    
    notes = models.TextField(
        _("Notes"), 
        blank=True
    )
    
    # Préférences d'interface
    preferences = models.JSONField(
        _("Préférences d'interface"), 
        default=dict,
        blank=True,
        help_text=_("Préférences pour l'interface de notation (thème, disposition, etc.)")
    )
    
    # Logs et métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    last_active = models.DateTimeField(_("Dernière activité"), null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_qualification_level_display()})"
    
    class Meta:
        verbose_name = _("Profil de juge")
        verbose_name_plural = _("Profils de juges")
        ordering = ['-qualification_level', '-experience_years']
    
    def is_chief_judge(self):
        """Vérifie si l'utilisateur est un juge en chef."""
        return 'chief' in self.judge_types.split(',')
    
    def is_technical_judge(self):
        """Vérifie si l'utilisateur est un juge technique."""
        return 'technical' in self.judge_types.split(',')
    
    def is_combat_referee(self):
        """Vérifie si l'utilisateur est un arbitre de combat."""
        return 'combat' in self.judge_types.split(',')
    
    def is_assistant(self):
        """Vérifie si l'utilisateur est un assistant/chronométreur."""
        return 'assistant' in self.judge_types.split(',')
    
    def certification_is_valid(self):
        """Vérifie si la certification est encore valide."""
        if not self.certification_expiry:
            return True
        return self.certification_expiry >= timezone.now().date()
    
    def record_activity(self):
        """Enregistre l'heure de la dernière activité."""
        self.last_active = timezone.now()
        self.save(update_fields=['last_active'])


class JudgeQualification(models.Model):
    """Qualifications spécifiques d'un juge pour différentes disciplines."""
    
    QUALIFICATION_LEVELS = [
        ('novice', _('Novice')),
        ('regional', _('Régional')),
        ('national', _('National')),
        ('international', _('International')),
    ]
    
    QUALIFICATION_TYPES = [
        ('technical', _('Juge Technique')),
        ('combat', _('Arbitre Combat')),
        ('chief', _('Juge en Chef')),
        ('assistant', _('Assistant/Chronométreur')),
    ]
    
    judge = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='judge_qualifications',
        verbose_name=_("Juge")
    )
    discipline = models.ForeignKey(
        'competitions.Discipline', 
        on_delete=models.CASCADE, 
        related_name='judge_qualifications',
        verbose_name=_("Discipline")
    )
    
    qualification_type = models.CharField(
        _("Type de qualification"), 
        max_length=20, 
        choices=QUALIFICATION_TYPES
    )
    qualification_level = models.CharField(
        _("Niveau de qualification"), 
        max_length=20, 
        choices=QUALIFICATION_LEVELS, 
        default='novice'
    )
    
    certification_date = models.DateField(
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
    certifying_entity = models.CharField(
        _("Entité certificatrice"), 
        max_length=100, 
        blank=True
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    is_active = models.BooleanField(_("Actif"), default=True)
    
    def __str__(self):
        return f"{self.judge} - {self.discipline} - {self.get_qualification_type_display()} ({self.get_qualification_level_display()})"
    
    class Meta:
        verbose_name = _("Qualification de juge")
        verbose_name_plural = _("Qualifications de juge")
        unique_together = [['judge', 'discipline', 'qualification_type']]
        ordering = ['judge', 'discipline', 'qualification_type']
    
    def is_valid(self):
        """Vérifie si la qualification est encore valide."""
        if not self.expiry_date or not self.is_active:
            return self.is_active
        return self.expiry_date >= timezone.now().date() and self.is_active


class JudgeAssignment(models.Model):
    """Assignation d'un juge à une catégorie de compétition."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('confirmed', _('Confirmé')),
        ('declined', _('Refusé')),
        ('cancelled', _('Annulé')),
        ('completed', _('Terminé')),
    ]
    
    ROLE_CHOICES = [
        ('chief', _('Juge en Chef')),
        ('technical', _('Juge Technique')),
        ('combat', _('Arbitre Combat')),
        ('assistant', _('Assistant/Chronométreur')),
        ('scorer', _('Marqueur')),
        ('timekeeper', _('Chronométreur')),
    ]
    
    competition = models.ForeignKey(
        Competition, 
        on_delete=models.CASCADE, 
        related_name='judge_assignments',
        verbose_name=_("Compétition")
    )
    category = models.ForeignKey(
        CompetitionCategory, 
        on_delete=models.CASCADE, 
        related_name='judge_assignments',
        verbose_name=_("Catégorie"),
        null=True,
        blank=True
    )
    judge = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='judge_assignments',
        verbose_name=_("Juge")
    )
    
    role = models.CharField(
        _("Rôle"), 
        max_length=20, 
        choices=ROLE_CHOICES
    )
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    # Position sur le tatami (pour l'affichage)
    tatami = models.PositiveSmallIntegerField(
        _("Tatami"), 
        null=True, 
        blank=True
    )
    position = models.PositiveSmallIntegerField(
        _("Position"), 
        null=True, 
        blank=True,
        help_text=_("Position du juge (ex: 1 pour juge 1, 2 pour juge 2, etc.)")
    )
    
    # Planification
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
    
    # Pour les rotations de juges
    rotation_group = models.CharField(
        _("Groupe de rotation"), 
        max_length=50, 
        blank=True,
        help_text=_("Identifiant de groupe pour la rotation des juges")
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Gestion des invitations
    invitation_sent = models.BooleanField(
        _("Invitation envoyée"), 
        default=False
    )
    invitation_sent_at = models.DateTimeField(
        _("Invitation envoyée le"), 
        null=True, 
        blank=True
    )
    response_at = models.DateTimeField(
        _("Réponse reçue le"), 
        null=True, 
        blank=True
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_judge_assignments',
        verbose_name=_("Assigné par")
    )
    
    def __str__(self):
        category_name = self.category.name if self.category else "Compétition générale"
        return f"{self.judge} - {category_name} ({self.get_role_display()})"
    
    class Meta:
        verbose_name = _("Assignation de juge")
        verbose_name_plural = _("Assignations de juges")
        ordering = ['competition', 'category', 'tatami', 'position']
    
    def confirm(self):
        """Confirmer l'assignation."""
        self.status = 'confirmed'
        self.response_at = timezone.now()
        self.save(update_fields=['status', 'response_at'])
    
    def decline(self):
        """Refuser l'assignation."""
        self.status = 'declined'
        self.response_at = timezone.now()
        self.save(update_fields=['status', 'response_at'])
    
    def cancel(self):
        """Annuler l'assignation."""
        self.status = 'cancelled'
        self.save(update_fields=['status'])
    
    def complete(self):
        """Marquer l'assignation comme terminée."""
        self.status = 'completed'
        self.save(update_fields=['status'])
    
    def send_invitation(self):
        """Envoyer une invitation au juge."""
        # Logique d'envoi d'invitation (email, notification, etc.)
        # À implémenter
        self.invitation_sent = True
        self.invitation_sent_at = timezone.now()
        self.save(update_fields=['invitation_sent', 'invitation_sent_at'])


class JudgeAvailability(models.Model):
    """Disponibilité d'un juge pour une compétition."""
    
    judge = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='judge_availabilities',
        verbose_name=_("Juge")
    )
    competition = models.ForeignKey(
        Competition, 
        on_delete=models.CASCADE, 
        related_name='judge_availabilities',
        verbose_name=_("Compétition")
    )
    
    is_available = models.BooleanField(
        _("Disponible"), 
        default=True
    )
    
    # Périodes de disponibilité spécifiques
    date = models.DateField(
        _("Date"), 
        null=True, 
        blank=True,
        help_text=_("Date spécifique de disponibilité (optionnel)")
    )
    start_time = models.TimeField(
        _("Heure de début"), 
        null=True, 
        blank=True
    )
    end_time = models.TimeField(
        _("Heure de fin"), 
        null=True, 
        blank=True
    )
    
    # Catégories préférées
    preferred_categories = models.ManyToManyField(
        CompetitionCategory, 
        blank=True, 
        related_name='preferred_judges',
        verbose_name=_("Catégories préférées")
    )
    
    preferred_roles = models.CharField(
        _("Rôles préférés"), 
        max_length=255, 
        blank=True,
        help_text=_("Rôles préférés séparés par des virgules: chief,technical,combat,assistant")
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    def __str__(self):
        date_str = f" - {self.date}" if self.date else ""
        return f"{self.judge} - {self.competition}{date_str} - {'Disponible' if self.is_available else 'Non disponible'}"
    
    class Meta:
        verbose_name = _("Disponibilité de juge")
        verbose_name_plural = _("Disponibilités de juges")
        unique_together = [['judge', 'competition', 'date']]
        ordering = ['competition', 'date', 'start_time']


class JudgeApplication(models.Model):
    """Candidature pour devenir juge."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('incomplete', _('Incomplète')),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='judge_applications',
        verbose_name=_("Utilisateur")
    )
    
    # Informations personnelles
    first_name = models.CharField(_("Prénom"), max_length=100)
    last_name = models.CharField(_("Nom"), max_length=100)
    email = models.EmailField(_("Email"))
    phone = models.CharField(_("Téléphone"), max_length=20, blank=True)
    
    # Qualifications
    experience_years = models.PositiveSmallIntegerField(
        _("Années d'expérience"), 
        default=0
    )
    disciplines = models.ManyToManyField(
        'competitions.Discipline', 
        related_name='judge_applicants',
        verbose_name=_("Disciplines")
    )
    
    qualification_type = models.CharField(
        _("Type de qualification"), 
        max_length=20, 
        choices=JudgeQualification.QUALIFICATION_TYPES,
        default='technical'
    )
    qualification_level = models.CharField(
        _("Niveau de qualification"), 
        max_length=20, 
        choices=JudgeQualification.QUALIFICATION_LEVELS,
        default='novice'
    )
    
    # Pièces jointes
    resume = models.FileField(
        _("CV"), 
        upload_to='judges/applications/resumes/', 
        null=True, 
        blank=True
    )
    certification_document = models.FileField(
        _("Document de certification"), 
        upload_to='judges/applications/certifications/', 
        null=True, 
        blank=True
    )
    other_documents = models.FileField(
        _("Autres documents"), 
        upload_to='judges/applications/documents/', 
        null=True, 
        blank=True
    )
    
    # Détails de la candidature
    qualifications_description = models.TextField(_("Description des qualifications"), blank=True)
    previous_experience = models.TextField(_("Expérience précédente"), blank=True)
    motivation = models.TextField(_("Motivation"), blank=True)
    
    # Statut de la candidature
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    application_date = models.DateTimeField(_("Date de candidature"), auto_now_add=True)
    
    # Évaluation
    reviewed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_judge_applications',
        verbose_name=_("Évalué par")
    )
    review_date = models.DateTimeField(_("Date d'évaluation"), null=True, blank=True)
    review_notes = models.TextField(_("Notes d'évaluation"), blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = _("Candidature de juge")
        verbose_name_plural = _("Candidatures de juge")
        ordering = ['-application_date']
    
    def approve(self, reviewer):
        """Approuver la candidature et créer un profil de juge."""
        with models.transaction.atomic():
            # Mettre à jour le statut
            self.status = 'approved'
            self.reviewed_by = reviewer
            self.review_date = timezone.now()
            self.save(update_fields=['status', 'reviewed_by', 'review_date'])
            
            # Créer/mettre à jour le profil de juge
            profile, created = JudgeProfile.objects.update_or_create(
                user=self.user,
                defaults={
                    'qualification_level': self.qualification_level,
                    'judge_types': self.qualification_type,
                    'experience_years': self.experience_years,
                    'is_active': True,
                }
            )
            
            # Créer des qualifications pour chaque discipline
            for discipline in self.disciplines.all():
                JudgeQualification.objects.create(
                    judge=self.user,
                    discipline=discipline,
                    qualification_type=self.qualification_type,
                    qualification_level=self.qualification_level,
                    certification_date=timezone.now().date(),
                    notes=self.qualifications_description,
                    is_active=True,
                )
    
    def reject(self, reviewer, notes=None):
        """Rejeter la candidature."""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.review_date = timezone.now()
        if notes:
            self.review_notes = notes
        self.save(update_fields=['status', 'reviewed_by', 'review_date', 'review_notes'])


class JudgeSessionLog(models.Model):
    """Journal de session pour les juges (connexion, activité, soumissions)."""
    
    ACTION_TYPES = [
        ('login', _('Connexion')),
        ('logout', _('Déconnexion')),
        ('score_submit', _('Soumission de score')),
        ('score_edit', _('Modification de score')),
        ('note_add', _('Ajout de note')),
        ('flag_issue', _('Signalement de problème')),
    ]
    
    judge = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='judge_session_logs',
        verbose_name=_("Juge")
    )
    competition = models.ForeignKey(
        Competition, 
        on_delete=models.CASCADE, 
        related_name='judge_session_logs',
        verbose_name=_("Compétition")
    )
    
    action_type = models.CharField(
        _("Type d'action"), 
        max_length=20, 
        choices=ACTION_TYPES
    )
    timestamp = models.DateTimeField(_("Horodatage"), auto_now_add=True)
    
    # Détails optionnels selon le type d'action
    category = models.ForeignKey(
        CompetitionCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='judge_logs',
        verbose_name=_("Catégorie")
    )
    performance_id = models.PositiveIntegerField(
        _("ID de la performance"), 
        null=True, 
        blank=True
    )
    
    details = models.JSONField(
        _("Détails"), 
        default=dict,
        blank=True,
        help_text=_("Détails supplémentaires sur l'action (dépend du type)")
    )
    ip_address = models.GenericIPAddressField(
        _("Adresse IP"), 
        null=True, 
        blank=True
    )
    device_info = models.TextField(_("Informations sur l'appareil"), blank=True)
    
    def __str__(self):
        return f"{self.judge} - {self.get_action_type_display()} - {self.timestamp}"
    
    class Meta:
        verbose_name = _("Journal de session de juge")
        verbose_name_plural = _("Journal des sessions de juges")
        ordering = ['-timestamp']