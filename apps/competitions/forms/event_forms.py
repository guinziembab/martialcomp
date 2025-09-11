# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models

from apps.competitions.models.event import Event, EventParticipant
from apps.organizations.models import Organization


class EventForm(forms.ModelForm):
    """
    Formulaire pour créer ou modifier un événement.
    """
    # Champs simplifiés pour la date et l'heure
    start_date = forms.DateField(
        label=_("Date de début"),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    end_date = forms.DateField(
        label=_("Date de fin"),
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    start_time = forms.TimeField(
        label=_("Heure de début"),
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    end_time = forms.TimeField(
        label=_("Heure de fin"),
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    # Champ pour la date limite d'inscription
    registration_deadline_date = forms.DateField(
        label=_("Date limite d'inscription"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    registration_deadline_time = forms.TimeField(
        label=_("Heure limite d'inscription"),
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'organization',
            'start_date', 'end_date', 'start_time', 'end_time', 'all_day',
            'location', 'address', 'city', 'postal_code',
            'visibility', 'is_public', 'max_participants', 'registration_required',
            'price', 'contact_person', 'contact_email', 'contact_phone',
            'image', 'color'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'organization': forms.HiddenInput(),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Préremplir les champs date/heure si on a une instance
        if self.instance and self.instance.pk and self.instance.registration_deadline:
            self.fields['registration_deadline_date'].initial = self.instance.registration_deadline.date()
            self.fields['registration_deadline_time'].initial = self.instance.registration_deadline.time()
        
        # Ajouter la classe CSS pour les champs select
        for field_name in ['event_type', 'visibility', 'contact_person']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': 'form-select'})
        
        # Rendre certains champs conditionnels
        self.fields['max_participants'].widget.attrs.update({
            'min': '1',
            'data-depends-on': 'registration_required'
        })
        
        # Si l'utilisateur est lié Ã  des organisations, filtrer les organisations disponibles
        if self.user and not self.user.is_superuser:
            # Récupérer les organisations dont l'utilisateur est admin ou membre
            user_orgs = Organization.objects.filter(
                members__user=self.user,
                members__is_active=True
            ).distinct()
            self.fields['organization'].queryset = user_orgs
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des dates
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _("La date de fin doit Ãªtre égale ou postérieure Ã  la date de début."))
        
        # Validation des heures
        all_day = cleaned_data.get('all_day')
        if not all_day:
            start_time = cleaned_data.get('start_time')
            end_time = cleaned_data.get('end_time')
            
            if start_time and end_time and start_date == end_date and start_time >= end_time:
                self.add_error('end_time', _("L'heure de fin doit Ãªtre postérieure Ã  l'heure de début pour un événement le mÃªme jour."))
        
        # Gérer la date limite d'inscription
        registration_required = cleaned_data.get('registration_required')
        registration_deadline_date = cleaned_data.get('registration_deadline_date')
        registration_deadline_time = cleaned_data.get('registration_deadline_time')
        
        if registration_required and registration_deadline_date:
            # Si l'heure n'est pas fournie, utiliser 23:59:59
            if not registration_deadline_time:
                registration_deadline_time = timezone.datetime.max.time().replace(microsecond=0)
            
            # Combiner date et heure
            registration_deadline = timezone.datetime.combine(
                registration_deadline_date, 
                registration_deadline_time
            )
            registration_deadline = timezone.make_aware(registration_deadline)
            
            # Vérifier que la date limite est avant la date de début
            if start_date:
                event_start = timezone.datetime.combine(
                    start_date,
                    cleaned_data.get('start_time') or timezone.datetime.min.time()
                )
                event_start = timezone.make_aware(event_start)
                
                if registration_deadline >= event_start:
                    self.add_error('registration_deadline_date', 
                        _("La date limite d'inscription doit Ãªtre antérieure Ã  la date de début de l'événement."))
            
            cleaned_data['registration_deadline'] = registration_deadline
        else:
            cleaned_data['registration_deadline'] = None
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir le créateur si on crée un nouvel événement
        if self.user and not instance.pk:
            instance.created_by = self.user
        
        # Mettre Ã  jour l'all_day
        if instance.all_day:
            instance.start_time = None
            instance.end_time = None
        
        # Mettre Ã  jour la date limite d'inscription
        instance.registration_deadline = self.cleaned_data.get('registration_deadline')
        
        if commit:
            instance.save()
        
        return instance


class EventParticipantForm(forms.ModelForm):
    """
    Formulaire pour s'inscrire Ã  un événement.
    """
    notes = forms.CharField(
        label=_("Notes ou commentaires"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': _("Informations supplémentaires, exigences alimentaires, etc.")})
    )
    
    class Meta:
        model = EventParticipant
        fields = ['notes']
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Ajouter des champs dynamiques selon les besoins de l'événement
        if self.event and self.event.price > 0:
            self.fields['accept_payment_terms'] = forms.BooleanField(
                label=_("J'accepte de payer les frais de {price} pour cet événement").format(
                    price=f"{self.event.price} â‚¬"
                ),
                required=True
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier si l'événement est complet
        if self.event and self.event.is_full and not self.instance.pk:
            raise forms.ValidationError(_("Désolé, cet événement est complet."))
        
        # Vérifier si la date limite d'inscription est dépassée
        if self.event and self.event.registration_deadline and \
           self.event.registration_deadline < timezone.now():
            raise forms.ValidationError(_("Désolé, la date limite d'inscription est dépassée."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir l'événement et l'utilisateur
        if self.event:
            instance.event = self.event
        if self.user:
            instance.user = self.user
        
        # Déterminer le statut (liste d'attente ou inscrit)
        if self.event and self.event.is_full and not self.instance.pk:
            instance.status = 'waitlist'
        
        if commit:
            instance.save()
        
        return instance


class EventFilterForm(forms.Form):
    """
    Formulaire pour filtrer les événements.
    """
    type = forms.ChoiceField(
        label=_("Type d'événement"),
        choices=[('', _('Tous'))] + Event.TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    start_date = forms.DateField(
        label=_("Ã€ partir de"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    end_date = forms.DateField(
        label=_("Jusqu'Ã "),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label=_("Organisation"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        label=_("Recherche"),
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _("Rechercher..."),
            'class': 'form-control'
        })
    )
    
    include_past = forms.BooleanField(
        label=_("Inclure les événements passés"),
        required=False,
        initial=False
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les organisations si l'utilisateur n'est pas admin
        if self.user and not self.user.is_superuser:
            orgs = Organization.objects.filter(
                members__user=self.user,
                members__is_active=True
            ).distinct()
            self.fields['organization'].queryset = orgs

