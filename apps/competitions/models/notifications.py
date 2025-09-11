from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class Notification(models.Model):
    """
    Modèle de notification discret et professionnel
    Conforme à la directive d'amélioration du système
    """
    
    NOTIFICATION_TYPES = [
        ('info', _('Information')),
        ('warning', _('Avertissement')),
        ('error', _('Erreur')),
        ('success', _('Succès')),
    ]
    
    PRIORITY_LEVELS = [
        ('low', _('Faible')),
        ('standard', _('Standard')),
        ('important', _('Important')),
        ('critical', _('Critique')),
    ]
    
    # Destinataire
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    
    # Contenu de la notification
    title = models.CharField(max_length=200, verbose_name=_("Titre"))
    message = models.TextField(verbose_name=_("Message"))
    
    # Classification
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES, 
        default='info',
        verbose_name=_("Type de notification")
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='standard',
        verbose_name=_("Priorité")
    )
    
    # État de lecture
    is_read = models.BooleanField(default=False, verbose_name=_("Lu"))
    read_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Lu le"))
    
    # Métadonnées - CORRIGÉ: Utilisation de timezone.now au lieu de auto_now_add
    created_at = models.DateTimeField(default=timezone.now, verbose_name=_("Créé le"))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Expire le"))
    
    # Liens et actions
    action_url = models.URLField(null=True, blank=True, verbose_name=_("URL d'action"))
    action_text = models.CharField(max_length=100, null=True, blank=True, verbose_name=_("Texte d'action"))
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
        
    def __str__(self):
        return f"{self.title} ({self.user.username})"
        
    def save(self, *args, **kwargs):
        """
        Surcharge save pour s'assurer que created_at a un timezone
        """
        # S'assurer que created_at a un timezone si défini manuellement
        if self.created_at and timezone.is_naive(self.created_at):
            self.created_at = timezone.make_aware(self.created_at)
        
        # Si created_at n'est pas défini, utiliser maintenant
        if not self.created_at:
            self.created_at = timezone.now()
            
        super().save(*args, **kwargs)
        
    def mark_as_read(self):
        """Marque la notification comme lue"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
            
    @property
    def is_expired(self):
        """Vérifie si la notification a expiré"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
        
    @property
    def css_class(self):
        """Retourne la classe CSS selon le type"""
        return {
            'info': 'text-info',
            'warning': 'text-warning', 
            'error': 'text-danger',
            'success': 'text-success',
        }.get(self.notification_type, 'text-info')
        
    @property
    def icon_class(self):
        """Retourne l'icône selon le type"""
        return {
            'info': 'fas fa-info-circle',
            'warning': 'fas fa-exclamation-triangle',
            'error': 'fas fa-exclamation-circle',
            'success': 'fas fa-check-circle',
        }.get(self.notification_type, 'fas fa-info-circle')


class NotificationPreference(models.Model):
    """
    Préférences de notification pour chaque utilisateur
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Préférences par type de notification (méthodes d'envoi)
    email_enabled = models.BooleanField(default=True, verbose_name=_("Email activé"))
    sms_enabled = models.BooleanField(default=False, verbose_name=_("SMS activé"))
    push_enabled = models.BooleanField(default=True, verbose_name=_("Notifications push activées"))
    
    # Préférences par catégorie
    competition_notifications = models.BooleanField(default=True, verbose_name=_("Notifications de compétition"))
    training_notifications = models.BooleanField(default=True, verbose_name=_("Notifications d'entraînement"))
    grade_notifications = models.BooleanField(default=True, verbose_name=_("Notifications de grade"))
    order_notifications = models.BooleanField(default=True, verbose_name=_("Notifications de commande"))
    membership_notifications = models.BooleanField(default=True, verbose_name=_("Notifications d'adhésion"))
    message_notifications = models.BooleanField(default=True, verbose_name=_("Notifications de message"))
    system_notifications = models.BooleanField(default=True, verbose_name=_("Notifications système"))
    
    # Fréquence
    FREQUENCY_CHOICES = [
        ('immediate', _('Immédiat')),
        ('daily', _('Quotidien')),
        ('weekly', _('Hebdomadaire')),
    ]
    
    notification_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='immediate',
        verbose_name=_("Fréquence des notifications")
    )
    
    # Heures de silence
    quiet_hours_start = models.TimeField(null=True, blank=True, verbose_name=_("Début des heures de silence"))
    quiet_hours_end = models.TimeField(null=True, blank=True, verbose_name=_("Fin des heures de silence"))
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Préférence de notification")
        verbose_name_plural = _("Préférences de notifications")
        
    def __str__(self):
        return f"Préférences de {self.user.username}"