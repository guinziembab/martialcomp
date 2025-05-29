from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from organizations.models import Organization, OrganizationMember, OrganizationRole


class Notification(models.Model):
    """Modèle pour les notifications des utilisateurs."""
    
    TYPE_CHOICES = [
        ('competition', _('Compétition')),
        ('order', _('Commande')),
        ('grade', _('Grade')),
        ('membership', _('Adhésion')),
        ('training', _('Entraînement')),
        ('message', _('Message')),
        ('system', _('Système')),
    ]
    
    PRIORITY_CHOICES = [
        ('low', _('Basse')),
        ('medium', _('Moyenne')),
        ('high', _('Haute')),
        ('urgent', _('Urgente')),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_("Utilisateur")
    )
    type = models.CharField(_("Type"), max_length=20, choices=TYPE_CHOICES, default='system')
    priority = models.CharField(_("Priorité"), max_length=10, choices=PRIORITY_CHOICES, default='medium')
    
    title = models.CharField(_("Titre"), max_length=200)
    message = models.TextField(_("Message"))
    
    # Lien optionnel vers un objet
    link = models.CharField(_("Lien"), max_length=255, blank=True)
    
    # Métadonnées
    is_read = models.BooleanField(_("Lu"), default=False)
    is_actionable = models.BooleanField(_("Actionnable"), default=False)
    action_text = models.CharField(_("Texte d'action"), max_length=50, blank=True)
    action_url = models.CharField(_("URL d'action"), max_length=200, blank=True)
    
    # Dates
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    read_at = models.DateTimeField(_("Lu le"), null=True, blank=True)
    expires_at = models.DateTimeField(_("Expire le"), null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_type_display()} - {self.title}"
    
    def mark_as_read(self):
        """Marque la notification comme lue."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    @property
    def is_expired(self):
        """Vérifie si la notification a expiré."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']


class NotificationPreference(models.Model):
    """Préférences de notification par utilisateur."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notification_preferences'
    )
    
    # Types de notifications activées
    competition_notifications = models.BooleanField(_("Notifications de compétition"), default=True)
    order_notifications = models.BooleanField(_("Notifications de commande"), default=True)
    grade_notifications = models.BooleanField(_("Notifications de grade"), default=True)
    membership_notifications = models.BooleanField(_("Notifications d'adhésion"), default=True)
    training_notifications = models.BooleanField(_("Notifications d'entraînement"), default=True)
    message_notifications = models.BooleanField(_("Notifications de message"), default=True)
    system_notifications = models.BooleanField(_("Notifications système"), default=True)
    
    # Canaux de notification
    email_enabled = models.BooleanField(_("Email activé"), default=True)
    sms_enabled = models.BooleanField(_("SMS activé"), default=False)
    push_enabled = models.BooleanField(_("Push activé"), default=True)
    
    # Fréquence
    notification_frequency = models.CharField(
        _("Fréquence"),
        max_length=20,
        choices=[
            ('instant', _('Instantané')),
            ('hourly', _('Toutes les heures')),
            ('daily', _('Quotidien')),
            ('weekly', _('Hebdomadaire')),
        ],
        default='instant'
    )
    
    # Heures de notification
    quiet_hours_start = models.TimeField(_("Début heures silencieuses"), null=True, blank=True)
    quiet_hours_end = models.TimeField(_("Fin heures silencieuses"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    class Meta:
        verbose_name = _("Préférence de notification")
        verbose_name_plural = _("Préférences de notification")