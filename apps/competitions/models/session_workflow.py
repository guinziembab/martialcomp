"""
Session de notation technique — Workflow Juge Principal.

Gère le lifecycle : PENDING → STARTED → STOPPED → VALIDATED → CLOSED
avec contrôle d'accès strict entre Juge Principal et Admin Central.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CategorySession(models.Model):
    """
    Session de notation pour une catégorie.
    Gère le lifecycle Start → Stop → Validation → Clôture.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', _("En attente")
        STARTED = 'started', _("En cours")
        STOPPED = 'stopped', _("Notation terminée")
        VALIDATING = 'validating', _("En vérification")
        VALIDATED = 'validated', _("Validée")
        NEEDS_REVOTE = 'needs_revote', _("2e tour requis")
        CLOSED = 'closed', _("Clôturée")

    VALIDATION_RESULTS = [
        ('ok', _("Validé — aucun conflit")),
        ('tie', _("Égalité détectée — 2e tour requis")),
        ('conflict', _("Conflit de position détecté")),
    ]

    competition = models.ForeignKey(
        'competitions.Competition', on_delete=models.CASCADE,
        related_name='category_sessions'
    )
    category = models.ForeignKey(
        'competitions.CompetitionCategory', on_delete=models.CASCADE,
        related_name='sessions'
    )

    # Acteurs
    head_judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='head_judge_sessions',
        verbose_name=_("Juge principal")
    )

    # État
    status = models.CharField(
        _("Statut"), max_length=20,
        choices=Status.choices, default=Status.PENDING
    )
    round_number = models.PositiveSmallIntegerField(
        _("Numéro du tour"), default=1
    )

    # Timestamps
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    started_at = models.DateTimeField(_("Démarré le"), null=True, blank=True)
    stopped_at = models.DateTimeField(_("Arrêté le"), null=True, blank=True)
    validated_at = models.DateTimeField(_("Validé le"), null=True, blank=True)
    closed_at = models.DateTimeField(_("Clôturé le"), null=True, blank=True)

    # Résultat de validation
    validation_result = models.CharField(
        _("Résultat"), max_length=20, blank=True,
        choices=VALIDATION_RESULTS
    )
    validation_notes = models.TextField(_("Notes de validation"), blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='validated_sessions',
        verbose_name=_("Validé par")
    )

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Session de catégorie")
        verbose_name_plural = _("Sessions de catégorie")
        unique_together = ['category', 'round_number']
        ordering = ['competition', 'category', 'round_number']

    def __str__(self):
        return f"{self.category} — Tour {self.round_number} — {self.get_status_display()}"

    # ── Transitions d'état ──

    def start(self, user):
        if self.status not in (self.Status.PENDING, self.Status.STOPPED):
            raise ValueError(_("La session ne peut être démarrée que depuis l'état 'En attente' ou 'Notation terminée'"))
        if user != self.head_judge:
            raise PermissionError(_("Seul le juge principal peut démarrer la session"))
        self.status = self.Status.STARTED
        if not self.started_at:
            self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])

    def stop(self, user):
        if self.status != self.Status.STARTED:
            raise ValueError(_("La session ne peut être arrêtée que depuis l'état 'En cours'"))
        if user != self.head_judge:
            raise PermissionError(_("Seul le juge principal peut arrêter la session"))
        self.status = self.Status.STOPPED
        self.stopped_at = timezone.now()
        self.save(update_fields=['status', 'stopped_at'])
        self._notify_admin_verification_needed()

    def validate(self, user, result, notes=''):
        if self.status not in (self.Status.STOPPED, self.Status.VALIDATING):
            raise ValueError(_("La session doit être en état 'Notation terminée' pour être validée"))
        self.validated_by = user
        self.validated_at = timezone.now()
        self.validation_result = result
        self.validation_notes = notes
        if result == 'ok':
            self.status = self.Status.VALIDATED
        else:
            self.status = self.Status.NEEDS_REVOTE
        self.save(update_fields=[
            'status', 'validated_by', 'validated_at',
            'validation_result', 'validation_notes'
        ])
        self._notify_head_judge_validation_result()

    def close(self, user):
        if self.status != self.Status.VALIDATED:
            raise ValueError(_("La session doit être validée avant d'être clôturée"))
        if user != self.head_judge:
            raise PermissionError(_("Seul le juge principal peut clôturer la session"))
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=['status', 'closed_at'])
        self._publish_results()

    def create_next_round(self):
        if self.status != self.Status.NEEDS_REVOTE:
            raise ValueError(_("Un nouveau tour ne peut être créé que si un 2e tour est requis"))
        return CategorySession.objects.create(
            competition=self.competition,
            category=self.category,
            head_judge=self.head_judge,
            round_number=self.round_number + 1,
            status=self.Status.PENDING
        )

    # ── Propriétés calculées ──

    @property
    def scoring_progress(self):
        total_expected = self._count_expected_scores()
        total_submitted = self._count_submitted_scores()
        if total_expected == 0:
            return 0
        return int((total_submitted / total_expected) * 100)

    @property
    def is_scoring_allowed(self):
        return self.status == self.Status.STARTED

    @property
    def has_ties(self):
        rankings = self._compute_rankings()
        if not rankings:
            return False
        scores = [r['final_score'] for r in rankings]
        return len(scores) != len(set(scores))

    # ── Méthodes privées ──

    def _count_expected_scores(self):
        from apps.competitions.models.technical_scoring import (
            TechnicalPerformance, ScoringCriterion
        )
        from apps.competitions.models.judges import JudgeAssignment
        performances = TechnicalPerformance.objects.filter(
            category=self.category
        ).exclude(is_absent=True).count()
        judges = JudgeAssignment.objects.filter(
            category=self.category,
            assignment_type='technical_judge',
            status='confirmed'
        ).count()
        criteria = ScoringCriterion.objects.filter(
            category=self.category, is_active=True
        ).count()
        return performances * judges * criteria

    def _count_submitted_scores(self):
        from apps.competitions.models.technical_scoring import TechnicalScore
        return TechnicalScore.objects.filter(
            performance__category=self.category,
            round_number=self.round_number
        ).count()

    def _notify_admin_verification_needed(self):
        try:
            from apps.competitions.models.notifications import Notification
            # Notifier les staff et admins de la compétition
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title=_("Catégorie terminée — vérification requise"),
                    message=_(
                        "La catégorie '%(category)s' (Tour %(round)d) "
                        "a terminé la notation. Veuillez vérifier les résultats."
                    ) % {'category': str(self.category), 'round': self.round_number},
                    notification_type='warning',
                    priority='important',
                    action_url=f'/competitions/technical-scoring/session/{self.pk}/progress/',
                    action_text=_("Vérifier")
                )
        except Exception:
            pass

    def _notify_head_judge_validation_result(self):
        if not self.head_judge:
            return
        try:
            from apps.competitions.models.notifications import Notification
            if self.validation_result == 'ok':
                title = _("Catégorie validée")
                message = _("La catégorie a été validée. Vous pouvez clôturer la session.")
                ntype = 'success'
            else:
                title = _("2e tour requis")
                message = _("Un 2e tour est nécessaire (égalité détectée).")
                ntype = 'warning'
            Notification.objects.create(
                user=self.head_judge,
                title=title,
                message=message,
                notification_type=ntype,
                priority='important',
                action_url=f'/competitions/technical-scoring/session/{self.pk}/progress/',
                action_text=_("Voir")
            )
        except Exception:
            pass

    def _publish_results(self):
        """Publie les résultats après clôture — à étendre selon la logique existante."""
        pass

    def _compute_rankings(self):
        """Calcule le classement provisoire."""
        from apps.competitions.models.technical_scoring import TechnicalPerformance
        performances = TechnicalPerformance.objects.filter(
            category=self.category
        ).exclude(is_absent=True)
        rankings = []
        for perf in performances:
            score = perf.calculate_final_score(round_number=self.round_number)
            rankings.append({
                'performance': perf,
                'practitioner': perf.practitioner,
                'final_score': score or 0,
            })
        rankings.sort(key=lambda r: r['final_score'], reverse=True)
        return rankings
