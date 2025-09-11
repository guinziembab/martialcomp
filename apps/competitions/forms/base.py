from django import forms
from ..utils.discipline_filtering import get_filtered_disciplines_for_user, get_filtered_federations_for_discipline


class BaseFilteredForm(forms.ModelForm):
    """
    Classe de base pour tous les formulaires avec filtrage par discipline/fédération.
    
    Cette classe restreint automatiquement les choix de disciplines et fédérations
    selon les accès de l'utilisateur.
    """
    
    def __init__(self, *args, **kwargs):
        # Récupérer l'utilisateur et le retirer des kwargs
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if not user or user.is_superuser:
            return
        
        # Restreindre les choix de disciplines
        if 'discipline' in self.fields:
            self.fields['discipline'].queryset = get_filtered_disciplines_for_user(user)
        
        # Restreindre les choix de fédérations en fonction de la discipline sélectionnée
        if 'federation' in self.fields:
            # Si on édite un objet existant, limiter aux fédérations de sa discipline
            if self.instance and self.instance.pk and hasattr(self.instance, 'discipline'):
                discipline = self.instance.discipline
                self.fields['federation'].queryset = get_filtered_federations_for_discipline(user, discipline)
            else:
                # Sinon, vider temporairement les choix (seront remplis par JavaScript)
                self.fields['federation'].queryset = self.fields['federation'].queryset.none()


class DisciplineFilterForm(forms.Form):
    """
    Formulaire de base pour filtrer par discipline.
    """
    discipline = forms.ModelChoiceField(
        queryset=None,  # Sera défini dans __init__
        required=False,
        empty_label="Toutes les disciplines",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['discipline'].queryset = get_filtered_disciplines_for_user(user)
        else:
            from apps.competitions.models import Discipline
            self.fields['discipline'].queryset = Discipline.objects.all() 

