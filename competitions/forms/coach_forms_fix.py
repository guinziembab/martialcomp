from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory

from ..models import CoachProfile, DisciplineExpertise, Discipline


class CoachProfileForm(forms.ModelForm):
    """Formulaire pour le profil coach"""
    
    class Meta:
        model = CoachProfile
        fields = [
            'profile_type',
            'years_teaching',
            'primary_teaching_place',
            'teaching_philosophy',
            'available_for_seminars',
            'available_for_private_lessons',
            'available_for_online_coaching',
            'hourly_rate_range'
        ]
        widgets = {
            'teaching_philosophy': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': _("Décrivez votre approche pédagogique...")
            }),
            'profile_type': forms.Select(attrs={'class': 'form-control'}),
            'years_teaching': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'primary_teaching_place': forms.Select(attrs={'class': 'form-control'}),
            'hourly_rate_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Ex: 50-80€")
            })
        }


class DisciplineExpertiseFormFixed(forms.ModelForm):
    """Version corrigée du formulaire pour l'expertise dans une discipline (sans years_experience et is_primary)"""
    
    class Meta:
        model = DisciplineExpertise
        fields = [
            'discipline',
            'level',
            # 'years_experience' a été retiré car il manque dans la base de données
            'years_teaching',
            # 'is_primary' a été retiré car il manque dans la base de données
            'current_grade',
            'teaching_certification',
            'federation',
            'public_description'
        ]
        widgets = {
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'years_teaching': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'current_grade': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Ex: 3ème Dan")
            }),
            'teaching_certification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Ex: DEJEPS")
            }),
            'federation': forms.Select(attrs={'class': 'form-control'}),
            'public_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _("Décrivez votre expertise dans cette discipline...")
            })
        }


# Formset pour gérer plusieurs expertises de disciplines (sans years_experience)
DisciplineExpertiseFormSetFixed = inlineformset_factory(
    CoachProfile,
    DisciplineExpertise,
    form=DisciplineExpertiseFormFixed,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class CoachAvailabilityForm(forms.ModelForm):
    """Formulaire pour les disponibilités du coach"""
    
    class Meta:
        model = CoachProfile
        fields = [
            'available_for_seminars',
            'available_for_private_lessons',
            'available_for_online_coaching',
            'hourly_rate_range'
        ]
        widgets = {
            'hourly_rate_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Ex: 50-80€")
            })
        }


class MultiDisciplineSelectionForm(forms.Form):
    """Formulaire pour la sélection multiple de disciplines"""
    
    primary_discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all(),
        label=_("Discipline principale"),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    
    secondary_disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.all(),
        label=_("Disciplines secondaires"),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    def clean(self):
        cleaned_data = super().clean()
        primary = cleaned_data.get('primary_discipline')
        secondaries = cleaned_data.get('secondary_disciplines', [])
        
        if primary and primary in secondaries:
            raise forms.ValidationError(
                _("La discipline principale ne peut pas être aussi une discipline secondaire.")
            )
        
        return cleaned_data