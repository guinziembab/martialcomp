from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError

from ..models import CoachProfile, DisciplineExpertise, Discipline, Federation


class CoachProfileForm(forms.ModelForm):
    """Formulaire pour le profil coach"""
    
    # Ajout d'un champ pour saisir le lieu d'enseignement manuellement
    teaching_place_name = forms.CharField(
        label=_("Lieu ou club d'enseignement"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom de votre club, dojo ou lieu d'enseignement principal")
        })
    )
    
    # Ajout de champs pour les réseaux sociaux et le site web
    website = forms.URLField(
        label=_("Site web"),
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': _("https://votre-site-web.com")
        })
    )
    
    social_links = forms.CharField(
        label=_("Réseaux sociaux"),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'class': 'form-control',
            'placeholder': _("Instagram: @votrecompte\nYouTube: votre-chaine")
        })
    )
    
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
            'profile_type': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': _("Sélectionnez votre type de profil")
            }),
            'years_teaching': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'primary_teaching_place': forms.Select(attrs={
                'class': 'form-control select2',
                'data-placeholder': _("Sélectionnez votre club principal (optionnel)")
            }),
            'hourly_rate_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Ex: 50-80€")
            }),
            'available_for_seminars': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'available_for_private_lessons': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'available_for_online_coaching': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuration additionnelle des champs
        self.fields['primary_teaching_place'].required = False
        
        # Ajout d'un texte d'aide
        self.fields['hourly_rate_range'].help_text = _("Approximation de vos tarifs horaires, sera affiché sur votre profil public (optionnel)")
        
        # Si une instance existe déjà, initialiser les champs personnalisés
        if self.instance and self.instance.pk:
            self.initial['teaching_place_name'] = self.instance.teaching_place_name
            
            # Initialiser les champs pour les données JSON
            visibility_settings = self.instance.visibility_settings or {}
            self.initial['website'] = visibility_settings.get('website', '')
            self.initial['social_links'] = visibility_settings.get('social_links', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Sauvegarder le lieu d'enseignement personnalisé
        if self.cleaned_data.get('teaching_place_name'):
            instance.teaching_place_name = self.cleaned_data['teaching_place_name']
        
        # Sauvegarder les paramètres de visibilité avec les nouveaux champs
        visibility_settings = instance.visibility_settings or {}
        visibility_settings['website'] = self.cleaned_data.get('website', '')
        visibility_settings['social_links'] = self.cleaned_data.get('social_links', '')
        instance.visibility_settings = visibility_settings
        
        if commit:
            instance.save()
        
        return instance


class DisciplineExpertiseForm(forms.ModelForm):
    """Formulaire pour l'expertise dans une discipline"""
    
    # Champ fédération optionnel avec possibilité 'Autre'
    federation_other = forms.CharField(
        label=_("Autre fédération"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom de la fédération")
        })
    )
    
    # Ajout d'un champ pour l'enseignement en ligne
    offers_online_training = forms.BooleanField(
        label=_("Propose des cours en ligne pour cette discipline"),
        required=False,
        initial=False
    )
    
    class Meta:
        model = DisciplineExpertise
        fields = [
            'discipline',
            'level',
            'years_experience',
            'years_teaching',
            'is_primary',
            'current_grade',
            'teaching_certification',
            'federation',
            'public_description'
        ]
        widgets = {
            'discipline': forms.Select(attrs={
                'class': 'form-control discipline-select',
                'data-placeholder': _("Sélectionnez une discipline")
            }),
            'level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'years_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
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
            'federation': forms.Select(attrs={
                'class': 'form-control federation-select',
                'data-placeholder': _("Sélectionnez une fédération")
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input primary-discipline-checkbox'
            }),
            'public_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _("Décrivez votre expertise dans cette discipline...")
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter l'option "Autre" à la liste des fédérations
        federation_choices = list(self.fields['federation'].choices)
        federation_choices.append((None, _("Autre (spécifier)...")))
        self.fields['federation'].choices = federation_choices
        
        # Modifier les labels pour plus de clarté
        self.fields['is_primary'].label = _("Discipline principale")
        self.fields['years_experience'].label = _("Années de pratique")
        self.fields['years_teaching'].label = _("Années d'enseignement")
        
        # Si une instance existe déjà, initialiser les valeurs
        if self.instance and self.instance.pk:
            # Charger l'autre fédération si nécessaire
            if not self.instance.federation:
                self.initial['federation_other'] = self.instance.federation_name
    
    def clean(self):
        cleaned_data = super().clean()
        federation = cleaned_data.get('federation')
        federation_other = cleaned_data.get('federation_other')
        is_primary = cleaned_data.get('is_primary')
        
        # Vérification de la cohérence des données de fédération
        if not federation and not federation_other:
            self.add_error('federation', _("Veuillez sélectionner une fédération ou en spécifier une autre."))
        
        return cleaned_data


class BaseDisciplineExpertiseFormSet(BaseInlineFormSet):
    """Formset de base personnalisé pour gérer les validations entre formulaires"""
    
    def clean(self):
        """Ensure at least one discipline is marked as primary"""
        super().clean()
        
        if any(self.errors):
            # Ne pas valider si les formulaires individuels ont des erreurs
            return
        
        # Vérifier qu'au moins un formulaire est rempli
        if not self.forms or all(form.cleaned_data.get('DELETE', False) for form in self.forms):
            raise ValidationError(_('Vous devez spécifier au moins une discipline.'))
        
        # Vérifier qu'au moins une discipline est marquée comme principale
        primary_count = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_primary'):
                    primary_count += 1
                    
        if primary_count == 0:
            raise ValidationError(_('Vous devez désigner au moins une discipline comme principale.'))
        elif primary_count > 1:
            raise ValidationError(_('Vous ne pouvez pas avoir plusieurs disciplines principales.'))
        
        # Vérifier qu'une même discipline n'est pas présente plusieurs fois
        disciplines = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                discipline = form.cleaned_data.get('discipline')
                if discipline in disciplines:
                    raise ValidationError(_('Vous ne pouvez pas ajouter la même discipline plusieurs fois.'))
                disciplines.append(discipline)

# Formset pour gérer plusieurs expertises de disciplines
DisciplineExpertiseFormSet = inlineformset_factory(
    CoachProfile,
    DisciplineExpertise,
    form=DisciplineExpertiseForm,
    formset=BaseDisciplineExpertiseFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    max_num=10,  # Limite raisonnable
    validate_min=True,
    validate_max=True
)


class CoachAvailabilityForm(forms.ModelForm):
    """Formulaire pour les disponibilités du coach"""
    
    # Champs pour les disponibilités détaillées
    available_weekdays = forms.MultipleChoiceField(
        label=_("Jours disponibles"),
        choices=[
            (0, _("Lundi")),
            (1, _("Mardi")),
            (2, _("Mercredi")),
            (3, _("Jeudi")),
            (4, _("Vendredi")),
            (5, _("Samedi")),
            (6, _("Dimanche"))
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    available_timeframes = forms.MultipleChoiceField(
        label=_("Tranches horaires disponibles"),
        choices=[
            ('morning', _("Matinée (8h-12h)")),
            ('afternoon', _("Après-midi (12h-18h)")),
            ('evening', _("Soirée (18h-22h)")),
            ('weekend', _("Week-end"))
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    travel_radius = forms.IntegerField(
        label=_("Rayon de déplacement (km)"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0',
            'placeholder': '50'
        }),
        help_text=_("Distance maximale que vous êtes prêt à parcourir pour enseigner (en km)")
    )
    
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
            }),
            'available_for_seminars': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'available_for_private_lessons': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'available_for_online_coaching': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Textes d'aide pour les champs existants
        self.fields['available_for_seminars'].label = _("Disponible pour animer des stages et séminaires")
        self.fields['available_for_private_lessons'].label = _("Disponible pour des cours particuliers")
        self.fields['available_for_online_coaching'].label = _("Disponible pour des cours en ligne")
        
        # Si une instance existe déjà, initialiser les champs personnalisés depuis les paramètres
        if self.instance and self.instance.pk:
            availability_settings = self.instance.visibility_settings.get('availability', {}) if self.instance.visibility_settings else {}
            
            # Convertir les jours disponibles en liste d'entiers
            weekdays = availability_settings.get('weekdays', [])
            self.initial['available_weekdays'] = [int(day) for day in weekdays] if weekdays else []
            
            # Autres paramètres
            self.initial['available_timeframes'] = availability_settings.get('timeframes', [])
            self.initial['travel_radius'] = availability_settings.get('travel_radius', 0)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Initialiser les paramètres de visibilité si nécessaire
        if not instance.visibility_settings:
            instance.visibility_settings = {}
        
        # Sauvegarder les informations de disponibilité
        availability = instance.visibility_settings.get('availability', {})
        
        # Mettre à jour avec les nouvelles valeurs
        availability['weekdays'] = self.cleaned_data.get('available_weekdays', [])
        availability['timeframes'] = self.cleaned_data.get('available_timeframes', [])
        availability['travel_radius'] = self.cleaned_data.get('travel_radius', 0)
        
        # Mettre à jour les paramètres de visibilité
        instance.visibility_settings['availability'] = availability
        
        if commit:
            instance.save()
        
        return instance


class MultiDisciplineSelectionForm(forms.Form):
    """Formulaire pour la sélection multiple de disciplines"""
    
    primary_discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all(),
        label=_("Discipline principale"),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': _("Sélectionnez votre discipline principale")
        }),
        required=True
    )
    
    secondary_disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.all(),
        label=_("Disciplines secondaires"),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input discipline-checkbox'
        }),
        required=False,
        help_text=_("Sélectionnez jusqu'à 9 disciplines secondaires que vous enseignez")
    )
    
    experience_years = forms.IntegerField(
        label=_("Années d'expérience totale"),
        min_value=0,
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '0'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Tri des disciplines par nom
        self.fields['primary_discipline'].queryset = Discipline.objects.all().order_by('name')
        self.fields['secondary_disciplines'].queryset = Discipline.objects.all().order_by('name')
    
    def clean(self):
        cleaned_data = super().clean()
        primary = cleaned_data.get('primary_discipline')
        secondaries = cleaned_data.get('secondary_disciplines', [])
        
        if primary and primary in secondaries:
            raise forms.ValidationError(
                _("La discipline principale ne peut pas être aussi une discipline secondaire.")
            )
            
        if secondaries and len(secondaries) > 9:
            raise forms.ValidationError(
                _("Vous ne pouvez pas sélectionner plus de 9 disciplines secondaires.")
            )
        
        return cleaned_data