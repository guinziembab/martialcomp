"""
Formulaires pour la gestion des combats.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from apps.competitions.models.combat import (
    CombatConfiguration, 
    Equipe, 
    MembreEquipe, 
    Poule, 
    Combat, 
    ActionCombat
)

class CombatConfigurationForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une configuration de combat.
    """
    class Meta:
        model = CombatConfiguration
        fields = [
            'discipline', 'nom', 'system', 'description',
            'durees_combat', 'durees_prolongation',
            'nb_sorties_avertissement', 'nb_sorties_disqualification',
            'valeurs_points', 'valeurs_penalites',
            'nb_avertissements_sanction', 'valeur_sanction'
        ]
        widgets = {
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'system': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'durees_combat': forms.Textarea(attrs={'class': 'form-control'}),
            'durees_prolongation': forms.Textarea(attrs={'class': 'form-control'}),
            'nb_sorties_avertissement': forms.NumberInput(attrs={'class': 'form-control'}),
            'nb_sorties_disqualification': forms.NumberInput(attrs={'class': 'form-control'}),
            'valeurs_points': forms.Textarea(attrs={'class': 'form-control'}),
            'valeurs_penalites': forms.Textarea(attrs={'class': 'form-control'}),
            'nb_avertissements_sanction': forms.NumberInput(attrs={'class': 'form-control'}),
            'valeur_sanction': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class EquipeForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une équipe.
    """
    class Meta:
        model = Equipe
        fields = ['nom', 'competition', 'club', 'coach']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'competition': forms.Select(attrs={'class': 'form-control'}),
            'club': forms.Select(attrs={'class': 'form-control'}),
            'coach': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les compétitions disponibles
        from apps.competitions.models import Competition
        available_competitions = Competition.objects.filter(
            status__in=['draft', 'published', 'ongoing']  # Exclure les compétitions terminées/annulées
        ).order_by('-created_at')
        
        self.fields['competition'].queryset = available_competitions
        
        # Si aucune compétition n'est disponible, désactiver le formulaire
        if not available_competitions.exists():
            self.fields['competition'].help_text = "Aucune compétition disponible. Créez d'abord une compétition."
            self.fields['competition'].widget.attrs['disabled'] = True
            # Ajouter une option vide avec message
            self.fields['competition'].empty_label = "--- Aucune compétition disponible ---"
        else:
            self.fields['competition'].help_text = "Sélectionnez la compétition pour cette équipe."
            self.fields['competition'].empty_label = "--- Sélectionnez une compétition ---"


class MembreEquipeForm(forms.ModelForm):
    """
    Formulaire pour ajouter un membre Ã  une équipe.
    """
    class Meta:
        model = MembreEquipe
        fields = ['equipe', 'pratiquant', 'est_remplacant', 'ordre']
        widgets = {
            'equipe': forms.Select(attrs={'class': 'form-control'}),
            'pratiquant': forms.Select(attrs={'class': 'form-control'}),
            'est_remplacant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class PouleForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier une poule.
    """
    class Meta:
        model = Poule
        fields = ['competition', 'nom', 'numero', 'phase', 'equipes', 'pratiquants']
        widgets = {
            'competition': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'phase': forms.Select(attrs={'class': 'form-control'}),
            'equipes': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'pratiquants': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class CombatForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un combat.
    """
    class Meta:
        model = Combat
        fields = [
            'competition', 'poule', 'type_combat', 'status',
            'equipe_rouge', 'equipe_blanc', 'pratiquant_rouge', 'pratiquant_blanc',
            'duree_combat', 'duree_prolongation', 'configuration',
            'date_planifiee', 'arbitre_central', 'arbitres_lateraux'
        ]
        widgets = {
            'competition': forms.Select(attrs={'class': 'form-control'}),
            'poule': forms.Select(attrs={'class': 'form-control'}),
            'type_combat': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'equipe_rouge': forms.Select(attrs={'class': 'form-control'}),
            'equipe_blanc': forms.Select(attrs={'class': 'form-control'}),
            'pratiquant_rouge': forms.Select(attrs={'class': 'form-control'}),
            'pratiquant_blanc': forms.Select(attrs={'class': 'form-control'}),
            'duree_combat': forms.NumberInput(attrs={'class': 'form-control', 'min': 30}),
            'duree_prolongation': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'configuration': forms.Select(attrs={'class': 'form-control'}),
            'date_planifiee': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'arbitre_central': forms.Select(attrs={'class': 'form-control'}),
            'arbitres_lateraux': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """
        Validation personnalisée pour s'assurer que les bons participants sont définis en fonction
        du type de combat (individuel ou par équipe).
        """
        cleaned_data = super().clean()
        type_combat = cleaned_data.get('type_combat')
        
        if type_combat == 'individuel':
            if not cleaned_data.get('pratiquant_rouge'):
                self.add_error('pratiquant_rouge', _("Un pratiquant rouge est requis pour un combat individuel."))
            if not cleaned_data.get('pratiquant_blanc'):
                self.add_error('pratiquant_blanc', _("Un pratiquant blanc est requis pour un combat individuel."))
        
        elif type_combat == 'equipe':
            if not cleaned_data.get('equipe_rouge'):
                self.add_error('equipe_rouge', _("Une équipe rouge est requise pour un combat par équipe."))
            if not cleaned_data.get('equipe_blanc'):
                self.add_error('equipe_blanc', _("Une équipe blanche est requise pour un combat par équipe."))
        
        return cleaned_data


class ActionCombatForm(forms.ModelForm):
    """
    Formulaire pour enregistrer une action dans un combat.
    """
    class Meta:
        model = ActionCombat
        fields = ['combat', 'type_action', 'couleur', 'valeur', 'description', 'arbitre']
        widgets = {
            'combat': forms.Select(attrs={'class': 'form-control'}),
            'type_action': forms.Select(attrs={'class': 'form-control'}),
            'couleur': forms.Select(attrs={'class': 'form-control'}),
            'valeur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'arbitre': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        """
        Validation personnalisée pour s'assurer que la valeur est cohérente avec le type d'action.
        """
        cleaned_data = super().clean()
        type_action = cleaned_data.get('type_action')
        valeur = cleaned_data.get('valeur')
        
        if type_action == 'point' and valeur <= 0:
            self.add_error('valeur', _("La valeur d'un point doit Ãªtre positive."))
        
        if type_action == 'penalite' and valeur >= 0:
            self.add_error('valeur', _("La valeur d'une pénalité doit Ãªtre négative."))
        
        return cleaned_data


class GenerationPoulesForm(forms.Form):
    """
    Formulaire pour générer automatiquement des poules pour une compétition.
    """
    competition = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    nombre_poules = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1})
    )
    eviter_clubs_meme_poule = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    eviter_pays_meme_poule = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.competitions.models import Competition
        self.fields['competition'].queryset = Competition.objects.all()


class AttributionPointForm(forms.Form):
    """
    Formulaire pour attribuer rapidement des points lors d'un combat en cours.
    """
    POINT_CHOICES = [
        (0.25, _('Â¼ point - PhÃ¢n Tu Äiá»ƒm')),
        (0.5, _('Â½ point - Ná»­a Äiá»ƒm')),
        (1.0, _('1 point - Má»™t Äiá»ƒm')),
        (1.5, _('1Â½ points - Má»™t Äiá»ƒm DÆ°á»›i')),
        (2.0, _('2 points - Hai Äiá»ƒm')),
    ]
    
    PENALITE_CHOICES = [
        (0, _('Avertissement - Cáº£nh CÃ¡o')),
        (-0.5, _('Retrait Â½ point - Kém Äiá»ƒm')),
        (-1.0, _('Retrait 1 point - Pháº¡t')),
        (-2.0, _('Disqualification - Pháº¡t Hai/Loáº¡i')),
    ]
    
    combat = forms.ModelChoiceField(
        queryset=None,
        widget=forms.HiddenInput()
    )
    couleur = forms.ChoiceField(
        choices=[('rouge', _('Rouge')), ('blanc', _('Blanc'))],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    type_action = forms.ChoiceField(
        choices=[('point', _('Point')), ('penalite', _('Pénalité'))],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    valeur_point = forms.ChoiceField(
        choices=POINT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    valeur_penalite = forms.ChoiceField(
        choices=PENALITE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        combat = kwargs.pop('combat', None)
        super().__init__(*args, **kwargs)
        from apps.competitions.models.combat import Combat
        self.fields['combat'].queryset = Combat.objects.all()
        
        if combat:
            self.fields['combat'].initial = combat.id
    
    def clean(self):
        """
        Validation personnalisée pour s'assurer que la bonne valeur est fournie
        en fonction du type d'action.
        """
        cleaned_data = super().clean()
        type_action = cleaned_data.get('type_action')
        
        if type_action == 'point' and not cleaned_data.get('valeur_point'):
            self.add_error('valeur_point', _("Vous devez sélectionner une valeur de point."))
        
        if type_action == 'penalite' and not cleaned_data.get('valeur_penalite'):
            self.add_error('valeur_penalite', _("Vous devez sélectionner une valeur de pénalité."))
        
        return cleaned_data

