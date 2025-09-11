"""
Formulaires pour l'administration des tenants.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.multitenant.models import Tenant, Domain, TenantFeature
import re


class TenantForm(forms.ModelForm):
    """Formulaire de création/modification de tenant."""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'slug', 'continent', 'subscription_plan',
            'timezone', 'currency', 'is_active', 'country'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du club'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'identifiant-unique'
            }),
            'continent': forms.Select(attrs={'class': 'form-control'}),
            'subscription_plan': forms.Select(attrs={'class': 'form-control'}),
            'timezone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Europe/Paris'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EUR'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_slug(self):
        """Valide le slug (identifiant unique)."""
        slug = self.cleaned_data.get('slug')
        
        if not slug:
            raise ValidationError("L'identifiant est requis.")
        
        # Valider le format
        if not re.match(r'^[a-z0-9-]+$', slug):
            raise ValidationError(
                "L'identifiant ne peut contenir que des lettres minuscules, "
                "des chiffres et des tirets."
            )
        
        # Vérifier l'unicité
        existing = Tenant.objects.filter(slug=slug)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("Cet identifiant est déjÃ  utilisé.")
        
        return slug
    
    def save(self, commit=True):
        """Sauvegarde le tenant avec création automatique du domaine principal."""
        tenant = super().save(commit=False)
        
        # Générer le schema_name si nouveau
        if not tenant.schema_name:
            tenant.schema_name = tenant.slug.replace('-', '_')
        
        # Générer le domaine complet
        tenant.domain = f"{tenant.slug}.martialcomp.com"
        
        if commit:
            tenant.save()
            
            # Créer le domaine principal si nouveau tenant
            if not tenant.domains.filter(is_primary=True).exists():
                Domain.objects.create(
                    tenant=tenant,
                    domain=tenant.domain,
                    is_primary=True
                )
        
        return tenant


class DomainForm(forms.ModelForm):
    """Formulaire pour ajouter un domaine personnalisé."""
    
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary']
        widgets = {
            'domain': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'exemple.com'
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.instance.tenant = self.tenant
    
    def clean_domain(self):
        """Valide le domaine."""
        domain = self.cleaned_data.get('domain')
        
        if not domain:
            raise ValidationError("Le domaine est requis.")
        
        # Retirer le protocole s'il est présent
        domain = domain.replace('http://', '').replace('https://', '')
        
        # Valider le format basique
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
            raise ValidationError("Format de domaine invalide.")
        
        # Vérifier l'unicité
        existing = Domain.objects.filter(domain=domain)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("Ce domaine est déjÃ  configuré.")
        
        return domain.lower()
    
    def clean_is_primary(self):
        """Valide qu'il n'y a qu'un seul domaine principal."""
        is_primary = self.cleaned_data.get('is_primary')
        
        if is_primary and self.tenant:
            existing_primary = self.tenant.domains.filter(is_primary=True)
            if self.instance.pk:
                existing_primary = existing_primary.exclude(pk=self.instance.pk)
            
            if existing_primary.exists():
                raise ValidationError(
                    "Un domaine principal existe déjÃ . "
                    "Désactivez-le d'abord avant d'en définir un nouveau."
                )
        
        return is_primary


class TenantFeatureForm(forms.ModelForm):
    """Formulaire pour gérer les features d'un tenant."""
    
    feature_code = forms.ChoiceField(
        label=_("Code de la fonctionnalité"),
        choices=[
            ('basic_management', _('Gestion de base')),
            ('grades', _('Système de grades')),
            ('local_competitions', _('Compétitions locales')),
            ('all_competitions', _('Toutes compétitions')),
            ('technical_scoring', _('Notation technique')),
            ('reporting', _('Rapports avancés')),
            ('api_access', _('Accès API')),
            ('white_label', _('White label')),
            ('advanced_analytics', _('Analytics avancés')),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = TenantFeature
        fields = ['feature_code', 'is_enabled', 'metadata']
        widgets = {
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'metadata': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': '{"key": "value"}'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        if self.tenant:
            self.instance.tenant = self.tenant
    
    def clean_metadata(self):
        """Valide que les métadonnées sont un JSON valide."""
        metadata = self.cleaned_data.get('metadata')
        
        if metadata:
            import json
            try:
                json.loads(metadata)
            except json.JSONDecodeError:
                raise ValidationError("Les métadonnées doivent Ãªtre un JSON valide.")
        
        return metadata


class TenantSearchForm(forms.Form):
    """Formulaire de recherche de tenants."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, domaine...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Tous'),
            ('active', 'Actifs'),
            ('inactive', 'Inactifs'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    plan = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous')] + Tenant.SUBSCRIPTION_PLAN_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    continent = forms.ChoiceField(
        required=False,
        choices=[('', 'Tous')] + Tenant.CONTINENT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class TenantOnboardingForm(forms.ModelForm):
    """Formulaire d'onboarding pour la création d'un nouveau tenant."""
    
    email = forms.EmailField(
        label=_("Email du responsable"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@monclub.com'
        })
    )
    
    password = forms.CharField(
        label=_("Mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢'
        })
    )
    
    password_confirm = forms.CharField(
        label=_("Confirmer le mot de passe"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢'
        })
    )
    
    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'continent', 'country', 'timezone', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom de votre organisation')
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('identifiant-unique')
            }),
            'continent': forms.Select(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'FR'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Europe/Paris'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EUR'
            }),
        }
    
    def clean_password_confirm(self):
        """Valide que les mots de passe correspondent."""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError(_("Les mots de passe ne correspondent pas."))
        
        return password_confirm
    
    def save(self, commit=True):
        """Sauvegarde le tenant et crée l'utilisateur admin."""
        tenant = super().save(commit=False)
        
        # Configurer les valeurs par défaut
        tenant.subscription_plan = 'trial'
        tenant.is_trial = True
        
        # Générer le schema_name si nouveau
        if not tenant.schema_name:
            tenant.schema_name = tenant.slug.replace('-', '_')
        
        # Générer le domaine complet
        tenant.domain = f"{tenant.slug}.martialcomp.com"
        
        if commit:
            tenant.save()
            
            # Créer le domaine principal
            Domain.objects.create(
                tenant=tenant,
                domain=tenant.domain,
                is_primary=True
            )
            
            # TODO: Créer l'utilisateur admin pour ce tenant
            # Cela nécessite une intégration avec le système d'authentification
        
        return tenant


class TenantSettingsForm(forms.ModelForm):
    """Formulaire pour les paramètres d'un tenant."""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'timezone', 'currency',
            'max_users', 'max_disciplines'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'timezone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'max_users': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'max_disciplines': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
        }


class TenantBillingForm(forms.ModelForm):
    """Formulaire pour la facturation d'un tenant."""
    
    billing_name = forms.CharField(
        label=_("Nom de facturation"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Nom de votre organisation')
        })
    )
    
    billing_address = forms.CharField(
        label=_("Adresse de facturation"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Adresse complète')
        })
    )
    
    billing_city = forms.CharField(
        label=_("Ville"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ville')
        })
    )
    
    billing_postal_code = forms.CharField(
        label=_("Code postal"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Code postal')
        })
    )
    
    billing_vat = forms.CharField(
        label=_("Numéro de TVA"),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('FR12345678901')
        })
    )
    
    class Meta:
        model = Tenant
        fields = ['subscription_plan', 'payment_provider']
        widgets = {
            'subscription_plan': forms.Select(attrs={
                'class': 'form-control'
            }),
            'payment_provider': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter les informations de facturation depuis payment_config si disponible
        if self.instance and self.instance.payment_config:
            billing_info = self.instance.payment_config.get('billing_info', {})
            self.fields['billing_name'].initial = billing_info.get('name', self.instance.name)
            self.fields['billing_address'].initial = billing_info.get('address', '')
            self.fields['billing_city'].initial = billing_info.get('city', '')
            self.fields['billing_postal_code'].initial = billing_info.get('postal_code', '')
            self.fields['billing_vat'].initial = billing_info.get('vat_number', '')
    
    def save(self, commit=True):
        """Sauvegarde les informations de facturation dans payment_config."""
        tenant = super().save(commit=False)
        
        # Sauvegarder les informations de facturation
        if not tenant.payment_config:
            tenant.payment_config = {}
        
        tenant.payment_config['billing_info'] = {
            'name': self.cleaned_data.get('billing_name'),
            'address': self.cleaned_data.get('billing_address'),
            'city': self.cleaned_data.get('billing_city'),
            'postal_code': self.cleaned_data.get('billing_postal_code'),
            'vat_number': self.cleaned_data.get('billing_vat', ''),
        }
        
        if commit:
            tenant.save()
        
        return tenant

