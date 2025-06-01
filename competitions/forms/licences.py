# competitions/forms/licences.py
from django import forms
from django.utils.translation import gettext_lazy as _
from competitions.models import License

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = [
            'practitioner', 'license_number', 'issue_date', 'expiry_date',
            'status', 'is_competition_valid', 'license_type', 'notes'
        ]
        widgets = {
            'practitioner': forms.Select(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_competition_valid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'license_type': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if issue_date and expiry_date and expiry_date <= issue_date:
            raise forms.ValidationError(_("La date d'expiration doit être postérieure à la date d'émission."))
        
        return cleaned_data