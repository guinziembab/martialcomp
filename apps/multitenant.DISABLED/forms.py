"""
Forms for multi-tenant functionality
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Tenant


class TenantOnboardingForm(forms.ModelForm):
    """Form for creating a new tenant during onboarding"""
    
    # Owner information
    owner_email = forms.EmailField(
        label=_("Email de l'administrateur"),
        help_text=_("Cette adresse sera utilisée pour la connexion")
    )
    owner_first_name = forms.CharField(
        label=_("Prénom"),
        max_length=30
    )
    owner_last_name = forms.CharField(
        label=_("Nom"),
        max_length=30
    )
    owner_password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput,
        help_text=_("Minimum 8 caractères")
    )
    owner_password_confirm = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput
    )
    
    # Additional fields
    subdomain = forms.SlugField(
        label=_("Sous-domaine"),
        help_text=_("Votre URL sera : [sous-domaine].martialcomp.com"),
        max_length=50
    )
    
    accept_terms = forms.BooleanField(
        label=_("J'accepte les conditions d'utilisation"),
        required=True
    )
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'continent', 'country', 'language',
            'subscription_plan', 'currency', 'timezone'
        ]
        labels = {
            'name': _("Nom de votre organisation"),
            'continent': _("Continent"),
            'country': _("Pays"),
            'language': _("Langue préférée"),
            'subscription_plan': _("Plan d'abonnement"),
            'currency': _("Devise"),
            'timezone': _("Fuseau horaire"),
        }
        help_texts = {
            'name': _("Le nom complet de votre club ou fédération"),
            'subscription_plan': _("Vous pouvez commencer avec un essai gratuit"),
        }
        widgets = {
            'continent': forms.Select(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'subscription_plan': forms.RadioSelect(),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'timezone': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set initial plan to trial
        self.fields['subscription_plan'].initial = 'essentials'
        
        # Add CSS classes
        for field_name, field in self.fields.items():
            if not hasattr(field.widget, 'attrs'):
                field.widget.attrs = {}
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control'
    
    def clean_subdomain(self):
        """Validate subdomain uniqueness"""
        subdomain = self.cleaned_data['subdomain'].lower()
        
        # Check if subdomain is already taken
        if Tenant.objects.filter(slug=subdomain).exists():
            raise forms.ValidationError(
                _("Ce sous-domaine est déjÃ  utilisé. Veuillez en choisir un autre.")
            )
        
        # Check reserved subdomains
        reserved = ['www', 'api', 'admin', 'mail', 'ftp', 'blog', 'app', 'dashboard']
        if subdomain in reserved:
            raise forms.ValidationError(
                _("Ce sous-domaine est réservé. Veuillez en choisir un autre.")
            )
        
        return subdomain
    
    def clean_owner_email(self):
        """Validate owner email uniqueness"""
        email = self.cleaned_data['owner_email'].lower()
        
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("Un compte existe déjÃ  avec cette adresse email.")
            )
        
        return email
    
    def clean(self):
        """Validate password confirmation"""
        cleaned_data = super().clean()
        password = cleaned_data.get('owner_password')
        password_confirm = cleaned_data.get('owner_password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError(
                    _("Les mots de passe ne correspondent pas.")
                )
            
            if len(password) < 8:
                raise forms.ValidationError(
                    _("Le mot de passe doit contenir au moins 8 caractères.")
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        """Create tenant and owner user"""
        tenant = super().save(commit=False)
        
        # Set additional fields
        tenant.slug = self.cleaned_data['subdomain']
        tenant.schema_name = f"tenant_{tenant.slug.replace('-', '_')}"
        tenant.domain = f"{tenant.slug}.martialcomp.com"
        tenant.is_active = True
        tenant.is_trial = True
        
        if commit:
            # Create owner user
            owner = User.objects.create_user(
                username=self.cleaned_data['owner_email'],
                email=self.cleaned_data['owner_email'],
                password=self.cleaned_data['owner_password'],
                first_name=self.cleaned_data['owner_first_name'],
                last_name=self.cleaned_data['owner_last_name']
            )
            
            tenant.owner = owner
            tenant.save()
            
            # Create primary domain
            from .models import Domain
            Domain.objects.create(
                tenant=tenant,
                domain=tenant.domain,
                is_primary=True
            )
        
        return tenant


class TenantSettingsForm(forms.ModelForm):
    """Form for updating tenant settings"""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'country', 'language', 'currency', 
            'timezone', 'logo', 'primary_color', 'secondary_color'
        ]
        labels = {
            'name': _("Nom de l'organisation"),
            'country': _("Pays"),
            'language': _("Langue préférée"),
            'currency': _("Devise"),
            'timezone': _("Fuseau horaire"),
            'logo': _("Logo"),
            'primary_color': _("Couleur principale"),
            'secondary_color': _("Couleur secondaire"),
        }
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color'}),
        }


class TenantBillingForm(forms.Form):
    """Form for updating billing information"""
    
    billing_name = forms.CharField(
        label=_("Nom de facturation"),
        max_length=255
    )
    billing_address = forms.CharField(
        label=_("Adresse"),
        widget=forms.Textarea(attrs={'rows': 3})
    )
    billing_city = forms.CharField(
        label=_("Ville"),
        max_length=100
    )
    billing_postal_code = forms.CharField(
        label=_("Code postal"),
        max_length=20
    )
    billing_country = forms.CharField(
        label=_("Pays"),
        max_length=100
    )
    billing_tax_id = forms.CharField(
        label=_("Numéro de TVA"),
        max_length=50,
        required=False
    )
