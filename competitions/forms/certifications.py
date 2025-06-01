from django import forms
from django.utils.translation import gettext_lazy as _
from ..models.certifications import JudgeCertification, CertificationRegistration

class JudgeCertificationForm(forms.ModelForm):
    """Formulaire pour créer ou modifier une certification de juge."""
    
    class Meta:
        model = JudgeCertification
        fields = [
            'title', 
            'code',
            'discipline', 
            'level', 
            'description', 
            'requirements',
            'validity_period',
            'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Titre de la certification')}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Code de référence (facultatif)')}),
            'discipline': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description détaillée')}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Prérequis nécessaires')}),
            'validity_period': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec personnalisation des champs."""
        super().__init__(*args, **kwargs)
        
        # Ajouter des descriptions supplémentaires
        self.fields['validity_period'].help_text = _("Durée de validité en mois (par exemple 36 pour 3 ans)")
        self.fields['code'].help_text = _("Code unique pour identifier rapidement cette certification")
        
        # Rendre certains champs obligatoires
        self.fields['discipline'].required = True


class CertificationRegistrationForm(forms.ModelForm):
    """Formulaire pour s'inscrire à une certification."""
    
    class Meta:
        model = CertificationRegistration
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Informations complémentaires')}),
        }


class ReviewCertificationRegistrationForm(forms.ModelForm):
    """Formulaire pour l'examen d'une demande de certification."""
    
    DECISION_CHOICES = [
        ('approve', _('Approuver')),
        ('reject', _('Rejeter')),
    ]
    
    decision = forms.ChoiceField(
        label=_("Décision"),
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = CertificationRegistration
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Commentaires sur la décision')}),
        }