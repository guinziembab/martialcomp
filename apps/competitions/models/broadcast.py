# -*- coding: utf-8 -*-
"""
Modèles pour les groupes de diffusion (Broadcast Groups).
Permet aux instructeurs d'envoyer des messages à des groupes de pratiquants.
"""

import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BroadcastGroup(models.Model):
    """
    Groupe de diffusion pour les instructeurs.
    Permet de cibler des membres par critères (âge, grade, genre) ou sélection manuelle.
    """

    TARGET_TYPE_CHOICES = [
        ('criteria', _('Par critères')),
        ('manual', _('Sélection manuelle')),
    ]

    AGE_CATEGORY_CHOICES = [
        ('enfants', _('Enfants (6-12 ans)')),
        ('juniors', _('Juniors (13-17 ans)')),
        ('adultes', _('Adultes (18+ ans)')),
        ('all', _('Tous âges')),
    ]

    GENDER_CHOICES = [
        ('male', _('Hommes')),
        ('female', _('Femmes')),
        ('all', _('Tous')),
    ]

    # Identité
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(_("Nom du groupe"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    icon = models.CharField(_("Icône"), max_length=50, default='users', blank=True)
    color = models.CharField(_("Couleur"), max_length=7, default='#6366F1', blank=True)

    # Propriétaire
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='broadcast_groups',
        verbose_name=_("Organisation")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_broadcast_groups',
        verbose_name=_("Créé par")
    )

    # Type de ciblage
    target_type = models.CharField(
        _("Type de ciblage"),
        max_length=20,
        choices=TARGET_TYPE_CHOICES,
        default='criteria'
    )

    # Critères de filtrage (si target_type='criteria')
    age_category = models.CharField(
        _("Catégorie d'âge"),
        max_length=20,
        choices=AGE_CATEGORY_CHOICES,
        default='all'
    )
    min_age = models.PositiveSmallIntegerField(
        _("Âge minimum"),
        null=True,
        blank=True,
        help_text=_("Âge minimum personnalisé (remplace la catégorie)")
    )
    max_age = models.PositiveSmallIntegerField(
        _("Âge maximum"),
        null=True,
        blank=True,
        help_text=_("Âge maximum personnalisé (remplace la catégorie)")
    )

    gender_filter = models.CharField(
        _("Filtrer par genre"),
        max_length=10,
        choices=GENDER_CHOICES,
        default='all'
    )

    # Filtrage par grade
    grades = models.ManyToManyField(
        'grades.Grade',
        blank=True,
        related_name='broadcast_groups',
        verbose_name=_("Grades spécifiques")
    )
    min_grade_level = models.PositiveSmallIntegerField(
        _("Niveau de grade minimum"),
        null=True,
        blank=True
    )
    max_grade_level = models.PositiveSmallIntegerField(
        _("Niveau de grade maximum"),
        null=True,
        blank=True
    )

    # Sélection manuelle (si target_type='manual')
    members = models.ManyToManyField(
        'competitions.Practitioner',
        blank=True,
        related_name='broadcast_groups',
        verbose_name=_("Membres manuels")
    )

    # Métadonnées
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Groupe de diffusion")
        verbose_name_plural = _("Groupes de diffusion")
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    def get_recipients(self):
        """
        Retourne les pratiquants ciblés selon les critères du groupe.
        """
        from apps.competitions.models import Practitioner

        if self.target_type == 'manual':
            return self.members.filter(is_active=True)

        # Filtrage par critères
        queryset = Practitioner.objects.filter(
            organization=self.organization,
            is_active=True
        )

        today = timezone.now().date()

        # Filtrage par catégorie d'âge prédéfinie
        if self.age_category != 'all' and not (self.min_age or self.max_age):
            if self.age_category == 'enfants':
                # 6-12 ans
                min_birth = today - timedelta(days=12 * 365)
                max_birth = today - timedelta(days=6 * 365)
                queryset = queryset.filter(
                    birth_date__gte=min_birth,
                    birth_date__lte=max_birth
                )
            elif self.age_category == 'juniors':
                # 13-17 ans
                min_birth = today - timedelta(days=17 * 365)
                max_birth = today - timedelta(days=13 * 365)
                queryset = queryset.filter(
                    birth_date__gte=min_birth,
                    birth_date__lte=max_birth
                )
            elif self.age_category == 'adultes':
                # 18+ ans
                max_birth = today - timedelta(days=18 * 365)
                queryset = queryset.filter(birth_date__lte=max_birth)

        # Âge personnalisé (remplace la catégorie)
        if self.min_age:
            max_birth = today - timedelta(days=self.min_age * 365)
            queryset = queryset.filter(birth_date__lte=max_birth)
        if self.max_age:
            min_birth = today - timedelta(days=self.max_age * 365)
            queryset = queryset.filter(birth_date__gte=min_birth)

        # Filtrage par genre
        if self.gender_filter != 'all':
            queryset = queryset.filter(gender=self.gender_filter)

        # Filtrage par grade
        if self.grades.exists():
            queryset = queryset.filter(grade__in=self.grades.all())
        elif self.min_grade_level or self.max_grade_level:
            if self.min_grade_level:
                queryset = queryset.filter(grade__level__gte=self.min_grade_level)
            if self.max_grade_level:
                queryset = queryset.filter(grade__level__lte=self.max_grade_level)

        return queryset.distinct()

    @property
    def member_count(self):
        """Nombre de membres actuels dans le groupe."""
        return self.get_recipients().count()

    @property
    def last_message_date(self):
        """Date du dernier message envoyé."""
        last_msg = self.messages.filter(sent_at__isnull=False).order_by('-sent_at').first()
        return last_msg.sent_at if last_msg else None


class BroadcastMessage(models.Model):
    """
    Message de diffusion envoyé à un groupe.
    """

    PRIORITY_CHOICES = [
        ('low', _('Faible')),
        ('normal', _('Normal')),
        ('high', _('Important')),
        ('urgent', _('Urgent')),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Groupe cible
    group = models.ForeignKey(
        BroadcastGroup,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_("Groupe")
    )

    # Contenu
    title = models.CharField(_("Titre"), max_length=200)
    content = models.TextField(_("Message"))

    # Expéditeur
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_broadcasts',
        verbose_name=_("Expéditeur")
    )

    # Classification
    priority = models.CharField(
        _("Priorité"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal'
    )

    # Timestamps
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    sent_at = models.DateTimeField(_("Envoyé le"), null=True, blank=True)
    expires_at = models.DateTimeField(_("Expire le"), null=True, blank=True)

    # Statistiques (cache)
    recipients_count = models.PositiveIntegerField(_("Nombre de destinataires"), default=0)
    read_count = models.PositiveIntegerField(_("Nombre de lectures"), default=0)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Message de diffusion")
        verbose_name_plural = _("Messages de diffusion")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['-sent_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.group.name}"

    def send(self, send_push=True):
        """
        Envoie le message à tous les destinataires.
        Crée un BroadcastReceipt pour chaque destinataire.
        Crée une Notification pour ceux qui ont un compte utilisateur.
        """
        from apps.competitions.models.notifications import Notification

        if self.sent_at:
            # Déjà envoyé
            return []

        recipients = list(self.group.get_recipients())
        notifications_created = []
        receipts_created = []

        # Mapping priorité vers notification
        priority_map = {
            'low': 'low',
            'normal': 'standard',
            'high': 'important',
            'urgent': 'critical',
        }

        for practitioner in recipients:
            notification = None

            # Créer la notification seulement si le pratiquant a un compte utilisateur
            if practitioner.user:
                notification = Notification.objects.create(
                    user=practitioner.user,
                    title=self.title,
                    message=self.content,
                    notification_type='info',
                    priority=priority_map.get(self.priority, 'standard'),
                )
                notifications_created.append(notification)

                # Envoyer push notification si demandé
                if send_push:
                    self._send_push_notification(practitioner, notification)

            # Créer le reçu de diffusion pour TOUS les pratiquants (avec ou sans compte)
            receipt = BroadcastReceipt.objects.create(
                broadcast=self,
                practitioner=practitioner,
                notification=notification  # Peut être None si pas de compte
            )
            receipts_created.append(receipt)

        # Mettre à jour les statistiques
        # recipients_count = nombre total de destinataires (pas seulement ceux avec compte)
        self.sent_at = timezone.now()
        self.recipients_count = len(receipts_created)
        self.save(update_fields=['sent_at', 'recipients_count'])

        return notifications_created

    def _send_push_notification(self, practitioner, notification):
        """
        Envoie une notification push au pratiquant.
        """
        try:
            from apps.competitions.services.notification_service import NotificationService

            # Utiliser le service existant si disponible
            if hasattr(NotificationService, 'send_push_notification'):
                NotificationService.send_push_notification(
                    user=practitioner.user,
                    title=self.title,
                    body=self.content[:200],
                    data={
                        'type': 'broadcast',
                        'broadcast_id': str(self.uuid),
                        'notification_id': str(notification.id),
                    }
                )
        except Exception:
            # Ne pas bloquer l'envoi si le push échoue
            pass

    @property
    def read_percentage(self):
        """Pourcentage de lectures."""
        if self.recipients_count == 0:
            return 0
        return round((self.read_count / self.recipients_count) * 100, 1)

    def update_read_count(self):
        """Met à jour le compteur de lectures."""
        self.read_count = self.receipts.filter(read_at__isnull=False).count()
        self.save(update_fields=['read_count'])


class BroadcastReceipt(models.Model):
    """
    Reçu de diffusion - lie un message à un destinataire.
    Permet de suivre la livraison et la lecture par destinataire.
    """

    broadcast = models.ForeignKey(
        BroadcastMessage,
        on_delete=models.CASCADE,
        related_name='receipts',
        verbose_name=_("Message")
    )
    practitioner = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='broadcast_receipts',
        verbose_name=_("Pratiquant")
    )
    notification = models.ForeignKey(
        'competitions.Notification',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='broadcast_receipt',
        verbose_name=_("Notification")
    )

    # Statut
    delivered_at = models.DateTimeField(_("Livré le"), auto_now_add=True)
    read_at = models.DateTimeField(_("Lu le"), null=True, blank=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Reçu de diffusion")
        verbose_name_plural = _("Reçus de diffusion")
        unique_together = ['broadcast', 'practitioner']
        indexes = [
            models.Index(fields=['broadcast', 'read_at']),
            models.Index(fields=['practitioner', '-delivered_at']),
        ]

    def __str__(self):
        return f"{self.broadcast.title} -> {self.practitioner.full_name}"

    def mark_as_read(self):
        """Marque le message comme lu."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

            # Marquer aussi la notification comme lue
            if self.notification:
                self.notification.is_read = True
                self.notification.read_at = self.read_at
                self.notification.save(update_fields=['is_read', 'read_at'])

            # Mettre à jour les statistiques du message
            self.broadcast.update_read_count()
