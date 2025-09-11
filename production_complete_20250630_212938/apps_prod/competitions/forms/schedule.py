from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from competitions.models import Competition, CompetitionCategory, Match

# Importez d'autres modèles selon les besoins de votre application


class ScheduleForm(forms.Form):
    """
    Formulaire de base pour la planification des horaires de compétition.
    """
    competition = forms.ModelChoiceField(
        queryset=Competition.objects.filter(
            is_published=True,
            end_date__gte=timezone.now().date()
        ).exclude(status='cancelled'),
        label=_("Compétition"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        competition = self.initial.get('competition')
        if competition:
            # Date par défaut = date de début de la compétition
            self.fields['date'].initial = competition.start_date


class CompetitionScheduleForm(forms.ModelForm):
    """
    Formulaire pour la planification globale d'une compétition.
    """
    class Meta:
        model = Competition
        fields = ['start_date', 'end_date', 'start_time', 'end_time']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        }


class CategoryScheduleForm(forms.ModelForm):
    """
    Formulaire pour la planification des horaires par catégorie.
    """
    class Meta:
        model = CompetitionCategory
        fields = ['competition']
        widgets = {
            'competition': forms.Select(attrs={'class': 'form-select'}),
        }
    
    # Champs supplémentaires pour la planification
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    start_time = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    end_time = forms.TimeField(
        label=_("Heure de fin"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    tatami = forms.IntegerField(
        label=_("Tatami"),
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class TatamiScheduleForm(forms.Form):
    """
    Formulaire pour la gestion des plannings par tatami.
    """
    competition = forms.ModelChoiceField(
        queryset=Competition.objects.filter(
            is_published=True,
            end_date__gte=timezone.now().date()
        ).exclude(status='cancelled'),
        label=_("Compétition"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tatami_number = forms.IntegerField(
        label=_("Numéro de tatami"),
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    start_time = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    end_time = forms.TimeField(
        label=_("Heure de fin"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )


class MatchTimeSlotForm(forms.ModelForm):
    """
    Formulaire pour la gestion des créneaux horaires des matchs.
    """
    class Meta:
        model = Match
        fields = ['date_match', 'start_time', 'end_time']
        widgets = {
            'date_match': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        }
    
    category = forms.ModelChoiceField(
        queryset=CompetitionCategory.objects.all(),
        label=_("Catégorie"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    tatami = forms.IntegerField(
        label=_("Tatami"),
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class BulkCategoryScheduleForm(forms.Form):
    """
    Formulaire pour la planification en masse des catégories de compétition.
    """
    competition = forms.ModelChoiceField(
        queryset=Competition.objects.filter(
            is_published=True,
            end_date__gte=timezone.now().date()
        ).exclude(status='cancelled'),
        label=_("Compétition"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    categories = forms.ModelMultipleChoiceField(
        queryset=CompetitionCategory.objects.all(),
        label=_("Catégories"),
        widget=forms.SelectMultiple(attrs={'class': 'form-select'})
    )
    
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    start_time = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    end_time = forms.TimeField(
        label=_("Heure de fin"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    tatami = forms.IntegerField(
        label=_("Tatami"),
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    interval_minutes = forms.IntegerField(
        label=_("Intervalle entre catégories (minutes)"),
        min_value=0,
        initial=15,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        competition = self.initial.get('competition')
        if competition:
            self.fields['categories'].queryset = CompetitionCategory.objects.filter(
                competition=competition
            )
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_("L'heure de fin doit être postérieure à l'heure de début."))
        
        return cleaned_data