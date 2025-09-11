from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.competitions.models.judge_training import JudgeTraining
from apps.competitions.models.discipline import Discipline
from apps.competitions.models.training import (
    TrainingProgram, TrainingModule, TrainingExercise, 
    TrainingSlot, TrainingSession, ProgramEnrollment
)

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
        
        # Filtrer les instructeurs selon leur rÃ´le
        try:
            self.fields['instructor'].queryset = User.objects.filter(
                profile__role__in=['federation_admin', 'judge']
            ).order_by('last_name', 'first_name')
        except:
            # Fallback si le profil n'existe pas
            from apps.competitions.models import Judge
            judge_user_ids = Judge.objects.values_list('user_id', flat=True)
            self.fields['instructor'].queryset = User.objects.filter(
                id__in=judge_user_ids
            ).order_by('last_name', 'first_name')
        
        # Gérer la fédération
        if federation:
            self.initial['federation'] = federation
            # Filtrer les disciplines selon la fédération
            self.fields['disciplines'].queryset = Discipline.objects.filter(
                organization=federation
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
            self.add_error('end_date', _("La date de fin doit Ãªtre postérieure Ã  la date de début"))
        
        # Vérifier que la date limite d'inscription est avant la date de début
        if start_date and registration_deadline and registration_deadline > start_date:
            self.add_error('registration_deadline', _("La date limite d'inscription doit Ãªtre antérieure Ã  la date de début"))
        
        return cleaned_data


class TrainingProgramForm(forms.ModelForm):
    """Formulaire pour créer ou modifier un programme d'entraînement."""
    
    class Meta:
        model = TrainingProgram
        fields = [
            'name', 'description', 'disciplines', 'level',
            'duration_weeks', 'sessions_per_week',
            'objectives', 'prerequisites', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _("Ex: Programme débutant Karaté")
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': _("Description détaillée du programme...")
            }),
            'disciplines': forms.SelectMultiple(attrs={
                'class': 'form-select', 
                'size': 4
            }),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'duration_weeks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 52,
                'placeholder': _("Ex: 12")
            }),
            'sessions_per_week': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 7,
                'placeholder': _("Ex: 3")
            }),
            'objectives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _("Objectifs du programme...")
            }),
            'prerequisites': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _("Prérequis (optionnel)...")
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, **kwargs):
        club = kwargs.pop('club', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les disciplines disponibles pour le club si fourni
        if club and hasattr(club, 'organization') and club.organization:
            # Récupérer les disciplines associées au club via l'organisation
            self.fields['disciplines'].queryset = club.organization.disciplines.all()
        elif club:
            # Fallback pour les clubs legacy
            try:
                self.fields['disciplines'].queryset = club.disciplines.all()
            except:
                self.fields['disciplines'].queryset = Discipline.objects.all()
        
        # Rendre certains champs optionnels
        self.fields['prerequisites'].required = False


class TrainingSlotForm(forms.ModelForm):
    """Formulaire pour créer ou modifier un créneau d'entraînement."""
    
    class Meta:
        model = TrainingSlot
        fields = [
            'name', 'description', 'discipline', 'day_of_week',
            'start_time', 'end_time', 'level', 'instructor',
            'location', 'max_participants', 'is_active',
            'start_date', 'end_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Ex: Karaté débutants")
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'discipline': forms.Select(attrs={'class': 'form-select'}),
            'day_of_week': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _("Ex: Dojo principal")
            }),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
    
    def __init__(self, *args, **kwargs):
        club = kwargs.pop('club', None)
        super().__init__(*args, **kwargs)
        
        if club:
            # Filtrer les instructeurs du club via l'organisation
            if hasattr(club, 'organization') and club.organization:
                self.fields['instructor'].queryset = User.objects.filter(
                    organization_memberships__organization=club.organization,
                    organization_memberships__is_active=True,
                    is_active=True
                ).distinct().order_by('last_name', 'first_name')
                
                # Filtrer les disciplines via l'organisation
                self.fields['discipline'].queryset = club.organization.disciplines.all()
            else:
                # Fallback pour clubs legacy ou sans organisation
                # Chercher les utilisateurs via les pratiquants du club
                from apps.competitions.models import Practitioner
                practitioner_user_ids = Practitioner.objects.filter(
                    organization=club if hasattr(club, 'practitioners') else None
                ).values_list('user_id', flat=True)
                
                self.fields['instructor'].queryset = User.objects.filter(
                    id__in=practitioner_user_ids,
                    is_active=True
                ).order_by('last_name', 'first_name')
                
                # Utiliser toutes les disciplines comme fallback
                self.fields['discipline'].queryset = Discipline.objects.all()
        
        # Rendre certains champs optionnels
        self.fields['description'].required = False
        self.fields['instructor'].required = False
        self.fields['end_date'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Vérifier les heures
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', _("L'heure de fin doit être après l'heure de début"))
        
        # Vérifier les dates
        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', _("La date de fin doit être après la date de début"))
        
        return cleaned_data

