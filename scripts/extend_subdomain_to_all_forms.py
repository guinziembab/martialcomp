#!/usr/bin/env python3
"""
Script pour étendre la génération de sous-domaines à tous les formulaires d'organisation
"""

# Mixin réutilisable pour tous les formulaires d'organisation
SUBDOMAIN_MIXIN_CODE = '''
from django import forms
from django.utils.translation import gettext_lazy as _
from competitions.utils.subdomain_generator import SubdomainGenerator

class SubdomainMixin:
    """Mixin pour ajouter la fonctionnalité de sous-domaine à tous les formulaires d'organisation."""
    
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
        generator = SubdomainGenerator()
        if subdomain in generator.RESERVED_SUBDOMAINS:
            raise forms.ValidationError(_("Ce sous-domaine est réservé. Veuillez en choisir un autre."))
        
        # Vérifier l'unicité
        if generator._subdomain_exists(subdomain):
            raise forms.ValidationError(_("Ce sous-domaine est déjà utilisé. Veuillez en choisir un autre."))
        
        return subdomain
    
    def clean_subdomain_fields(self):
        """Validation globale des champs de sous-domaine."""
        cleaned_data = super().clean() if hasattr(super(), 'clean') else self.cleaned_data
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
                organization.save()  # Sauvegarder à nouveau avec l'URL du sous-domaine
        
        return organization
    
    def _create_subdomain_for_organization(self, organization, custom_subdomain=None):
        """Crée un sous-domaine pour l'organisation."""
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
            protocol = 'https'  # Utiliser HTTPS par défaut en production
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
'''

# Exemple d'utilisation pour le formulaire de club
CLUB_FORM_EXAMPLE = '''
# competitions/forms/club.py

from .mixins import SubdomainMixin

class ClubForm(SubdomainMixin, forms.ModelForm):
    """Formulaire pour la création et modification des clubs avec sous-domaines."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter les champs de sous-domaine
        self.add_subdomain_fields()
        
        # Modifier le placeholder pour les clubs
        self.fields['custom_subdomain'].widget.attrs['placeholder'] = _('mon-club')
        self.fields['custom_subdomain'].help_text = _("Optionnel. Sera utilisé comme: mon-club.martialcomp.com")
    
    def clean(self):
        """Validation globale incluant les sous-domaines."""
        cleaned_data = super().clean()
        return self.clean_subdomain_fields()
    
    def save(self, commit=True):
        """Sauvegarde avec gestion du sous-domaine."""
        club = super().save(commit=False)
        
        # Logique spécifique au club
        # ...
        
        # Sauvegarder avec sous-domaine
        return self.save_with_subdomain(club, commit)
'''

# Exemple pour les événements
EVENT_FORM_EXAMPLE = '''
# competitions/forms/event.py

from .mixins import SubdomainMixin

class EventForm(SubdomainMixin, forms.ModelForm):
    """Formulaire pour la création d'événements avec sous-domaines."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter les champs de sous-domaine
        self.add_subdomain_fields()
        
        # Modifier pour les événements
        self.fields['custom_subdomain'].widget.attrs['placeholder'] = _('mon-evenement')
        self.fields['custom_subdomain'].help_text = _("Optionnel. Sera utilisé comme: mon-evenement.martialcomp.com")
        
        # Pour les événements, on pourrait vouloir un site temporaire
        self.fields['website_type'].help_text = _("Les événements peuvent avoir un site temporaire dédié")
    
    def clean(self):
        """Validation globale incluant les sous-domaines."""
        cleaned_data = super().clean()
        return self.clean_subdomain_fields()
    
    def save(self, commit=True):
        """Sauvegarde avec gestion du sous-domaine."""
        event = super().save(commit=False)
        
        # Logique spécifique à l'événement
        # ...
        
        return self.save_with_subdomain(event, commit)
'''

print("🚀 Extension de la génération de sous-domaines à tous les profils")
print("=" * 60)

print("\n📁 1. Créer le fichier mixins:")
print("   competitions/forms/mixins.py")
print("\n📝 Contenu du mixin:")
print(SUBDOMAIN_MIXIN_CODE)

print("\n📁 2. Exemple d'utilisation pour les clubs:")
print(CLUB_FORM_EXAMPLE)

print("\n📁 3. Exemple d'utilisation pour les événements:")
print(EVENT_FORM_EXAMPLE)

print("\n🎯 Avantages de cette approche:")
print("   ✅ Code réutilisable pour tous les types d'organisation")
print("   ✅ Validation cohérente des sous-domaines")
print("   ✅ Interface utilisateur unifiée")
print("   ✅ Gestion d'erreurs centralisée")
print("   ✅ Facilite la maintenance et les mises à jour")

print("\n📋 Types d'organisation supportés:")
print("   • Fédérations (federation)")
print("   • Clubs (club)")
print("   • Coachs (coach)")
print("   • Événements (event)")
print("   • Organisations génériques (organization)")

print("\n🔧 Prochaines étapes:")
print("   1. Créer competitions/forms/mixins.py avec SubdomainMixin")
print("   2. Modifier ClubForm pour hériter de SubdomainMixin")
print("   3. Modifier EventForm pour hériter de SubdomainMixin")
print("   4. Ajouter le JavaScript aux templates correspondants")
print("   5. Tester la génération de sous-domaines pour chaque type")