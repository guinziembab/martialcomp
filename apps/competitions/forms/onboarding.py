from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from ..models import Club, Discipline, Federation, Practitioner
from ..choices import COUNTRY_CHOICES

# Import des formulaires coach
from .coach_forms import CoachProfileForm, DisciplineExpertiseFormSet

# Formulaire pour le profil participant
class ParticipantProfileForm(forms.ModelForm):
    """Formulaire pour le profil participant dans le processus d'onboarding."""
    
    class Meta:
        model = Practitioner
        fields = ['first_name', 'last_name', 'birth_date', 'gender', 'phone', 'address', 'city', 'postal_code', 'nationality']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Prénom')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de famille')}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nationalité')}),
        }
        labels = {
            'first_name': _('Prénom'),
            'last_name': _('Nom de famille'),
            'birth_date': _('Date de naissance'),
            'gender': _('Genre'),
            'phone': _('Téléphone'),
            'address': _('Adresse'),
            'city': _('Ville'),
            'postal_code': _('Code postal'),
            'nationality': _('Nationalité'),
        }

# Formulaire de sélection du rôle
# Note: Les profils Juge/Arbitre et Participant/Compétiteur ont été retirés car
# ils sont créés directement par le responsable de club et reçoivent le bon template
ROLE_CHOICES = [
    ('federation_admin', _('Administrateur de fédération')),
    ('club_manager', _('Responsable de club')),
    ('coach', _('Coach / Enseignant')),
    ('spectator', _('Spectateur')),
    ('external_organizer', _('Organisateur non-membre')),
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
    
    # Champ pays avec sélecteur automatisé personnalisé
    country = forms.ChoiceField(
        label=_("Pays"),
        required=True,
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Sélectionnez votre pays")
    )
    
    # Champs pour la gestion du sous-domaine
    enable_custom_subdomain = forms.BooleanField(
        label=_("Je veux personnaliser mon sous-domaine"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    custom_subdomain = forms.CharField(
        label=_("Sous-domaine personnalisé"),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': _('mon-federation'),
            'pattern': '^[a-z0-9-]+$'
        }),
        help_text=_("Seules les lettres minuscules, chiffres et tirets sont autorisés")
    )
    
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG, SVG. Taille max: 2 Mo")
    )

    # Ajout de champs pour adresse complète
    address = forms.CharField(
        label=_("Adresse"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')})
    )

    city = forms.CharField(
        label=_("Ville"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')})
    )

    postal_code = forms.CharField(
        label=_("Code postal"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')})
    )

    founding_date = forms.DateField(
        label=_("Date de fondation"),
        required=False,
    )


    # Champ pour les disciplines
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label=_("Disciplines"),
        help_text=_("Sélectionnez les disciplines gérées par votre fédération")
    )
    
    class Meta:
        model = Federation
        fields = ['name', 'country', 'description', 'logo', 'website', 'contact_email', 'contact_phone', 'address', 'city', 'postal_code', 'founding_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de la fédération')}),
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
                raise forms.ValidationError(_("Le fichier est trop volumineux. La taille maximale autorisée est de 2 Mo."))
        return logo
    
    def clean_country(self):
        """Validation du pays."""
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError(_("Le pays est obligatoire."))
        return country
    
    def clean_custom_subdomain(self):
        """Validation du sous-domaine personnalisé."""
        subdomain = self.cleaned_data.get('custom_subdomain')
        enable_custom = self.cleaned_data.get('enable_custom_subdomain', False)
        
        if enable_custom and not subdomain:
            raise forms.ValidationError(_("Veuillez spécifier un sous-domaine personnalisé."))
        
        if subdomain:
            # Vérifier que le sous-domaine n'est pas déjà utilisé
            existing_federation = Federation.objects.filter(subdomain=subdomain).exclude(pk=self.instance.pk if self.instance.pk else None)
            if existing_federation.exists():
                raise forms.ValidationError(_("Ce sous-domaine est déjà utilisé par une autre fédération."))
        
        return subdomain
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Générer automatiquement le sous-domaine si non personnalisé
        if not cleaned_data.get('enable_custom_subdomain', False):
            name = cleaned_data.get('name', '')
            if name:
                # Créer un sous-domaine basé sur le nom de la fédération
                subdomain = name.lower()
                # Remplacer les espaces et caractères spéciaux par des tirets
                import re
                subdomain = re.sub(r'[^a-z0-9-]', '-', subdomain)
                subdomain = re.sub(r'-+', '-', subdomain).strip('-')
                cleaned_data['subdomain'] = subdomain
        
        return cleaned_data

class ClubCreationForm(forms.ModelForm):
    """Formulaire pour la création d'un club dans le processus d'onboarding."""
    
    # Champ pays avec sélecteur automatisé personnalisé
    country = forms.ChoiceField(
        label=_("Pays"),
        required=True,
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Sélectionnez votre pays")
    )
    
    # Champs pour la gestion du sous-domaine
    enable_custom_subdomain = forms.BooleanField(
        label=_("Je veux personnaliser mon sous-domaine"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    custom_subdomain = forms.CharField(
        label=_("Sous-domaine personnalisé"),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': _('mon-club'),
            'pattern': '^[a-z0-9-]+$'
        }),
        help_text=_("Seules les lettres minuscules, chiffres et tirets sont autorisés")
    )
    
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG, SVG. Taille max: 2 Mo")
    )

    # Ajout de champs pour adresse complète
    address = forms.CharField(
        label=_("Adresse"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')})
    )

    city = forms.CharField(
        label=_("Ville"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')})
    )

    postal_code = forms.CharField(
        label=_("Code postal"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')})
    )

    founding_date = forms.DateField(
        label=_("Date de fondation"),
        required=False,
    )

    class Meta:
        model = Club
        fields = ['name', 'country', 'description', 'logo', 'website', 'contact_email', 'contact_phone', 'address', 'city', 'postal_code', 'founding_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du club')}),
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
                raise forms.ValidationError(_("Le fichier est trop volumineux. La taille maximale autorisée est de 2 Mo."))
        return logo
    
    def clean_country(self):
        """Validation du pays."""
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError(_("Le pays est obligatoire."))
        return country
    
    def clean_custom_subdomain(self):
        """Validation du sous-domaine personnalisé."""
        subdomain = self.cleaned_data.get('custom_subdomain')
        enable_custom = self.cleaned_data.get('enable_custom_subdomain', False)
        
        if enable_custom and not subdomain:
            raise forms.ValidationError(_("Veuillez spécifier un sous-domaine personnalisé."))
        
        if subdomain:
            # Vérifier que le sous-domaine n'est pas déjà utilisé
            existing_club = Club.objects.filter(subdomain=subdomain).exclude(pk=self.instance.pk if self.instance.pk else None)
            if existing_club.exists():
                raise forms.ValidationError(_("Ce sous-domaine est déjà utilisé par un autre club."))
        
        return subdomain
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Générer automatiquement le sous-domaine si non personnalisé
        if not cleaned_data.get('enable_custom_subdomain', False):
            name = cleaned_data.get('name', '')
            if name:
                # Créer un sous-domaine basé sur le nom du club
                subdomain = name.lower()
                # Remplacer les espaces et caractères spéciaux par des tirets
                import re
                subdomain = re.sub(r'[^a-z0-9-]', '-', subdomain)
                subdomain = re.sub(r'-+', '-', subdomain).strip('-')
                cleaned_data['subdomain'] = subdomain
        
        return cleaned_data

class PractitionerProfileForm(forms.ModelForm):
    """Formulaire pour la création d'un profil de pratiquant."""
    
    # Champ pays avec sélecteur automatisé personnalisé
    country = forms.ChoiceField(
        label=_("Pays"),
        required=True,
        choices=COUNTRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text=_("Sélectionnez votre pays")
    )
    
    # Champs pour les informations personnelles
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre prénom')})
    )
    
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre nom')})
    )
    
    date_of_birth = forms.DateField(
        label=_("Date de naissance"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    # Champs pour les informations de contact
    phone = forms.CharField(
        label=_("Téléphone"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre numéro de téléphone')})
    )
    
    address = forms.CharField(
        label=_("Adresse"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre adresse')})
    )
    
    city = forms.CharField(
        label=_("Ville"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre ville')})
    )
    
    postal_code = forms.CharField(
        label=_("Code postal"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre code postal')})
    )
    
    # Champs pour les informations martiales
    license_number = forms.CharField(
        label=_("Numéro de licence"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre numéro de licence')})
    )
    
    emergency_contact_name = forms.CharField(
        label=_("Nom du contact d'urgence"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du contact d\'urgence')})
    )
    
    emergency_contact_phone = forms.CharField(
        label=_("Téléphone du contact d'urgence"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone du contact d\'urgence')})
    )
    
    class Meta:
        model = Practitioner
        fields = ['first_name', 'last_name', 'date_of_birth', 'phone', 'address', 'city', 'postal_code', 'country', 'license_number', 'emergency_contact_name', 'emergency_contact_phone']
    
    def clean_country(self):
        """Validation du pays."""
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError(_("Le pays est obligatoire."))
        return country

# Import des autres formulaires
# from .competitions import *
# from .grades import *