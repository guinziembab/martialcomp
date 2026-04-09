"""
Rôle Placateur — Appel des compétiteurs et gestion de présence.

Le placateur est un BÉNÉVOLE sans compte MartialComp.
Il accède à l'interface via un lien + code PIN (même pattern que AireCombat/Kiosque).
Il voit les catégories de la compétition, fait l'appel et amène les pratiquants
à l'aire indiquée. Il n'a AUCUN accès à la notation ni aux résultats.
"""
import uuid
import random
import string

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PlacateurAccess(models.Model):
    """
    Point d'accès placateur pour une compétition.
    Accès public via token URL + code PIN (pas de compte requis).
    Un organisateur peut créer plusieurs accès placateur si nécessaire.
    """
    competition = models.ForeignKey(
        'competitions.Competition', on_delete=models.CASCADE,
        related_name='placateur_accesses',
        verbose_name=_("Compétition")
    )
    nom = models.CharField(
        _("Nom du placateur"), max_length=100,
        help_text=_("Ex: Placateur Tatami 1, Marie, Bénévole Zone A")
    )

    # Accès sans authentification (même pattern que AireCombat)
    pin_code = models.CharField(
        _("Code PIN"), max_length=6,
        help_text=_("Code PIN à 4 chiffres pour accéder à l'interface")
    )
    access_token = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True,
        help_text=_("Token unique pour l'URL d'accès")
    )

    # Catégories visibles par ce placateur (vide = toutes)
    categories = models.ManyToManyField(
        'competitions.CompetitionCategory',
        related_name='placateur_accesses',
        verbose_name=_("Catégories assignées"),
        blank=True,
        help_text=_("Laisser vide pour accéder à toutes les catégories")
    )

    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Accès placateur")
        verbose_name_plural = _("Accès placateurs")
        ordering = ['competition', 'nom']

    def __str__(self):
        return f"Placateur: {self.nom} — {self.competition.title}"

    def save(self, *args, **kwargs):
        if not self.pin_code:
            self.pin_code = ''.join(random.choices(string.digits, k=4))
        super().save(*args, **kwargs)

    def regenerate_pin(self):
        self.pin_code = ''.join(random.choices(string.digits, k=4))
        self.access_token = uuid.uuid4()
        self.save(update_fields=['pin_code', 'access_token'])

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse(
            'competitions:technical_scoring:placateur_login',
            kwargs={'token': str(self.access_token)}
        )

    def get_visible_categories(self):
        """Retourne les catégories visibles par ce placateur."""
        if self.categories.exists():
            return self.categories.all()
        return self.competition.categories.all()


class CompetitorCallStatus(models.Model):
    """
    Statut d'appel de chaque compétiteur par le placateur.
    Processus : En attente → Appelé → Présent / Absent → Passé.
    """

    class Status(models.TextChoices):
        WAITING = 'waiting', _("En attente")
        CALLED = 'called', _("Appelé")
        PRESENT = 'present', _("Présent")
        ABSENT = 'absent', _("Absent")
        PASSED = 'passed', _("Passé")

    session = models.ForeignKey(
        'competitions.CategorySession', on_delete=models.CASCADE,
        related_name='call_statuses'
    )
    performance = models.ForeignKey(
        'competitions.TechnicalPerformance', on_delete=models.CASCADE,
        related_name='call_status'
    )
    placateur_access = models.ForeignKey(
        PlacateurAccess, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='call_statuses',
        verbose_name=_("Accès placateur")
    )

    status = models.CharField(
        _("Statut"), max_length=20,
        choices=Status.choices, default=Status.WAITING
    )
    call_order = models.PositiveSmallIntegerField(
        _("Ordre de passage"), default=0
    )
    called_at = models.DateTimeField(_("Appelé à"), null=True, blank=True)
    status_changed_at = models.DateTimeField(_("Modifié le"), auto_now=True)
    notes = models.CharField(_("Notes"), max_length=200, blank=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Statut d'appel compétiteur")
        verbose_name_plural = _("Statuts d'appel compétiteurs")
        ordering = ['call_order']
        unique_together = ['session', 'performance']

    def __str__(self):
        return f"{self.performance.practitioner.full_name} — {self.get_status_display()}"

    def mark_called(self):
        self.status = self.Status.CALLED
        self.called_at = timezone.now()
        self.save(update_fields=['status', 'called_at', 'status_changed_at'])

    def mark_present(self):
        self.status = self.Status.PRESENT
        self.save(update_fields=['status', 'status_changed_at'])

    def mark_absent(self):
        self.status = self.Status.ABSENT
        self.save(update_fields=['status', 'status_changed_at'])
        self.performance.is_absent = True
        self.performance.absence_noted_at = timezone.now()
        self.performance.save(update_fields=['is_absent', 'absence_noted_at'])

    def mark_passed(self):
        self.status = self.Status.PASSED
        self.save(update_fields=['status', 'status_changed_at'])
