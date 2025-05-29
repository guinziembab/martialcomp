from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from organizations.models import Organization, OrganizationMember, OrganizationRole


class ScoringCriterion(models.Model):
    """
    Critère de notation pour les compétitions techniques.
    Exemple: Technique, Puissance, Équilibre, Respect du kata, etc.
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    weight = models.FloatField(
        _("Pondération"), 
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(10.0)],
        help_text=_("Valeur relative de ce critère par rapport aux autres")
    )
    min_score = models.FloatField(
        _("Score minimum"), 
        default=0.0,
        validators=[MinValueValidator(0.0)]
    )
    max_score = models.FloatField(
        _("Score maximum"), 
        default=10.0,
        validators=[MinValueValidator(0.1)]
    )
    step = models.FloatField(
        _("Pas de notation"), 
        default=0.25, 
        validators=[MinValueValidator(0.05)],
        help_text=_("Incrément minimal pour les scores (ex: 0.25)")
    )
    # Catégorie de compétition (lien vers le modèle CompetitionCategory)
    category = models.ForeignKey(
        'competitions.CompetitionCategory', 
        on_delete=models.CASCADE, 
        related_name='scoring_criteria',
        verbose_name=_("Catégorie")
    )
    
    # Champs additionnels pour gérer l'ordre et l'état
    order = models.PositiveIntegerField(_("Ordre d'affichage"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    class Meta:
        verbose_name = _("Critère de notation")
        verbose_name_plural = _("Critères de notation")
        ordering = ['category', 'order', 'name']
        unique_together = [['name', 'category']]
    
    def clean(self):
        """Validation supplémentaire des données."""
        from django.core.exceptions import ValidationError
        
        # Vérifier que max_score > min_score
        if self.max_score <= self.min_score:
            raise ValidationError(_("Le score maximum doit être supérieur au score minimum."))
        
        # Vérifier que le pas est cohérent avec la plage de scores
        score_range = self.max_score - self.min_score
        if self.step > score_range:
            raise ValidationError(_("Le pas de notation ne peut pas être supérieur à la plage de scores."))


class ScoringConfiguration(models.Model):
    """
    Configuration du système de notation pour une catégorie de compétition.
    Définit les paramètres globaux de notation pour une catégorie.
    """
    category = models.OneToOneField(
        'competitions.CompetitionCategory', 
        on_delete=models.CASCADE, 
        related_name='scoring_configuration',
        verbose_name=_("Catégorie")
    )
    min_score = models.DecimalField(
        _("Note minimale"), 
        max_digits=4, 
        decimal_places=2, 
        default=0.0
    )
    max_score = models.DecimalField(
        _("Note maximale"), 
        max_digits=4, 
        decimal_places=2, 
        default=10.0
    )
    score_step = models.DecimalField(
        _("Pas de notation"), 
        max_digits=3, 
        decimal_places=2, 
        default=0.25,
        help_text=_("Valeur de l'incrément pour les scores (ex: 0.25)")
    )
    exclude_extreme_scores = models.BooleanField(
        _("Exclure les notes extrêmes"), 
        default=False,
        help_text=_("Exclure la note la plus haute et la plus basse du calcul final")
    )
    allow_ties = models.BooleanField(
        _("Autoriser les ex-æquo"), 
        default=True,
        help_text=_("Autoriser les ex-æquo en 3ème place")
    )
    allow_score_modification = models.BooleanField(
        _("Autoriser la modification des notes"), 
        default=False,
        help_text=_("Permettre aux juges de modifier leurs notes après soumission")
    )
    real_time_results = models.BooleanField(
        _("Résultats en temps réel"), 
        default=False,
        help_text=_("Afficher les résultats en temps réel pendant la compétition")
    )
    training_judges_included = models.BooleanField(
        _("Inclure les juges en formation"), 
        default=False,
        help_text=_("Inclure les notes des juges en formation (à des fins de comparaison)")
    )
    # Paramètres avancés sous forme JSON (options configurables)
    advanced_config = models.JSONField(
        _("Configuration avancée"), 
        blank=True, 
        null=True,
        help_text=_("Options avancées de configuration au format JSON")
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    def __str__(self):
        return f"Configuration de notation pour {self.category}"
    
    class Meta:
        verbose_name = _("Configuration de notation")
        verbose_name_plural = _("Configurations de notation")
    
    def clean(self):
        """Validation supplémentaire des données."""
        from django.core.exceptions import ValidationError
        
        # Vérifier que max_score > min_score
        if self.max_score <= self.min_score:
            raise ValidationError(_("Le score maximum doit être supérieur au score minimum."))
    
    def set_default_criteria(self):
        """
        Crée les critères de notation par défaut pour cette catégorie en fonction de la discipline.
        Cette méthode est utilisée lors de la création initiale de la configuration.
        """
        discipline_name = self.category.discipline.name.lower() if self.category.discipline else ""
        
        # Liste de critères par défaut pour différentes disciplines
        default_criteria = {
            'karaté': [
                {'name': _('Technique'), 'weight': 1.5, 'description': _('Précision et exécution correcte des mouvements')},
                {'name': _('Puissance'), 'weight': 1.0, 'description': _('Force et énergie dans l\'exécution')},
                {'name': _('Rythme'), 'weight': 1.0, 'description': _('Tempo et fluidité de l\'enchaînement')},
                {'name': _('Kime'), 'weight': 1.2, 'description': _('Concentration de l\'énergie au moment de l\'impact')},
                {'name': _('Respiration'), 'weight': 0.8, 'description': _('Coordination de la respiration avec les mouvements')}
            ],
            'judo': [
                {'name': _('Technique'), 'weight': 1.5, 'description': _('Précision et exécution correcte des mouvements')},
                {'name': _('Efficacité'), 'weight': 1.2, 'description': _('Efficacité et applicabilité des techniques')},
                {'name': _('Contrôle'), 'weight': 1.0, 'description': _('Maîtrise et contrôle des mouvements')},
                {'name': _('Coordination'), 'weight': 0.8, 'description': _('Coordination et fluidité des enchaînements')}
            ],
            'taekwondo': [
                {'name': _('Technique'), 'weight': 1.5, 'description': _('Précision et exécution correcte des mouvements')},
                {'name': _('Force'), 'weight': 1.0, 'description': _('Puissance des coups')},
                {'name': _('Équilibre'), 'weight': 1.0, 'description': _('Stabilité et équilibre pendant l\'exécution')},
                {'name': _('Vitesse'), 'weight': 1.2, 'description': _('Rapidité d\'exécution des techniques')},
                {'name': _('Présentation'), 'weight': 0.8, 'description': _('Présentation générale et attitude')}
            ],
            'wushu': [
                {'name': _('Technique'), 'weight': 1.2, 'description': _('Précision et exécution correcte des mouvements')},
                {'name': _('Performance'), 'weight': 1.0, 'description': _('Fluidité et expression artistique')},
                {'name': _('Difficulté'), 'weight': 1.5, 'description': _('Niveau de difficulté des mouvements exécutés')},
                {'name': _('Chorégraphie'), 'weight': 1.0, 'description': _('Structure et composition de la routine')},
                {'name': _('Synchronisation'), 'weight': 0.8, 'description': _('Coordination de la respiration avec les mouvements')}
            ],
            'qwan ki do': [
                {'name': _('Technique'), 'weight': 1.2, 'description': _('Précision et exécution correcte des mouvements')},
                {'name': _('Puissance'), 'weight': 1.0, 'description': _('Force et énergie dans l\'exécution')},
                {'name': _('Équilibre'), 'weight': 1.0, 'description': _('Stabilité et équilibre pendant l\'exécution')},
                {'name': _('Rythme'), 'weight': 0.8, 'description': _('Tempo et fluidité de l\'enchaînement')},
                {'name': _('Concentration'), 'weight': 1.0, 'description': _('Concentration et esprit martial')}
            ],
            # Critères par défaut si aucune discipline spécifique n'est reconnue
            'default': [
                {'name': _('Technique'), 'weight': 1.2, 'description': _('Précision et exécution correcte des mouvements')},
                {'name': _('Performance'), 'weight': 1.0, 'description': _('Qualité globale de la prestation')},
                {'name': _('Présentation'), 'weight': 0.8, 'description': _('Présentation générale et attitude')}
            ]
        }
        
        # Déterminer quelle liste de critères utiliser
        criteria_list = None
        for key in default_criteria.keys():
            if key in discipline_name:
                criteria_list = default_criteria[key]
                break
        
        # Si aucune correspondance n'est trouvée, utiliser la liste par défaut
        if criteria_list is None:
            criteria_list = default_criteria['default']
        
        # Créer les critères pour cette catégorie
        for idx, criterion_data in enumerate(criteria_list):
            ScoringCriterion.objects.create(
                category=self.category,
                name=criterion_data['name'],
                description=criterion_data['description'],
                weight=criterion_data['weight'],
                min_score=float(self.min_score),
                max_score=float(self.max_score),
                step=float(self.score_step),
                order=idx,
                is_active=True
            )