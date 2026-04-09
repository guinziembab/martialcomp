"""
Formulaires pour la gestion des combats.
"""
from django import forms
from django.db import models
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
    Formulaire pour creer ou modifier une configuration de combat.
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
    Formulaire pour creer ou modifier une equipe.
    """
    class Meta:
        model = Equipe
        fields = ['nom', 'competition', 'category', 'club', 'coach']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'competition': forms.Select(attrs={'class': 'form-control', 'id': 'id_competition'}),
            'category': forms.Select(attrs={'class': 'form-control', 'id': 'id_category'}),
            'club': forms.Select(attrs={'class': 'form-control'}),
            'coach': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filtrer les competitions disponibles
        from apps.competitions.models import Competition, CompetitionCategory
        available_competitions = Competition.objects.filter(
            status__in=['draft', 'published', 'ongoing']  # Exclure les competitions terminees/annulees
        ).order_by('-created_at')

        self.fields['competition'].queryset = available_competitions

        # Configurer le champ categorie
        self.fields['category'].required = False
        self.fields['category'].empty_label = _("--- Selectionnez une categorie ---")
        self.fields['category'].help_text = _("Categorie de combat pour cette equipe (optionnel)")

        # Si on a une instance avec une competition, filtrer les categories
        if self.instance and self.instance.pk and self.instance.competition:
            self.fields['category'].queryset = CompetitionCategory.objects.filter(
                competition=self.instance.competition
            ).order_by('name')
        elif 'competition' in self.data:
            try:
                competition_id = int(self.data.get('competition'))
                self.fields['category'].queryset = CompetitionCategory.objects.filter(
                    competition_id=competition_id
                ).order_by('name')
            except (ValueError, TypeError):
                self.fields['category'].queryset = CompetitionCategory.objects.none()
        elif self.initial.get('competition'):
            # Cas GET avec competition pre-selectionnee via initial (ex: creer_equipe)
            competition = self.initial.get('competition')
            competition_id = competition.pk if hasattr(competition, 'pk') else int(competition)
            self.fields['category'].queryset = CompetitionCategory.objects.filter(
                competition_id=competition_id
            ).order_by('name')
        else:
            self.fields['category'].queryset = CompetitionCategory.objects.none()

        # Si aucune competition n'est disponible, desactiver le formulaire
        if not available_competitions.exists():
            self.fields['competition'].help_text = _("Aucune competition disponible. Creez d'abord une competition.")
            self.fields['competition'].widget.attrs['disabled'] = True
            self.fields['competition'].empty_label = _("--- Aucune competition disponible ---")
        else:
            self.fields['competition'].help_text = _("Selectionnez la competition pour cette equipe.")
            self.fields['competition'].empty_label = _("--- Selectionnez une competition ---")


def _get_competition_practitioners(equipe):
    """Retourne les pratiquants inscrits à la compétition de l'équipe."""
    from apps.competitions.models import Practitioner, CompetitionRegistration
    if equipe and equipe.competition_id:
        registered_ids = CompetitionRegistration.objects.filter(
            competition_id=equipe.competition_id
        ).values_list('practitioner_id', flat=True)
        return Practitioner.objects.filter(id__in=registered_ids).order_by('last_name', 'first_name')
    return Practitioner.objects.all().order_by('last_name', 'first_name')


class MembreEquipeForm(forms.ModelForm):
    """
    Formulaire pour ajouter un membre a une equipe.
    Filtre les pratiquants selon le club de l'equipe et la competition.
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Recuperer l'equipe depuis initial ou instance
        equipe = None
        if self.initial.get('equipe'):
            equipe = self.initial['equipe']
        elif self.instance and self.instance.pk and self.instance.equipe:
            equipe = self.instance.equipe

        # Filtrer les pratiquants par club et par organisation
        if equipe:
            from apps.competitions.models import Practitioner

            # Cacher le champ equipe (deja defini)
            self.fields['equipe'].widget = forms.HiddenInput()

            # Recuperer les pratiquants du club principal et des clubs partenaires
            clubs = equipe.get_all_clubs() if hasattr(equipe, 'get_all_clubs') else [equipe.club] if equipe.club else []

            if clubs:
                # Recuperer les organisations des clubs
                organization_ids = [club.organization_id for club in clubs if club and club.organization_id]

                if organization_ids:
                    practitioners = Practitioner.objects.filter(
                        organization_id__in=organization_ids
                    ).order_by('last_name', 'first_name')
                else:
                    # Fallback : tous les pratiquants inscrits a la competition
                    practitioners = _get_competition_practitioners(equipe)
            else:
                # Fallback : tous les pratiquants inscrits a la competition
                practitioners = _get_competition_practitioners(equipe)

            # Exclure les pratiquants deja membres de cette equipe
            existing_member_ids = equipe.memberships.values_list('pratiquant_id', flat=True)
            practitioners = practitioners.exclude(id__in=existing_member_ids)

            self.fields['pratiquant'].queryset = practitioners
            self.fields['pratiquant'].empty_label = _("--- Selectionnez un pratiquant ---")
        else:
            # Pas d'equipe definie - liste vide
            from apps.competitions.models import Practitioner
            self.fields['pratiquant'].queryset = Practitioner.objects.none()
            self.fields['pratiquant'].empty_label = _("--- Selectionnez d'abord une equipe ---")


class PouleForm(forms.ModelForm):
    """
    Formulaire pour creer ou modifier une poule.
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
    Formulaire pour creer ou modifier un combat.
    """
    class Meta:
        model = Combat
        fields = [
            'competition', 'poule', 'type_combat',
            'equipe_rouge', 'equipe_blanc', 'pratiquant_rouge', 'pratiquant_blanc',
            'duree_combat', 'duree_prolongation', 'configuration',
            'date_planifiee', 'arbitre_central', 'arbitres_lateraux'
        ]
        widgets = {
            'competition': forms.Select(attrs={'class': 'form-control'}),
            'poule': forms.Select(attrs={'class': 'form-control'}),
            'type_combat': forms.Select(attrs={'class': 'form-control'}),
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

    def __init__(self, *args, **kwargs):
        competition_id = kwargs.pop('competition_id', None)
        super().__init__(*args, **kwargs)

        from apps.competitions.models import Competition, Judge
        from apps.competitions.models.combat import Poule

        # Filtrer les configurations de combat disponibles
        self._competition_id = competition_id
        if competition_id:
            try:
                competition = Competition.objects.get(id=competition_id)
                # Verrouiller la compétition — la rendre non-requise car gérée en hidden
                self.fields['competition'].queryset = Competition.objects.filter(id=competition_id)
                self.fields['competition'].initial = competition
                self.fields['competition'].required = False
                self.fields['competition'].widget = forms.HiddenInput()
                # Filtrer les poules par compétition
                self.fields['poule'].queryset = Poule.objects.filter(competition=competition)
                # Filtrer par discipline de la competition
                self.fields['configuration'].queryset = CombatConfiguration.objects.filter(
                    discipline=competition.discipline
                )
            except Competition.DoesNotExist:
                self.fields['configuration'].queryset = CombatConfiguration.objects.all()
        else:
            self.fields['configuration'].queryset = CombatConfiguration.objects.all()

        # Rendre les participants optionnels (la sélection se fait ailleurs)
        for f in ['pratiquant_rouge', 'pratiquant_blanc', 'equipe_rouge', 'equipe_blanc']:
            if f in self.fields:
                self.fields[f].required = False

        # Rendre le champ configuration optionnel avec un message clair
        self.fields['configuration'].required = False
        if not self.fields['configuration'].queryset.exists():
            self.fields['configuration'].help_text = _("Aucune configuration disponible. Vous pouvez creer un combat sans configuration.")
            self.fields['configuration'].empty_label = "--- Aucune configuration (optionnel) ---"
        else:
            self.fields['configuration'].help_text = _("Configuration de scoring pour ce combat (optionnel).")
            self.fields['configuration'].empty_label = "--- Selectionnez une configuration (optionnel) ---"

        # Filtrer les arbitres disponibles (objets Judge actifs)
        arbitres_queryset = Judge.objects.filter(
            active=True,
            user__is_active=True
        ).select_related('user')

        self.fields['arbitre_central'].queryset = arbitres_queryset
        self.fields['arbitres_lateraux'].queryset = arbitres_queryset

        # Rendre le champ arbitre_central optionnel
        self.fields['arbitre_central'].required = False
        if not arbitres_queryset.exists():
            self.fields['arbitre_central'].help_text = _("Aucun arbitre disponible. Vous pouvez creer un combat sans arbitre.")
            self.fields['arbitre_central'].empty_label = "--- Aucun arbitre disponible (optionnel) ---"
        else:
            self.fields['arbitre_central'].help_text = _("Arbitre principal pour ce combat (optionnel).")
            self.fields['arbitre_central'].empty_label = "--- Selectionnez un arbitre (optionnel) ---"

    def clean(self):
        """
        Validation personnalisee. Les participants sont optionnels
        car ils sont assignés via les poules ou manuellement après création.
        """
        cleaned_data = super().clean()
        # Forcer la compétition si elle est verrouillée
        if self._competition_id and not cleaned_data.get('competition'):
            from apps.competitions.models import Competition
            try:
                cleaned_data['competition'] = Competition.objects.get(id=self._competition_id)
            except Competition.DoesNotExist:
                pass
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # S'assurer que la compétition est bien définie
        if self._competition_id and not instance.competition_id:
            instance.competition_id = self._competition_id
        if commit:
            instance.save()
            self.save_m2m()
        return instance


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
        Validation personnalisee pour s'assurer que la valeur est coherente avec le type d'action.
        """
        cleaned_data = super().clean()
        type_action = cleaned_data.get('type_action')
        valeur = cleaned_data.get('valeur')

        if type_action == 'point' and valeur <= 0:
            self.add_error('valeur', _("La valeur d'un point doit etre positive."))

        if type_action == 'penalite' and valeur >= 0:
            self.add_error('valeur', _("La valeur d'une penalite doit etre negative."))

        return cleaned_data


class GenerationPoulesForm(forms.Form):
    """
    Formulaire pour generer automatiquement des poules pour une competition.
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
        (0.25, _('1/4 point - Phan Tu Diem')),
        (0.5, _('1/2 point - Nua Diem')),
        (1.0, _('1 point - Mot Diem')),
        (1.5, _('1.5 points - Mot Diem Duoi')),
        (2.0, _('2 points - Hai Diem')),
    ]

    PENALITE_CHOICES = [
        (0, _('Avertissement - Canh Cao')),
        (-0.5, _('Retrait 1/2 point - Kem Diem')),
        (-1.0, _('Retrait 1 point - Phat')),
        (-2.0, _('Disqualification - Phat Hai/Loai')),
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
        choices=[('point', _('Point')), ('penalite', _('Penalite'))],
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
        Validation personnalisee pour s'assurer que la bonne valeur est fournie
        en fonction du type d'action.
        """
        cleaned_data = super().clean()
        type_action = cleaned_data.get('type_action')

        if type_action == 'point' and not cleaned_data.get('valeur_point'):
            self.add_error('valeur_point', _("Vous devez selectionner une valeur de point."))

        if type_action == 'penalite' and not cleaned_data.get('valeur_penalite'):
            self.add_error('valeur_penalite', _("Vous devez selectionner une valeur de penalite."))

        return cleaned_data
