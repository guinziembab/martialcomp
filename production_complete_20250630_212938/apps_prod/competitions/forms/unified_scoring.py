from django import forms
from django.utils.translation import gettext_lazy as _

from competitions.models.unified_scoring import (
    ScoringSystem, ScoringCriterion, CategoryScoringConfig,
    Performance, Score, JudgeSubmission, CompetitionRanking,
    JudgeSettings
)


class ScoringSystemForm(forms.ModelForm):
    """Form for creating/editing a scoring system."""
    
    class Meta:
        model = ScoringSystem
        fields = [
            'name', 'description', 'system_type', 
            'min_score', 'max_score', 'score_step',
            'exclude_extreme_scores', 'allow_ties', 'real_time_results'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        score_step = cleaned_data.get('score_step')
        
        if min_score is not None and max_score is not None and min_score >= max_score:
            self.add_error('min_score', _('Minimum score must be less than maximum score.'))
        
        if score_step is not None and score_step <= 0:
            self.add_error('score_step', _('Score step must be greater than zero.'))
        
        if min_score is not None and max_score is not None and score_step is not None:
            if (max_score - min_score) < score_step:
                self.add_error('score_step', _('Score step must be less than the range between min and max scores.'))
        
        return cleaned_data


class ScoringCriterionForm(forms.ModelForm):
    """Form for creating/editing a scoring criterion."""
    
    class Meta:
        model = ScoringCriterion
        fields = [
            'name', 'description', 'weight', 
            'min_score', 'max_score', 'step',
            'order', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make min_score, max_score, and step optional in the form
        self.fields['min_score'].required = False
        self.fields['max_score'].required = False
        self.fields['step'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        step = cleaned_data.get('step')
        
        if min_score is not None and max_score is not None and min_score >= max_score:
            self.add_error('min_score', _('Minimum score must be less than maximum score.'))
        
        if step is not None and step <= 0:
            self.add_error('step', _('Score step must be greater than zero.'))
        
        if min_score is not None and max_score is not None and step is not None:
            if (max_score - min_score) < step:
                self.add_error('step', _('Score step must be less than the range between min and max scores.'))
        
        return cleaned_data


class CategoryScoringConfigForm(forms.ModelForm):
    """Form for configuring category scoring settings."""
    
    class Meta:
        model = CategoryScoringConfig
        fields = [
            'scoring_system', 
            'override_min_score', 'override_max_score', 'override_score_step',
            'exclude_extreme_scores', 'allow_ties', 'real_time_results'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make override fields optional
        self.fields['override_min_score'].required = False
        self.fields['override_max_score'].required = False
        self.fields['override_score_step'].required = False
        self.fields['exclude_extreme_scores'].required = False
        self.fields['allow_ties'].required = False
        self.fields['real_time_results'].required = False
        
        # Set choices for scoring_system field
        self.fields['scoring_system'].queryset = ScoringSystem.objects.all().order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('override_min_score')
        max_score = cleaned_data.get('override_max_score')
        score_step = cleaned_data.get('override_score_step')
        
        if min_score is not None and max_score is not None and min_score >= max_score:
            self.add_error('override_min_score', _('Minimum score must be less than maximum score.'))
        
        if score_step is not None and score_step <= 0:
            self.add_error('override_score_step', _('Score step must be greater than zero.'))
        
        if min_score is not None and max_score is not None and score_step is not None:
            if (max_score - min_score) < score_step:
                self.add_error('override_score_step', _('Score step must be less than the range between min and max scores.'))
        
        return cleaned_data


class PerformanceForm(forms.ModelForm):
    """Form for creating/editing a performance."""
    
    class Meta:
        model = Performance
        fields = [
            'practitioner', 'round_type', 'round_number', 
            'performance_order', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default order if this is a new performance
        if not self.instance.pk and 'performance_order' in self.fields:
            last_order = Performance.objects.filter(
                category=self.instance.category,
                round_type=self.instance.round_type or Performance.PRELIMINARY,
                round_number=self.instance.round_number or 1
            ).aggregate(models.Max('performance_order'))['performance_order__max'] or 0
            
            self.fields['performance_order'].initial = last_order + 1


class ScoreForm(forms.ModelForm):
    """Form for creating/editing a score."""
    
    class Meta:
        model = Score
        fields = ['value', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, criterion=None, config=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set min, max, and step based on criterion or config
        if criterion:
            min_score = criterion.min_score
            max_score = criterion.max_score
            step = criterion.step
            
            if config and (min_score is None or max_score is None or step is None):
                min_score = min_score or config.get_effective_min_score()
                max_score = max_score or config.get_effective_max_score()
                step = step or config.get_effective_score_step()
            
            if min_score is not None and max_score is not None:
                self.fields['value'].widget = forms.NumberInput(attrs={
                    'step': str(step or 0.1),
                    'min': str(min_score),
                    'max': str(max_score),
                })


class JudgeSettingsForm(forms.ModelForm):
    """Form for judge UI preferences."""
    
    class Meta:
        model = JudgeSettings
        fields = [
            'display_mode', 'notification_sounds', 
            'auto_submit', 'theme'
        ]


class RankingSnapshotForm(forms.Form):
    """Form for creating a ranking snapshot."""
    
    name = forms.CharField(
        max_length=100, 
        required=False,
        help_text=_("Optional name for this snapshot. If not provided, a timestamp will be used.")
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text=_("Optional notes about this snapshot.")
    )
    
    publish = forms.BooleanField(
        required=False,
        initial=True,
        help_text=_("Make this snapshot visible to users with appropriate permissions.")
    )
    
    is_final = forms.BooleanField(
        required=False,
        initial=False,
        help_text=_("Mark this as the final official results.")
    )