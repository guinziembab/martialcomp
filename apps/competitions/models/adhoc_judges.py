# apps/competitions/models/adhoc_judges.py
"""
Modèle pour la gestion des juges ad-hoc (temporaires/bénévoles).
Permet de recruter des pratiquants adultes pour aider à juger lors des compétitions.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from datetime import date


class AdHocJudge(models.Model):
    """
    Juge temporaire recruté parmi les participants pour une compétition.
    Permet de gérer les juges bénévoles qui ne sont pas des juges officiels.
    """

    STATUS_CHOICES = [
        ('pending', _('En attente de confirmation')),
        ('active', _('Actif')),
        ('completed', _('Mission terminée')),
        ('declined', _('A décliné')),
        ('revoked', _('Révoqué')),
    ]

    JUDGE_TYPE_CHOICES = [
        ('technical_judge', _('Juge Technique')),
        ('combat_referee', _('Arbitre Combat')),
        ('assistant_referee', _('Arbitre Assistant')),
        ('timekeeper', _('Chronométreur')),
        ('scorekeeper', _('Marqueur')),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ('novice', _('Novice - Première expérience')),
        ('beginner', _('Débutant - Quelques compétitions')),
        ('intermediate', _('Intermédiaire - Expérience régulière')),
        ('experienced', _('Expérimenté - Nombreuses compétitions')),
    ]

    SOURCE_CHOICES = [
        ('competition_participant', _('Participant à cette compétition')),
        ('club_member', _('Membre du club organisateur')),
        ('discipline_practitioner', _('Pratiquant de la discipline')),
        ('external_volunteer', _('Bénévole externe')),
        ('official_judge', _('Juge officiel certifié')),
    ]

    # Relations principales
    competition = models.ForeignKey(
        'Competition',
        on_delete=models.CASCADE,
        related_name='adhoc_judges',
        verbose_name=_("Compétition")
    )
    practitioner = models.ForeignKey(
        'Practitioner',
        on_delete=models.CASCADE,
        related_name='adhoc_judge_assignments',
        verbose_name=_("Pratiquant")
    )

    # Source du recrutement
    source = models.CharField(
        _("Source de recrutement"),
        max_length=30,
        choices=SOURCE_CHOICES,
        default='competition_participant'
    )

    # Type et statut
    judge_type = models.CharField(
        _("Type de juge"),
        max_length=20,
        choices=JUDGE_TYPE_CHOICES,
        default='technical_judge'
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    experience_level = models.CharField(
        _("Niveau d'expérience"),
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        default='novice'
    )

    # Catégories assignées
    assigned_categories = models.ManyToManyField(
        'CompetitionCategory',
        related_name='adhoc_judges',
        verbose_name=_("Catégories assignées"),
        blank=True
    )

    # Période d'activation
    activated_at = models.DateTimeField(_("Activé le"), null=True, blank=True)
    deactivated_at = models.DateTimeField(_("Désactivé le"), null=True, blank=True)

    # Traçabilité
    recruited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recruited_adhoc_judges',
        verbose_name=_("Recruté par")
    )
    recruitment_date = models.DateTimeField(_("Date de recrutement"), auto_now_add=True)

    # Consentement et briefing
    has_accepted = models.BooleanField(_("A accepté la mission"), default=False)
    briefing_completed = models.BooleanField(_("Briefing effectué"), default=False)
    briefing_date = models.DateTimeField(_("Date du briefing"), null=True, blank=True)

    # Notes et évaluation
    notes = models.TextField(_("Notes"), blank=True)
    performance_rating = models.PositiveSmallIntegerField(
        _("Évaluation de performance"),
        null=True,
        blank=True,
        help_text=_("Note de 1 à 5 sur la qualité du travail")
    )
    performance_comments = models.TextField(_("Commentaires sur la performance"), blank=True)

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Juge ad-hoc")
        verbose_name_plural = _("Juges ad-hoc")
        unique_together = ['competition', 'practitioner', 'judge_type']
        ordering = ['-recruitment_date']

    def __str__(self):
        return f"{self.practitioner.full_name} - {self.get_judge_type_display()} ({self.competition.title})"

    def activate(self, user=None):
        """Active le juge ad-hoc et lui donne accès au dashboard."""
        self.status = 'active'
        self.activated_at = timezone.now()
        self.has_accepted = True
        self.save()

        # Activer le flag juge dans la registration si existante
        self._update_registration_flags(True)

        # Créer un compte utilisateur si nécessaire
        if not self.practitioner.user:
            self.practitioner.create_user_account()

        return True

    def deactivate(self, reason='completed'):
        """Désactive le juge ad-hoc."""
        self.status = reason
        self.deactivated_at = timezone.now()
        self.save()

        # Retirer le flag juge de la registration
        self._update_registration_flags(False)

    def mark_briefing_completed(self):
        """Marque le briefing comme effectué."""
        self.briefing_completed = True
        self.briefing_date = timezone.now()
        self.save()

    def _update_registration_flags(self, is_judge: bool):
        """Met à jour les flags de juge dans l'inscription."""
        from .registrations import CompetitionRegistration

        try:
            registration = CompetitionRegistration.objects.get(
                competition=self.competition,
                practitioner=self.practitioner
            )
            if self.judge_type == 'technical_judge':
                registration.is_technical_judge = is_judge
            elif self.judge_type in ['combat_referee', 'assistant_referee']:
                registration.is_combat_referee = is_judge
            registration.save()
        except CompetitionRegistration.DoesNotExist:
            pass

    @property
    def is_active(self):
        """Vérifie si le juge est actuellement actif."""
        return self.status == 'active'

    @property
    def practitioner_age(self):
        """Retourne l'âge du pratiquant."""
        return self.practitioner.age if self.practitioner else None

    @property
    def can_access_judge_dashboard(self):
        """Vérifie si le juge peut accéder au dashboard juge."""
        return self.is_active and self.practitioner.user is not None

    @classmethod
    def get_eligible_participants(cls, competition, judge_type='technical_judge', min_age=18):
        """
        Retourne les participants éligibles pour être juges ad-hoc.

        Critères:
        - Âge minimum (par défaut 18 ans)
        - Inscrits à la compétition OU pratiquants adultes de la discipline

        Note: Les pratiquants déjà recrutés sont inclus dans la liste
        pour permettre l'affichage de leur statut dans l'interface.
        """
        from .practitioners import Practitioner
        from .registrations import CompetitionRegistration

        # Calculer la date de naissance maximum pour avoir min_age
        today = date.today()
        max_birth_date = date(today.year - min_age, today.month, today.day)

        # Option 1: Participants inscrits à la compétition (adultes)
        # Inclure les statuts 'approved' et 'pending' (inscriptions validées ou en attente)
        registered_ids = CompetitionRegistration.objects.filter(
            competition=competition,
            status__in=['approved', 'pending', 'confirmed']
        ).values_list('practitioner_id', flat=True)

        # Ne plus exclure les pratiquants déjà assignés pour qu'ils restent visibles
        eligible_registered = Practitioner.objects.filter(
            id__in=registered_ids,
            birth_date__lte=max_birth_date,
            is_active=True
        ).select_related('organization')

        # Option 2: Pratiquants adultes de la discipline (non inscrits)
        # Récupérer les disciplines de la compétition
        discipline_ids = []
        if hasattr(competition, 'disciplines'):
            discipline_ids = list(competition.disciplines.values_list('id', flat=True))
        elif hasattr(competition, 'discipline') and competition.discipline:
            discipline_ids = [competition.discipline.id]

        eligible_discipline = Practitioner.objects.none()
        if discipline_ids:
            eligible_discipline = Practitioner.objects.filter(
                birth_date__lte=max_birth_date,
                is_active=True
            ).filter(
                models.Q(primary_discipline_id__in=discipline_ids) |
                models.Q(secondary_disciplines__id__in=discipline_ids)
            ).exclude(
                id__in=registered_ids  # Exclure ceux déjà dans la liste des inscrits
            ).distinct().select_related('organization')

        return {
            'registered_participants': eligible_registered,
            'discipline_practitioners': eligible_discipline,
        }

    @classmethod
    def get_active_for_competition(cls, competition):
        """Retourne tous les juges ad-hoc actifs pour une compétition."""
        return cls.objects.filter(
            competition=competition,
            status='active'
        ).select_related('practitioner', 'practitioner__organization').prefetch_related('assigned_categories')

    @classmethod
    def get_for_practitioner(cls, practitioner):
        """Retourne toutes les assignations ad-hoc d'un pratiquant."""
        return cls.objects.filter(
            practitioner=practitioner
        ).select_related('competition').prefetch_related('assigned_categories')

    @classmethod
    def get_active_for_practitioner(cls, practitioner):
        """Retourne les assignations ad-hoc actives d'un pratiquant."""
        today = date.today()
        return cls.objects.filter(
            practitioner=practitioner,
            status='active',
            competition__end_date__gte=today
        ).select_related('competition').prefetch_related('assigned_categories')
