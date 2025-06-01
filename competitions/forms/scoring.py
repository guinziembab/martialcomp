from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

from competitions.models.technical_scoring import (
    ScoringCriterion, JudgeSubmissionStatus,
    ScoringConfiguration, TechnicalPerformance, TechnicalScore,
    CompetitionRanking
)
from competitions.models import CompetitionRegistration, JudgeAssignment


class ScoringCriterionForm(forms.ModelForm):
    """
    Formulaire pour la création et la modification des critères de notation.
    """
    class Meta:
        model = ScoringCriterion
        fields = ['name', 'description', 'weight', 'min_score', 'max_score', 'step', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du critère')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Description détaillée du critère')}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'min_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'step': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        step = cleaned_data.get('step')
        
        if min_score is not None and max_score is not None:
            if min_score >= max_score:
                raise forms.ValidationError(_("Le score minimum doit être inférieur au score maximum."))
        
        if step is not None and step <= 0:
            raise forms.ValidationError(_("Le pas de notation doit être positif."))
        
        return cleaned_data


class ScoringConfigurationForm(forms.ModelForm):
    """
    Formulaire pour la configuration du système de notation d'une catégorie.
    """
    class Meta:
        model = ScoringConfiguration
        fields = [
            'min_score', 'max_score', 'score_step', 'exclude_extreme_scores', 
            'allow_ties', 'allow_score_modification', 'real_time_results', 
            'training_judges_included'
        ]
        widgets = {
            'min_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'max_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'score_step': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'exclude_extreme_scores': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_ties': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_score_modification': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'real_time_results': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'training_judges_included': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_score = cleaned_data.get('min_score')
        max_score = cleaned_data.get('max_score')
        score_step = cleaned_data.get('score_step')
        
        if min_score is not None and max_score is not None:
            if min_score >= max_score:
                raise forms.ValidationError(_("Le score minimum doit être inférieur au score maximum."))
        
        if score_step is not None and score_step <= 0:
            raise forms.ValidationError(_("Le pas de notation doit être positif."))
        
        return cleaned_data




class TechnicalPerformanceForm(forms.ModelForm):
    """
    Formulaire pour la création et la modification des performances techniques.
    """
    class Meta:
        model = TechnicalPerformance
        fields = ['practitioner', 'performance_order', 'notes']
        widgets = {
            'practitioner': forms.Select(attrs={'class': 'form-select'}),
            'performance_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        competition = kwargs.pop('competition', None)
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les participants disponibles
        if competition and category:
            # Récupérer les participants déjà assignés à une performance
            existing_performers = TechnicalPerformance.objects.filter(
                category=category
            ).values_list('practitioner__id', flat=True)
            
            # Exclure l'instance actuelle pour l'édition
            if self.instance and self.instance.pk:
                existing_performers = existing_performers.exclude(practitioner=self.instance.practitioner)
            
            # Récupérer les participants inscrits et approuvés pour cette catégorie
            self.fields['practitioner'].queryset = CompetitionRegistration.objects.filter(
                competition=competition,
                categories=category,
                is_competitor=True,
                status='approved'
            ).exclude(
                practitioner__id__in=existing_performers
            ).select_related('practitioner').values_list('practitioner', flat=True)
            
            # Convertir les IDs en QuerySet de Practitioner
            from competitions.models import Practitioner
            self.fields['practitioner'].queryset = Practitioner.objects.filter(
                id__in=self.fields['practitioner'].queryset
            )
            
            # Si c'est une édition, ajouter le participant actuel à la liste
            if self.instance and self.instance.pk and self.instance.practitioner:
                self.fields['practitioner'].queryset |= Practitioner.objects.filter(
                    id=self.instance.practitioner.id
                )


class ScoringForm(forms.Form):
    """
    Formulaire pour l'attribution des scores.
    """
    judge = forms.ModelChoiceField(
        queryset=None,
        label=_("Juge"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    criterion = forms.ModelChoiceField(
        queryset=None,
        label=_("Critère"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    value = forms.DecimalField(
        label=_("Note"),
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'})
    )
    
    def __init__(self, *args, **kwargs):
        performance = kwargs.pop('performance', None)
        super().__init__(*args, **kwargs)
        
        if performance:
            # Récupérer les juges assignés à cette catégorie
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            judge_ids = JudgeAssignment.objects.filter(
                category=performance.category,
                assignment_type__in=['technical_judge', 'chief_judge']
            ).values_list('user', flat=True)
            
            self.fields['judge'].queryset = User.objects.filter(id__in=judge_ids)
            
            # Récupérer les critères de cette catégorie
            self.fields['criterion'].queryset = ScoringCriterion.objects.filter(
                category=performance.category
            ).order_by('order')
            
            # Ajouter des validateurs pour la note
            if self.fields['criterion'].queryset.exists():
                first_criterion = self.fields['criterion'].queryset.first()
                self.fields['value'].validators = [
                    MinValueValidator(first_criterion.min_score),
                    MaxValueValidator(first_criterion.max_score)
                ]
                
                # Mettre à jour le step en fonction du premier critère
                self.fields['value'].widget.attrs['step'] = first_criterion.step
    
    def clean(self):
        cleaned_data = super().clean()
        judge = cleaned_data.get('judge')
        criterion = cleaned_data.get('criterion')
        value = cleaned_data.get('value')
        
        if criterion and value is not None:
            if value < criterion.min_score or value > criterion.max_score:
                raise forms.ValidationError(_("La note doit être comprise entre {} et {}.").format(
                    criterion.min_score, criterion.max_score))
            
            # Vérifier que la note respecte le pas
            if criterion.step > 0:
                # Convertir en float pour la comparaison
                value_float = float(value)
                step_float = float(criterion.step)
                remainder = value_float % step_float
                
                # Permettre une petite marge d'erreur pour les problèmes d'arrondi
                if remainder != 0 and abs(remainder - step_float) > 0.001:
                    raise forms.ValidationError(_("La note doit être un multiple de {}.").format(criterion.step))
        
        return cleaned_data