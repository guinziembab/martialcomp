# -*- coding: utf-8 -*-
"""
Modèles de l'application Super Admin.

Ce fichier contient les modèles pour :
- Gestion des profils de membership (MembershipProfile, EventPass, MembershipTransformation)
- Monitoring système (SystemMetric, ServiceStatus, AdminAction, PlatformAlert)
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal


# =============================================================================
# MODÈLES MEMBERSHIP
# =============================================================================

class MembershipProfileManager(models.Manager):
    """Manager personnalisé pour MembershipProfile."""

    def active(self):
        """Retourne les profils actifs."""
        return self.filter(is_active=True)

    def global_profiles(self):
        """Retourne les profils globaux (créés par super admin)."""
        return self.filter(is_global=True, is_active=True)

    def for_event(self, competition):
        """Retourne les profils applicables à un événement."""
        return self.filter(
            models.Q(is_global=True) |
            models.Q(linked_event=competition) |
            models.Q(created_by_organization=competition.organization)
        ).filter(is_active=True)

    def subscription_profiles(self):
        """Retourne les profils de type abonnement."""
        return self.filter(profile_type='subscription', is_active=True)

    def event_profiles(self):
        """Retourne les profils de type événement."""
        return self.filter(profile_type='event', is_active=True)


class MembershipProfile(models.Model):
    """
    Profil de membership définissant les caractéristiques d'un type d'adhésion.

    Peut être :
    - Global (créé par super admin, applicable à tous)
    - Lié à une organisation (créé par l'organisation)
    - Lié à un événement spécifique
    """

    PROFILE_TYPE_CHOICES = [
        ('subscription', _('Abonnement')),
        ('event', _('Événement')),
        ('hybrid', _('Hybride')),
    ]

    VALIDITY_TYPE_CHOICES = [
        ('duration', _('Durée fixe')),
        ('event_bound', _('Lié à un événement')),
    ]

    PRICING_MODEL_CHOICES = [
        ('per_member', _('Par membre')),
        ('flat', _('Forfait')),
        ('free', _('Gratuit')),
    ]

    # Identification
    name = models.CharField(_('Nom'), max_length=100)
    slug = models.SlugField(_('Slug'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)

    # Type et validité
    profile_type = models.CharField(
        _('Type de profil'),
        max_length=20,
        choices=PROFILE_TYPE_CHOICES,
        default='subscription'
    )
    validity_type = models.CharField(
        _('Type de validité'),
        max_length=20,
        choices=VALIDITY_TYPE_CHOICES,
        default='duration'
    )
    validity_duration = models.IntegerField(
        _('Durée de validité (jours)'),
        null=True, blank=True,
        help_text=_('Nombre de jours de validité. Null si lié à un événement.')
    )

    # Relations
    linked_event = models.ForeignKey(
        'competitions.Competition',
        verbose_name=_('Événement lié'),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='membership_profiles'
    )
    created_by_organization = models.ForeignKey(
        'organizations.Organization',
        verbose_name=_('Organisation créatrice'),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_membership_profiles'
    )

    # Portée
    is_global = models.BooleanField(
        _('Profil global'),
        default=False,
        help_text=_('Profil créé par le super admin, applicable à tous.')
    )

    # Configuration des features (stocké en JSON pour flexibilité)
    feature_overrides = models.JSONField(
        _('Surcharges de features'),
        default=dict,
        blank=True,
        help_text=_('Format: {"feature_code": true/false}')
    )

    # Tarification
    pricing_model = models.CharField(
        _('Modèle de tarification'),
        max_length=20,
        choices=PRICING_MODEL_CHOICES,
        default='per_member'
    )
    price = models.DecimalField(
        _('Prix'),
        max_digits=10, decimal_places=2,
        default=Decimal('0.00')
    )
    currency = models.CharField(
        _('Devise'),
        max_length=3,
        default='EUR'
    )

    # Contraintes
    max_participants = models.IntegerField(
        _('Nombre max de participants'),
        default=0,
        help_text=_('0 = illimité')
    )
    allowed_disciplines = models.ManyToManyField(
        'competitions.Discipline',
        verbose_name=_('Disciplines autorisées'),
        blank=True,
        related_name='membership_profiles'
    )
    requires_approval = models.BooleanField(
        _('Approbation requise'),
        default=False
    )

    # Statut
    is_active = models.BooleanField(_('Actif'), default=True)

    # Timestamps
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    objects = MembershipProfileManager()

    class Meta:
        verbose_name = _('Profil de membership')
        verbose_name_plural = _('Profils de membership')
        ordering = ['-is_global', 'name']
        indexes = [
            models.Index(fields=['profile_type', 'is_active']),
            models.Index(fields=['is_global', 'is_active']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Vérifie si le profil est valide et actif."""
        return self.is_active

    def get_features(self):
        """
        Retourne la liste des features disponibles pour ce profil.
        Utilise le JSONField feature_overrides.
        """
        return self.feature_overrides or {}

    def can_access(self, feature_code):
        """Vérifie si ce profil donne accès à une feature."""
        features = self.get_features()
        return features.get(feature_code, False)

    def get_price_display(self):
        """Retourne le prix formaté."""
        if self.pricing_model == 'free':
            return _('Gratuit')
        return f"{self.price} {self.currency}"


class EventPassManager(models.Manager):
    """Manager personnalisé pour EventPass."""

    def active(self):
        """Retourne les passes actifs."""
        return self.filter(status='active', expires_at__gt=timezone.now())

    def pending(self):
        """Retourne les passes en attente."""
        return self.filter(status='pending')

    def for_competition(self, competition):
        """Retourne les passes pour une compétition."""
        return self.filter(competition=competition)

    def for_user(self, user):
        """Retourne les passes d'un utilisateur."""
        return self.filter(user=user)


class EventPass(models.Model):
    """
    Passe d'accès événementiel pour un utilisateur non-membre.

    Permet à un utilisateur d'accéder à une compétition spécifique
    avec un profil de membership temporaire.
    """

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('active', _('Actif')),
        ('expired', _('Expiré')),
        ('cancelled', _('Annulé')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('paid', _('Payé')),
        ('free', _('Gratuit')),
        ('refunded', _('Remboursé')),
    ]

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Utilisateur'),
        on_delete=models.CASCADE,
        related_name='event_passes'
    )
    membership_profile = models.ForeignKey(
        MembershipProfile,
        verbose_name=_('Profil de membership'),
        on_delete=models.PROTECT,
        related_name='event_passes'
    )
    competition = models.ForeignKey(
        'competitions.Competition',
        verbose_name=_('Compétition'),
        on_delete=models.CASCADE,
        related_name='event_passes'
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        verbose_name=_('Organisation'),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='event_passes',
        help_text=_('Club invité (si applicable)')
    )

    # Statuts
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    payment_status = models.CharField(
        _('Statut du paiement'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_reference = models.CharField(
        _('Référence de paiement'),
        max_length=100,
        blank=True, null=True
    )

    # Approbation
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Approuvé par'),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_event_passes'
    )
    approved_at = models.DateTimeField(_('Approuvé le'), null=True, blank=True)

    # Validité
    expires_at = models.DateTimeField(_('Expire le'))

    # Timestamps
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mis à jour le'), auto_now=True)

    objects = EventPassManager()

    class Meta:
        verbose_name = _("Passe d'événement")
        verbose_name_plural = _("Passes d'événement")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'competition']),
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['competition', 'status']),
        ]
        unique_together = ['user', 'competition', 'membership_profile']

    def __str__(self):
        return f"{self.user} - {self.competition} ({self.membership_profile})"

    def is_valid(self):
        """Vérifie si le passe est valide."""
        return (
            self.status == 'active' and
            self.expires_at > timezone.now()
        )

    def approve(self, approved_by):
        """Approuve le passe."""
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at'])

    def activate(self):
        """Active le passe."""
        self.status = 'active'
        self.save(update_fields=['status'])

    def cancel(self):
        """Annule le passe."""
        self.status = 'cancelled'
        self.save(update_fields=['status'])

    def expire(self):
        """Marque le passe comme expiré."""
        self.status = 'expired'
        self.save(update_fields=['status'])


class MembershipTransformation(models.Model):
    """
    Enregistre les transformations de membership (upgrades, downgrades, conversions).

    Utilisé pour le suivi et les statistiques des transformations.
    """

    TRANSFORMATION_TYPE_CHOICES = [
        ('upgrade', _('Mise à niveau')),
        ('downgrade', _('Rétrogradation')),
        ('conversion', _('Conversion')),
        ('new', _('Nouveau')),
    ]

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Utilisateur'),
        on_delete=models.CASCADE,
        related_name='membership_transformations'
    )
    from_profile = models.ForeignKey(
        MembershipProfile,
        verbose_name=_('Profil source'),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='transformations_from'
    )
    to_profile = models.ForeignKey(
        MembershipProfile,
        verbose_name=_('Profil cible'),
        on_delete=models.SET_NULL,
        null=True,
        related_name='transformations_to'
    )

    # Type de transformation
    transformation_type = models.CharField(
        _('Type de transformation'),
        max_length=20,
        choices=TRANSFORMATION_TYPE_CHOICES,
        default='new'
    )

    # Événement source (si conversion depuis event pass)
    source_event = models.ForeignKey(
        'competitions.Competition',
        verbose_name=_('Événement source'),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='membership_transformations'
    )

    # Réduction
    discount_applied = models.DecimalField(
        _('Réduction appliquée'),
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    discount_code = models.CharField(
        _('Code de réduction'),
        max_length=50,
        blank=True, null=True
    )

    # Timestamp
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('Transformation de membership')
        verbose_name_plural = _('Transformations de membership')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transformation_type', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        from_str = self.from_profile.name if self.from_profile else 'Aucun'
        to_str = self.to_profile.name if self.to_profile else 'Aucun'
        return f"{self.user}: {from_str} → {to_str}"


# =============================================================================
# MODÈLES MONITORING
# =============================================================================

class SystemMetricManager(models.Manager):
    """Manager personnalisé pour SystemMetric."""

    def latest(self, metric_type=None):
        """Retourne la dernière métrique d'un type donné ou toutes."""
        qs = self.all()
        if metric_type:
            qs = qs.filter(metric_type=metric_type)
        return qs.order_by('-recorded_at').first()

    def history(self, hours=24, metric_type=None):
        """Retourne l'historique des métriques sur les X dernières heures."""
        since = timezone.now() - timezone.timedelta(hours=hours)
        qs = self.filter(recorded_at__gte=since)
        if metric_type:
            qs = qs.filter(metric_type=metric_type)
        return qs.order_by('recorded_at')

    def aggregate_by_hour(self, hours=24, metric_type=None):
        """Agrège les métriques par heure."""
        from django.db.models.functions import TruncHour
        since = timezone.now() - timezone.timedelta(hours=hours)
        qs = self.filter(recorded_at__gte=since)
        if metric_type:
            qs = qs.filter(metric_type=metric_type)
        return qs.annotate(
            hour=TruncHour('recorded_at')
        ).values('hour').annotate(
            avg_value=models.Avg('value'),
            max_value=models.Max('value'),
            min_value=models.Min('value')
        ).order_by('hour')


class SystemMetric(models.Model):
    """
    Stocke les métriques système collectées périodiquement.
    """

    METRIC_TYPE_CHOICES = [
        ('db_size', _('Taille base de données')),
        ('db_connections', _('Connexions DB')),
        ('storage_total', _('Stockage total')),
        ('storage_used', _('Stockage utilisé')),
        ('cpu_usage', _('Utilisation CPU')),
        ('memory_usage', _('Utilisation mémoire')),
        ('active_users', _('Utilisateurs actifs')),
        ('requests_per_minute', _('Requêtes par minute')),
    ]

    metric_type = models.CharField(
        _('Type de métrique'),
        max_length=30,
        choices=METRIC_TYPE_CHOICES
    )
    value = models.DecimalField(
        _('Valeur'),
        max_digits=20, decimal_places=4
    )
    unit = models.CharField(
        _('Unité'),
        max_length=20,
        help_text=_("Ex: 'GB', '%', 'count', 'req/min'")
    )
    recorded_at = models.DateTimeField(_('Enregistré le'), auto_now_add=True)
    metadata = models.JSONField(
        _('Métadonnées'),
        null=True, blank=True,
        help_text=_('Détails supplémentaires')
    )

    objects = SystemMetricManager()

    class Meta:
        verbose_name = _('Métrique système')
        verbose_name_plural = _('Métriques système')
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', 'recorded_at']),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} {self.unit}"


class ServiceStatus(models.Model):
    """
    Stocke le statut des services de la plateforme.
    """

    SERVICE_NAME_CHOICES = [
        ('web', _('Serveur Web')),
        ('database', _('Base de données')),
        ('redis', _('Redis')),
        ('celery', _('Celery Worker')),
        ('celery_beat', _('Celery Beat')),
        ('nginx', _('Nginx')),
    ]

    STATUS_CHOICES = [
        ('ok', _('OK')),
        ('warning', _('Avertissement')),
        ('error', _('Erreur')),
        ('unknown', _('Inconnu')),
    ]

    service_name = models.CharField(
        _('Nom du service'),
        max_length=20,
        choices=SERVICE_NAME_CHOICES,
        unique=True
    )
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='unknown'
    )
    response_time_ms = models.IntegerField(
        _('Temps de réponse (ms)'),
        null=True, blank=True
    )
    pid = models.IntegerField(
        _('PID'),
        null=True, blank=True
    )
    cpu_percent = models.DecimalField(
        _('CPU (%)'),
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    memory_mb = models.DecimalField(
        _('Mémoire (MB)'),
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )
    last_check = models.DateTimeField(_('Dernière vérification'), auto_now=True)
    error_message = models.TextField(
        _("Message d'erreur"),
        blank=True, null=True
    )

    class Meta:
        verbose_name = _('Statut de service')
        verbose_name_plural = _('Statuts des services')

    def __str__(self):
        return f"{self.get_service_name_display()}: {self.get_status_display()}"

    @classmethod
    def check_all(cls):
        """Vérifie tous les services et met à jour leur statut."""
        from apps.superadmin.services.system_control import SystemControlService
        service = SystemControlService()
        return service.check_all_services()


class AdminAction(models.Model):
    """
    Enregistre les actions d'administration pour l'audit.
    """

    ACTION_TYPE_CHOICES = [
        ('restart_service', _('Redémarrage service')),
        ('maintenance_mode', _('Mode maintenance')),
        ('emergency_stop', _("Arrêt d'urgence")),
        ('config_change', _('Modification configuration')),
        ('profile_create', _('Création de profil')),
        ('profile_modify', _('Modification de profil')),
        ('profile_delete', _('Suppression de profil')),
        ('user_action', _('Action utilisateur')),
        ('backup_trigger', _('Déclenchement backup')),
        ('cache_clear', _('Vidage cache')),
    ]

    STATUS_CHOICES = [
        ('initiated', _('Initié')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
    ]

    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Administrateur'),
        on_delete=models.SET_NULL,
        null=True,
        related_name='admin_actions'
    )
    action_type = models.CharField(
        _("Type d'action"),
        max_length=30,
        choices=ACTION_TYPE_CHOICES
    )
    target_service = models.CharField(
        _('Service cible'),
        max_length=50,
        blank=True, null=True
    )
    target_object_type = models.CharField(
        _("Type d'objet cible"),
        max_length=100,
        blank=True, null=True
    )
    target_object_id = models.IntegerField(
        _("ID de l'objet cible"),
        null=True, blank=True
    )
    description = models.TextField(_('Description'))
    ip_address = models.GenericIPAddressField(_('Adresse IP'))
    user_agent = models.TextField(_('User Agent'))
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )
    result_message = models.TextField(
        _('Message de résultat'),
        blank=True, null=True
    )
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    completed_at = models.DateTimeField(_('Terminé le'), null=True, blank=True)

    class Meta:
        verbose_name = _("Action d'administration")
        verbose_name_plural = _("Actions d'administration")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['admin_user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.admin_user}: {self.get_action_type_display()} ({self.status})"

    def complete(self, success=True, message=''):
        """Marque l'action comme terminée."""
        self.status = 'completed' if success else 'failed'
        self.result_message = message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'result_message', 'completed_at'])


class PlatformAlert(models.Model):
    """
    Alertes de la plateforme (disk space, services, etc.).
    """

    ALERT_TYPE_CHOICES = [
        ('disk_space', _('Espace disque')),
        ('db_connections', _('Connexions DB')),
        ('memory', _('Mémoire')),
        ('service_down', _('Service hors ligne')),
        ('high_error_rate', _("Taux d'erreur élevé")),
        ('security', _('Sécurité')),
        ('performance', _('Performance')),
    ]

    SEVERITY_CHOICES = [
        ('info', _('Information')),
        ('warning', _('Avertissement')),
        ('critical', _('Critique')),
    ]

    alert_type = models.CharField(
        _("Type d'alerte"),
        max_length=30,
        choices=ALERT_TYPE_CHOICES
    )
    severity = models.CharField(
        _('Sévérité'),
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='warning'
    )
    title = models.CharField(_('Titre'), max_length=200)
    message = models.TextField(_('Message'))
    is_resolved = models.BooleanField(_('Résolu'), default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Résolu par'),
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField(_('Résolu le'), null=True, blank=True)
    auto_resolved = models.BooleanField(_('Résolution automatique'), default=False)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)

    class Meta:
        verbose_name = _('Alerte plateforme')
        verbose_name_plural = _('Alertes plateforme')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'is_resolved', 'created_at']),
            models.Index(fields=['severity', 'is_resolved']),
        ]

    def __str__(self):
        status = '✓' if self.is_resolved else '!'
        return f"[{status}] {self.title}"

    def resolve(self, user=None, auto=False):
        """Résout l'alerte."""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.auto_resolved = auto
        if user:
            self.resolved_by = user
        self.save(update_fields=['is_resolved', 'resolved_at', 'resolved_by', 'auto_resolved'])

    @classmethod
    def create_if_threshold(cls, alert_type, severity, title, message, threshold_check=True):
        """
        Crée une alerte si la condition est remplie et qu'une alerte similaire
        non résolue n'existe pas déjà.
        """
        if not threshold_check:
            return None

        # Vérifier si une alerte similaire existe déjà
        existing = cls.objects.filter(
            alert_type=alert_type,
            is_resolved=False
        ).first()

        if existing:
            return existing

        # Créer la nouvelle alerte
        return cls.objects.create(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message
        )
