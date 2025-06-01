from django import forms
from django.utils.translation import gettext_lazy as _
from competitions.models import Competition, Discipline, Club, CompetitionType
from django.core.validators import FileExtensionValidator, MinValueValidator
from ..models import Competition, CompetitionCategory
from competitions.models import Match, CompetitionCategory
# Références par chaîne pour éviter l'importation circulaire
def get_models():
    from ..models import Competition, Discipline, CompetitionCategory
    from ..models import CompetitionRegistration, ParticipantCategoryRegistration, CompetitionType
    from ..models.judges import JudgeQualification, QUALIFICATION_LEVELS
    return {
        'Competition': Competition,
        'Discipline': Discipline,
        'CompetitionCategory': CompetitionCategory,
        'CompetitionRegistration': CompetitionRegistration,
        'ParticipantCategoryRegistration': ParticipantCategoryRegistration,
        'CompetitionType': CompetitionType,
        'JudgeQualification': JudgeQualification,
        'QUALIFICATION_LEVELS': QUALIFICATION_LEVELS
    }
from django.utils import timezone


class CompetitionForm(forms.ModelForm):
    """
    Formulaire unifié pour la création et modification des compétitions.
    Utilisable par tous les profils (fédération, club, etc.)
    """
    # Champs supplémentaires qui ne sont pas directement dans le modèle
    is_published = forms.BooleanField(
        label=_("Publier immédiatement"),
        required=False,
        initial=True,
        help_text=_("Si non cochée, la compétition sera enregistrée comme brouillon")
    )
    
    # Sélection des types de compétition (ManyToMany)
    competition_types = forms.ModelMultipleChoiceField(
        queryset=CompetitionType.objects.all(),
        label=_("Types de compétition"),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        help_text=_("Sélectionnez un ou plusieurs types de compétition (Ctrl+clic pour sélectionner plusieurs)"),
        required=True
    )
    
    # Champs pour les dates et heures
    start_time = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=False
    )
    
    end_time = forms.TimeField(
        label=_("Heure de fin"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=False
    )
    
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo/Bannière"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])
        ],
        widget=forms.FileInput(attrs={'class': 'custom-file-input'}),
        help_text=_("Formats acceptés: JPG, JPEG, PNG, GIF. Taille max: 2 Mo")
    )
    
    # Nombre max de participants
    max_participants = forms.IntegerField(
        label=_("Nombre maximum de participants"),
        validators=[MinValueValidator(1)],
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
    
    # Âge minimum des participants
    min_age = forms.IntegerField(
        label=_("Âge minimum"),
        validators=[MinValueValidator(0)],
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )
    
    class Meta:
        model = Competition
        fields = [
            'title', 'description', 'start_date', 'end_date', 
            'address', 'city', 'discipline', 'registration_deadline',
            'logo'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Ex: Championnat National de Qwan Ki Do 2025')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': '4', 
                'placeholder': _('Description détaillée de la compétition...')
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Ex: Gymnase Jean Bouin, 5 Rue des Sports')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('Ex: Paris')
            }),
            'discipline': forms.Select(attrs={
                'class': 'form-control'
            }),
            'registration_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre certains champs obligatoires
        self.fields['title'].required = True
        self.fields['start_date'].required = True
        self.fields['end_date'].required = True
        self.fields['address'].required = True
        
        # Rendre la discipline obligatoire
        self.fields['discipline'].required = True
        
        # Définir des aides contextuelles
        self.fields['registration_deadline'].help_text = _("Date limite pour l'inscription des participants")
        
        # Filtrer les disciplines actives
        self.fields['discipline'].queryset = Discipline.objects.filter(is_active=True)
        
        # Si nous sommes en mode édition (instance existante)
        if self.instance and self.instance.pk:
            # Initialiser la sélection des types de compétition
            self.fields['competition_types'].initial = self.instance.competition_types.all()
            
            # Marquer comme "publié" si c'est le cas
            self.fields['is_published'].initial = self.instance.status == 'published'
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Vérifier que la date de fin est après la date de début
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', _("La date de fin doit être postérieure ou égale à la date de début."))
        
        # Vérifier que la date limite d'inscription est avant la date de début
        registration_deadline = cleaned_data.get('registration_deadline')
        
        if registration_deadline and start_date and registration_deadline > start_date:
            self.add_error('registration_deadline', _("La date limite d'inscription doit être antérieure à la date de début."))
        
        # Vérifier la taille du logo
        logo = cleaned_data.get('logo')
        if logo and hasattr(logo, 'size') and logo.size > 2 * 1024 * 1024:  # 2 MB
            self.add_error('logo', _("La taille du fichier ne doit pas dépasser 2 Mo."))
        
        return cleaned_data

class CompetitionRegistrationForm(forms.ModelForm):
    # Champs pour afficher les informations du pratiquant (non-modifiables)
    club = forms.CharField(disabled=True, required=False)
    first_name = forms.CharField(disabled=True, required=False)
    last_name = forms.CharField(disabled=True, required=False)
    birth_date = forms.DateField(disabled=True, required=False)
    grade = forms.CharField(disabled=True, required=False)
    age = forms.IntegerField(disabled=True, required=False)
    
    # Participation à la compétition
    is_competitor = forms.BooleanField(label=_("Participer en tant que compétiteur"), required=False)
    
    # Les champs pour les qualifications seront initialisés dans __init__
    technical_judge_level = None
    combat_referee_level = None
    
    class Meta:
        model = None  # Sera défini dans __init__
        fields = ['is_competitor', 'is_technical_judge', 'is_combat_referee', 
                  'is_volunteer', 'is_coach', 'notes']
        
    def __init__(self, *args, **kwargs):
        self.competition = kwargs.pop('competition', None)
        self.practitioner = kwargs.pop('practitioner', None)
        
        # Initialisation des modèles pour éviter les problèmes d'importation
        models = get_models()
        self.Meta.model = models['CompetitionRegistration']
        
        # Initialiser les champs de qualification
        self.base_fields['technical_judge_level'] = forms.ChoiceField(
            label=_("Niveau de qualification (Juge Technique)"),
            choices=[('', '---------')] + list(models['QUALIFICATION_LEVELS']),
            required=False
        )
        self.base_fields['combat_referee_level'] = forms.ChoiceField(
            label=_("Niveau de qualification (Arbitre Combat)"),
            choices=[('', '---------')] + list(models['QUALIFICATION_LEVELS']),
            required=False
        )
        
        super().__init__(*args, **kwargs)
        
        if self.practitioner:
            # Pré-remplir les infos du pratiquant
            self.fields['club'].initial = self.practitioner.club.name if self.practitioner.club else ""
            self.fields['first_name'].initial = self.practitioner.first_name
            self.fields['last_name'].initial = self.practitioner.last_name
            self.fields['birth_date'].initial = self.practitioner.birth_date
            self.fields['grade'].initial = self.practitioner.grade
            self.fields['age'].initial = self.practitioner.age
            
            # Récupérer les qualifications existantes
            try:
                technical_qual = models['JudgeQualification'].objects.get(
                    practitioner=self.practitioner,
                    qualification_type='technical_judge'
                )
                self.fields['technical_judge_level'].initial = technical_qual.level
            except models['JudgeQualification'].DoesNotExist:
                pass
                
            try:
                combat_qual = models['JudgeQualification'].objects.get(
                    practitioner=self.practitioner,
                    qualification_type='combat_referee'
                )
                self.fields['combat_referee_level'].initial = combat_qual.level
            except models['JudgeQualification'].DoesNotExist:
                pass
        
        if self.competition:
            # Ajouter des champs dynamiques pour les types de compétition
            competition_types = self.competition.competition_types.all()
            
            for comp_type in competition_types:
                field_name = f'type_{comp_type.id}'
                self.fields[field_name] = forms.BooleanField(
                    label=comp_type.name,
                    required=False
                )
                
                # Ajouter des champs pour les catégories de chaque type
                categories = models['CompetitionCategory'].objects.filter(
                    competition=self.competition,
                    competition_type=comp_type
                )
                
                if categories.exists():
                    category_field = f'category_for_type_{comp_type.id}'
                    self.fields[category_field] = forms.ModelChoiceField(
                        queryset=categories,
                        label=_("Catégorie"),
                        required=False,
                        widget=forms.RadioSelect
                    )


class CompetitionCategoryForm(forms.ModelForm):
    """
    Formulaire pour la création/modification des catégories de compétition.
    """
    class Meta:
        model = CompetitionCategory
        fields = [
            'competition_type', 'name', 'gender',
            'min_age', 'max_age', 'min_weight', 'max_weight',
            'min_grade', 'max_grade'
        ]
        widgets = {
            'competition_type': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de la catégorie')}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'max_age': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'min_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.1'}),
            'max_weight': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.1'}),
            'min_grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: Ceinture verte')}),
            'max_grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: Ceinture noire')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Rendre certains champs obligatoires
        self.fields['competition_type'].required = True
        self.fields['name'].required = True
        
        # Définir des aides contextuelles
        self.fields['gender'].help_text = _("Genre pour cette catégorie")
        self.fields['min_age'].help_text = _("Âge minimum, laisser vide si pas de limite")
        self.fields['max_age'].help_text = _("Âge maximum, laisser vide si pas de limite")
        self.fields['min_weight'].help_text = _("Poids minimum en kg, laisser vide si pas de limite")
        self.fields['max_weight'].help_text = _("Poids maximum en kg, laisser vide si pas de limite")
        self.fields['min_grade'].help_text = _("Grade minimum, laisser vide si pas de limite")
        self.fields['max_grade'].help_text = _("Grade maximum, laisser vide si pas de limite")
        
        # Si nous sommes en mode édition (instance existante) et que la compétition est associée
        if self.instance and self.instance.pk and hasattr(self.instance, 'competition') and self.instance.competition:
            # Filtrer les types de compétition disponibles pour cette compétition
            self.fields['competition_type'].queryset = self.instance.competition.competition_types.all()
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Vérifier que l'âge maximum est supérieur à l'âge minimum
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')
        
        if min_age is not None and max_age is not None and max_age < min_age:
            self.add_error('max_age', _("L'âge maximum doit être supérieur ou égal à l'âge minimum."))
        
        # Vérifier que le poids maximum est supérieur au poids minimum
        min_weight = cleaned_data.get('min_weight')
        max_weight = cleaned_data.get('max_weight')
        
        if min_weight is not None and max_weight is not None and max_weight < min_weight:
            self.add_error('max_weight', _("Le poids maximum doit être supérieur ou égal au poids minimum."))
        
        return cleaned_data
    
class CompetitionScheduleForm(forms.ModelForm):
    """
    Formulaire pour la gestion des horaires de compétition.
    """
    class Meta:
        model = Competition  # ou tout autre modèle pertinent
        fields = ['start_date', 'end_date', 'start_time', 'end_time']
        widgets = {
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        }


class TatamiScheduleForm(forms.ModelForm):
    """
    Formulaire pour la gestion des plannings par tatami.
    """
    class Meta:
        model = Competition  # ou un modèle plus approprié si disponible
        fields = []  # Ajouter les champs appropriés du modèle
    
    # Ajouter des champs personnalisés si nécessaire
    tatami_number = forms.IntegerField(
        label=_("Numéro de tatami"),
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    start_hour = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    end_hour = forms.TimeField(
        label=_("Heure de fin"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    # Ajouter des méthodes de validation ou de sauvegarde personnalisées
    def clean(self):
        cleaned_data = super().clean()
        start_hour = cleaned_data.get('start_hour')
        end_hour = cleaned_data.get('end_hour')
        
        if start_hour and end_hour and start_hour >= end_hour:
            raise forms.ValidationError(_("L'heure de fin doit être postérieure à l'heure de début."))
        
        return cleaned_data
    
class CategoryScheduleForm(forms.ModelForm):
    """
    Formulaire pour la gestion des plannings par catégorie de compétition.
    """
    class Meta:
        model = CompetitionCategory
        fields = ['name', 'competition']  # Ajustez selon les champs disponibles dans votre modèle
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'competition': forms.Select(attrs={'class': 'form-select'})
        }
    
    # Champs supplémentaires pour la planification
    date = forms.DateField(
        label=_("Date"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    start_time = forms.TimeField(
        label=_("Heure de début"),
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    end_time = forms.TimeField(
        label=_("Heure de fin"),
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    
    tatami = forms.IntegerField(
        label=_("Tatami"),
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_("L'heure de fin doit être postérieure à l'heure de début."))
        
        return cleaned_data
    
class MatchTimeSlotForm(forms.ModelForm):
    """
    Formulaire pour la gestion des créneaux horaires des matchs.
    """
    class Meta:
        model = Match  # Assurez-vous que ce modèle existe dans votre application
        fields = ['date_match', 'start_time', 'end_time']  # Ajustez selon votre modèle
        widgets = {
            'date_match': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        }
    
    # Champs supplémentaires si nécessaire
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
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        date_match = cleaned_data.get('date_match')
        
        # Vérification des champs temporels
        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_("L'heure de fin doit être postérieure à l'heure de début."))
        
        # Autres validations spécifiques au créneau de match
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Logique de sauvegarde personnalisée si nécessaire
        
        if commit:
            instance.save()
        return instance
    
class BulkCategoryScheduleForm(forms.Form):
    """
    Formulaire pour la planification en masse des catégories de compétition.
    """
    # Correction du filtre is_active en utilisant des champs réels
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
    

