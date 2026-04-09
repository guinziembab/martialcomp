"""
Modeles pour le module core.
Inclut les modeles d'audit et de securite.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class DisciplineAccessLog(models.Model):
    """
    PHASE 3 SECURITY: Journal des acces aux donnees par discipline.

    Ce modele enregistre toutes les tentatives d'acces aux donnees
    filtrees par discipline, permettant un audit de securite complet.

    Usage:
        DisciplineAccessLog.log_access(
            user=request.user,
            discipline=discipline,
            organization=organization,
            action='view',
            allowed=True,
            ip_address=get_client_ip(request)
        )
    """

    ACTION_CHOICES = [
        ('view', _('Consultation')),
        ('edit', _('Modification')),
        ('create', _('Creation')),
        ('delete', _('Suppression')),
        ('export', _('Export')),
        ('api_access', _('Acces API')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='discipline_access_logs',
        verbose_name=_('Utilisateur')
    )
    discipline = models.ForeignKey(
        'competitions.Discipline',
        on_delete=models.CASCADE,
        related_name='access_logs',
        verbose_name=_('Discipline')
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='discipline_access_logs',
        verbose_name=_('Organisation'),
        null=True,
        blank=True
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_('Action')
    )
    allowed = models.BooleanField(
        verbose_name=_('Autorise'),
        help_text=_("Indique si l'acces a ete autorise ou refuse")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Horodatage')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('Adresse IP')
    )
    user_agent = models.TextField(
        blank=True,
        default='',
        verbose_name=_('User Agent')
    )
    resource_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name=_('Type de ressource'),
        help_text=_("Ex: Grade, Practitioner, Competition")
    )
    resource_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('ID de la ressource')
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Details'),
        help_text=_("Informations supplementaires en JSON")
    )

    class Meta:
        app_label = 'core'
        verbose_name = _('Journal acces discipline')
        verbose_name_plural = _('Journaux acces disciplines')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['discipline', '-timestamp']),
            models.Index(fields=['allowed', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]

    def __str__(self):
        status = "OK" if self.allowed else "DENIED"
        return f"[{status}] {self.user.username} - {self.discipline} - {self.action} ({self.timestamp})"

    @classmethod
    def log_access(cls, user, discipline, action, allowed,
                   organization=None, ip_address=None, user_agent='',
                   resource_type='', resource_id=None, details=None):
        """
        Methode helper pour enregistrer un acces.

        Args:
            user: L'utilisateur effectuant l'acces
            discipline: La discipline concernee
            action: Le type d'action (view, edit, create, delete, export, api_access)
            allowed: Si l'acces a ete autorise
            organization: L'organisation concernee (optionnel)
            ip_address: L'adresse IP du client (optionnel)
            user_agent: Le User-Agent du navigateur (optionnel)
            resource_type: Le type de ressource accedee (optionnel)
            resource_id: L'ID de la ressource (optionnel)
            details: Dict avec des details supplementaires (optionnel)

        Returns:
            L'instance DisciplineAccessLog creee
        """
        return cls.objects.create(
            user=user,
            discipline=discipline,
            organization=organization,
            action=action,
            allowed=allowed,
            ip_address=ip_address,
            user_agent=user_agent or '',
            resource_type=resource_type or '',
            resource_id=resource_id,
            details=details or {}
        )

    @classmethod
    def log_denied_access(cls, user, discipline, action, request=None,
                          resource_type='', resource_id=None, reason=''):
        """
        Methode helper specifique pour les acces refuses.

        Args:
            user: L'utilisateur
            discipline: La discipline
            action: L'action tentee
            request: L'objet HttpRequest (optionnel, pour extraire IP et User-Agent)
            resource_type: Le type de ressource
            resource_id: L'ID de la ressource
            reason: La raison du refus

        Returns:
            L'instance DisciplineAccessLog creee
        """
        ip_address = None
        user_agent = ''
        organization = None

        if request:
            ip_address = cls._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

            # Tenter de recuperer l'organisation de l'utilisateur
            try:
                from apps.competitions.models.users import UserProfile
                profile = UserProfile.objects.get(user=user)
                organization = profile.organization
            except:
                pass

        return cls.log_access(
            user=user,
            discipline=discipline,
            action=action,
            allowed=False,
            organization=organization,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details={'reason': reason} if reason else {}
        )

    @staticmethod
    def _get_client_ip(request):
        """Extrait l'adresse IP du client depuis la requete."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @classmethod
    def get_denied_accesses(cls, since=None, user=None, discipline=None):
        """
        Recupere les acces refuses pour analyse.

        Args:
            since: Datetime depuis lequel filtrer (optionnel)
            user: Filtrer par utilisateur (optionnel)
            discipline: Filtrer par discipline (optionnel)

        Returns:
            QuerySet des acces refuses
        """
        qs = cls.objects.filter(allowed=False)

        if since:
            qs = qs.filter(timestamp__gte=since)
        if user:
            qs = qs.filter(user=user)
        if discipline:
            qs = qs.filter(discipline=discipline)

        return qs.select_related('user', 'discipline', 'organization')

    @classmethod
    def get_access_stats(cls, since=None):
        """
        Retourne des statistiques d'acces.

        Args:
            since: Datetime depuis lequel calculer (optionnel)

        Returns:
            Dict avec les statistiques
        """
        from django.db.models import Count

        qs = cls.objects.all()
        if since:
            qs = qs.filter(timestamp__gte=since)

        total = qs.count()
        denied = qs.filter(allowed=False).count()
        allowed = total - denied

        by_action = qs.values('action').annotate(count=Count('id'))
        by_discipline = qs.values('discipline__name').annotate(count=Count('id'))

        return {
            'total': total,
            'allowed': allowed,
            'denied': denied,
            'denial_rate': (denied / total * 100) if total > 0 else 0,
            'by_action': list(by_action),
            'by_discipline': list(by_discipline),
        }
