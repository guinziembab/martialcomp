from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from ..models import Club, Discipline
from organizations.models import Organization

class ClubForm(forms.ModelForm):
    """Formulaire pour la création et modification des clubs."""
    
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG, SVG. Taille max: 2 Mo")
    )
    
    # Validation supplémentaire pour la bannière
    banner = forms.ImageField(
        label=_("Bannière"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG. Taille max: 3 Mo")
    )
    
    class Meta:
        model = Club
        fields = [
            # Informations de base
            'name', 'description', 'address', 'city', 'postal_code',
            # Contacts
            'contact_email', 'contact_phone', 'website',
            # Médias
            'logo', 'banner',
            # Relations
            'disciplines', 'main_discipline', 'organization',  # Remplacé 'federation' par 'organization'
            # Équipements
            'has_equipment', 'has_changing_rooms', 'has_showers', 'has_parking',
            # Tranches d'âge
            'accepts_children', 'accepts_teenagers', 'accepts_adults', 'accepts_seniors',
            # Autres informations
            'training_hours', 'is_active'
        ]
        widgets = {
            # Informations de base
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du club')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description du club')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')}),
            
            # Contacts
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('contact@club.com')}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://example.com')}),
            
            # Relations
            'disciplines': forms.CheckboxSelectMultiple(),
            'main_discipline': forms.Select(attrs={'class': 'form-control'}),
            'organization': forms.Select(attrs={'class': 'form-control'}),  # Remplacé 'federation' par 'organization'
            
            # Équipements
            'has_equipment': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_changing_rooms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_showers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'has_parking': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Tranches d'âge
            'accepts_children': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accepts_teenagers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accepts_adults': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'accepts_seniors': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
            # Autres informations
            'training_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Ex: Lundi 18h-20h, Mercredi 19h-21h...')}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les disciplines actives
        self.fields['disciplines'].queryset = Discipline.objects.filter(is_active=True).order_by('name')
        self.fields['disciplines'].help_text = _("Sélectionnez les disciplines pratiquées dans ce club")
        
        # Configurer le champ main_discipline
        self.fields['main_discipline'].queryset = Discipline.objects.filter(is_active=True).order_by('name')
        self.fields['main_discipline'].help_text = _("Discipline principale du club")
        self.fields['main_discipline'].empty_label = _("Aucune discipline principale")
        
        # Ajouter des descriptions/help_text pour les autres champs
        self.fields['organization'].empty_label = _("Aucune organisation")  # Changé le message pour refléter 'organization'
        
        # Grouper visuellement les checkboxes
        self.fields['has_equipment'].help_text = _("Le club dispose d'équipements d'entraînement")
        self.fields['has_changing_rooms'].help_text = _("Le club dispose de vestiaires")
        self.fields['has_showers'].help_text = _("Le club dispose de douches")
        self.fields['has_parking'].help_text = _("Le club dispose d'un parking")
        
        self.fields['is_active'].help_text = _("Décochez pour désactiver temporairement ce club")
    
    def clean_logo(self):
        """Validation supplémentaire pour le logo."""
        logo = self.cleaned_data.get('logo')
        if logo:
            if logo.size > 2 * 1024 * 1024:  # 2 MB en octets
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 2 Mo."))
        return logo
    
    def clean_banner(self):
        """Validation supplémentaire pour la bannière."""
        banner = self.cleaned_data.get('banner')
        if banner:
            if banner.size > 3 * 1024 * 1024:  # 3 MB en octets
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 3 Mo."))
        return banner
    
    def clean_website(self):
        """Ajoute http:// si le site web n'a pas de préfixe de protocole."""
        website = self.cleaned_data.get('website')
        if website and not (website.startswith('http://') or website.startswith('https://')):
            website = 'https://' + website
        return website
    

class ClubDisciplineForm(forms.ModelForm):
    """Formulaire pour gérer les disciplines d'un club."""
    
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.filter(is_active=True).order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Disciplines pratiquées")
    )
    
    main_discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label=_("Sélectionnez une discipline principale"),
        label=_("Discipline principale")
    )
    
    class Meta:
        model = Club
        fields = ['disciplines', 'main_discipline']
        
    def clean(self):
        cleaned_data = super().clean()
        disciplines = cleaned_data.get('disciplines')
        main_discipline = cleaned_data.get('main_discipline')
        
        # S'assurer que la discipline principale est dans les disciplines sélectionnées
        if main_discipline and disciplines and main_discipline not in disciplines:
            self.add_error('main_discipline', _("La discipline principale doit faire partie des disciplines sélectionnées."))
        
        return cleaned_data