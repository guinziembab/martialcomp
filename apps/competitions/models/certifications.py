from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
import hashlib

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole

User = get_user_model()

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


class CertificateTemplate(models.Model):
    """Modèle de template pour les certificats PDF."""

    TEMPLATE_TYPE_CHOICES = [
        ('judge', _('Certification de juge')),
        ('grade', _('Diplôme de grade')),
        ('participation', _('Attestation de participation')),
        ('achievement', _('Certificat de réussite')),
    ]

    ORIENTATION_CHOICES = [
        ('landscape', _('Paysage')),
        ('portrait', _('Portrait')),
    ]

    # Relations
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='certificate_templates',
        verbose_name=_("Organisation")
    )

    # Informations générales
    name = models.CharField(_("Nom du modèle"), max_length=100)
    template_type = models.CharField(
        _("Type de certificat"),
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        default='judge'
    )
    description = models.TextField(_("Description"), blank=True)

    # Configuration visuelle
    orientation = models.CharField(
        _("Orientation"),
        max_length=20,
        choices=ORIENTATION_CHOICES,
        default='landscape'
    )
    background_image = models.ImageField(
        _("Image de fond"),
        upload_to='certificates/backgrounds/',
        blank=True,
        null=True
    )
    logo_position = models.CharField(
        _("Position du logo"),
        max_length=20,
        default='top-center',
        help_text=_("Position: top-left, top-center, top-right")
    )

    # Couleurs et polices
    primary_color = models.CharField(_("Couleur primaire"), max_length=7, default='#1a1f2e')
    secondary_color = models.CharField(_("Couleur secondaire"), max_length=7, default='#c9a227')
    text_color = models.CharField(_("Couleur du texte"), max_length=7, default='#333333')
    title_font_size = models.PositiveIntegerField(_("Taille titre (pt)"), default=36)
    body_font_size = models.PositiveIntegerField(_("Taille corps (pt)"), default=14)

    # Contenu du template
    header_text = models.CharField(_("Texte d'en-tête"), max_length=200, blank=True)
    title_text = models.CharField(
        _("Texte du titre"),
        max_length=200,
        default=_("CERTIFICAT")
    )
    body_template = models.TextField(
        _("Template du corps"),
        help_text=_("Variables disponibles: {recipient_name}, {certification_type}, {level}, {date}, {certification_number}, {organization_name}, {discipline}"),
        default="Certifie que {recipient_name} a obtenu la certification de {certification_type} niveau {level} en date du {date}."
    )
    footer_text = models.TextField(_("Texte de pied de page"), blank=True)

    # Signatures
    show_signature_line = models.BooleanField(_("Afficher ligne de signature"), default=True)
    signature_label = models.CharField(_("Label signature"), max_length=100, default=_("Le Président"))
    signature_image = models.ImageField(
        _("Image de signature"),
        upload_to='certificates/signatures/',
        blank=True,
        null=True
    )
    show_stamp = models.BooleanField(_("Afficher cachet"), default=True)
    stamp_image = models.ImageField(
        _("Image du cachet"),
        upload_to='certificates/stamps/',
        blank=True,
        null=True
    )

    # QR Code
    include_qr_code = models.BooleanField(_("Inclure QR code de vérification"), default=True)
    qr_position = models.CharField(
        _("Position QR code"),
        max_length=20,
        default='bottom-right'
    )

    # Métadonnées
    is_default = models.BooleanField(_("Modèle par défaut"), default=False)
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_certificate_templates',
        verbose_name=_("Créé par")
    )

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Modèle de certificat")
        verbose_name_plural = _("Modèles de certificats")
        ordering = ['organization', 'template_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    def save(self, *args, **kwargs):
        # S'assurer qu'il n'y a qu'un seul modèle par défaut par type et organisation
        if self.is_default:
            CertificateTemplate.objects.filter(
                organization=self.organization,
                template_type=self.template_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class IssuedCertificate(models.Model):
    """Certificat délivré à un utilisateur."""

    STATUS_CHOICES = [
        ('valid', _('Valide')),
        ('expired', _('Expiré')),
        ('revoked', _('Révoqué')),
        ('suspended', _('Suspendu')),
    ]

    # Identifiant unique
    certificate_uuid = models.UUIDField(
        _("UUID du certificat"),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    verification_code = models.CharField(
        _("Code de vérification"),
        max_length=12,
        unique=True,
        editable=False
    )

    # Relations
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='issued_certificates',
        verbose_name=_("Organisation émettrice")
    )
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_certificates',
        verbose_name=_("Modèle utilisé")
    )
    recipient = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='received_certificates',
        verbose_name=_("Bénéficiaire")
    )
    judge = models.ForeignKey(
        'Judge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certificates',
        verbose_name=_("Profil juge")
    )

    # Lien vers certification ou examen
    certification = models.ForeignKey(
        JudgeCertification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_certificates',
        verbose_name=_("Type de certification")
    )
    exam = models.ForeignKey(
        'Exam',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_certificates',
        verbose_name=_("Examen associé")
    )

    # Informations du certificat
    certificate_number = models.CharField(_("Numéro de certificat"), max_length=50)
    title = models.CharField(_("Titre du certificat"), max_length=200)
    recipient_name = models.CharField(_("Nom du bénéficiaire"), max_length=200)
    certification_type = models.CharField(_("Type de certification"), max_length=100)
    level = models.CharField(_("Niveau"), max_length=50, blank=True)
    discipline = models.CharField(_("Discipline"), max_length=100, blank=True)

    # Dates
    issue_date = models.DateField(_("Date d'émission"), default=timezone.now)
    valid_from = models.DateField(_("Valide à partir de"), default=timezone.now)
    valid_until = models.DateField(_("Valide jusqu'au"), null=True, blank=True)

    # Statut
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='valid'
    )
    revocation_reason = models.TextField(_("Raison de révocation"), blank=True)
    revoked_at = models.DateTimeField(_("Révoqué le"), null=True, blank=True)
    revoked_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_certificates',
        verbose_name=_("Révoqué par")
    )

    # Fichier PDF
    pdf_file = models.FileField(
        _("Fichier PDF"),
        upload_to='certificates/issued/',
        blank=True,
        null=True
    )

    # Métadonnées
    issued_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='issued_certificates_as_issuer',
        verbose_name=_("Émis par")
    )
    notes = models.TextField(_("Notes internes"), blank=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    # Compteurs
    download_count = models.PositiveIntegerField(_("Nombre de téléchargements"), default=0)
    verification_count = models.PositiveIntegerField(_("Nombre de vérifications"), default=0)
    last_verified_at = models.DateTimeField(_("Dernière vérification"), null=True, blank=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Certificat émis")
        verbose_name_plural = _("Certificats émis")
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"{self.certificate_number} - {self.recipient_name}"

    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = self.generate_verification_code()
        super().save(*args, **kwargs)

    def generate_verification_code(self):
        """Génère un code de vérification unique de 12 caractères."""
        unique_string = f"{self.certificate_uuid}{timezone.now().timestamp()}"
        hash_object = hashlib.sha256(unique_string.encode())
        return hash_object.hexdigest()[:12].upper()

    @property
    def is_valid(self):
        """Vérifie si le certificat est valide."""
        if self.status != 'valid':
            return False
        if self.valid_until and self.valid_until < timezone.now().date():
            return False
        return True

    @property
    def verification_url(self):
        """URL de vérification du certificat."""
        from django.urls import reverse
        return reverse('competitions:certificate_verify', kwargs={'code': self.verification_code})

    def revoke(self, user, reason=""):
        """Révoque le certificat."""
        self.status = 'revoked'
        self.revoked_by = user
        self.revoked_at = timezone.now()
        self.revocation_reason = reason
        self.save()

    def suspend(self, reason=""):
        """Suspend le certificat."""
        self.status = 'suspended'
        self.revocation_reason = reason
        self.save()

    def reactivate(self):
        """Réactive un certificat suspendu."""
        if self.status == 'suspended':
            self.status = 'valid'
            self.revocation_reason = ""
            self.save()

    def record_verification(self):
        """Enregistre une vérification du certificat."""
        self.verification_count += 1
        self.last_verified_at = timezone.now()
        self.save(update_fields=['verification_count', 'last_verified_at'])

    def record_download(self):
        """Enregistre un téléchargement du certificat."""
        self.download_count += 1
        self.save(update_fields=['download_count'])


class CertificationRequest(models.Model):
    """Demande de certification par un juge/club."""

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('under_review', _('En cours d\'examen')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
        ('cancelled', _('Annulée')),
    ]

    # Relations
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='certification_requests',
        verbose_name=_("Organisation (fédération)")
    )
    applicant = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='certification_requests',
        verbose_name=_("Demandeur")
    )
    judge = models.ForeignKey(
        'Judge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certification_requests',
        verbose_name=_("Profil juge")
    )
    certification_type = models.ForeignKey(
        JudgeCertification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        verbose_name=_("Type de certification demandée")
    )

    # Informations de la demande
    requested_level = models.CharField(
        _("Niveau demandé"),
        max_length=20,
        choices=[
            ('novice', _('Novice')),
            ('regional', _('Régional')),
            ('national', _('National')),
            ('international', _('International')),
        ],
        default='regional'
    )
    motivation = models.TextField(_("Motivation"), help_text=_("Expliquez pourquoi vous demandez cette certification"))
    experience_description = models.TextField(_("Description de l'expérience"), blank=True)

    # Pièces jointes
    cv_file = models.FileField(
        _("CV"),
        upload_to='certification_requests/cv/',
        blank=True,
        null=True
    )
    supporting_documents = models.FileField(
        _("Documents justificatifs"),
        upload_to='certification_requests/documents/',
        blank=True,
        null=True
    )

    # Statut
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Traitement
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_certification_requests',
        verbose_name=_("Examiné par")
    )
    reviewed_at = models.DateTimeField(_("Examiné le"), null=True, blank=True)
    reviewer_notes = models.TextField(_("Notes de l'examinateur"), blank=True)
    rejection_reason = models.TextField(_("Raison du rejet"), blank=True)

    # Certificat généré
    issued_certificate = models.OneToOneField(
        IssuedCertificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='certification_request',
        verbose_name=_("Certificat émis")
    )

    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Demande de certification")
        verbose_name_plural = _("Demandes de certification")
        ordering = ['-created_at']

    def __str__(self):
        return f"Demande de {self.applicant.get_full_name() or self.applicant.username} - {self.get_requested_level_display()}"

    def approve(self, reviewer, notes=""):
        """Approuve la demande."""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.reviewer_notes = notes
        self.save()

    def reject(self, reviewer, reason=""):
        """Rejette la demande."""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()

    def start_review(self, reviewer):
        """Marque la demande comme en cours d'examen."""
        self.status = 'under_review'
        self.reviewed_by = reviewer
        self.save()
