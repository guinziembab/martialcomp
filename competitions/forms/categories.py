# competitions/forms/categories.py

from django import forms
from django.utils.translation import gettext_lazy as _
from competitions.models import CategoryTemplate, CompetitionCategory, Discipline


class CompetitionCategoryForm(forms.ModelForm):
    """Formulaire pour la création/modification d'une catégorie de compétition."""
    
    class Meta:
        model = CompetitionCategory
        fields = [
            'name', 'competition_type', 'template', 'min_age', 'max_age', 
            'min_grade', 'max_grade', 'min_weight', 'max_weight', 
            'gender', 'max_participants', 'registration_status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'competition_type': forms.Select(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'max_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'min_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'max_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')
        min_weight = cleaned_data.get('min_weight')
        max_weight = cleaned_data.get('max_weight')

        # Validation de l'âge
        if min_age and max_age and min_age > max_age:
            raise forms.ValidationError(
                _("L'âge minimum ne peut pas être supérieur à l'âge maximum.")
            )

        # Validation du poids
        if min_weight and max_weight and min_weight > max_weight:
            raise forms.ValidationError(
                _("Le poids minimum ne peut pas être supérieur au poids maximum.")
            )

        return cleaned_data


class CategoryTemplateForm(forms.ModelForm):
    """Formulaire pour la création/modification d'un template de catégorie."""
    
    class Meta:
        model = CategoryTemplate
        fields = [
            'name', 'discipline', 'competition_type', 'min_age', 'max_age',
            'min_grade', 'max_grade', 'min_weight', 'max_weight', 'gender',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du template')}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'competition_type': forms.Select(attrs={'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Âge minimum')}),
            'max_age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Âge maximum')}),
            'min_grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Grade minimum')}),
            'max_grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Grade maximum')}),
            'min_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Poids minimum (kg)'), 'step': '0.1'}),
            'max_weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Poids maximum (kg)'), 'step': '0.1'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')
        min_weight = cleaned_data.get('min_weight')
        max_weight = cleaned_data.get('max_weight')

        # Validation de l'âge
        if min_age and max_age and min_age > max_age:
            raise forms.ValidationError(
                _("L'âge minimum ne peut pas être supérieur à l'âge maximum.")
            )

        # Validation du poids
        if min_weight and max_weight and min_weight > max_weight:
            raise forms.ValidationError(
                _("Le poids minimum ne peut pas être supérieur au poids maximum.")
            )

        return cleaned_data


