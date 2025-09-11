from django import forms
from django.utils.translation import gettext_lazy as _
from apps.competitions.models import Club, Discipline

class ClubAffiliationForm(forms.ModelForm):
    """Formulaire pour créer ou affilier un club Ã  une fédération."""
    
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Disciplines pratiquées")
    )
    
    class Meta:
        model = Club
        fields = [
            'name', 'address', 'city', 'postal_code', 'contact_phone', 
            'contact_email', 'website', 'description', 'logo', 'disciplines',
            'main_discipline', 'has_equipment', 'has_changing_rooms',
            'has_showers', 'has_parking', 'accepts_children', 'accepts_teenagers',
            'accepts_adults', 'accepts_seniors', 'training_hours'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du club')}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse')}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ville')}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code postal')}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Téléphone')}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Email')}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': _('https://...')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'main_discipline': forms.Select(attrs={'class': 'form-select'}),
            'training_hours': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Lundi: 18h-20h, Mardi: ...')}),
        }

