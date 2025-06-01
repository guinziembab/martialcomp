from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Organization, Affiliation, OrganizationMember

User = get_user_model()

class OrganizationForm(forms.ModelForm):
    """Formulaire pour la création et la modification d'une organisation."""
    
    # Validation supplémentaire pour le logo
    logo = forms.ImageField(
        label=_("Logo"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'svg'])
        ],
        help_text=_("Formats acceptés: JPG, JPEG, PNG, SVG. Taille max: 2 Mo")
    )
    
    class Meta:
        model = Organization
        fields = [
            'name', 'short_name', 'organization_type', 'disciplines',
            'description', 'email', 'phone', 'website',
            'country', 'address', 'city', 'postal_code', 'logo', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de l\'organisation')}),
            'short_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Acronyme ou nom court')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description de l\'organisation')}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('Adresse')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://example.com')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('contact@organisation.com')}),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation du formulaire avec des options supplémentaires."""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Appliquer des classes CSS pour le style
        for field_name, field in self.fields.items():
            if field_name not in ['is_active', 'disciplines']:
                if not isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                    field.widget.attrs.update({'class': 'form-control'})
            
            if field_name == 'disciplines':
                field.widget.attrs.update({'class': 'form-select', 'multiple': 'multiple'})
            
        # Définir des placeholders selon le type d'organisation
        self.fields['organization_type'].widget.attrs.update({'class': 'form-select'})
    
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
        """Sauvegarde le formulaire en définissant l'utilisateur créateur si nouveau."""
        instance = super().save(commit=False)
        
        # Si c'est une nouvelle organisation, définir l'utilisateur créateur
        if not instance.pk and self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
            self.save_m2m()  # Pour sauvegarder les relations ManyToMany
            
            # Si c'est une nouvelle organisation, ajouter l'utilisateur comme propriétaire
            if not self.instance.pk and self.user and not instance.members.filter(user=self.user).exists():
                OrganizationMember.objects.create(
                    user=self.user,
                    organization=instance,
                    role='owner',
                    can_manage_members=True,
                    can_edit_organization=True,
                    can_manage_competitions=True
                )
        
        return instance

class AffiliationForm(forms.ModelForm):
    """Formulaire pour la création et la modification d'une affiliation."""
    
    class Meta:
        model = Affiliation
        fields = [
            'parent_organization', 'child_organization', 'affiliation_type',
            'start_date', 'end_date', 'certification_number', 'notes', 'is_active'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'certification_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec filtrage optionnel des organisations."""
        # Si une organisation parent est fournie, limiter les choix pour l'enfant
        parent_org = kwargs.pop('parent_org', None)
        child_org = kwargs.pop('child_org', None)
        
        super().__init__(*args, **kwargs)
        
        # Appliquer des classes CSS pour le style
        self.fields['parent_organization'].widget.attrs.update({'class': 'form-select'})
        self.fields['child_organization'].widget.attrs.update({'class': 'form-select'})
        self.fields['affiliation_type'].widget.attrs.update({'class': 'form-select'})
        
        # Définir la date de début par défaut à aujourd'hui
        if not self.instance.pk:
            self.fields['start_date'].initial = timezone.now().date()
        
        if parent_org:
            self.fields['parent_organization'].initial = parent_org
            self.fields['parent_organization'].widget.attrs['readonly'] = True
            
            # Exclure cette organisation et ses parents pour éviter les cycles
            excluded_orgs = [parent_org.id]
            
            # Exclure aussi toutes les organisations parentes pour éviter les cycles
            # Vérifier si la méthode existe avant de l'appeler
            if hasattr(parent_org, 'get_parent_organizations'):
                for org in parent_org.get_parent_organizations(include_inactive=True):
                    excluded_orgs.append(org.id)
            
            self.fields['child_organization'].queryset = Organization.objects.exclude(
                id__in=excluded_orgs
            ).filter(is_active=True).order_by('name')
        
        if child_org:
            self.fields['child_organization'].initial = child_org
            self.fields['child_organization'].widget.attrs['readonly'] = True
            
            # Exclure cette organisation et ses enfants pour éviter les cycles
            excluded_orgs = [child_org.id]
            
            # Exclure aussi toutes les organisations affiliées pour éviter les cycles
            # Vérifier si la méthode existe avant de l'appeler
            if hasattr(child_org, 'get_affiliated_organizations'):
                for org in child_org.get_affiliated_organizations(include_inactive=True):
                    excluded_orgs.append(org.id)
            
            self.fields['parent_organization'].queryset = Organization.objects.exclude(
                id__in=excluded_orgs
            ).filter(is_active=True).order_by('name')
    
    def clean(self):
        """Validation supplémentaire pour l'affiliation."""
        cleaned_data = super().clean()
        parent_org = cleaned_data.get('parent_organization')
        child_org = cleaned_data.get('child_organization')
        
        if parent_org and child_org:
            # Vérifier que ce ne sont pas la même organisation
            if parent_org == child_org:
                raise forms.ValidationError(_("Une organisation ne peut pas s'affilier à elle-même."))
            
            # Vérifier qu'il n'existe pas déjà une affiliation inverse
            if Affiliation.objects.filter(
                parent_organization=child_org,
                child_organization=parent_org
            ).exclude(pk=self.instance.pk if self.instance.pk else None).exists():
                raise forms.ValidationError(
                    _("Une affiliation inverse existe déjà. {0} est déjà affiliée à {1}.").format(
                        parent_org.name, child_org.name
                    )
                )
        
        return cleaned_data

class OrganizationMemberForm(forms.ModelForm):
    """Formulaire pour la gestion des membres d'une organisation."""
    
    # Définir join_date comme un champ de formulaire explicite si nécessaire
    join_date = forms.DateField(
        label=_("Date d'adhésion"), 
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = OrganizationMember
        fields = [
            'user', 'organization', 'role', 'title',
            # Ne pas inclure join_date ici s'il n'est pas dans le modèle
            'end_date', 'notes',
            'can_manage_members', 'can_edit_organization', 'can_manage_competitions',
            'is_active'
        ]
        widgets = {
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec filtrage pour une organisation spécifique."""
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Appliquer des classes CSS pour le style
        self.fields['user'].widget.attrs.update({'class': 'form-select'})
        self.fields['organization'].widget.attrs.update({'class': 'form-select'})
        self.fields['role'].widget.attrs.update({'class': 'form-select'})
        
        # Définir la date d'adhésion par défaut à aujourd'hui
        self.fields['join_date'].initial = timezone.now().date()
        
        if organization:
            self.fields['organization'].initial = organization
            self.fields['organization'].widget.attrs['readonly'] = True
            self.fields['organization'].queryset = Organization.objects.filter(id=organization.id)
            
            # Filtrer les utilisateurs qui ne sont pas déjà membres de cette organisation
            existing_users = OrganizationMember.objects.filter(
                organization=organization,
                is_active=True
            ).values_list('user_id', flat=True)
            
            if self.instance.pk:
                # Si on édite un membre existant, inclure son utilisateur
                self.fields['user'].queryset = User.objects.exclude(
                    id__in=existing_users
                ).exclude(id=self.instance.user.id).order_by('last_name', 'first_name')
            else:
                # Pour un nouveau membre, exclure tous les utilisateurs déjà membres
                self.fields['user'].queryset = User.objects.exclude(
                    id__in=existing_users
                ).order_by('last_name', 'first_name')
    
    def clean(self):
        """Validation supplémentaire pour le membre."""
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        organization = cleaned_data.get('organization')
        role = cleaned_data.get('role')
        
        if user and organization and not self.instance.pk:
            # Vérifier que l'utilisateur n'est pas déjà membre
            if OrganizationMember.objects.filter(user=user, organization=organization).exists():
                raise forms.ValidationError(
                    _("Cet utilisateur est déjà membre de cette organisation.")
                )
        
        # Si c'est le propriétaire, vérifier qu'il n'y a pas déjà un propriétaire
        if role == 'owner' and not self.instance.pk:
            if OrganizationMember.objects.filter(
                organization=organization,
                role='owner',
                is_active=True
            ).exists():
                raise forms.ValidationError(
                    _("Cette organisation a déjà un propriétaire. Il ne peut y avoir qu'un seul propriétaire par organisation.")
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Sauvegarde avec gestion du champ join_date."""
        instance = super().save(commit=False)
        
        # Gérer le champ join_date manuellement puisqu'il n'est pas dans Meta.fields
        join_date = self.cleaned_data.get('join_date')
        if hasattr(instance, 'join_date') and join_date:
            instance.join_date = join_date
        
        if commit:
            instance.save()
        
        return instance

class OrganizationSearchForm(forms.Form):
    """Formulaire de recherche d'organisations."""
    
    q = forms.CharField(
        label=_("Recherche"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Nom, description...'),
        })
    )
    
    type = forms.ChoiceField(
        label=_("Type d'organisation"),
        required=False,
        choices=[('', '--------')] + list(Organization._meta.get_field('organization_type').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    country = forms.ChoiceField(
        label=_("Pays"),
        required=False,
        choices=[('', '--------')],  # Sera rempli dynamiquement
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        countries = kwargs.pop('countries', [])
        super().__init__(*args, **kwargs)
        
        # Définir dynamiquement les pays disponibles
        country_choices = [('', '--------')]
        for country in countries:
            if country:  # Éviter les pays vides
                country_choices.append((country, country))
        
        self.fields['country'].choices = country_choices

class AffiliationSearchForm(forms.Form):
    """Formulaire de recherche d'affiliations."""
    
    q = forms.CharField(
        label=_("Recherche"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Nom d\'organisation...'),
        })
    )
    
    type = forms.ChoiceField(
        label=_("Type d'affiliation"),
        required=False,
        choices=[('', '--------')] + list(Affiliation._meta.get_field('affiliation_type').choices),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.ChoiceField(
        label=_("Statut"),
        required=False,
        choices=[
            ('', '--------'),
            ('true', _('Actives')),
            ('false', _('Inactives')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )