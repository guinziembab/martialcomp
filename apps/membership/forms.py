# -*- coding: utf-8 -*-
"""
Formulaires pour le système d'adhésion MartialComp v2.0
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from .models import MembershipPackage, MembershipSubscription
from apps.competitions.models import Discipline


class MembershipPackageForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un package d'adhésion
    """
    
    class Meta:
        model = MembershipPackage
        fields = [
            'name', 'description', 'package_type', 'category',
            'base_price', 'currency',
            'disciplines', 'max_sessions_per_week',
            'includes_competitions', 'includes_seminars', 'includes_equipment',
            'auto_renewal', 'grace_period_days',
            'min_age', 'max_age',
            'is_active', 'is_featured', 'sort_order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Package Étudiant Mensuel')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Description détaillée du package...')
            }),
            'package_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 3,
                'placeholder': 'EUR'
            }),
            'disciplines': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '5'
            }),
            'max_sessions_per_week': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': _('0 = illimité')
            }),
            'includes_competitions': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'includes_seminars': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'includes_equipment': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'auto_renewal': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'grace_period_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'min_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '120'
            }),
            'max_age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '120'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            })
        }
        labels = {
            'name': _('Nom du package'),
            'description': _('Description'),
            'package_type': _('Type de package'),
            'category': _('Catégorie'),
            'base_price': _('Prix de base'),
            'currency': _('Devise'),
            'disciplines': _('Disciplines incluses'),
            'max_sessions_per_week': _('Sessions max/semaine'),
            'includes_competitions': _('Inclut les compétitions'),
            'includes_seminars': _('Inclut les stages'),
            'includes_equipment': _('Inclut l\'équipement'),
            'auto_renewal': _('Renouvellement automatique'),
            'grace_period_days': _('Période de grâce (jours)'),
            'min_age': _('Âge minimum'),
            'max_age': _('Âge maximum'),
            'is_active': _('Actif'),
            'is_featured': _('Mis en avant'),
            'sort_order': _('Ordre d\'affichage')
        }
        help_texts = {
            'max_sessions_per_week': _('Laissez vide ou mettez 0 pour des sessions illimitées'),
            'currency': _('Code devise à 3 lettres (EUR, USD, etc.)'),
            'grace_period_days': _('Nombre de jours après expiration où le package reste accessible'),
            'sort_order': _('Plus petit = affiché en premier'),
            'is_featured': _('Ce package sera mis en avant visuellement'),
            'disciplines': _('Maintenez Ctrl (ou Cmd) pour sélectionner plusieurs disciplines')
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les disciplines par organisation si nécessaire
        if self.organization:
            # Si l'organisation a des disciplines spécifiques, les filtrer
            # Sinon, afficher toutes les disciplines
            self.fields['disciplines'].queryset = Discipline.objects.all()

    def clean_base_price(self):
        """Valider que le prix est positif"""
        price = self.cleaned_data.get('base_price')
        if price is not None and price < 0:
            raise forms.ValidationError(_('Le prix ne peut pas être négatif.'))
        return price

    def clean_currency(self):
        """Valider le format de la devise"""
        currency = self.cleaned_data.get('currency', '').upper()
        if len(currency) != 3:
            raise forms.ValidationError(_('La devise doit être un code à 3 lettres (ex: EUR, USD).'))
        return currency

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        min_age = cleaned_data.get('min_age')
        max_age = cleaned_data.get('max_age')
        
        # Vérifier que l'âge minimum n'est pas supérieur à l'âge maximum
        if min_age is not None and max_age is not None:
            if min_age > max_age:
                raise forms.ValidationError(
                    _('L\'âge minimum ne peut pas être supérieur à l\'âge maximum.')
                )
        
        return cleaned_data

    def save(self, commit=True):
        """Sauvegarder le package avec l'organisation"""
        package = super().save(commit=False)
        if self.organization:
            package.organization = self.organization
        
        if commit:
            package.save()
            # Sauvegarder les relations many-to-many
            self.save_m2m()
        
        return package


class MembershipSubscriptionForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une souscription d'adhésion
    """
    
    class Meta:
        model = MembershipSubscription
        fields = [
            'practitioner', 'package', 'start_date', 'end_date',
            'status', 'auto_renew', 'price_paid', 'currency', 'notes'
        ]
        widgets = {
            'practitioner': forms.Select(attrs={'class': 'form-control'}),
            'package': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'auto_renew': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'price_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 3
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        labels = {
            'practitioner': _('Pratiquant'),
            'package': _('Package'),
            'start_date': _('Date de début'),
            'end_date': _('Date de fin'),
            'status': _('Statut'),
            'auto_renew': _('Renouvellement automatique'),
            'price_paid': _('Prix payé'),
            'currency': _('Devise'),
            'notes': _('Notes')
        }

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les pratiquants et packages par organisation
        if self.organization:
            from apps.competitions.models import Practitioner
            self.fields['practitioner'].queryset = Practitioner.objects.filter(
                organization=self.organization
            )
            self.fields['package'].queryset = MembershipPackage.objects.filter(
                organization=self.organization,
                is_active=True
            )