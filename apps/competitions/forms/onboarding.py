from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from ..models import Club, Discipline, Federation, Practitioner
from ..choices import COUNTRY_CHOICES

# Import des formulaires coach
from .coach_forms import CoachProfileForm, DisciplineExpertiseFormSet

# Formulaire de sélection du rÃ´le
ROLE_CHOICES = [
    ('federation_admin', _('Administrateur de fédération')),
    ('club_manager', _('Responsable de club')),
    ('judge', _('Juge/Arbitre')),
    ('coach', _('Coach / Enseignant')),
    ('participant', _('Participant/Compétiteur')),
    ('spectator', _('Spectateur')),
    ('external_organizer', _('Organisateur non-membre')),
]

class RoleSelectionForm(forms.Form):
    """Formulaire pour la sélection du rÃ´le dans le processus d'onboarding."""
    role = forms.ChoiceField(
        label=_("Sélectionnez votre rÃ´le"),
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-radio'})
    )

class FederationCreationForm(forms.ModelForm):
    """Formulaire pour la création d'une fédération dans le processus d'onboarding."""
    
    # Champ pays avec sélecteur automatisé personnalisé
    country = forms.CharField(
        label=_("Pays"),
        required=True,
        widget=forms.HiddenInput(),
        help_text=_("Commencez Ã  taper pour rechercher votre pays")
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
            FileExtensionValidator(allowed_extensions=['jpeg', 'png', 'svg'])
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
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = Federation
        fields = ['name', 'country', 'description', 'logo', 'website', 'contact_email', 'contact_phone']
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
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 2 Mo."))
        return logo
    
    def clean_country(self):
        """Validation du champ pays."""
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError(_("Veuillez sélectionner un pays."))
        
        # Liste des pays valides (noms en français)
        valid_countries = [
            'Afghanistan', 'Afrique du Sud', 'Albanie', 'Algérie', 'Allemagne', 'Andorre', 'Angola',
            'Antigua-et-Barbuda', 'Arabie Saoudite', 'Argentine', 'Arménie', 'Australie', 'Autriche',
            'AzerbaÃ¯djan', 'Bahamas', 'BahreÃ¯n', 'Bangladesh', 'Barbade', 'Belgique', 'Belize', 'Bénin',
            'Bhoutan', 'Biélorussie', 'Bolivie', 'Bosnie-Herzégovine', 'Botswana', 'Brésil', 'Brunei',
            'Bulgarie', 'Burkina Faso', 'Burundi', 'Cambodge', 'Cameroun', 'Canada', 'Cap-Vert', 'Chili',
            'Chine', 'Chypre', 'Colombie', 'Comores', 'Congo', 'Congo (RDC)', 'Corée du Sud', 'Corée du Nord',
            'Costa Rica', 'CÃ´te d\'Ivoire', 'Croatie', 'Cuba', 'Danemark', 'Djibouti', 'Dominique', 'Ã‰gypte',
            'Ã‰mirats Arabes Unis', 'Ã‰quateur', 'Ã‰rythrée', 'Espagne', 'Estonie', 'Ã‰tats-Unis', 'Ã‰thiopie',
            'Fidji', 'Finlande', 'France', 'Gabon', 'Gambie', 'Géorgie', 'Ghana', 'Grèce', 'Grenade',
            'Guatemala', 'Guinée', 'Guinée-Bissau', 'Guinée équatoriale', 'Guyana', 'HaÃ¯ti', 'Honduras',
            'Hongrie', 'Inde', 'Indonésie', 'Irak', 'Iran', 'Irlande', 'Islande', 'IsraÃ«l', 'Italie',
            'JamaÃ¯que', 'Japon', 'Jordanie', 'Kazakhstan', 'Kenya', 'Kirghizistan', 'Kiribati', 'KoweÃ¯t',
            'Laos', 'Lesotho', 'Lettonie', 'Liban', 'Libéria', 'Libye', 'Liechtenstein', 'Lituanie',
            'Luxembourg', 'Macédoine du Nord', 'Madagascar', 'Malaisie', 'Malawi', 'Maldives', 'Mali', 'Malte',
            'Maroc', 'ÃŽles Marshall', 'Maurice', 'Mauritanie', 'Mexique', 'Micronésie', 'Moldavie', 'Monaco',
            'Mongolie', 'Monténégro', 'Mozambique', 'Myanmar', 'Namibie', 'Nauru', 'Népal', 'Nicaragua',
            'Niger', 'Nigéria', 'Niue', 'Norvège', 'Nouvelle-Zélande', 'Oman', 'Ouganda', 'Ouzbékistan',
            'Pakistan', 'Palaos', 'Panama', 'Papouasie-Nouvelle-Guinée', 'Paraguay', 'Pays-Bas', 'Pérou',
            'Philippines', 'Pologne', 'Portugal', 'Qatar', 'République Dominicaine', 'République Tchèque',
            'Roumanie', 'Royaume-Uni', 'Russie', 'Rwanda', 'Saint-Christophe-et-Niévès', 'Saint-Marin',
            'Saint-Vincent-et-les-Grenadines', 'Sainte-Lucie', 'ÃŽles Salomon', 'Samoa', 'Sao Tomé-et-Principe',
            'Sénégal', 'Serbie', 'Seychelles', 'Sierra Leone', 'Singapour', 'Slovaquie', 'Slovénie',
            'Somalie', 'Soudan', 'Soudan du Sud', 'Sri Lanka', 'Suède', 'Suisse', 'Suriname', 'Eswatini',
            'Syrie', 'Tadjikistan', 'Tanzanie', 'Tchad', 'ThaÃ¯lande', 'Timor oriental', 'Togo', 'Tonga',
            'Trinité-et-Tobago', 'Tunisie', 'Turkménistan', 'Turquie', 'Tuvalu', 'Ukraine', 'Uruguay',
            'Vanuatu', 'Vatican', 'Venezuela', 'Vietnam', 'Yémen', 'Zambie', 'Zimbabwe'
        ]
        
        # Vérifier que le nom du pays existe dans notre liste
        if country not in valid_countries:
            raise forms.ValidationError(_("Nom de pays invalide."))
        
        return country
    
    def clean_custom_subdomain(self):
        """Validation du sous-domaine personnalisé."""
        enable_custom = self.cleaned_data.get('enable_custom_subdomain')
        subdomain = self.cleaned_data.get('custom_subdomain')
        
        if enable_custom and not subdomain:
            raise forms.ValidationError(_("Veuillez saisir un sous-domaine personnalisé."))
        
        if subdomain:
            # Normaliser le sous-domaine
            subdomain = subdomain.lower().strip()
            
            # Validation des caractères
            import re
            if not re.match(r'^[a-z0-9-]+$', subdomain):
                raise forms.ValidationError(_("Le sous-domaine ne peut contenir que des lettres minuscules, des chiffres et des tirets."))
            
            # Validation de la longueur
            if len(subdomain) < 2:
                raise forms.ValidationError(_("Le sous-domaine doit contenir au moins 2 caractères."))
            
            if len(subdomain) > 50:
                raise forms.ValidationError(_("Le sous-domaine ne peut pas dépasser 50 caractères."))
            
            # Vérifier les préfixes/suffixes interdits
            if subdomain.startswith('-') or subdomain.endswith('-'):
                raise forms.ValidationError(_("Le sous-domaine ne peut pas commencer ou finir par un tiret."))
        
        return subdomain
    
    def clean_website(self):
        """Ajoute http:// si le site web n'a pas de préfixe de protocole."""
        website = self.cleaned_data.get('website')
        if website and not (website.startswith('http://') or website.startswith('https://')):
            website = 'https://' + website
        return website
    
    def save(self, commit=True):
        """Surcharge save pour gérer la génération de sous-domaines."""
        federation = super().save(commit=False)
        
        # Ajouter les champs personnalisés
        if hasattr(self, 'cleaned_data'):
            federation.address = self.cleaned_data.get('address', '')
            federation.city = self.cleaned_data.get('city', '')
            federation.postal_code = self.cleaned_data.get('postal_code', '')
            
            # Gérer la date de fondation
            founding_date = self.cleaned_data.get('founding_date')
            if founding_date:
                notes = getattr(federation, 'notes', '') or ''
                if "Date de fondation:" not in notes:
                    notes += f"\nDate de fondation: {founding_date.strftime('%Y-%m-%d')}"
                federation.notes = notes
        
        if commit:
            federation.save()
            
            # Générer le sous-domaine après la création
            self._create_subdomain_for_federation(federation)
            
        return federation
    
    def _create_subdomain_for_federation(self, federation):
        """Crée un sous-domaine pour la fédération."""
        try:
            from ...utils.subdomain_generator import SubdomainGenerator
            
            generator = SubdomainGenerator()
            
            # Déterminer le sous-domaine Ã  utiliser
            enable_custom = self.cleaned_data.get('enable_custom_subdomain', False)
            custom_subdomain = self.cleaned_data.get('custom_subdomain')
            
            if enable_custom and custom_subdomain:
                subdomain = custom_subdomain
            else:
                # Générer automatiquement depuis le nom
                subdomain = generator.generate_subdomain(federation)
            
            # Créer le tenant avec le sous-domaine
            tenant = generator.create_tenant_for_organization(federation, subdomain)
            
            # Construire l'URL complète du sous-domaine
            from django.conf import settings
            if getattr(settings, 'DEBUG', False):
                protocol = 'http'
            else:
                protocol = 'https'
            subdomain_url = f"{protocol}://{tenant.domain}"
            
            # Mettre Ã  jour l'URL du site web de la fédération
            federation.website = subdomain_url
            federation.save()
            
            return subdomain_url
            
        except Exception as e:
            # En cas d'erreur, loguer et continuer sans sous-domaine
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du sous-domaine pour {federation.name}: {str(e)}")
            
            # Fallback : laisser le site web tel quel
            return None

class ClubCreationForm(forms.ModelForm):
    """Formulaire pour la création d'un club dans le processus d'onboarding."""
    website = forms.URLField(required=False, label=_("Site web"))
    country = forms.ChoiceField(
        label=_("Pays"),
        choices=COUNTRY_CHOICES,
        required=True,
        initial='FR',
        widget=forms.Select(attrs={'class': 'form-control'})
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
        fields = [
            'name', 'address', 'city', 'postal_code', 'country',
            'logo', 'description', 'website', 'contact_email', 'contact_phone'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du club')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')}),
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
        if not website:  # Si le champ est vide, retourner une chaÃ®ne vide
            return ''
        
        # S'assurer que l'URL a un protocole
        if website and not (website.startswith('http://') or website.startswith('https://')):
            website = 'https://' + website
        return website

class ClubDetailsForm(forms.ModelForm):
    """Formulaire pour la mise Ã  jour des détails d'un club."""
    
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
        
        # Au moins un type de juge doit Ãªtre sélectionné
        is_technical_judge = cleaned_data.get('is_technical_judge')
        is_combat_referee = cleaned_data.get('is_combat_referee')
        
        if not is_technical_judge and not is_combat_referee:
            raise forms.ValidationError(
                _("Vous devez sélectionner au moins un type de rÃ´le : juge technique ou arbitre de combat.")
            )
        
        return cleaned_data

class ParticipantProfileForm(forms.ModelForm):
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
    
    birth_date = forms.DateField(
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
    
    photo = forms.ImageField(
        label=_("Photo de profil"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG. Taille max: 2 Mo")
    )
    
    # Certificat médical (fichier)
    medical_certificate = forms.FileField(
        label=_("Certificat médical"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])
        ],
        help_text=_("Formats acceptés: PDF, JPG, JPEG, PNG. Taille max: 5 Mo")
    )
    
    # Champs additionnels pour correspondre au template
    nationality = forms.CharField(
        label=_("Nationalité"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nationalité')})
    )
    
    # Champs pour la gestion des grades par discipline
    main_discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        label=_("Discipline principale"),
        required=False,
        empty_label=_("Sélectionnez une discipline"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    other_discipline = forms.CharField(
        label=_("Autre discipline"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Champs cachés pour la gestion des grades
    selected_grade_id = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    selected_grade_name = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
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
    
    def clean_photo(self):
        """Validation supplémentaire pour la photo."""
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 2 * 1024 * 1024:  # 2 MB en octets
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 2 Mo."))
        return photo
    
    def clean_medical_certificate(self):
        """Validation supplémentaire pour le certificat médical."""
        medical_certificate = self.cleaned_data.get('medical_certificate')
        if medical_certificate:
            if medical_certificate.size > 5 * 1024 * 1024:  # 5 MB en octets
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 5 Mo."))
        return medical_certificate
    
    class Meta:
        model = Practitioner
        fields = [
            'first_name', 'last_name', 'email', 'birth_date', 'gender',
            'organization', 'disciplines', 'grade_text', 'license_number',
            'weight', 'height', 'nationality', 'phone', 'address', 'city',
            'photo', 'medical_certificate', 'medical_certificate_date', 'notes'
        ]

