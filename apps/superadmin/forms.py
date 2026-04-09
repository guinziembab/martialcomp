# -*- coding: utf-8 -*-
"""
Formulaires de l'application Super Admin.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal
import json

from apps.superadmin.models import MembershipProfile, EventPass


class MembershipProfileForm(forms.ModelForm):
    """
    Formulaire pour les profils d'adhésion.
    """

    # Champs de fonctionnalités (affichés comme checkboxes)
    feature_competition_creation = forms.BooleanField(
        required=False,
        label=_('Création de compétitions')
    )
    feature_advanced_scoring = forms.BooleanField(
        required=False,
        label=_('Scoring avancé')
    )
    feature_real_time_combat = forms.BooleanField(
        required=False,
        label=_('Combat temps réel')
    )
    feature_mobile_app = forms.BooleanField(
        required=False,
        label=_('Application mobile')
    )
    feature_basic_registration = forms.BooleanField(
        required=False,
        label=_('Inscription de base')
    )
    feature_results_display = forms.BooleanField(
        required=False,
        label=_('Affichage résultats')
    )
    feature_export_data = forms.BooleanField(
        required=False,
        label=_('Export de données')
    )
    feature_custom_categories = forms.BooleanField(
        required=False,
        label=_('Catégories personnalisées')
    )
    feature_ai_recommendations = forms.BooleanField(
        required=False,
        label=_('Recommandations IA')
    )
    feature_white_label = forms.BooleanField(
        required=False,
        label=_('Marque blanche')
    )
    feature_api_access = forms.BooleanField(
        required=False,
        label=_('Accès API')
    )
    feature_priority_support = forms.BooleanField(
        required=False,
        label=_('Support prioritaire')
    )

    class Meta:
        model = MembershipProfile
        fields = [
            'name', 'slug', 'description', 'profile_type',
            'validity_type', 'validity_duration', 'is_global',
            'pricing_model', 'price', 'currency',
            'max_participants', 'requires_approval', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom du profil')
            }),
            'slug': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('identifiant-unique')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description du profil')
            }),
            'profile_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'validity_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'validity_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Durée en jours')
            }),
            'pricing_model': forms.Select(attrs={
                'class': 'form-select'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'currency': forms.Select(attrs={
                'class': 'form-select'
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': _('0 = illimité')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialiser les champs de fonctionnalités depuis feature_overrides
        if self.instance.pk and self.instance.feature_overrides:
            features = self.instance.feature_overrides
            self.fields['feature_competition_creation'].initial = features.get('competition_creation', False)
            self.fields['feature_advanced_scoring'].initial = features.get('advanced_scoring', False)
            self.fields['feature_real_time_combat'].initial = features.get('real_time_combat', False)
            self.fields['feature_mobile_app'].initial = features.get('mobile_app', False)
            self.fields['feature_basic_registration'].initial = features.get('basic_registration', False)
            self.fields['feature_results_display'].initial = features.get('results_display', False)
            self.fields['feature_export_data'].initial = features.get('export_data', False)
            self.fields['feature_custom_categories'].initial = features.get('custom_categories', False)
            self.fields['feature_ai_recommendations'].initial = features.get('ai_recommendations', False)
            self.fields['feature_white_label'].initial = features.get('white_label', False)
            self.fields['feature_api_access'].initial = features.get('api_access', False)
            self.fields['feature_priority_support'].initial = features.get('priority_support', False)

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        # Vérifier l'unicité
        qs = MembershipProfile.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_('Ce slug est déjà utilisé.'))
        return slug

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < Decimal('0'):
            raise forms.ValidationError(_('Le prix ne peut pas être négatif.'))
        return price

    def clean(self):
        cleaned_data = super().clean()

        # Valider que validity_duration est défini si validity_type == 'duration'
        validity_type = cleaned_data.get('validity_type')
        validity_duration = cleaned_data.get('validity_duration')

        if validity_type == 'duration' and not validity_duration:
            self.add_error('validity_duration', _('La durée est obligatoire pour ce type de validité.'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Construire feature_overrides depuis les checkboxes
        instance.feature_overrides = {
            'competition_creation': self.cleaned_data.get('feature_competition_creation', False),
            'advanced_scoring': self.cleaned_data.get('feature_advanced_scoring', False),
            'real_time_combat': self.cleaned_data.get('feature_real_time_combat', False),
            'mobile_app': self.cleaned_data.get('feature_mobile_app', False),
            'basic_registration': self.cleaned_data.get('feature_basic_registration', False),
            'results_display': self.cleaned_data.get('feature_results_display', False),
            'export_data': self.cleaned_data.get('feature_export_data', False),
            'custom_categories': self.cleaned_data.get('feature_custom_categories', False),
            'ai_recommendations': self.cleaned_data.get('feature_ai_recommendations', False),
            'white_label': self.cleaned_data.get('feature_white_label', False),
            'api_access': self.cleaned_data.get('feature_api_access', False),
            'priority_support': self.cleaned_data.get('feature_priority_support', False),
        }

        if commit:
            instance.save()

        return instance


class EventPassForm(forms.ModelForm):
    """
    Formulaire pour les passes événement.
    """

    class Meta:
        model = EventPass
        fields = [
            'user', 'membership_profile', 'competition', 'organization',
            'status', 'payment_status',
        ]
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'membership_profile': forms.Select(attrs={'class': 'form-select'}),
            'competition': forms.Select(attrs={'class': 'form-select'}),
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'payment_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les profils de type 'event' uniquement
        self.fields['membership_profile'].queryset = MembershipProfile.objects.filter(
            profile_type='event',
            is_active=True
        )
