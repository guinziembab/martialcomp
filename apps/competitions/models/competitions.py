from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.utils import timezone
from urllib.parse import quote

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole
from apps.core.isolation import OrganizationSecureManager
from .discipline import Discipline


class StreamPlatform(models.TextChoices):
    """Plateformes de streaming supportées"""
    YOUTUBE = 'youtube', 'YouTube'
    TWITCH = 'twitch', 'Twitch'
    FACEBOOK = 'facebook', 'Facebook Live'
    VIMEO = 'vimeo', 'Vimeo'
    DAILYMOTION = 'dailymotion', 'Dailymotion'
    CUSTOM = 'custom', _('URL personnalisée')

class Competition(models.Model):
    title = models.CharField(_("Titre"), max_length=255)
    slug = models.SlugField(_("Slug"), max_length=255, unique=True, blank=True)
    description = models.TextField(_("Description"), blank=True)
    start_date = models.DateField(_("Date de début"))
    end_date = models.DateField(_("Date de fin"))
    start_time = models.TimeField(_("Heure de début"), null=True, blank=True)
    end_time = models.TimeField(_("Heure de fin"), null=True, blank=True)
    venue_name = models.CharField(_("Lieu"), max_length=255, blank=True)
    address = models.CharField(_("Adresse"), max_length=255, blank=True)
    city = models.CharField(_("Ville"), max_length=100, blank=True)
    postal_code = models.CharField(_("Code postal"), max_length=20, blank=True)
    
    # Ajout des nouveaux champs
    max_participants = models.PositiveIntegerField(_("Nombre maximum de participants"), null=True, blank=True)
    registration_deadline = models.DateField(_("Date limite d'inscription"), null=True, blank=True)
    logo = models.ImageField(_("Logo"), upload_to='competitions/logos/', null=True, blank=True)
    
    # Champs pour les critères d'éligibilité
    min_age = models.PositiveSmallIntegerField(_("Âge minimum"), null=True, blank=True)
    max_age = models.PositiveSmallIntegerField(_("Âge maximum"), null=True, blank=True)
    requires_medical_certificate = models.BooleanField(_("Certificat médical requis"), default=False)
    requires_license = models.BooleanField(_("Licence requise"), default=False)
    
    # Relation avec l'organisation
    organizing_organization = models.ForeignKey('organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organized_competitions",
        verbose_name=_("Organisation organisatrice")
    )

    # Créateur de la compétition
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_competitions",
        verbose_name=_("Créé par")
    )

    # Visibilité publique
    is_published = models.BooleanField(_("Publiée"), default=False, help_text=_("Indique si la compétition est visible publiquement"))

    # Options de visibilité
    allow_online_registration = models.BooleanField(_("Autoriser les inscriptions en ligne"), default=True)
    show_participants_list = models.BooleanField(_("Afficher la liste des participants"), default=False)
    live_results = models.BooleanField(_("Résultats en temps réel"), default=False)
    
    discipline = models.ForeignKey(
        'Discipline',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="competitions",
        verbose_name=_("Discipline")
    )
    competition_types = models.ManyToManyField('CompetitionType', related_name='competitions')
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=[
            ('draft', _('Brouillon')),
            ('published', _('Publiée')),
            ('ongoing', _('En cours')),
            ('completed', _('Terminée')),
            ('cancelled', _('Annulée')),
        ],
        default='draft'
    )

    # =========================================================================
    # CHAMPS STREAMING
    # =========================================================================

    # Configuration du stream
    stream_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Streaming activé"),
        help_text=_("Activer l'intégration du streaming pour cette compétition")
    )

    stream_platform = models.CharField(
        max_length=20,
        choices=StreamPlatform.choices,
        null=True,
        blank=True,
        verbose_name=_("Plateforme de streaming"),
        help_text=_("Sélectionner la plateforme utilisée pour le streaming")
    )

    stream_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL du stream"),
        help_text=_("URL complète du stream (ex: https://youtube.com/watch?v=xxxxx)")
    )

    stream_embed_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL d'intégration"),
        help_text=_("URL d'embed générée automatiquement")
    )

    stream_chat_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Chat du stream activé"),
        help_text=_("Afficher le chat de la plateforme à côté du stream")
    )

    stream_chat_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL du chat"),
        help_text=_("URL d'intégration du chat (optionnel)")
    )

    # État du stream
    is_live = models.BooleanField(
        default=False,
        verbose_name=_("En direct"),
        help_text=_("Indique si le stream est actuellement en direct")
    )

    stream_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Début du stream")
    )

    stream_ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fin du stream")
    )

    stream_viewer_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de spectateurs")
    )

    # Archive/Replay
    stream_replay_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL du replay"),
        help_text=_("URL de la vidéo enregistrée après la fin du stream")
    )

    stream_replay_available = models.BooleanField(
        default=False,
        verbose_name=_("Replay disponible")
    )

    # =========================================================================

    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            # Génère le slug de base à partir du titre
            base_slug = slugify(self.title)

            # Vérifie si ce slug existe déjà
            slug = base_slug
            counter = 1

            # Tant que le slug existe déjà, ajoute un compteur à la fin
            while Competition.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        # Synchronisation automatique entre is_published et le statut
        if self.status == 'published' or self.status == 'ongoing':
            self.is_published = True
        elif self.status in ['draft', 'cancelled']:
            self.is_published = False

        # Générer automatiquement l'URL d'embed si stream_url est défini
        if self.stream_url and self.stream_enabled:
            self.stream_embed_url = self.generate_embed_url()

        super().save(*args, **kwargs)
    
    @property
    def is_active(self):
        """Détermine si la compétition est active (publiée et pas encore terminée)"""
        today = timezone.now().date()
        return self.is_published and self.end_date >= today and self.status != 'cancelled'
        
    @property
    def is_registration_open(self):
        """Détermine si les inscriptions sont ouvertes"""
        today = timezone.now().date()
        if not self.is_published or self.status not in ['published', 'ongoing']:
            return False
        if self.registration_deadline and today > self.registration_deadline:
            return False
        return today <= self.start_date
    
    def check_eligibility(self, practitioner):
        """
        Vérifie si un pratiquant est éligible pour cette compétition.
        Renvoie un tuple (is_eligible, reasons) où reasons est une liste des raisons d'inéligibilité.
        """
        reasons = []
        
        # Vérifier l'âge
        if self.min_age is not None and practitioner.age < self.min_age:
            reasons.append(_("L'âge minimum requis est de {} ans").format(self.min_age))
            
        if self.max_age is not None and practitioner.age > self.max_age:
            reasons.append(_("L'âge maximum autorisé est de {} ans").format(self.max_age))
        
        # Vérifier le certificat médical
        if self.requires_medical_certificate and not practitioner.medical_certificate_date:
            reasons.append(_("Un certificat médical est requis"))
            
        # Vérifier si le certificat médical est valide (moins d'un an)
        if self.requires_medical_certificate and practitioner.medical_certificate_date:
            cert_age = timezone.now().date() - practitioner.medical_certificate_date
            if cert_age.days > 365:
                reasons.append(_("Le certificat médical doit dater de moins d'un an"))
        
        # Vérifier la licence
        if self.requires_license and not practitioner.license_number:
            reasons.append(_("Une licence valide est requise"))
        
        # Vérifier si inscriptions complètes
        if self.max_participants and self.registrations.count() >= self.max_participants:
            reasons.append(_("Le nombre maximum de participants est atteint"))
        
        is_eligible = len(reasons) == 0
        return is_eligible, reasons

    # =========================================================================
    # MÉTHODES STREAMING
    # =========================================================================

    def generate_embed_url(self):
        """
        Convertit l'URL du stream en URL d'intégration iframe.
        Supporte YouTube, Twitch, Vimeo, Facebook Live, Dailymotion.
        """
        if not self.stream_url:
            return None

        url = self.stream_url.strip()

        # YouTube - format watch
        if 'youtube.com/watch' in url:
            try:
                video_id = url.split('v=')[1].split('&')[0]
                return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
            except IndexError:
                return None

        # YouTube - format court youtu.be
        if 'youtu.be/' in url:
            try:
                video_id = url.split('youtu.be/')[1].split('?')[0]
                return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
            except IndexError:
                return None

        # YouTube - format live
        if 'youtube.com/live/' in url:
            try:
                video_id = url.split('/live/')[1].split('?')[0]
                return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
            except IndexError:
                return None

        # Twitch
        if 'twitch.tv/' in url:
            try:
                channel = url.split('twitch.tv/')[1].split('/')[0].split('?')[0]
                parent_domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'martialcomp.com'
                return f"https://player.twitch.tv/?channel={channel}&parent={parent_domain}&autoplay=true"
            except IndexError:
                return None

        # Vimeo
        if 'vimeo.com/' in url:
            try:
                video_id = url.split('vimeo.com/')[1].split('/')[0].split('?')[0]
                return f"https://player.vimeo.com/video/{video_id}?autoplay=1"
            except IndexError:
                return None

        # Facebook Live
        if 'facebook.com/' in url and '/videos/' in url:
            encoded_url = quote(url, safe='')
            return f"https://www.facebook.com/plugins/video.php?href={encoded_url}&autoplay=true"

        # Dailymotion
        if 'dailymotion.com/video/' in url:
            try:
                video_id = url.split('/video/')[1].split('_')[0]
                return f"https://www.dailymotion.com/embed/video/{video_id}?autoplay=1"
            except IndexError:
                return None

        # URL personnalisée - retourner telle quelle
        return url

    def generate_chat_url(self):
        """
        Génère l'URL du chat pour la plateforme de streaming.
        Actuellement supporte uniquement Twitch.
        """
        if not self.stream_url or not self.stream_chat_enabled:
            return None

        # YouTube Live Chat - pas d'embed simple disponible
        if 'youtube.com' in self.stream_url or 'youtu.be' in self.stream_url:
            return None

        # Twitch Chat
        if 'twitch.tv/' in self.stream_url:
            try:
                channel = self.stream_url.split('twitch.tv/')[1].split('/')[0]
                parent_domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'martialcomp.com'
                return f"https://www.twitch.tv/embed/{channel}/chat?parent={parent_domain}&darkpopout"
            except IndexError:
                return None

        return None

    def start_stream(self):
        """Marquer le stream comme démarré"""
        self.is_live = True
        self.stream_started_at = timezone.now()
        self.stream_ended_at = None
        self.save(update_fields=['is_live', 'stream_started_at', 'stream_ended_at'])

    def end_stream(self):
        """Marquer le stream comme terminé"""
        self.is_live = False
        self.stream_ended_at = timezone.now()
        self.save(update_fields=['is_live', 'stream_ended_at'])

    def update_viewer_count(self, count):
        """Mettre à jour le nombre de spectateurs"""
        self.stream_viewer_count = count
        self.save(update_fields=['stream_viewer_count'])

    @property
    def stream_duration(self):
        """Durée du stream en cours ou terminé"""
        if not self.stream_started_at:
            return None
        end_time = self.stream_ended_at or timezone.now()
        return end_time - self.stream_started_at

    # =========================================================================

    # Propriété pour compatibilité avec OrganizationSecureManager
    @property
    def organization(self):
        return self.organizing_organization
    
    # Manager sécurisé pour l'isolation par organisation
    objects = OrganizationSecureManager()
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Compétition")
        verbose_name_plural = _("Compétitions")
        ordering = ['-start_date']


class CompetitionType(models.Model):
    SCORING_SYSTEM_CHOICES = [
        ('technical', _('Technique')),
        ('combat', _('Combat')),
        ('mixed', _('Mixte')),
        ('custom', _('Personnalisé')),
    ]
    
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, related_name='competition_types')
    team_based = models.BooleanField(default=False)
    min_team_size = models.PositiveSmallIntegerField(null=True, blank=True)
    max_team_size = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_category = models.BooleanField(_("Catégorie de poids"), default=False)
    scoring_system = models.CharField(
        _("Système de notation"),
        max_length=20,
        choices=SCORING_SYSTEM_CHOICES,
        default='technical',
        help_text=_("Type de système de notation utilisé pour ce type de compétition")
    )
    order = models.PositiveSmallIntegerField(_("Ordre d'affichage"), default=0)
    
    def __str__(self):
        return f"{self.name} ({self.discipline.name})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Type de compétition")
        verbose_name_plural = _("Types de compétition")
        ordering = ['discipline', 'order', 'name']


class CompetitionRole(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(_("Nom du rôle"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.competition.title})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Rôle de compétition")
        verbose_name_plural = _("Rôles de compétition")
        unique_together = ('competition', 'name')


class ParticipantCategoryRegistration(models.Model):
    registration = models.ForeignKey('competitions.CompetitionRegistration', on_delete=models.CASCADE, related_name='category_registrations')
    competition_type = models.ForeignKey('CompetitionType', on_delete=models.CASCADE)
    category = models.ForeignKey('competitions.CompetitionCategory', on_delete=models.CASCADE)
    
    class Meta:
        app_label = 'competitions'
        unique_together = ('registration', 'competition_type')
        verbose_name = _("Inscription à une catégorie")
        verbose_name_plural = _("Inscriptions aux catégories")