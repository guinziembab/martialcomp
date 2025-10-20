from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from apps.competitions.models.practitioners import Practitioner
from apps.competitions.models.notifications import NotificationPreference
from apps.competitions.models.support import SupportTicket


class PractitionerProfileForm(forms.ModelForm):
    """Formulaire de mise Ã  jour du profil pratiquant"""
    
    class Meta:
        model = Practitioner
        fields = [
            'first_name', 'last_name', 'gender', 'birth_date',
            'license_number', 'medical_certificate_date', 
            'nationality', 'phone', 'email',
            'address', 'city', 'postal_code',
            'emergency_contact_name', 'emergency_contact_phone'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'medical_certificate_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
        }


class NotificationPreferenceForm(forms.ModelForm):
    """Formulaire des préférences de notification"""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'competition_notifications',
            'order_notifications',
            'grade_notifications',
            'membership_notifications',
            'training_notifications',
            'message_notifications',
            'system_notifications',
            'email_enabled',
            'sms_enabled',
            'push_enabled',
            'notification_frequency'
        ]
        widgets = {
            'competition_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grade_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'membership_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'training_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'message_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'system_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'push_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_frequency': forms.Select(attrs={'class': 'form-select'})
        }


class SupportTicketForm(forms.ModelForm):
    """Formulaire de création de ticket de support"""
    
    class Meta:
        model = SupportTicket
        fields = ['category', 'subject', 'description', 'priority']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-select'})
        }


class PersonalGoalForm(forms.ModelForm):
    """Formulaire de création d'objectif personnel"""
    
    GOAL_TYPE_CHOICES = [
        ('competition', _('Compétition')),
        ('training', _('EntraÃ®nement')),
        ('grade', _('Grade')),
        ('skill', _('Compétence')),
        ('fitness', _('Forme physique')),
        ('other', _('Autre'))
    ]
    
    goal_type = forms.ChoiceField(
        choices=GOAL_TYPE_CHOICES,
        label=_("Type d'objectif"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    title = forms.CharField(
        label=_("Titre"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    description = forms.CharField(
        label=_("Description"),
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    
    target_date = forms.DateField(
        label=_("Date cible"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    target_value = forms.CharField(
        label=_("Valeur cible"),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )


class TrainingReservationForm(forms.Form):
    """Formulaire de réservation d'entraÃ®nement"""
    
    training_slot = forms.ChoiceField(
        label=_("Créneau d'entraÃ®nement"),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    additional_notes = forms.CharField(
        label=_("Notes additionnelles"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
    )
    
    def __init__(self, *args, practitioner=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if practitioner and hasattr(practitioner, 'club') and practitioner.club:
            # Filtrer les créneaux disponibles pour le club du pratiquant
            from apps.competitions.models.training import TrainingSlot
            slots = TrainingSlot.objects.filter(
                club=practitioner.club,
                is_active=True
            )
            self.fields['training_slot'].choices = [(slot.id, f"{slot.day_of_week} - {slot.start_time} - {slot.discipline}") for slot in slots]

