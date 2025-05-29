from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from ..models import Discipline
from organizations.models import Organization


class FederationForm(forms.ModelForm):
    """Formulaire pour la création et modification des fédérations."""
    
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG, SVG. Taille max: 2 Mo")
    )
    
    # Ajout du champ founding_date comme champ de formulaire normal (pas relié au modèle)
    founding_date = forms.DateField(
        label=_("Date de fondation"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = Organization
        fields = [
            'name', 'description', 'country', 'address', 'city', 'postal_code',
            'logo', 'website', 'email', 'phone',
            # 'founding_date' est retiré d'ici car il n'existe pas dans le modèle Organization
            'disciplines'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de la fédération')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description de la fédération')}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Pays')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://example.com')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('contact@federation.com')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone')}),
            'disciplines': forms.CheckboxSelectMultiple()  # Widget pour afficher les cases à cocher
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les disciplines actives
        self.fields['disciplines'].queryset = Discipline.objects.filter(is_active=True).order_by('name')
        self.fields['disciplines'].help_text = _("Sélectionnez les disciplines gérées par cette fédération")
        
        # Définir le type d'organisation comme 'national_federation' par défaut
        if 'initial' not in kwargs or 'organization_type' not in kwargs.get('initial', {}):
            self.initial['organization_type'] = 'national_federation'
        
        # Si l'instance existe, initialiser founding_date depuis les notes ou des métadonnées
        if self.instance and self.instance.pk:
            # Vous pouvez stocker founding_date dans les notes ou dans un champ JSON
            # Ceci est un exemple, à adapter selon votre implémentation
            if hasattr(self.instance, 'metadata') and self.instance.metadata:
                try:
                    import json
                    metadata = json.loads(self.instance.metadata)
                    if 'founding_date' in metadata:
                        self.fields['founding_date'].initial = metadata['founding_date']
                except (ValueError, TypeError):
                    pass
        
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
    
    def save(self, commit=True):
        """Surcharge save pour gérer le champ founding_date qui n'est pas dans le modèle."""
        organization = super().save(commit=False)
        
        # Gérer le champ founding_date (par exemple, le stocker dans notes ou un champ JSON)
        founding_date = self.cleaned_data.get('founding_date')
        if founding_date:
            # Option 1: Stocker dans les notes
            notes = getattr(organization, 'notes', '')
            if not notes:
                notes = ''
            if "Date de fondation:" not in notes:
                notes += f"\nDate de fondation: {founding_date.strftime('%Y-%m-%d')}"
            organization.notes = notes
            
            # Option 2: Si vous avez un champ metadata (JSONField)
            if hasattr(organization, 'metadata'):
                import json
                metadata = {}
                if organization.metadata:
                    try:
                        metadata = json.loads(organization.metadata)
                    except (ValueError, TypeError):
                        metadata = {}
                metadata['founding_date'] = founding_date.strftime('%Y-%m-%d')
                organization.metadata = json.dumps(metadata)
        
        if commit:
            organization.save()
        
        return organization


class OrganizationAffiliationForm(forms.Form):
    """Formulaire pour affilier une organisation à une organisation parente."""
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.none(),
        label=_("Organisation à affilier"),
        empty_label=_("Sélectionnez une organisation"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        parent_organization = kwargs.pop('parent_organization', None)
        organization_type = kwargs.pop('organization_type', 'club')  # Type d'organisation par défaut: club
        super().__init__(*args, **kwargs)
        
        if parent_organization:
            # Récupérer les organisations du type spécifié qui ne sont pas déjà affiliées
            self.fields['organization'].queryset = Organization.objects.filter(
                organization_type=organization_type,
                is_active=True
            ).exclude(
                id__in=Organization.objects.filter(
                    parent_affiliations__parent_organization=parent_organization
                ).values_list('id', flat=True)
            ).order_by('name')


# Pour la compatibilité avec le code existant, on garde aussi l'ancien nom de formulaire
ClubAffiliationForm = OrganizationAffiliationForm