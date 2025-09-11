from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from ..models.certifications import JudgeCertification, CertificationRegistration, Exam, ExamRegistration
from ..models import Discipline

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
    """Formulaire pour s'inscrire Ã  une certification."""
    
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


class ExamForm(forms.ModelForm):
    """Formulaire pour créer ou modifier un examen."""
    
    class Meta:
        model = Exam
        fields = [
            'title', 'description', 'exam_type', 'discipline',
            'start_date', 'end_date', 'start_time', 'end_time',
            'location', 'address', 'registration_start', 'registration_end',
            'max_participants', 'registration_fee', 'chief_examiner',
            'examiners', 'requirements', 'rules', 'materials_needed', 'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Titre de l\'examen')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Description de l\'examen')}),
            'exam_type': forms.Select(attrs={'class': 'form-select'}),
            'discipline': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Lieu de l\'examen')}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Adresse complète')}),
            'registration_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'registration_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'chief_examiner': forms.Select(attrs={'class': 'form-select'}),
            'examiners': forms.SelectMultiple(attrs={'class': 'form-select', 'multiple': True}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Prérequis pour participer')}),
            'rules': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Règlement de l\'examen')}),
            'materials_needed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Matériel à apporter')}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        federation = kwargs.pop('federation', None)
        super().__init__(*args, **kwargs)
        
        if federation:
            # Filtrer les disciplines de la fédération
            self.fields['discipline'].queryset = federation.disciplines.all()
            
            # Filtrer les utilisateurs potentiels pour les examinateurs
            # Pour simplifier, on prend tous les utilisateurs actifs
            # Dans une vraie application, on filtrerait par compétences/certifications
            self.fields['chief_examiner'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
            self.fields['examiners'].queryset = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Ajouter des textes d'aide
        self.fields['registration_fee'].help_text = _("Frais d'inscription en euros")
        self.fields['max_participants'].help_text = _("Nombre maximum de participants")
        self.fields['end_date'].help_text = _("Laisser vide si l'examen ne dure qu'une journée")
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_start = cleaned_data.get('registration_start')
        registration_end = cleaned_data.get('registration_end')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Vérifier les dates
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError(_("La date de fin doit être postérieure à la date de début."))
        
        if registration_start and registration_end and registration_end < registration_start:
            raise forms.ValidationError(_("La fin des inscriptions doit être postérieure au début."))
        
        if registration_end and start_date and registration_end > start_date:
            raise forms.ValidationError(_("Les inscriptions doivent se terminer avant le début de l'examen."))
        
        # Vérifier les heures
        if start_time and end_time and end_time <= start_time:
            raise forms.ValidationError(_("L'heure de fin doit être postérieure à l'heure de début."))
        
        return cleaned_data


class ExamRegistrationForm(forms.ModelForm):
    """Formulaire pour s'inscrire à un examen."""
    
    class Meta:
        model = ExamRegistration
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': _('Informations complémentaires ou motivation')
            }),
        }


class ExamResultsForm(forms.ModelForm):
    """Formulaire pour saisir les résultats d'un examen."""
    
    class Meta:
        model = ExamRegistration
        fields = ['score', 'grade_obtained', 'passed', 'examiner_feedback']
        widgets = {
            'score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '20'}),
            'grade_obtained': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Grade obtenu')}),
            'passed': forms.Select(choices=[(True, _('Réussi')), (False, _('Échoué'))], attrs={'class': 'form-select'}),
            'examiner_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Commentaires de l\'examinateur')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['score'].help_text = _("Note sur 20")
        self.fields['passed'].required = True
