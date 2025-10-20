from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Row, Column, Submit, Button
from crispy_forms.bootstrap import FormActions

from ..models import CompetitionType, Discipline


class CompetitionTypeForm(forms.ModelForm):
    """Formulaire pour créer/modifier un type de compétition."""
    
    class Meta:
        model = CompetitionType
        fields = [
            'name', 'description', 'discipline', 'team_based',
            'min_team_size', 'max_team_size', 'weight_category',
            'scoring_system', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom du type de compétition')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description du type de compétition')
            }),
            'discipline': forms.Select(attrs={
                'class': 'form-select'
            }),
            'team_based': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'min_team_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'max_team_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'weight_category': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'scoring_system': forms.Select(attrs={
                'class': 'form-select'
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurer le helper Crispy Forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'needs-validation'
        self.helper.attrs = {'novalidate': ''}
        
        # Layout du formulaire
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('order', css_class='col-md-4'),
            ),
            'description',
            Row(
                Column('discipline', css_class='col-md-6'),
                Column('scoring_system', css_class='col-md-6'),
            ),
            Row(
                Column('team_based', css_class='col-md-4'),
                Column('weight_category', css_class='col-md-4'),
            ),
            Row(
                Column('min_team_size', css_class='col-md-6'),
                Column('max_team_size', css_class='col-md-6'),
            ),
            FormActions(
                Submit('submit', _('Enregistrer'), css_class='btn btn-primary'),
                Button('cancel', _('Annuler'), css_class='btn btn-secondary', onclick='history.back()'),
            )
        )
        
        # Filtrer les disciplines actives
        self.fields['discipline'].queryset = Discipline.objects.filter(is_active=True)
        
        # Ajouter des classes CSS pour la validation
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
    
    def clean(self):
        cleaned_data = super().clean()
        team_based = cleaned_data.get('team_based')
        min_team_size = cleaned_data.get('min_team_size')
        max_team_size = cleaned_data.get('max_team_size')
        
        # Validation pour les équipes
        if team_based:
            if not min_team_size:
                self.add_error('min_team_size', _('La taille minimale d\'équipe est requise pour les compétitions par équipe.'))
            if not max_team_size:
                self.add_error('max_team_size', _('La taille maximale d\'équipe est requise pour les compétitions par équipe.'))
            
            if min_team_size and max_team_size and min_team_size > max_team_size:
                self.add_error('max_team_size', _('La taille maximale doit être supérieure ou égale à la taille minimale.'))
        else:
            # Si ce n'est pas une compétition par équipe, vider les champs de taille
            cleaned_data['min_team_size'] = None
            cleaned_data['max_team_size'] = None
        
        return cleaned_data
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        discipline = self.cleaned_data.get('discipline')
        
        if name and discipline:
            # Vérifier l'unicité du nom par discipline
            queryset = CompetitionType.objects.filter(
                name__iexact=name,
                discipline=discipline
            )
            
            # Exclure l'instance actuelle si on est en mode édition
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise forms.ValidationError(
                    _('Un type de compétition avec ce nom existe déjà pour cette discipline.')
                )
        
        return name


class CompetitionTypeFilterForm(forms.Form):
    """Formulaire de filtrage pour la liste des types de compétition."""
    
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        required=False,
        empty_label=_('Toutes les disciplines'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    scoring_system = forms.ChoiceField(
        choices=[('', _('Tous les systèmes'))] + CompetitionType.SCORING_SYSTEM_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    team_based = forms.ChoiceField(
        choices=[
            ('', _('Tous')),
            ('true', _('Par équipe')),
            ('false', _('Individuel')),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Rechercher par nom ou description...')
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'row g-3'
        self.helper.layout = Layout(
            Row(
                Column('search', css_class='col-md-4'),
                Column('discipline', css_class='col-md-3'),
                Column('scoring_system', css_class='col-md-3'),
                Column('team_based', css_class='col-md-2'),
            ),
            FormActions(
                Submit('filter', _('Filtrer'), css_class='btn btn-primary'),
                Button('reset', _('Réinitialiser'), css_class='btn btn-outline-secondary', onclick='resetForm()'),
            )
        )