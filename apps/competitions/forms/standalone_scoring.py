"""
Forms for the standalone scoring system.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

from apps.competitions.models.standalone_scoring import (
    StandaloneScoringSystem,
    StandaloneScoringCriterion,
    StandaloneCategoryScoringConfig,
    StandalonePerformance,
    StandaloneJudgeSettings
)
from apps.competitions.models.categories import CompetitionCategory as Category
from apps.competitions.models.competitions import Competition
from apps.competitions.models.practitioners import Practitioner

class ScoringSystemForm(forms.ModelForm):
    """Form for creating and editing scoring systems."""
    
    class Meta:
        model = StandaloneScoringSystem
        fields = [
            'name', 'description', 'system_type', 'min_score', 'max_score',
            'score_step', 'exclude_extreme_scores', 'allow_ties', 'real_time_results'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        if min_score is not None and max_score is not None and min_score >= max_score:
            raise forms.ValidationError(_("Minimum score must be less than maximum score."))
        
        return cleaned_data

class ScoringCriterionForm(forms.ModelForm):
    """Form for creating and editing scoring criteria."""
    
    category_id = forms.IntegerField(
        required=False,
        label=_("Category"),
        help_text=_("Leave blank for global criteria applicable to all categories")
    )
    
    class Meta:
        model = StandaloneScoringCriterion
        fields = [
            'scoring_system', 'category_id', 'name', 'description', 'weight',
            'min_score', 'max_score', 'step', 'order_num', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'scoring_system': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'order_num': _("Display Order"),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate category choices dynamically
        categories = Category.objects.all().order_by('name')
        category_choices = [(None, _("Global (All Categories)"))]
        category_choices.extend([(category.id, category.name) for category in categories])
        
        self.fields['category_id'].widget = forms.Select(choices=category_choices)
        
        # Make min_score, max_score, and step optional
        self.fields['min_score'].required = False
        self.fields['max_score'].required = False
        self.fields['step'].required = False
        
        # Set help text for optional fields
        self.fields['min_score'].help_text = _("Leave blank to use system default")
        self.fields['max_score'].help_text = _("Leave blank to use system default")
        self.fields['step'].help_text = _("Leave blank to use system default")
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        
        if min_score is not None and max_score is not None and min_score >= max_score:
            raise forms.ValidationError(_("Minimum score must be less than maximum score."))
        
        return cleaned_data

class CategoryScoringConfigForm(forms.ModelForm):
    """Form for configuring scoring for a category."""
    
    class Meta:
        model = StandaloneCategoryScoringConfig
        fields = [
            'scoring_system', 'override_min_score', 'override_max_score',
            'override_score_step', 'exclude_extreme_scores', 'allow_ties', 'real_time_results'
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
        
        # Set help text
        self.fields['override_min_score'].help_text = _("Leave blank to use system default")
        self.fields['override_max_score'].help_text = _("Leave blank to use system default")
        self.fields['override_score_step'].help_text = _("Leave blank to use system default")
        self.fields['exclude_extreme_scores'].help_text = _("Leave blank to use system default")
        self.fields['allow_ties'].help_text = _("Leave blank to use system default")
        self.fields['real_time_results'].help_text = _("Leave blank to use system default")
    
    def clean(self):
        cleaned_data = super().clean()
        override_min_score = cleaned_data.get('override_min_score')
        override_max_score = cleaned_data.get('override_max_score')
        
        if (override_min_score is not None and override_max_score is not None and 
            override_min_score >= override_max_score):
            raise forms.ValidationError(_("Minimum score must be less than maximum score."))
        
        return cleaned_data

class PerformanceForm(forms.ModelForm):
    """Form for creating and editing performances."""
    
    competition_id = forms.ChoiceField(
        label=_("Competition"),
        required=True
    )
    
    category_id = forms.ChoiceField(
        label=_("Category"),
        required=True
    )
    
    practitioner_id = forms.ChoiceField(
        label=_("Practitioner"),
        required=True
    )
    
    class Meta:
        model = StandalonePerformance
        fields = [
            'competition_id', 'category_id', 'practitioner_id',
            'round_type', 'round_number', 'performance_order',
            'status', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate competition choices
        competitions = Competition.objects.filter(status__in=['published', 'active', 'ongoing']).order_by('title')
        self.fields['competition_id'].choices = [('', _("Select Competition"))]
        self.fields['competition_id'].choices.extend([(str(c.id), c.title) for c in competitions])

        # Populate category choices
        categories = Category.objects.all().order_by('name')
        self.fields['category_id'].choices = [('', _("Select Category"))]
        self.fields['category_id'].choices.extend([(str(c.id), str(c)) for c in categories])
        
        # Populate practitioner choices
        practitioners = Practitioner.objects.all().order_by('last_name', 'first_name')
        self.fields['practitioner_id'].choices = [('', _("Select Practitioner"))]
        self.fields['practitioner_id'].choices.extend([
            (str(p.id), f"{p.first_name} {p.last_name}") for p in practitioners
        ])
        
        # Set initial values if instance exists
        instance = kwargs.get('instance')
        if instance:
            self.fields['competition_id'].initial = str(instance.competition_id)
            self.fields['category_id'].initial = str(instance.category_id)
            self.fields['practitioner_id'].initial = str(instance.practitioner_id)
    
    def clean_competition_id(self):
        return int(self.cleaned_data['competition_id'])
    
    def clean_category_id(self):
        return int(self.cleaned_data['category_id'])
    
    def clean_practitioner_id(self):
        return int(self.cleaned_data['practitioner_id'])

class ScoreEntryForm(forms.Form):
    """Form for entering scores for a criterion."""
    
    score = forms.DecimalField(
        label=_("Score"),
        max_digits=5,
        decimal_places=2,
        required=True
    )
    
    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        max_length=500
    )
    
    def __init__(self, criterion=None, min_score=0.0, max_score=10.0, step=0.1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.criterion = criterion
        
        # Set field attributes based on parameters
        self.fields['score'].min_value = min_score
        self.fields['score'].max_value = max_score
        self.fields['score'].validators = [
            MinValueValidator(min_score),
            MaxValueValidator(max_score)
        ]
        
        # Set widget attributes
        self.fields['score'].widget.attrs.update({
            'class': 'form-control score-input',
            'step': step,
            'min': min_score,
            'max': max_score,
            'data-criterion-id': criterion.id if criterion else '',
            'data-criterion-name': criterion.name if criterion else '',
        })

class JudgeSettingsForm(forms.ModelForm):
    """Form for judge interface settings."""
    
    class Meta:
        model = StandaloneJudgeSettings
        fields = ['display_mode', 'notification_sounds', 'auto_submit', 'theme']
        widgets = {
            'display_mode': forms.Select(attrs={'class': 'form-select'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
        }
