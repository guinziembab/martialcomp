from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from organizations.models import Organization, OrganizationMember, OrganizationRole
from competitions.models import Competition, CompetitionCategory
from competitions.models import Practitioner
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
        verbose_name = _("Critère de notation")
        verbose_name_plural = _("Critères de notation")
        ordering = ['category', 'order', 'name']  # Utiliser order dans l'ordre

class Performance(models.Model):
    """Représente une performance à évaluer dans une compétition."""
    STATUS_CHOICES = [
        ('scheduled', _('Programmée')),
        ('ready', _('Prête')),
        ('in_progress', _('En cours')),
        ('pending_validation', _('En attente de validation')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée')),
    ]
    
    practitioner = models.ForeignKey('Practitioner', on_delete=models.CASCADE, 
                                    related_name='performances')
    category = models.ForeignKey('CompetitionCategory', on_delete=models.CASCADE, 
                                related_name='performances')
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
        return f"{self.practitioner} - {self.category}"
    
    class Meta:
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
        verbose_name = _("Statut de soumission")
        verbose_name_plural = _("Statuts de soumission")
        unique_together = ['judge', 'performance']

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
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('disqualified', _('Disqualifié')),
    ]
    status = models.CharField(_("Statut"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    class Meta:
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
    
    def calculate_final_score(self):
        """Calcule le score final en fonction des notes des juges"""
        from django.db.models import Avg, Max, Min
        
        # Récupérer toutes les notes pour cette prestation
        scores = TechnicalScore.objects.filter(performance=self)
        
        # Vérifier si les notes extrêmes doivent être exclues
        scoring_config = self.category.scoring_config
        if scoring_config and scoring_config.get('exclude_extreme_scores', False):
            # Calculer le score final en excluant la note la plus haute et la plus basse
            judges_count = scores.values('judge').distinct().count()
            if judges_count >= 3:  # Besoin d'au moins 3 juges pour exclure les extrêmes
                final_scores = []
                
                # Pour chaque critère
                for criterion in ScoringCriterion.objects.filter(category=self.category, is_active=True):
                    criterion_scores = scores.filter(criterion=criterion)
                    
                    # Exclure la note max et min pour ce critère
                    max_score = criterion_scores.order_by('-value').first()
                    min_score = criterion_scores.order_by('value').first()
                    
                    if max_score and min_score:
                        avg_score = criterion_scores.exclude(
                            id__in=[max_score.id, min_score.id]
                        ).aggregate(avg=Avg('value'))['avg'] or 0
                        
                        # Pondérer la note moyenne
                        weighted_score = avg_score * criterion.weight
                        final_scores.append(weighted_score)
                
                return sum(final_scores)
        
        # Méthode standard: moyenne pondérée de toutes les notes
        total_score = 0
        total_weight = 0
        
        for criterion in ScoringCriterion.objects.filter(category=self.category, is_active=True):
            avg_score = scores.filter(criterion=criterion).aggregate(avg=Avg('value'))['avg'] or 0
            total_score += avg_score * criterion.weight
            total_weight += criterion.weight
        
        if total_weight > 0:
            return total_score / total_weight
        return 0


class ScoringConfiguration(models.Model):
    """Configuration du système de notation pour une catégorie"""
    category = models.OneToOneField(CompetitionCategory, on_delete=models.CASCADE, 
                                  related_name='scoring_configuration',
                                  verbose_name=_("Catégorie"))
    min_score = models.DecimalField(_("Note minimale"), max_digits=3, decimal_places=2, default=0.0)
    max_score = models.DecimalField(_("Note maximale"), max_digits=3, decimal_places=2, default=10.0)
    score_step = models.DecimalField(_("Pas de notation"), max_digits=3, decimal_places=2, default=0.25)
    exclude_extreme_scores = models.BooleanField(_("Exclure les notes extrêmes"), default=False)
    allow_ties = models.BooleanField(_("Autoriser les ex-aequos en 3e place"), default=True)
    allow_score_modification = models.BooleanField(_("Autoriser la modification des notes après soumission"), default=False)
    real_time_results = models.BooleanField(_("Afficher les résultats en temps réel"), default=False)
    training_judges_included = models.BooleanField(_("Inclure les juges en formation"), default=False)
    
    # Configuration au format JSON pour des options avancées
    advanced_config = models.JSONField(_("Configuration avancée"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("Configuration de notation")
        verbose_name_plural = _("Configurations de notation")
    
    def __str__(self):
        return f"Configuration pour {self.category}"

class TechnicalScore(models.Model):
    """Note technique attribuée par un juge"""
    performance = models.ForeignKey(TechnicalPerformance, on_delete=models.CASCADE, 
                                  related_name='scores',
                                  verbose_name=_("Prestation"))
    judge = models.ForeignKey(User, on_delete=models.CASCADE, 
                           related_name='technical_scores',
                           verbose_name=_("Juge"))
    criterion = models.ForeignKey(ScoringCriterion, on_delete=models.CASCADE, 
                                related_name='technical_scores',  # Ajout de la virgule ici
                                verbose_name=_("Critère"))
    value = models.DecimalField(_("Note"), max_digits=4, decimal_places=2)
    submitted_at = models.DateTimeField(_("Soumis le"), auto_now_add=True)
    is_locked = models.BooleanField(_("Verrouillé"), default=False)
    is_training_score = models.BooleanField(_("Note de formation"), default=False)
    
    class Meta:
        verbose_name = _("Note technique")
        verbose_name_plural = _("Notes techniques")
        unique_together = ['performance', 'judge', 'criterion']
    
    def __str__(self):
        return f"{self.judge.username}: {self.value} - {self.criterion.name}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Vérifier que la note est dans la plage autorisée
        config = self.performance.category.scoring_configuration
        if config:
            if self.value < config.min_score or self.value > config.max_score:
                raise ValidationError({
                    'value': _(f"La note doit être comprise entre {config.min_score} et {config.max_score}.")
                })
            
            # Vérifier que la note respecte le pas de notation
            if config.score_step > 0:
                remainder = self.value % config.score_step
                if remainder != 0 and abs(remainder - config.score_step) > 0.001:
                    raise ValidationError({
                        'value': _(f"La note doit être un multiple de {config.score_step}.")
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
        verbose_name = _("Classement de compétition")
        verbose_name_plural = _("Classements de compétition")
        unique_together = ['competition', 'category', 'practitioner']
        ordering = ['competition', 'category', 'rank']
    
    def __str__(self):
        return f"{self.rank}. {self.practitioner.full_name} ({self.final_score})"
    

