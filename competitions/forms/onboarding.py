from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from ..models import Club, Discipline, Federation

# Import des formulaires coach
from .coach_forms import CoachProfileForm, DisciplineExpertiseFormSet

# Formulaire de sélection du rôle
ROLE_CHOICES = [
    ('federation_admin', _('Administrateur de fédération')),
    ('club_manager', _('Responsable de club')),
    ('judge', _('Juge/Arbitre')),
    ('coach', _('Coach / Enseignant')),
    ('participant', _('Participant/Compétiteur')),
    ('spectator', _('Spectateur')),
]

class RoleSelectionForm(forms.Form):
    """Formulaire pour la sélection du rôle dans le processus d'onboarding."""
    role = forms.ChoiceField(
        label=_("Sélectionnez votre rôle"),
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-radio'})
    )

class FederationCreationForm(forms.ModelForm):
    """Formulaire pour la création d'une fédération dans le processus d'onboarding."""
    
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpeg', 'png', 'svg'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG, SVG. Taille max: 2 Mo")
    )
    
    class Meta:
        model = Federation
        fields = ['name', 'country', 'description', 'logo', 'website', 'contact_email', 'contact_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de la fédération')}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Pays')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description de la fédération')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://example.com')}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('contact@federation.com')}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone')})
        }
        
    def clean_logo(self):
        """Validation supplémentaire pour le logo."""
        logo = self.cleaned_data.get('logo')
        if logo:
            if logo.size > 2 * 1024 * 1024:  # 2 MB en octets
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 2 Mo."))
        return logo
    
    def clean_website(self):
        """Ajoute http:// si le site web n'a pas de préfixe de protocole."""
        website = self.cleaned_data.get('website')
        if website and not (website.startswith('http://') or website.startswith('https://')):
            website = 'https://' + website
        return website

class ClubCreationForm(forms.ModelForm):
    """Formulaire pour la création d'un club dans le processus d'onboarding."""
    website = forms.URLField(required=False, label=_("Site web"))
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG, SVG. Taille max: 2 Mo")
    )
    
    # Champ pour sélectionner une discipline
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        required=False,
        label=_("Discipline principale"),
        empty_label=_("Sélectionnez une discipline principale (optionnel)"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Club
        fields = ['name', 'address', 'city', 'logo', 'description', 'website', 'contact_email', 'contact_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du club')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description du club')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://example.com')}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('contact@club.com')}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone')})
        }
        
    def clean_logo(self):
        """Validation supplémentaire pour le logo."""
        logo = self.cleaned_data.get('logo')
        if logo:
            if logo.size > 2 * 1024 * 1024:  # 2 MB en octets
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 2 Mo."))
        return logo
    
    def clean_website(self):
        website = self.cleaned_data.get('website')
        if not website:  # Si le champ est vide, retourner une chaîne vide
            return ''
        
        # S'assurer que l'URL a un protocole
        if website and not (website.startswith('http://') or website.startswith('https://')):
            website = 'https://' + website
        return website

class ClubDetailsForm(forms.ModelForm):
    """Formulaire pour la mise à jour des détails d'un club."""
    
    class Meta:
        model = Club
        fields = ['name', 'address', 'city', 'contact_email', 'contact_phone', 
                 'website', 'description', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class JudgeProfileForm(forms.Form):
    """Formulaire pour la configuration du profil de juge."""
    
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    QUALIFICATION_CHOICES = [
        ('novice', _('Novice')),
        ('regional', _('Régional')),
        ('national', _('National')),
        ('international', _('International')),
    ]
    
    qualification_level = forms.ChoiceField(
        label=_("Niveau de qualification"),
        choices=QUALIFICATION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    years_experience = forms.IntegerField(
        label=_("Années d'expérience"),
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        label=_("Disciplines"),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    certification_number = forms.CharField(
        label=_("Numéro de certification"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    club = forms.ModelChoiceField(
        queryset=Club.objects.filter(is_active=True),
        label=_("Club affilié"),
        required=False,
        empty_label=_("Aucun club affilié"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    federation = forms.ModelChoiceField(
        queryset=Federation.objects.filter(is_active=True),
        label=_("Fédération affiliée"),
        required=False,
        empty_label=_("Aucune fédération affiliée"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        label=_("Notes additionnelles"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    is_technical_judge = forms.BooleanField(
        label=_("Juge technique"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_combat_referee = forms.BooleanField(
        label=_("Arbitre de combat"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Au moins un type de juge doit être sélectionné
        is_technical_judge = cleaned_data.get('is_technical_judge')
        is_combat_referee = cleaned_data.get('is_combat_referee')
        
        if not is_technical_judge and not is_combat_referee:
            raise forms.ValidationError(
                _("Vous devez sélectionner au moins un type de rôle : juge technique ou arbitre de combat.")
            )
        
        return cleaned_data

class ParticipantProfileForm(forms.Form):
    """Formulaire pour la configuration du profil de participant."""
    
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    date_of_birth = forms.DateField(
        label=_("Date de naissance"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    gender = forms.ChoiceField(
        label=_("Genre"),
        choices=[
            ('male', _('Homme')),
            ('female', _('Femme')),
            ('other', _('Autre'))
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    club = forms.ModelChoiceField(
        queryset=Club.objects.filter(is_active=True),
        label=_("Club"),
        required=False,
        empty_label=_("Aucun club"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        label=_("Disciplines pratiquées"),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    grade = forms.CharField(
        label=_("Grade actuel"),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: Ceinture noire 2ème dan')})
    )
    
    license_number = forms.CharField(
        label=_("Numéro de licence"),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    medical_certificate_date = forms.DateField(
        label=_("Date du certificat médical"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    avatar = forms.ImageField(
        label=_("Photo de profil"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG. Taille max: 2 Mo")
    )
    
    weight = forms.DecimalField(
        label=_("Poids (kg)"),
        max_digits=5,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    
    height = forms.DecimalField(
        label=_("Taille (cm)"),
        max_digits=5,
        decimal_places=1,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    
    notes = forms.CharField(
        label=_("Notes additionnelles"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    
    def clean_avatar(self):
        """Validation supplémentaire pour l'avatar."""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if avatar.size > 2 * 1024 * 1024:  # 2 MB en octets
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 2 Mo."))
        return avatar
    
