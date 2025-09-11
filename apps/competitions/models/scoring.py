from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationMember, OrganizationRole
from . import Competition, CompetitionCategory
from . import User
from . import Practitioner


class ScoringSystem(models.Model):
    """Système de notation utilisé pour une compétition ou une catégorie spécifique."""
    
    SYSTEM_TYPES = [
        ('standard', _('Standard (WKF)')),
        ('point', _('Points')),
        ('direct', _('Ã‰limination directe')),
        ('custom', _('Personnalisé')),
    ]
    
    name = models.CharField(_("Nom"), max_length=100)
    system_type = models.CharField(_("Type de système"), max_length=20, choices=SYSTEM_TYPES, default='standard')
    description = models.TextField(_("Description"), blank=True)
    
    min_score = models.DecimalField(
        _("Score minimum"), 
        max_digits=5, 
        decimal_places=2, 
        default=5.0,
        validators=[MinValueValidator(0.0)]
    )
    max_score = models.DecimalField(
        _("Score maximum"), 
        max_digits=5, 
        decimal_places=2, 
        default=10.0,
        validators=[MinValueValidator(0.1)]
    )
    score_step = models.DecimalField(
        _("Pas de notation"), 
        max_digits=5, 
        decimal_places=2, 
        default=0.25,
        validators=[MinValueValidator(0.01)]
    )
    decimal_places = models.PositiveSmallIntegerField(_("Décimales affichées"), default=2)
    
    exclude_extreme_scores = models.BooleanField(
        _("Exclure les notes extrÃªmes"), 
        default=True,
        help_text=_("Exclure les notes minimum et maximum du calcul")
    )
    allow_ties = models.BooleanField(
        _("Autoriser les ex-aequo"), 
        default=False
    )
    allow_score_modification = models.BooleanField(
        _("Autoriser modification des notes"), 
        default=False,
        help_text=_("Permettre aux juges de modifier leurs notes après soumission")
    )
    display_real_time_results = models.BooleanField(
        _("Afficher résultats en temps réel"), 
        default=True
    )
    include_training_judges = models.BooleanField(
        _("Inclure juges en formation"), 
        default=False,
        help_text=_("Inclure les juges en formation (leurs notes ne sont pas comptabilisées)")
    )
    
    TIE_BREAKER_CHOICES = [
        ('none', _('Aucun')),
        ('chief', _('Juge en chef')),
        ('highest_rank', _('Juge de plus haut rang')),
    ]
    
    judge_tiebreaker = models.CharField(
        _("Juge départageur"), 
        max_length=20, 
        choices=TIE_BREAKER_CHOICES, 
        default='none'
    )
    
    # Option pour permettre ou non le partage de la 3ème place (2 médailles de bronze)
    third_place_ties = models.BooleanField(
        _("Autoriser le partage de la 3ème place"), 
        default=True,
        help_text=_("Deux médailles de bronze peuvent Ãªtre attribuées")
    )
    
    # Formules de calcul personnalisées (JSON)
    scoring_formula = models.TextField(
        _("Formule de calcul"), 
        blank=True,
        help_text=_("Formule personnalisée pour le calcul des scores, laissez vide pour la formule standard")
    )
    
    # Méta-information
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='created_scoring_systems'
    )
    
    def __str__(self):
        return f"{self.name} ({self.get_system_type_display()})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Système de notation")
        verbose_name_plural = _("Systèmes de notation")


class ScoringCriterion(models.Model):
    """Critère de notation pour évaluer une performance technique."""
    
    scoring_system = models.ForeignKey(
        ScoringSystem, 
        on_delete=models.CASCADE, 
        related_name='criteria',
        verbose_name=_("Système de notation")
    )
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    weight = models.DecimalField(
        _("Pondération"), 
        max_digits=5, 
        decimal_places=2, 
        default=1.0,
        validators=[MinValueValidator(0.1)]
    )
    
    min_score = models.DecimalField(
        _("Score minimum"), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0.0)]
    )
    max_score = models.DecimalField(
        _("Score maximum"), 
        max_digits=5, 
        decimal_places=2, 
        blank=True, 
        null=True,
        validators=[MinValueValidator(0.1)]
    )
    
    APPLICABILITY_CHOICES = [
        ('kata', _('Kata uniquement')),
        ('kumite', _('Kumite uniquement')),
        ('both', _('Kata et Kumite')),
    ]
    
    applicability = models.CharField(
        _("Applicable Ã "), 
        max_length=10, 
        choices=APPLICABILITY_CHOICES, 
        default='both'
    )
    
    order = models.PositiveSmallIntegerField(_("Ordre d'affichage"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)
    
    def __str__(self):
        return f"{self.name} ({self.weight})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Critère de notation")
        verbose_name_plural = _("Critères de notation")
        ordering = ['scoring_system', 'order']
        unique_together = [['scoring_system', 'name']]

    def save(self, *args, **kwargs):
        # Si les scores min et max ne sont pas définis, utiliser ceux du système
        if self.min_score is None and self.scoring_system:
            self.min_score = self.scoring_system.min_score
        if self.max_score is None and self.scoring_system:
            self.max_score = self.scoring_system.max_score
        super().save(*args, **kwargs)


class CategoryScoringConfig(models.Model):
    """Configuration de notation spécifique Ã  une catégorie de compétition."""
    
    category = models.OneToOneField(
        CompetitionCategory, 
        on_delete=models.CASCADE, 
        related_name='scoring_config',
        verbose_name=_("Catégorie")
    )
    scoring_system = models.ForeignKey(
        ScoringSystem, 
        on_delete=models.CASCADE, 
        related_name='category_configs',
        verbose_name=_("Système de notation")
    )
    
    # Paramètres spécifiques qui peuvent remplacer ceux du système global
    override_min_score = models.DecimalField(
        _("Score minimum personnalisé"), 
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    override_max_score = models.DecimalField(
        _("Score maximum personnalisé"), 
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    override_score_step = models.DecimalField(
        _("Pas de notation personnalisé"), 
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Paramètres supplémentaires spécifiques Ã  la catégorie
    notes = models.TextField(_("Notes"), blank=True)
    
    def __str__(self):
        return f"Configuration de notation pour {self.category}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Configuration de notation de catégorie")
        verbose_name_plural = _("Configurations de notation de catégorie")


class Performance(models.Model):
    """Représente une performance qui doit Ãªtre notée (passage d'un compétiteur)."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('ready', _('PrÃªt')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('disqualified', _('Disqualifié')),
        ('cancelled', _('Annulé')),
    ]
    
    category = models.ForeignKey(
        CompetitionCategory, 
        on_delete=models.CASCADE, 
        related_name='performances',
        verbose_name=_("Catégorie")
    )
    practitioner = models.ForeignKey(
        Practitioner, 
        on_delete=models.CASCADE, 
        related_name='performances',
        verbose_name=_("Compétiteur")
    )
    
    round_type = models.CharField(
        _("Type de tour"), 
        max_length=50, 
        blank=True,
        help_text=_("Ex: Ã‰liminatoires, Quart de finale, Demi-finale, Finale")
    )
    round_number = models.PositiveSmallIntegerField(
        _("Numéro du tour"), 
        default=1
    )
    order = models.PositiveSmallIntegerField(
        _("Ordre de passage"), 
        default=0
    )
    
    kata_name = models.CharField(
        _("Nom du kata/technique"), 
        max_length=100, 
        blank=True,
        help_text=_("Nom du kata ou de la technique présentée")
    )
    
    scheduled_time = models.DateTimeField(
        _("Heure prévue"), 
        null=True, 
        blank=True
    )
    start_time = models.DateTimeField(
        _("Heure de début"), 
        null=True, 
        blank=True
    )
    end_time = models.DateTimeField(
        _("Heure de fin"), 
        null=True, 
        blank=True
    )
    
    status = models.CharField(
        _("Statut"), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    # Résultats calculés
    final_score = models.DecimalField(
        _("Score final"), 
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    rank = models.PositiveSmallIntegerField(
        _("Classement"), 
        null=True, 
        blank=True
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    
    # Méta-information
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    modified_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='modified_performances'
    )
    
    def __str__(self):
        return f"{self.practitioner} - {self.category} ({self.get_status_display()})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Performance")
        verbose_name_plural = _("Performances")
        ordering = ['category', 'round_number', 'order']
    
    def start_performance(self):
        """Démarrer cette performance."""
        self.status = 'in_progress'
        self.start_time = timezone.now()
        self.save(update_fields=['status', 'start_time'])
    
    def complete_performance(self):
        """Marquer cette performance comme terminée."""
        self.status = 'completed'
        self.end_time = timezone.now()
        self.save(update_fields=['status', 'end_time'])
    
    def disqualify(self, reason=''):
        """Disqualifier cette performance."""
        self.status = 'disqualified'
        if reason:
            self.notes = f"{self.notes}\nDisqualification: {reason}".strip()
        self.save(update_fields=['status', 'notes'])
    
    def calculate_final_score(self):
        """Calculer le score final Ã  partir des notes des juges."""
        scores = self.scores.all()
        if not scores.exists():
            return None
        
        # Récupérer la configuration de notation
        scoring_config = self.category.scoring_config
        if not scoring_config:
            return None
        
        scoring_system = scoring_config.scoring_system
        
        # Implémenter ici la logique de calcul en fonction du système de notation
        # (Standard, Points, Personnalisé, etc.)
        if scoring_system.system_type == 'standard':
            return self._calculate_standard_score(scores, scoring_system)
        elif scoring_system.system_type == 'point':
            return self._calculate_point_score(scores, scoring_system)
        elif scoring_system.system_type == 'custom':
            return self._calculate_custom_score(scores, scoring_system)
        
        return None
    
    def _calculate_standard_score(self, scores, system):
        """Calcul standard: moyenne pondérée avec exclusion des extrÃªmes."""
        total_scores = {}
        
        # Regrouper les scores par juge
        for score in scores:
            judge_id = score.judge_id
            if judge_id not in total_scores:
                total_scores[judge_id] = 0
            
            # Ajouter la note pondérée
            criterion_weight = score.criterion.weight
            total_scores[judge_id] += float(score.value) * float(criterion_weight)
        
        # Exclure les extrÃªmes si nécessaire
        if system.exclude_extreme_scores and len(total_scores) >= 3:
            min_score = min(total_scores.values())
            max_score = max(total_scores.values())
            total = sum(s for s in total_scores.values() if s != min_score and s != max_score)
            count = len(total_scores) - 2
        else:
            total = sum(total_scores.values())
            count = len(total_scores)
        
        # Calculer la moyenne
        if count > 0:
            return round(total / count, system.decimal_places)
        return None
    
    def _calculate_point_score(self, scores, system):
        """Calcul par points (pour le kumite par exemple)."""
        # Ã€ implémenter selon les règles de comptage de points spécifiques
        return None
    
    def _calculate_custom_score(self, scores, system):
        """Calcul personnalisé en fonction de la formule définie."""
        # Ã€ implémenter en utilisant la formule personnalisée du système
        return None


class Score(models.Model):
    """Score attribué par un juge pour un critère spécifique d'une performance."""
    
    performance = models.ForeignKey(
        Performance, 
        on_delete=models.CASCADE, 
        related_name='scores',
        verbose_name=_("Performance")
    )
    judge = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='given_scores',
        verbose_name=_("Juge")
    )
    criterion = models.ForeignKey(
        ScoringCriterion, 
        on_delete=models.CASCADE, 
        related_name='scores',
        verbose_name=_("Critère")
    )
    
    value = models.DecimalField(
        _("Valeur"), 
        max_digits=5, 
        decimal_places=2
    )
    
    is_training_score = models.BooleanField(
        _("Score d'entrainement"), 
        default=False,
        help_text=_("Score donné par un juge en formation, non comptabilisé dans le résultat")
    )
    is_modified = models.BooleanField(
        _("Modifié après soumission"), 
        default=False
    )
    original_value = models.DecimalField(
        _("Valeur originale"), 
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text=_("Valeur originale avant modification")
    )
    
    comments = models.TextField(_("Commentaires"), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    def __str__(self):
        return f"{self.judge} - {self.criterion}: {self.value}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Score")
        verbose_name_plural = _("Scores")
        unique_together = [['performance', 'judge', 'criterion']]
    
    def save(self, *args, **kwargs):
        # Si c'est une modification, sauvegarder la valeur originale
        if self.pk and not self.original_value:
            original = Score.objects.get(pk=self.pk)
            if original.value != self.value:
                self.is_modified = True
                self.original_value = original.value
        
        super().save(*args, **kwargs)
        
        # Mettre Ã  jour le score final de la performance
        if self.performance.status == 'completed':
            self.performance.final_score = self.performance.calculate_final_score()
            self.performance.save(update_fields=['final_score'])


class JudgeSubmission(models.Model):
    """Suivi de la soumission des scores par un juge pour une performance."""
    
    performance = models.ForeignKey(
        Performance, 
        on_delete=models.CASCADE, 
        related_name='judge_submissions',
        verbose_name=_("Performance")
    )
    judge = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='score_submissions',
        verbose_name=_("Juge")
    )
    
    is_submitted = models.BooleanField(
        _("Soumis"), 
        default=False
    )
    submitted_at = models.DateTimeField(
        _("Soumis le"), 
        null=True, 
        blank=True
    )
    
    comments = models.TextField(_("Commentaires"), blank=True)
    
    def __str__(self):
        return f"{self.judge} - {self.performance} - {'Soumis' if self.is_submitted else 'Non soumis'}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Soumission de juge")
        verbose_name_plural = _("Soumissions de juges")
        unique_together = [['performance', 'judge']]
    
    def submit(self):
        """Marquer les scores comme soumis."""
        self.is_submitted = True
        self.submitted_at = timezone.now()
        self.save(update_fields=['is_submitted', 'submitted_at'])


class CompetitionRanking(models.Model):
    """Classement final d'un compétiteur dans une catégorie."""
    
    category = models.ForeignKey(
        CompetitionCategory, 
        on_delete=models.CASCADE, 
        related_name='rankings',
        verbose_name=_("Catégorie")
    )
    practitioner = models.ForeignKey(
        Practitioner, 
        on_delete=models.CASCADE, 
        related_name='rankings',
        verbose_name=_("Compétiteur")
    )
    
    rank = models.PositiveSmallIntegerField(_("Classement"))
    final_score = models.DecimalField(
        _("Score final"), 
        max_digits=6, 
        decimal_places=2
    )
    
    # Pour la méthode de classement par "drapeaux"
    first_places = models.PositiveSmallIntegerField(
        _("Nombre de premières places"), 
        default=0
    )
    
    is_tie = models.BooleanField(
        _("Ex-aequo"), 
        default=False
    )
    
    medal = models.CharField(
        _("Médaille"), 
        max_length=10, 
        blank=True,
        help_text=_("Or, Argent, Bronze ou vide")
    )
    
    notes = models.TextField(_("Notes"), blank=True)
    generated_at = models.DateTimeField(_("Généré le"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.rank}. {self.practitioner} - {self.category} ({self.final_score})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Classement de compétition")
        verbose_name_plural = _("Classements de compétition")
        unique_together = [['category', 'practitioner']]
        ordering = ['category', 'rank']
    
    def save(self, *args, **kwargs):
        # Attribuer automatiquement les médailles en fonction du rang
        if self.rank == 1:
            self.medal = 'gold'
        elif self.rank == 2:
            self.medal = 'silver'
        elif self.rank == 3:
            self.medal = 'bronze'
        else:
            self.medal = ''
        
        super().save(*args, **kwargs)



