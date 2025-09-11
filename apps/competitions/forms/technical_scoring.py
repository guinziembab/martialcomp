from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from ..models import (
    ScoringCriterion,
    ScoringConfiguration,
    Discipline,
    Judge,
    CompetitionCategory
)
from ..models.technical_scoring import (
    TechnicalPerformance, 
    TechnicalScore, 
    Performance, 
    Score, 
    JudgeSettings,
    JudgeApplication
)

class ScoringConfigurationForm(forms.ModelForm):
    """Formulaire de configuration du système de notation"""
    
    class Meta:
        model = ScoringConfiguration
        fields = [
            'min_score', 'max_score', 'score_step',
            'exclude_extreme_scores', 'allow_ties',
            'allow_score_modification', 'real_time_results',
            'training_judges_included'
        ]
        widgets = {
            'min_score': forms.NumberInput(attrs={'step': '0.5', 'min': '0', 'max': '10'}),
            'max_score': forms.NumberInput(attrs={'step': '0.5', 'min': '0', 'max': '10'}),
            'score_step': forms.NumberInput(attrs={'step': '0.05', 'min': '0.05', 'max': '1'})
        }

    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        score_step = cleaned_data.get('score_step')
        
        if min_score is not None and max_score is not None:
            if min_score >= max_score:
                self.add_error('max_score', _("La note maximale doit Ãªtre supérieure Ã  la note minimale."))
            
            if score_step <= 0:
                self.add_error('score_step', _("Le pas de notation doit Ãªtre strictement positif."))
            elif (max_score - min_score) / score_step > 100:
                self.add_error('score_step', _("Le pas est trop petit par rapport Ã  l'amplitude des notes."))
        
        return cleaned_data


class ScoringCriterionForm(forms.ModelForm):
    """Formulaire pour les critères d'évaluation"""
    
    class Meta:
        model = ScoringCriterion
        fields = ['name', 'description', 'weight', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0.1', 'max': '10'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


# Formset pour gérer plusieurs critères Ã  la fois
ScoringCriterionFormSet = inlineformset_factory(
    CompetitionCategory,
    ScoringCriterion,
    form=ScoringCriterionForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class TechnicalScoreForm(forms.ModelForm):
    """Formulaire pour la saisie des notes techniques"""
    
    class Meta:
        model = TechnicalScore
        fields = ['value']
        widgets = {
            'value': forms.NumberInput(attrs={'step': '0.25', 'class': 'score-input'})
        }
    
    def __init__(self, *args, **kwargs):
        self.criterion = kwargs.pop('criterion', None)
        self.config = kwargs.pop('config', None)
        super().__init__(*args, **kwargs)
        
        if self.config:
            self.fields['value'].widget.attrs.update({
                'step': str(self.config.score_step),
                'min': str(self.config.min_score),
                'max': str(self.config.max_score)
            })
        
        if self.criterion:
            self.fields['value'].label = self.criterion.name
            if self.criterion.description:
                self.fields['value'].help_text = self.criterion.description


class JudgeAssignmentForm(forms.Form):
    """Formulaire pour assigner des juges Ã  une catégorie de compétition"""
    
    judges = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Sera filtré dans __init__
        label=_("Juges"),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    
    training_judges = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Sera filtré dans __init__
        label=_("Juges en formation"),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )
    
    chief_judge = forms.ModelChoiceField(
        queryset=User.objects.all(),  # Sera filtré dans __init__
        label=_("Juge en chef"),
        empty_label=_("Sélectionner un juge en chef"),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        competition = kwargs.pop('competition', None)
        super().__init__(*args, **kwargs)
        
        if competition:
            # Filtrer les juges disponibles pour cette compétition
            judge_queryset = User.objects.filter(
                role='judge',
                is_active=True
            ).exclude(
                technical_scores__performance__competition=competition
            ).distinct()
            
            self.fields['judges'].queryset = judge_queryset
            self.fields['training_judges'].queryset = judge_queryset
            self.fields['chief_judge'].queryset = judge_queryset
    
    def clean(self):
        cleaned_data = super().clean()
        judges = cleaned_data.get('judges', [])
        training_judges = cleaned_data.get('training_judges', [])
        chief_judge = cleaned_data.get('chief_judge')
        
        # Vérifier que le juge en chef n'est pas également dans les juges normaux
        if chief_judge and chief_judge in judges:
            self.add_error('chief_judge', _("Le juge en chef ne peut pas Ãªtre également un juge normal."))
        
        # Vérifier qu'un juge n'est pas Ã  la fois juge normal et juge en formation
        if judges and training_judges:
            common_judges = set(judges) & set(training_judges)
            if common_judges:
                self.add_error('judges', _("Un juge ne peut pas Ãªtre Ã  la fois juge officiel et juge en formation."))
                self.add_error('training_judges', _("Un juge ne peut pas Ãªtre Ã  la fois juge officiel et juge en formation."))
        
        return cleaned_data


class PerformanceOrderForm(forms.Form):
    """Formulaire pour définir l'ordre de passage des participants"""
    
    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        
        if category:
            # Récupérer toutes les prestations de cette catégorie
            performances = TechnicalPerformance.objects.filter(category=category).order_by('performance_order')
            
            # Créer un champ pour chaque performance
            for i, performance in enumerate(performances):
                field_name = f'performance_{performance.id}'
                self.fields[field_name] = forms.IntegerField(
                    initial=performance.performance_order,
                    min_value=1,
                    label=performance.practitioner.full_name,
                    widget=forms.NumberInput(attrs={'class': 'form-control'})
                )


class StartPerformanceForm(forms.Form):
    """Formulaire pour démarrer une prestation"""
    
    confirm = forms.BooleanField(
        required=True,
        label=_("Je confirme que le pratiquant est prÃªt Ã  commencer"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class PerformanceResultsForm(forms.Form):
    """Formulaire pour la validation des résultats d'une prestation"""
    
    publish_results = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Publier les résultats immédiatement"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    confirm_results = forms.BooleanField(
        required=True,
        label=_("Je confirme que les résultats sont corrects"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


# Formulaires ajoutés pour les fonctions manquantes

class JudgeSettingsForm(forms.ModelForm):
    """Formulaire pour configurer les paramètres de juge."""
    class Meta:
        model = JudgeSettings
        fields = [
            'display_mode', 
            'notification_sounds', 
            'auto_submit', 
            'show_timer', 
            'theme'
        ]
        widgets = {
            'display_mode': forms.Select(attrs={'class': 'form-select'}),
            'notification_sounds': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'auto_submit': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_timer': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
        }


class JudgeApplicationForm(forms.ModelForm):
    """Formulaire pour postuler en tant que juge."""
    class Meta:
        model = JudgeApplication
        fields = [
            'disciplines', 
            'experience_years', 
            'qualifications', 
            'resume'
        ]
        widgets = {
            'disciplines': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_experience_years(self):
        years = self.cleaned_data.get('experience_years')
        if years < 0:
            raise forms.ValidationError(_("Le nombre d'années d'expérience ne peut pas Ãªtre négatif."))
        return years


class ScoreForm(forms.Form):
    """Formulaire dynamique pour la notation d'une performance."""
    
    def __init__(self, *args, **kwargs):
        criteria = kwargs.pop('criteria', [])
        performance = kwargs.pop('performance', None)
        judge = kwargs.pop('judge', None)
        config = kwargs.pop('config', None)
        super(ScoreForm, self).__init__(*args, **kwargs)
        
        # Valeurs par défaut si aucune configuration n'est fournie
        min_score = 0
        max_score = 10
        step = 0.25
        
        # Utiliser la configuration si disponible
        if config:
            min_score = config.min_score
            max_score = config.max_score
            step = config.score_step
        
        # Créer dynamiquement les champs pour chaque critère
        for criterion in criteria:
            field_name = f'criterion_{criterion.id}'
            
            # Déterminer la valeur initiale (note existante si disponible)
            initial_value = None
            if performance and judge:
                try:
                    score = Score.objects.get(
                        performance=performance,
                        judge=judge,
                        criterion=criterion
                    )
                    initial_value = score.value
                except Score.DoesNotExist:
                    pass
            
            # Créer un champ nombre avec les contraintes du critère
            self.fields[field_name] = forms.FloatField(
                label=criterion.name,
                min_value=min_score,
                max_value=max_score,
                initial=initial_value,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control score-input',
                    'step': str(step),
                    'data-criterion-id': criterion.id,
                    'data-criterion-name': criterion.name,
                    'data-min': min_score,
                    'data-max': max_score,
                    'data-step': step,
                    'data-weight': criterion.weight,
                }),
                help_text=criterion.description
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier que tous les critères ont été notés
        for field_name, value in cleaned_data.items():
            if field_name.startswith('criterion_') and value is None:
                criterion_id = field_name.split('_')[1]
                self.add_error(field_name, _("Une note est requise pour ce critère"))
        
        return cleaned_data
