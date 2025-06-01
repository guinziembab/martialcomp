from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

from competitions.models.judge_training import JudgeTraining
from competitions.models.discipline import Discipline

User = get_user_model()

class JudgeTrainingForm(forms.ModelForm):
    """Formulaire pour créer ou modifier une formation de juges."""
    
    class Meta:
        model = JudgeTraining
        fields = [
            'title', 'description', 'training_type', 'level', 
            'start_date', 'end_date', 'location', 'max_participants',
            'status', 'instructor', 'registration_deadline', 'disciplines',
            'duration_hours', 'federation'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: Formation juge technique niveau régional')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Description de la formation...')}),
            'training_type': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Adresse complète du lieu de formation')}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'registration_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'disciplines': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '4'}),
            'duration_hours': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': _('Durée en heures')}),
            'federation': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        federation = kwargs.pop('federation', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les instructeurs selon leur rôle
        try:
            self.fields['instructor'].queryset = User.objects.filter(
                profile__role__in=['federation_admin', 'judge']
            ).order_by('last_name', 'first_name')
        except:
            # Fallback si le profil n'existe pas
            from competitions.models import Judge
            judge_user_ids = Judge.objects.values_list('user_id', flat=True)
            self.fields['instructor'].queryset = User.objects.filter(
                id__in=judge_user_ids
            ).order_by('last_name', 'first_name')
        
        # Gérer la fédération
        if federation:
            self.initial['federation'] = federation
            # Filtrer les disciplines selon la fédération
            self.fields['disciplines'].queryset = Discipline.objects.filter(
                federations=federation
            ).order_by('name')
        
        # Rendre certains champs optionnels
        self.fields['instructor'].required = False
        self.fields['federation'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        registration_deadline = cleaned_data.get('registration_deadline')
        
        # Vérifier que la date de fin est après la date de début
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', _("La date de fin doit être postérieure à la date de début"))
        
        # Vérifier que la date limite d'inscription est avant la date de début
        if start_date and registration_deadline and registration_deadline > start_date:
            self.add_error('registration_deadline', _("La date limite d'inscription doit être antérieure à la date de début"))
        
        return cleaned_data