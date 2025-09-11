"""
Mixins réutilisables pour les formulaires de MartialComp
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class SubdomainMixin:
    """Mixin pour ajouter la fonctionnalité de sous-domaine Ã  tous les formulaires d'organisation."""
    
    def add_subdomain_fields(self):
        """Ajoute les champs de sous-domaine au formulaire."""
        
        # Choix pour le type de site web
        self.fields['website_type'] = forms.ChoiceField(
            choices=[
                ('subdomain', _('Utiliser un sous-domaine MartialComp (recommandé)')),
                ('external', _('Site web externe personnalisé'))
            ],
            initial='subdomain',
            widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
            label=_("Type de site web"),
            help_text=_("Choisissez entre un sous-domaine automatique ou votre propre site web")
        )
        
        # Champ pour le sous-domaine personnalisé
        self.fields['custom_subdomain'] = forms.CharField(
            label=_("Sous-domaine personnalisé"),
            required=False,
            max_length=50,
            widget=forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('mon-organisation'),
                'pattern': '^[a-z0-9-]+$',
                'title': _('Lettres minuscules, chiffres et tirets uniquement')
            }),
            help_text=_("Optionnel. Laissez vide pour génération automatique. Sera utilisé comme: mon-organisation.martialcomp.com")
        )
        
        # Site web externe
        self.fields['external_website'] = forms.URLField(
            label=_("Site web externe"),
            required=False,
            widget=forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': _('https://votre-site.com')
            }),
            help_text=_("URL complète de votre site web externe")
        )
    
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
        from ..utils.subdomain_generator import SubdomainGenerator
        generator = SubdomainGenerator()
        if subdomain in generator.RESERVED_SUBDOMAINS:
            raise forms.ValidationError(_("Ce sous-domaine est réservé. Veuillez en choisir un autre."))
        
        # Vérifier l'unicité
        if generator._subdomain_exists(subdomain):
            raise forms.ValidationError(_("Ce sous-domaine est déjÃ  utilisé. Veuillez en choisir un autre."))
        
        return subdomain
    
    def clean_subdomain_fields(self):
        """Validation globale des champs de sous-domaine."""
        cleaned_data = self.cleaned_data
        website_type = cleaned_data.get('website_type')
        external_website = cleaned_data.get('external_website')
        
        # Si le type est "external", le site web externe est requis
        if website_type == 'external' and not external_website:
            raise forms.ValidationError({
                'external_website': _("Veuillez saisir l'URL de votre site web externe.")
            })
        
        return cleaned_data
    
    def save_with_subdomain(self, organization, commit=True):
        """Sauvegarde l'organisation avec gestion du sous-domaine."""
        
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
                organization.save()  # Sauvegarder Ã  nouveau avec l'URL du sous-domaine
        
        return organization
    
    def _create_subdomain_for_organization(self, organization, custom_subdomain=None):
        """Crée un sous-domaine pour l'organisation."""
        from ..utils.subdomain_generator import SubdomainGenerator
        
        generator = SubdomainGenerator()
        
        # Utiliser le sous-domaine personnalisé ou en générer un automatique
        if custom_subdomain:
            subdomain = custom_subdomain
        else:
            subdomain = generator.generate_subdomain(organization)
        
        try:
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
