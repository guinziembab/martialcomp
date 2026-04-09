# -*- coding: utf-8 -*-
"""
Formulaires pour la gestion des rôles des membres d'organisation.
"""
from django import forms
from django.utils.translation import gettext_lazy as _

from apps.organizations.models import OrganizationRole, OrganizationMember, MembershipStatus


class AssignRoleForm(forms.Form):
    """
    Formulaire pour attribuer un rôle à un pratiquant.
    """
    role = forms.ChoiceField(
        label=_("Rôle à attribuer"),
        choices=[
            ('', _("Sélectionner un rôle...")),
            (OrganizationRole.MANAGER, _("Gestionnaire - Gestion membres et compétitions")),
            (OrganizationRole.COACH, _("Entraîneur - Gestion cours et pratiquants")),
            (OrganizationRole.JUDGE, _("Juge/Arbitre - Arbitrage compétitions")),
            (OrganizationRole.MEMBER, _("Membre - Accès basique au club")),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'role-select'
        })
    )

    title = forms.CharField(
        label=_("Titre/Fonction"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Ex: Coach principal, Juge régional...")
        })
    )

    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Informations supplémentaires sur ce rôle...")
        })
    )

    # Champs spécifiques au rôle Juge
    is_technical_judge = forms.BooleanField(
        label=_("Juge technique"),
        required=False,
        help_text=_("Peut noter les performances techniques")
    )

    is_combat_referee = forms.BooleanField(
        label=_("Arbitre de combat"),
        required=False,
        help_text=_("Peut arbitrer les combats")
    )

    qualification_level = forms.ChoiceField(
        label=_("Niveau de qualification"),
        choices=[
            ('novice', _("Novice")),
            ('regional', _("Régional")),
            ('national', _("National")),
            ('international', _("International")),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    years_experience = forms.IntegerField(
        label=_("Années d'expérience"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0'
        })
    )

    certification_number = forms.CharField(
        label=_("Numéro de certification"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Numéro de licence ou certification")
        })
    )

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if not role:
            raise forms.ValidationError(_("Veuillez sélectionner un rôle."))
        return role


class ValidateRoleForm(forms.Form):
    """
    Formulaire pour valider ou rejeter une demande de rôle.
    """
    action = forms.ChoiceField(
        choices=[
            ('approve', _("Approuver")),
            ('reject', _("Rejeter")),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    rejection_reason = forms.CharField(
        label=_("Motif de refus"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Expliquez le motif du refus (optionnel)...")
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')

        # Si rejet, le motif est recommandé mais pas obligatoire
        if action == 'reject' and not rejection_reason:
            # Juste un warning, pas une erreur
            pass

        return cleaned_data


class BulkRoleValidationForm(forms.Form):
    """
    Formulaire pour valider plusieurs demandes de rôle en masse.
    """
    membership_ids = forms.CharField(
        widget=forms.HiddenInput()
    )

    action = forms.ChoiceField(
        choices=[
            ('approve', _("Approuver tout")),
            ('reject', _("Rejeter tout")),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    rejection_reason = forms.CharField(
        label=_("Motif de refus (pour tous)"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2
        })
    )

    def clean_membership_ids(self):
        ids_str = self.cleaned_data.get('membership_ids', '')
        if not ids_str:
            raise forms.ValidationError(_("Aucun membre sélectionné."))

        try:
            ids = [int(id.strip()) for id in ids_str.split(',') if id.strip()]
            if not ids:
                raise forms.ValidationError(_("Aucun membre sélectionné."))
            return ids
        except ValueError:
            raise forms.ValidationError(_("Format d'identifiants invalide."))
