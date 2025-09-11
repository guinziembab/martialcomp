from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

from ..models import Discipline, Federation, Club
from ..choices import COUNTRY_CHOICES, get_valid_country_codes
from apps.organizations.models import Organization


class FederationForm(forms.ModelForm):
    """Formulaire pour la création et modification des fédérations."""
    
    # Champ pays avec sélecteur automatisé personnalisé
    country = forms.CharField(
        label=_("Pays"),
        required=True,
        widget=forms.HiddenInput(),
        help_text=_("Commencez à taper pour rechercher votre pays")
    )
    
    # Choix pour le type de site web
    website_type = forms.ChoiceField(
        choices=[
            ('subdomain', _('Utiliser un sous-domaine MartialComp (recommandé)')),
            ('external', _('Site web externe personnalisé'))
        ],
        initial='subdomain',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_("Type de site web"),
        help_text=_("Choisissez entre un sous-domaine automatique ou votre propre site web")
    )
    
    # Champ pour le sous-domaine personnalisé (optionnel)
    custom_subdomain = forms.CharField(
        label=_("Sous-domaine personnalisé"),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': _('mon-club'),
            'pattern': '^[a-z0-9-]+$',
            'title': _('Lettres minuscules, chiffres et tirets uniquement')
        }),
        help_text=_("Optionnel. Laissez vide pour génération automatique. Sera utilisé comme: mon-club.martialcomp.com")
    )
    
    # Site web externe (affiché conditionnellement)
    external_website = forms.URLField(
        label=_("Site web externe"),
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control', 
            'placeholder': _('https://votre-site.com')
        }),
        help_text=_("URL complète de votre site web externe")
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
    
    # Ajout du champ founding_date comme champ de formulaire normal (pas relié au modèle)
    founding_date = forms.DateField(
        label=_("Date de fondation"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    class Meta:
        model = Federation
        fields = [
            'name', 'description', 'country', 'address', 'city', 'postal_code',
            'logo', 'website', 'contact_email', 'contact_phone', 'founding_date',
            'disciplines'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de la fédération')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description de la fédération')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://example.com')}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('contact@federation.com')}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone')}),
            'founding_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
        
        # Définir la France comme pays par défaut si aucun pays n'est sélectionné
        if not self.instance.pk and not self.initial.get('country'):
            self.initial['country'] = 'FR'
        
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
    
    def clean_country(self):
        """Validation du champ pays."""
        country = self.cleaned_data.get('country')
        if not country:
            raise forms.ValidationError(_("Veuillez sélectionner un pays."))
        
        # Liste des pays valides (noms en français)
        valid_countries = [
            'Afghanistan', 'Afrique du Sud', 'Albanie', 'Algérie', 'Allemagne', 'Andorre', 'Angola',
            'Antigua-et-Barbuda', 'Arabie Saoudite', 'Argentine', 'Arménie', 'Australie', 'Autriche',
            'Azerbaïdjan', 'Bahamas', 'Bahreïn', 'Bangladesh', 'Barbade', 'Belgique', 'Belize', 'Bénin',
            'Bhoutan', 'Biélorussie', 'Bolivie', 'Bosnie-Herzégovine', 'Botswana', 'Brésil', 'Brunei',
            'Bulgarie', 'Burkina Faso', 'Burundi', 'Cambodge', 'Cameroun', 'Canada', 'Cap-Vert', 'Chili',
            'Chine', 'Chypre', 'Colombie', 'Comores', 'Congo', 'Congo (RDC)', 'Corée du Sud', 'Corée du Nord',
            'Costa Rica', 'Côte d\'Ivoire', 'Croatie', 'Cuba', 'Danemark', 'Djibouti', 'Dominique', 'Égypte',
            'Émirats Arabes Unis', 'Équateur', 'Érythrée', 'Espagne', 'Estonie', 'États-Unis', 'Éthiopie',
            'Fidji', 'Finlande', 'France', 'Gabon', 'Gambie', 'Géorgie', 'Ghana', 'Grèce', 'Grenade',
            'Guatemala', 'Guinée', 'Guinée-Bissau', 'Guinée équatoriale', 'Guyana', 'Haïti', 'Honduras',
            'Hongrie', 'Inde', 'Indonésie', 'Irak', 'Iran', 'Irlande', 'Islande', 'Israël', 'Italie',
            'Jamaïque', 'Japon', 'Jordanie', 'Kazakhstan', 'Kenya', 'Kirghizistan', 'Kiribati', 'Koweït',
            'Laos', 'Lesotho', 'Lettonie', 'Liban', 'Libéria', 'Libye', 'Liechtenstein', 'Lituanie',
            'Luxembourg', 'Macédoine du Nord', 'Madagascar', 'Malaisie', 'Malawi', 'Maldives', 'Mali', 'Malte',
            'Maroc', 'Îles Marshall', 'Maurice', 'Mauritanie', 'Mexique', 'Micronésie', 'Moldavie', 'Monaco',
            'Mongolie', 'Monténégro', 'Mozambique', 'Myanmar', 'Namibie', 'Nauru', 'Népal', 'Nicaragua',
            'Niger', 'Nigéria', 'Niue', 'Norvège', 'Nouvelle-Zélande', 'Oman', 'Ouganda', 'Ouzbékistan',
            'Pakistan', 'Palaos', 'Panama', 'Papouasie-Nouvelle-Guinée', 'Paraguay', 'Pays-Bas', 'Pérou',
            'Philippines', 'Pologne', 'Portugal', 'Qatar', 'République Dominicaine', 'République Tchèque',
            'Roumanie', 'Royaume-Uni', 'Russie', 'Rwanda', 'Saint-Christophe-et-Niévès', 'Saint-Marin',
            'Saint-Vincent-et-les-Grenadines', 'Sainte-Lucie', 'Îles Salomon', 'Samoa', 'Sao Tomé-et-Principe',
            'Sénégal', 'Serbie', 'Seychelles', 'Sierra Leone', 'Singapour', 'Slovaquie', 'Slovénie',
            'Somalie', 'Soudan', 'Soudan du Sud', 'Sri Lanka', 'Suède', 'Suisse', 'Suriname', 'Eswatini',
            'Syrie', 'Tadjikistan', 'Tanzanie', 'Tchad', 'Thaïlande', 'Timor oriental', 'Togo', 'Tonga',
            'Trinité-et-Tobago', 'Tunisie', 'Turkménistan', 'Turquie', 'Tuvalu', 'Ukraine', 'Uruguay',
            'Vanuatu', 'Vatican', 'Venezuela', 'Vietnam', 'Yémen', 'Zambie', 'Zimbabwe'
        ]
        
        # Vérifier que le nom du pays existe dans notre liste
        if country not in valid_countries:
            raise forms.ValidationError(_("Nom de pays invalide."))
        
        return country
    
    def clean_custom_subdomain(self):
        """Validation du sous-domaine personnalisé."""
        subdomain = self.cleaned_data.get('custom_subdomain')
        if not subdomain:
            return subdomain
        
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
        
        # Vérifier les domaines réservés
        try:
            from ..utils.subdomain_generator import SubdomainGenerator
            generator = SubdomainGenerator()
            if subdomain in generator.RESERVED_SUBDOMAINS:
                raise forms.ValidationError(_("Ce sous-domaine est réservé. Veuillez en choisir un autre."))
            
            # Vérifier l'unicité
            if generator._subdomain_exists(subdomain):
                raise forms.ValidationError(_("Ce sous-domaine est déjà utilisé. Veuillez en choisir un autre."))
        except ImportError:
            # Si le module subdomain_generator n'existe pas, on passe cette validation
            pass
        
        return subdomain
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        website_type = cleaned_data.get('website_type')
        external_website = cleaned_data.get('external_website')
        
        # Si le type est "external", le site web externe est requis
        if website_type == 'external' and not external_website:
            raise forms.ValidationError({
                'external_website': _("Veuillez saisir l'URL de votre site web externe.")
            })
        
        return cleaned_data
    
    def clean_website(self):
        """Ajoute http:// si le site web n'a pas de préfixe de protocole."""
        website = self.cleaned_data.get('website')
        if website and not (website.startswith('http://') or website.startswith('https://')):
            website = 'https://' + website
        return website
    
    def save(self, commit=True):
        """Surcharge save pour gérer les champs personnalisés et la génération de sous-domaines."""
        organization = super().save(commit=False)
        
        # Gérer le champ founding_date
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
        
        # Gérer le type de site web et les URLs
        website_type = self.cleaned_data.get('website_type', 'subdomain')
        custom_subdomain = self.cleaned_data.get('custom_subdomain')
        external_website = self.cleaned_data.get('external_website')
        
        if website_type == 'external' and external_website:
            # Utiliser le site web externe
            organization.website = external_website
        else:
            # Utiliser le sous-domaine MartialComp
            if commit:
                # Sauvegarder d'abord l'organisation pour avoir un ID
                organization.save()
                
                # Générer et créer le sous-domaine
                subdomain_url = self._create_subdomain_for_organization(organization, custom_subdomain)
                organization.website = subdomain_url
                organization.save()  # Sauvegarder à nouveau avec l'URL du sous-domaine
            else:
                # Si commit=False, on ne peut pas encore créer le sous-domaine
                # Il sera créé lors de la sauvegarde finale
                pass
        
        if commit and website_type == 'subdomain':
            # S'assurer que le sous-domaine est créé même si on a fait commit=True
            if not getattr(organization, '_subdomain_created', False):
                subdomain_url = self._create_subdomain_for_organization(organization, custom_subdomain)
                organization.website = subdomain_url
                organization.save()
        
        return organization
    
    def _create_subdomain_for_organization(self, organization, custom_subdomain=None):
        """Crée un sous-domaine pour l'organisation."""
        try:
            from ..utils.subdomain_generator import SubdomainGenerator
            
            generator = SubdomainGenerator()
            
            # Utiliser le sous-domaine personnalisé ou en générer un automatique
            if custom_subdomain:
                subdomain = custom_subdomain
            else:
                subdomain = generator.generate_subdomain(organization)
            
            # Créer le tenant avec le sous-domaine
            tenant = generator.create_tenant_for_organization(organization, subdomain)
            
            # Construire l'URL complète du sous-domaine
            from django.conf import settings
            if getattr(settings, 'DEBUG', False):
                protocol = 'http'
            else:
                protocol = 'https'
            subdomain_url = f"{protocol}://{tenant.domain}"
            
            # Marquer que le sous-domaine a été créé
            organization._subdomain_created = True
            
            return subdomain_url
            
        except Exception as e:
            # En cas d'erreur, loguer et utiliser l'URL principale
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création du sous-domaine pour {organization.name}: {str(e)}")
            
            # Fallback vers l'URL principale
            from django.conf import settings
            base_url = getattr(settings, 'BASE_URL', 'https://martialcomp.com')
            return f"{base_url}/organizations/{organization.id}/"


class ClubAffiliationForm(forms.Form):
    """Formulaire pour l'affiliation d'un club à une fédération."""
    
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.none(),
        label=_("Club à affilier"),
        empty_label=_("Sélectionnez un club"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        # Récupérer et supprimer les arguments personnalisés des kwargs
        parent_organization = kwargs.pop('parent_organization', None)
        organization_type = kwargs.pop('organization_type', 'club')
        
        # Appeler le __init__ parent après avoir retiré les arguments personnalisés
        super().__init__(*args, **kwargs)
        
        if parent_organization:
            # Récupérer les organisations du type spécifié qui ne sont pas déjà affiliées
            self.fields['organization'].queryset = Organization.objects.filter(
                organization_type=organization_type,
                is_active=True
            ).exclude(
                child_affiliations__parent_organization=parent_organization,
                child_affiliations__is_active=True
            ).order_by('name')
        else:
            # Si pas d'organisation parente, afficher toutes les organisations du type spécifié
            self.fields['organization'].queryset = Organization.objects.filter(
                organization_type=organization_type,
                is_active=True
            ).order_by('name')

    def save(self, parent_organization=None, commit=True):
        """Créer une affiliation entre l'organisation sélectionnée et l'organisation parente."""
        from apps.organizations.models import Affiliation
        
        organization = self.cleaned_data['organization']
        if parent_organization and organization:
            affiliation, created = Affiliation.objects.get_or_create(
                parent_organization=parent_organization,
                child_organization=organization,
                defaults={'is_active': True}
            )
            return affiliation
        return None


# Alias pour la compatibilité avec le code existant
OrganizationAffiliationForm = ClubAffiliationForm