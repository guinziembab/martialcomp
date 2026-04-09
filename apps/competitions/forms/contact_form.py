from django import forms
from django.utils.translation import gettext_lazy as _

from apps.competitions.models.contact import ContactSubmission


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactSubmission
        fields = ['name', 'email', 'organization', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Votre nom complet'),
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('votre@email.com'),
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom de votre club, ecole ou federation (optionnel)'),
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': _('Votre message...'),
                'rows': 5,
            }),
        }
