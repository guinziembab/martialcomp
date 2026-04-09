from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole
from . import Competition, CompetitionCategory
from . import Practitioner
from django.contrib.auth.models import User
from django.conf import settings
from .judges import JudgeTechnicalApplication

class ScoringCriterion(models.Model):
    """Critère de notation pour les compétitions techniques."""
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    weight = models.FloatField(_("Pondération"), default=1.0)
    min_score = models.FloatField(_("Score minimum"), default=0.0)
    max_score = models.FloatField(_("Score maximum"), default=10.0)
    step = models.FloatField(_("Pas de notation"), default=0.25, 
                             help_text=_("Incrément minimal pour les scores (ex: 0.25)"))
    category = models.ForeignKey('CompetitionCategory', on_delete=models.CASCADE, 
                                related_name='scoring_criteria')
    
    # Ajouter les champs manquants
    order = models.PositiveIntegerField(_("Ordre d'affichage"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Critère de notation")
        verbose_name_plural = _("Critères de notation")
        ordering = ['category', 'order', 'name']  # Utiliser order dans l'ordre

class Performance(models.Model):
    """Représente une performance Ã  évaluer dans une compétition."""
    STATUS_CHOICES = [
        ('scheduled', _('Programmée')),
        ('ready', _('PrÃªte')),
        ('in_progress', _('En cours')),
        ('pending_validation', _('En attente de validation')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée')),
    ]
    
    practitioner = models.ForeignKey('Practitioner', on_delete=models.CASCADE,
                                    related_name='performances')
    category = models.ForeignKey('CompetitionCategory', on_delete=models.CASCADE,
                                related_name='performances')
    equipe = models.ForeignKey(
        'competitions.Equipe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='performances_technique',
        verbose_name=_("Equipe"),
        help_text=_("Pour les compétitions en équipe: l'équipe notée")
    )
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, 
                             default='scheduled')
    scheduled_time = models.DateTimeField(_("Heure planifiée"), null=True, blank=True)
    start_time = models.DateTimeField(_("Heure de début"), null=True, blank=True)
    completion_time = models.DateTimeField(_("Heure de fin"), null=True, blank=True)
    order = models.PositiveIntegerField(_("Ordre de passage"), default=0)
    total_score = models.FloatField(_("Score total"), null=True, blank=True)
    ranking = models.PositiveIntegerField(_("Classement"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)
    
    def __str__(self):
        if self.equipe:
            return f"{self.equipe.nom} - {self.category}"
        return f"{self.practitioner} - {self.category}"
    
    def calculate_total_score(self):
        """Calcule le score total de cette performance selon les critères pondérés."""
        from django.db.models import Avg
        
        scores_by_criterion = {}
        total_weighted_score = 0
        total_weight = 0
        
        # Récupérer tous les critères pour cette catégorie
        criteria = ScoringCriterion.objects.filter(category=self.category, is_active=True)
        
        for criterion in criteria:
            # Calculer la moyenne des notes des juges pour ce critère
            avg_score = self.scores.filter(criterion=criterion).aggregate(
                avg=Avg('value')
            )['avg']
            
            if avg_score is not None:
                # Appliquer la pondération
                weighted_score = avg_score * criterion.weight
                total_weighted_score += weighted_score
                total_weight += criterion.weight
                scores_by_criterion[criterion.name] = {
                    'avg_score': avg_score,
                    'weight': criterion.weight,
                    'weighted_score': weighted_score
                }
        
        # Calculer le score final
        if total_weight > 0:
            final_score = total_weighted_score / total_weight
            return round(final_score, 2)
        
        return 0.0
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Performance")
        verbose_name_plural = _("Performances")
        ordering = ['category', 'order']

class Score(models.Model):
    """Score attribué par un juge pour un critère spécifique d'une performance."""
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE, 
                                  related_name='scores')
    judge = models.ForeignKey('Judge', on_delete=models.CASCADE, 
                            related_name='scores')
    criterion = models.ForeignKey(ScoringCriterion, on_delete=models.CASCADE, 
                                related_name='performance_scores')  # Changement ici
    value = models.FloatField(_("Valeur"))
    comments = models.TextField(_("Commentaires"), blank=True)
    timestamp = models.DateTimeField(_("Horodatage"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.judge} - {self.criterion} - {self.value}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Score")
        verbose_name_plural = _("Scores")
        unique_together = ['performance', 'judge', 'criterion']

class JudgeSubmissionStatus(models.Model):
    """Statut de soumission des scores par un juge pour une performance."""
    judge = models.ForeignKey('Judge', on_delete=models.CASCADE)
    performance = models.ForeignKey(Performance, on_delete=models.CASCADE)
    submitted = models.BooleanField(_("Soumis"), default=False)
    submission_time = models.DateTimeField(_("Heure de soumission"), null=True, blank=True)

    def __str__(self):
        return f"{self.judge} - {self.performance} - {'Soumis' if self.submitted else 'Non soumis'}"

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Statut de soumission")
        verbose_name_plural = _("Statuts de soumission")
        unique_together = ['judge', 'performance']


class JudgeCategoryLock(models.Model):
    """
    PROMPT 10: Verrouillage des notes d'un juge pour une catégorie/round.
    Une fois verrouillé, le juge ne peut plus modifier ses notes pour ce round.
    """
    judge = models.ForeignKey('Judge', on_delete=models.CASCADE,
                             related_name='category_locks',
                             verbose_name=_("Juge"))
    category = models.ForeignKey('CompetitionCategory', on_delete=models.CASCADE,
                                related_name='judge_locks',
                                verbose_name=_("Catégorie"))
    round_number = models.PositiveIntegerField(_("Numéro de round"), default=1)
    is_locked = models.BooleanField(_("Verrouillé"), default=False)
    locked_at = models.DateTimeField(_("Verrouillé le"), null=True, blank=True)

    # Statistiques au moment du verrouillage
    scores_count = models.PositiveIntegerField(_("Nombre de notes"), default=0)
    average_score = models.DecimalField(_("Moyenne des notes"), max_digits=5, decimal_places=2,
                                       null=True, blank=True)
    min_score = models.DecimalField(_("Note minimale"), max_digits=5, decimal_places=2,
                                   null=True, blank=True)
    max_score = models.DecimalField(_("Note maximale"), max_digits=5, decimal_places=2,
                                   null=True, blank=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Verrouillage juge par catégorie")
        verbose_name_plural = _("Verrouillages juges par catégorie")
        unique_together = ['judge', 'category', 'round_number']
        ordering = ['category', 'round_number', 'judge']

    def __str__(self):
        status = "🔒" if self.is_locked else "🔓"
        return f"{status} {self.judge} - {self.category} (Round {self.round_number})"

    def lock(self):
        """Verrouille les notes du juge pour cette catégorie/round."""
        if not self.is_locked:
            self.is_locked = True
            self.locked_at = timezone.now()
            self.save()

    @classmethod
    def is_judge_locked(cls, judge, category, round_number=1):
        """Vérifie si un juge a verrouillé ses notes pour une catégorie/round."""
        return cls.objects.filter(
            judge=judge,
            category=category,
            round_number=round_number,
            is_locked=True
        ).exists()

class JudgeSettings(models.Model):
    """Paramètres personnalisés pour l'interface de notation d'un juge."""
    DISPLAY_MODE_CHOICES = [
        ('standard', _('Standard')),
        ('compact', _('Compact')),
        ('large', _('Grand')),
    ]
    
    THEME_CHOICES = [
        ('light', _('Clair')),
        ('dark', _('Sombre')),
        ('high_contrast', _('Contraste élevé')),
    ]
    
    judge = models.OneToOneField('Judge', on_delete=models.CASCADE, 
                                related_name='settings')
    display_mode = models.CharField(_("Mode d'affichage"), max_length=20, 
                                  choices=DISPLAY_MODE_CHOICES, default='standard')
    notification_sounds = models.BooleanField(_("Sons de notification"), default=True)
    auto_submit = models.BooleanField(_("Soumission automatique"), default=False)
    show_timer = models.BooleanField(_("Afficher le minuteur"), default=True)
    theme = models.CharField(_("Thème"), max_length=20, 
                           choices=THEME_CHOICES, default='light')
    
    def __str__(self):
        return f"Paramètres de {self.judge}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Paramètres de juge")
        verbose_name_plural = _("Paramètres de juge")

class JudgeApplication(models.Model):
    """Candidature pour devenir juge technique."""
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Rejetée')),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    disciplines = models.ManyToManyField('Discipline', related_name='judge_applications')
    experience_years = models.PositiveIntegerField(_("Années d'expérience"))
    qualifications = models.TextField(_("Qualifications"), help_text=_("Décrivez vos qualifications et expériences pertinentes"))
    resume = models.FileField(_("CV"), upload_to='judge_applications/resumes/', null=True, blank=True)
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='pending')
    submission_date = models.DateTimeField(_("Date de soumission"), auto_now_add=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='reviewed_applications')
    review_date = models.DateTimeField(_("Date d'examen"), null=True, blank=True)
    review_comments = models.TextField(_("Commentaires d'examen"), blank=True)
    
    def __str__(self):
        return f"Candidature de {self.user} - {self.get_status_display()}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Candidature de juge")
        verbose_name_plural = _("Candidatures de juge")
        ordering = ['-submission_date']


class TechnicalPerformance(models.Model):
    """Représente la prestation technique d'un participant"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, 
                                  related_name='technical_performances',
                                  verbose_name=_("Compétition"))
    category = models.ForeignKey(CompetitionCategory, on_delete=models.CASCADE, 
                               related_name='technical_performances',
                               verbose_name=_("Catégorie"))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, 
                                   related_name='technical_performances',
                                   verbose_name=_("Pratiquant"))
    performance_order = models.PositiveSmallIntegerField(_("Ordre de passage"), default=0)
    start_time = models.DateTimeField(_("Heure de début"), null=True, blank=True)
    end_time = models.DateTimeField(_("Heure de fin"), null=True, blank=True)
    is_completed = models.BooleanField(_("Terminé"), default=False)
    notes = models.TextField(_("Notes"), blank=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    # Champs d'absence (gérés par le Placateur)
    is_absent = models.BooleanField(_("Absent"), default=False)
    absence_noted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='noted_absences',
        verbose_name=_("Absence notée par")
    )
    absence_noted_at = models.DateTimeField(_("Absence notée le"), null=True, blank=True)

    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('disqualified', _('Disqualifié')),
    ]
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Prestation technique")
        verbose_name_plural = _("Prestations techniques")
        ordering = ['competition', 'category', 'performance_order']
        unique_together = ['competition', 'category', 'practitioner']
    
    def __str__(self):
        return f"{self.practitioner.full_name} - {self.category}"
    
    def start_performance(self):
        """Démarre la prestation"""
        self.start_time = timezone.now()
        self.status = 'in_progress'
        self.save()
    
    def end_performance(self):
        """Termine la prestation"""
        self.end_time = timezone.now()
        self.status = 'completed'
        self.is_completed = True
        self.save()
    
    @property
    def duration(self):
        """Retourne la durée de la prestation en secondes"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def calculate_final_score(self, round_number=None):
        """Calcule le score final en fonction des notes des juges.

        BUG #2 FIX: Prend en compte le round_number pour les barrages.
        Si round_number est None, utilise les notes actives pour le classement.
        """
        from django.db.models import Avg, Max, Min

        # BUG #2 FIX: Filtrer par round_number ou par is_active_for_ranking
        if round_number is not None:
            scores = TechnicalScore.objects.filter(performance=self, round_number=round_number)
        else:
            scores = TechnicalScore.objects.filter(performance=self, is_active_for_ranking=True)

        # Vérifier si les notes extremes doivent être exclues
        try:
            scoring_config = ScoringConfiguration.objects.get(category=self.category)
            exclude_extreme = scoring_config.exclude_extreme_scores
        except ScoringConfiguration.DoesNotExist:
            exclude_extreme = False

        if exclude_extreme:
            # Calculer le score final en excluant la note la plus haute et la plus basse
            judges_count = scores.values('judge').distinct().count()
            if judges_count >= 3:  # Besoin d'au moins 3 juges pour exclure les extremes
                final_scores = []

                # Pour chaque critere
                for criterion in ScoringCriterion.objects.filter(category=self.category, is_active=True):
                    criterion_scores = scores.filter(criterion=criterion)

                    # Exclure la note max et min pour ce critere
                    max_score = criterion_scores.order_by('-value').first()
                    min_score = criterion_scores.order_by('value').first()

                    if max_score and min_score:
                        avg_score = criterion_scores.exclude(
                            id__in=[max_score.id, min_score.id]
                        ).aggregate(avg=Avg('value'))['avg'] or 0

                        # Ponderer la note moyenne
                        weighted_score = avg_score * criterion.weight
                        final_scores.append(weighted_score)

                return sum(final_scores)

        # Methode standard: moyenne ponderee de toutes les notes
        total_score = 0.0
        total_weight = 0.0

        for criterion in ScoringCriterion.objects.filter(category=self.category, is_active=True):
            avg_score = scores.filter(criterion=criterion).aggregate(avg=Avg('value'))['avg']
            if avg_score is not None:
                # Convertir en float pour eviter les erreurs Decimal * float
                total_score += float(avg_score) * float(criterion.weight)
                total_weight += float(criterion.weight)

        if total_weight > 0:
            return total_score / total_weight
        return 0.0

    def get_current_round(self):
        """BUG #2 FIX: Retourne le round actuel (le plus élevé avec des notes)."""
        from django.db.models import Max
        max_round = TechnicalScore.objects.filter(
            performance=self
        ).aggregate(max_round=Max('round_number'))['max_round']
        return max_round or 1


class ScoringConfiguration(models.Model):
    """Configuration du système de notation pour une catégorie"""
    category = models.OneToOneField(CompetitionCategory, on_delete=models.CASCADE, 
                                  related_name='scoring_configuration',
                                  verbose_name=_("Catégorie"))
    min_score = models.DecimalField(_("Note minimale"), max_digits=3, decimal_places=2, default=0.0)
    max_score = models.DecimalField(_("Note maximale"), max_digits=3, decimal_places=2, default=10.0)
    score_step = models.DecimalField(_("Pas de notation"), max_digits=3, decimal_places=2, default=0.25)
    exclude_extreme_scores = models.BooleanField(_("Exclure les notes extrÃªmes"), default=False)
    allow_ties = models.BooleanField(_("Autoriser les ex-aequos en 3e place"), default=True)
    allow_score_modification = models.BooleanField(_("Autoriser la modification des notes après soumission"), default=False)
    real_time_results = models.BooleanField(_("Afficher les résultats en temps réel"), default=False)
    training_judges_included = models.BooleanField(_("Inclure les juges en formation"), default=False)
    
    # Configuration au format JSON pour des options avancées
    advanced_config = models.JSONField(_("Configuration avancée"), blank=True, null=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Configuration de notation")
        verbose_name_plural = _("Configurations de notation")
    
    def __str__(self):
        return f"Configuration pour {self.category}"


class ScoringPreset(models.Model):
    """Preset de configuration de notation réutilisable, lié à une discipline."""
    name = models.CharField(_("Nom du preset"), max_length=100)
    discipline = models.ForeignKey(
        'competitions.Discipline',
        on_delete=models.CASCADE,
        related_name='scoring_presets',
        verbose_name=_("Discipline")
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Créé par")
    )
    config_data = models.JSONField(
        _("Données de configuration"),
        help_text=_("Paramètres de notation, critères et configuration Tour 2")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Preset de notation")
        verbose_name_plural = _("Presets de notation")
        ordering = ['-updated_at']
        unique_together = ['name', 'discipline']

    def __str__(self):
        return f"{self.name} ({self.discipline.name})"


class TechnicalScore(models.Model):
    """Note technique attribuée par un juge"""

    ROUND_TYPES = [
        (1, _('Tour initial')),
        (2, _('Barrage 1')),
        (3, _('Barrage 2')),
        (4, _('Barrage 3')),
    ]

    performance = models.ForeignKey(TechnicalPerformance, on_delete=models.CASCADE,
                                  related_name='scores',
                                  verbose_name=_("Prestation"))
    judge = models.ForeignKey(User, on_delete=models.CASCADE,
                           related_name='technical_scores',
                           verbose_name=_("Juge"))
    criterion = models.ForeignKey(ScoringCriterion, on_delete=models.CASCADE,
                                related_name='technical_scores',
                                verbose_name=_("Critère"))
    value = models.DecimalField(_("Note"), max_digits=4, decimal_places=2)

    # BUG #2 FIX: Ajouter round_number pour supporter les barrages en cas d'égalité
    round_number = models.PositiveSmallIntegerField(
        _("Tour de notation"),
        choices=ROUND_TYPES,
        default=1,
        help_text=_("1 = Tour initial, 2+ = Barrages")
    )

    submitted_at = models.DateTimeField(_("Soumis le"), auto_now_add=True)
    is_locked = models.BooleanField(_("Verrouillé"), default=False)
    is_training_score = models.BooleanField(_("Note de formation"), default=False)

    # BUG #2 FIX: Flag pour indiquer si c'est la note active pour le classement
    is_active_for_ranking = models.BooleanField(
        _("Active pour le classement"),
        default=True,
        help_text=_("Si False, cette note n'est pas comptée dans le classement final")
    )

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Note technique")
        verbose_name_plural = _("Notes techniques")
        # BUG #2 FIX: Ajouter round_number à unique_together pour permettre plusieurs notes
        unique_together = ['performance', 'judge', 'criterion', 'round_number']
        ordering = ['performance', 'round_number', 'judge']
    
    def __str__(self):
        return f"{self.judge.username}: {self.value} - {self.criterion.name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Vérifier que la note est dans la plage autorisée
        config = self.performance.category.scoring_configuration
        if config:
            if self.value < config.min_score or self.value > config.max_score:
                raise ValidationError({
                    'value': _(f"La note doit Ãªtre comprise entre {config.min_score} et {config.max_score}.")
                })
            
            # Vérifier que la note respecte le pas de notation
            if config.score_step > 0:
                remainder = self.value % config.score_step
                if remainder != 0 and abs(remainder - config.score_step) > 0.001:
                    raise ValidationError({
                        'value': _(f"La note doit Ãªtre un multiple de {config.score_step}.")
                    })

class CompetitionRanking(models.Model):
    """Classement final d'une compétition technique"""
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, 
                                  related_name='rankings',
                                  verbose_name=_("Compétition"))
    category = models.ForeignKey(CompetitionCategory, on_delete=models.CASCADE, 
                               related_name='rankings',
                               verbose_name=_("Catégorie"))
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, 
                                   related_name='rankings',
                                   verbose_name=_("Pratiquant"))
    rank = models.PositiveSmallIntegerField(_("Classement"))
    final_score = models.DecimalField(_("Score final"), max_digits=5, decimal_places=2)
    first_places = models.PositiveSmallIntegerField(_("Premières places"), default=0)
    is_tie = models.BooleanField(_("Ex-aequo"), default=False)
    generated_at = models.DateTimeField(_("Généré le"), auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Classement de compétition")
        verbose_name_plural = _("Classements de compétition")
        unique_together = ['competition', 'category', 'practitioner']
        ordering = ['competition', 'category', 'rank']
    
    def __str__(self):
        return f"{self.rank}. {self.practitioner.full_name} ({self.final_score})"
    






