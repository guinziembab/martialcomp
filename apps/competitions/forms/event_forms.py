# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models

from apps.competitions.models.event import (
    Event,
    EventParticipant,
    EventOccurrence,
    EventOccurrenceAttendance,
    EventFormat,
    RecurrenceFrequency,
    Weekday,
    OccurrenceStatus,
    AttendanceStatus,
)
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

    # =========================================================================
    # CHAMPS DE RÉCURRENCE
    # =========================================================================
    is_recurring = forms.BooleanField(
        label=_("Événement récurrent"),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'data-toggle': 'recurrence-options'
        })
    )

    recurrence_frequency = forms.ChoiceField(
        label=_("Fréquence"),
        choices=[('', _('Sélectionner...'))] + list(RecurrenceFrequency.choices),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-recurrence-field': 'true'
        })
    )

    recurrence_days = forms.CharField(
        label=_("Jours de la semaine"),
        required=False,
        widget=forms.HiddenInput(attrs={
            'data-recurrence-field': 'true'
        })
    )

    recurrence_end_type = forms.ChoiceField(
        label=_("Fin de récurrence"),
        choices=[
            ('never', _('Jamais')),
            ('after', _('Après N occurrences')),
            ('on_date', _('À une date précise')),
        ],
        required=False,
        initial='never',
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'data-recurrence-field': 'true'
        })
    )

    recurrence_end_after = forms.IntegerField(
        label=_("Nombre d'occurrences"),
        required=False,
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ex: 12'),
            'data-recurrence-field': 'true'
        })
    )

    recurrence_end_date = forms.DateField(
        label=_("Date de fin de récurrence"),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'data-recurrence-field': 'true'
        })
    )

    # Champs pour les options mensuelles avancées
    recurrence_day_of_month = forms.IntegerField(
        label=_("Jour du mois"),
        required=False,
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ex: 15'),
            'data-recurrence-field': 'true'
        })
    )

    recurrence_week_of_month = forms.IntegerField(
        label=_("Semaine du mois"),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-recurrence-field': 'true'
        }, choices=[
            ('', _('Sélectionner...')),
            (1, _('1er')),
            (2, _('2ème')),
            (3, _('3ème')),
            (4, _('4ème')),
            (-1, _('Dernier')),
        ])
    )

    recurrence_day_of_week = forms.ChoiceField(
        label=_("Jour de la semaine"),
        required=False,
        choices=[('', _('Sélectionner...'))] + list(Weekday.choices),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-recurrence-field': 'true'
        })
    )

    # =========================================================================
    # CHAMPS VISIO / EN LIGNE
    # =========================================================================
    event_format = forms.ChoiceField(
        label=_("Format de l'événement"),
        choices=EventFormat.choices,
        initial=EventFormat.IN_PERSON,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
            'data-toggle': 'online-options'
        })
    )

    online_url = forms.URLField(
        label=_("URL de la visioconférence"),
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': _('https://zoom.us/j/...'),
            'data-online-field': 'true'
        })
    )

    online_platform = forms.CharField(
        label=_("Plateforme"),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ex: Zoom, Teams, Google Meet'),
            'data-online-field': 'true'
        })
    )

    online_meeting_id = forms.CharField(
        label=_("ID de réunion"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('ID de la réunion'),
            'data-online-field': 'true'
        })
    )

    online_password = forms.CharField(
        label=_("Mot de passe"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Mot de passe de la réunion'),
            'data-online-field': 'true'
        })
    )

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'organization',
            'start_date', 'end_date', 'start_time', 'end_time', 'all_day',
            'location', 'address', 'city', 'postal_code',
            'visibility', 'is_public', 'max_participants', 'registration_required',
            'price', 'contact_person', 'contact_email', 'contact_phone',
            'image', 'color',
            # Champs de récurrence
            'is_recurring', 'recurrence_frequency', 'recurrence_days',
            'recurrence_end_type', 'recurrence_end_after', 'recurrence_end_date',
            'recurrence_day_of_month', 'recurrence_week_of_month',
            # Champs en ligne
            'event_format', 'online_url', 'online_platform',
            'online_meeting_id', 'online_password',
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
    
    def clean_recurrence_days(self):
        """Parse les jours de récurrence depuis le JSON ou la liste."""
        import json
        value = self.cleaned_data.get('recurrence_days')

        if not value:
            return []

        # Si c'est déjà une liste, la retourner
        if isinstance(value, list):
            # Filtrer les valeurs vides ou invalides
            valid_days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
            return [d for d in value if d in valid_days]

        # Si c'est une chaîne JSON, la parser
        if isinstance(value, str):
            # Nettoyer les caractères d'échappement multiples
            value = value.strip()

            # Cas spécial: chaîne vide ou "[]"
            if value == '' or value == '[]':
                return []

            try:
                # Parser le JSON
                parsed = json.loads(value)

                # Si le résultat est une liste, continuer
                if isinstance(parsed, list):
                    # Vérifier si c'est un double encodage (liste contenant une chaîne JSON)
                    if len(parsed) == 1 and isinstance(parsed[0], str) and parsed[0].startswith('['):
                        try:
                            parsed = json.loads(parsed[0])
                        except json.JSONDecodeError:
                            pass

                    # Filtrer pour ne garder que les jours valides
                    valid_days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                    return [d for d in parsed if d in valid_days]

                return []

            except json.JSONDecodeError:
                # Peut être une chaîne séparée par des virgules
                valid_days = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                parts = [d.strip() for d in value.split(',') if d.strip()]
                return [d for d in parts if d in valid_days]

        return []

    def clean_online_url(self):
        """Valide l'URL de visioconférence - extrait l'URL si c'est un texte avec invitation."""
        import re
        value = self.cleaned_data.get('online_url', '')

        if not value:
            return ''

        # Si c'est déjà une URL valide, la retourner
        if value.startswith('http://') or value.startswith('https://'):
            return value

        # Essayer d'extraire une URL du texte (invitation Zoom copiée-collée)
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        matches = re.findall(url_pattern, value)

        if matches:
            return matches[0]

        # Si pas d'URL trouvée mais texte non vide, ajouter https://
        if value and not value.startswith('http'):
            # Ne pas modifier si c'est juste du texte d'invitation
            if 'zoom' in value.lower() or 'meet' in value.lower() or 'teams' in value.lower():
                self.add_error('online_url', _("Veuillez coller uniquement le lien de la réunion (ex: https://zoom.us/j/...), pas l'invitation complète."))
                return ''

        return value

    def clean(self):
        cleaned_data = super().clean()

        # Validation des dates
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _("La date de fin doit être égale ou postérieure à la date de début."))

        # Validation des heures
        all_day = cleaned_data.get('all_day')
        if not all_day:
            start_time = cleaned_data.get('start_time')
            end_time = cleaned_data.get('end_time')

            if start_time and end_time and start_date == end_date and start_time >= end_time:
                self.add_error('end_time', _("L'heure de fin doit être postérieure à l'heure de début pour un événement le même jour."))

        # Gérer la date limite d'inscription
        registration_required = cleaned_data.get('registration_required')
        registration_deadline_date = cleaned_data.get('registration_deadline_date')
        registration_deadline_time = cleaned_data.get('registration_deadline_time')

        if registration_required and registration_deadline_date:
            if not registration_deadline_time:
                registration_deadline_time = timezone.datetime.max.time().replace(microsecond=0)

            registration_deadline = timezone.datetime.combine(
                registration_deadline_date,
                registration_deadline_time
            )
            registration_deadline = timezone.make_aware(registration_deadline)

            if start_date:
                event_start = timezone.datetime.combine(
                    start_date,
                    cleaned_data.get('start_time') or timezone.datetime.min.time()
                )
                event_start = timezone.make_aware(event_start)

                if registration_deadline >= event_start:
                    self.add_error('registration_deadline_date',
                        _("La date limite d'inscription doit être antérieure à la date de début de l'événement."))

            cleaned_data['registration_deadline'] = registration_deadline
        else:
            cleaned_data['registration_deadline'] = None

        # =========================================================================
        # VALIDATION DE LA RÉCURRENCE
        # =========================================================================
        is_recurring = cleaned_data.get('is_recurring')

        if is_recurring:
            recurrence_frequency = cleaned_data.get('recurrence_frequency')

            if not recurrence_frequency:
                self.add_error('recurrence_frequency', _("Veuillez sélectionner une fréquence de récurrence."))

            if recurrence_frequency in ['weekly', 'biweekly']:
                recurrence_days = cleaned_data.get('recurrence_days')
                if not recurrence_days:
                    self.add_error('recurrence_days', _("Veuillez sélectionner au moins un jour de la semaine."))

            recurrence_end_type = cleaned_data.get('recurrence_end_type')

            if recurrence_end_type == 'after':
                recurrence_end_after = cleaned_data.get('recurrence_end_after')
                if not recurrence_end_after or recurrence_end_after < 1:
                    self.add_error('recurrence_end_after', _("Veuillez spécifier un nombre d'occurrences valide."))

            elif recurrence_end_type == 'on_date':
                recurrence_end_date = cleaned_data.get('recurrence_end_date')
                if not recurrence_end_date:
                    self.add_error('recurrence_end_date', _("Veuillez spécifier une date de fin de récurrence."))
                elif start_date and recurrence_end_date <= start_date:
                    self.add_error('recurrence_end_date', _("La date de fin de récurrence doit être postérieure à la date de début."))

        # =========================================================================
        # VALIDATION DES CHAMPS EN LIGNE
        # =========================================================================
        event_format = cleaned_data.get('event_format')

        if event_format in [EventFormat.ONLINE, EventFormat.HYBRID]:
            online_url = cleaned_data.get('online_url')
            if not online_url:
                self.add_error('online_url', _("Veuillez spécifier l'URL de la visioconférence."))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        is_new = not instance.pk

        # Définir le créateur si on crée un nouvel événement
        if self.user and is_new:
            instance.created_by = self.user

        # Mettre à jour l'all_day
        if instance.all_day:
            instance.start_time = None
            instance.end_time = None

        # Mettre à jour la date limite d'inscription
        instance.registration_deadline = self.cleaned_data.get('registration_deadline')

        # Gérer les champs de récurrence
        if instance.is_recurring:
            # Gérer le jour de la semaine pour les récurrences mensuelles
            day_of_week = self.cleaned_data.get('recurrence_day_of_week')
            if day_of_week and instance.recurrence_week_of_month:
                # Stocker le jour de la semaine dans recurrence_days pour la génération
                instance.recurrence_days = [day_of_week]

            # Générer la règle RRULE
            instance.generate_rrule()

        if commit:
            instance.save()

            # Générer les occurrences si événement récurrent et nouveau
            if instance.is_recurring and is_new:
                instance.generate_occurrences(months_ahead=6)

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


class PublicEventRegistrationForm(forms.Form):
    """
    Formulaire pour l'inscription publique à un événement (sans compte MartialComp).
    Utilisé pour les stages, séminaires, etc. ouverts au public.
    """
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre prénom")
        })
    )
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre nom")
        })
    )
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("votre@email.com")
        })
    )
    phone = forms.CharField(
        label=_("Téléphone"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Numéro de téléphone (optionnel)")
        })
    )
    club = forms.CharField(
        label=_("Club / Organisation"),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre club ou organisation (optionnel)")
        })
    )
    grade = forms.CharField(
        label=_("Grade / Niveau"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre grade ou niveau (optionnel)")
        })
    )
    notes = forms.CharField(
        label=_("Notes ou commentaires"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Informations supplémentaires, exigences alimentaires, etc.")
        })
    )

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

        # Ajouter le champ d'acceptation des conditions si l'événement est payant
        if self.event and self.event.price > 0:
            self.fields['accept_payment_terms'] = forms.BooleanField(
                label=_("J'accepte de payer les frais de {price} pour cet événement").format(
                    price=f"{self.event.price} €"
                ),
                required=True
            )

    def clean_email(self):
        """Vérifier si cet email n'est pas déjà inscrit à l'événement."""
        email = self.cleaned_data.get('email')
        if self.event and email:
            # Vérifier si un guest avec cet email est déjà inscrit
            from apps.competitions.models.event import EventParticipant
            if EventParticipant.objects.filter(
                event=self.event,
                guest_email__iexact=email,
                is_guest=True
            ).exists():
                raise forms.ValidationError(_("Cet email est déjà inscrit à cet événement."))
        return email

    def clean(self):
        cleaned_data = super().clean()

        # Vérifier si l'événement est complet
        if self.event and self.event.is_full:
            raise forms.ValidationError(_("Désolé, cet événement est complet."))

        # Vérifier si la date limite d'inscription est dépassée
        if self.event and self.event.registration_deadline and \
           self.event.registration_deadline < timezone.now():
            raise forms.ValidationError(_("Désolé, la date limite d'inscription est dépassée."))

        return cleaned_data


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


# =============================================================================
# FORMULAIRES POUR LES OCCURRENCES
# =============================================================================

class OccurrenceEditForm(forms.ModelForm):
    """
    Formulaire pour modifier une occurrence individuelle.
    Permet de modifier le lieu, l'URL visio, ou les notes sans affecter la série.
    """
    start_date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_time = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    end_time = forms.TimeField(
        label=_("Heure de fin"),
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )

    class Meta:
        model = EventOccurrence
        fields = [
            'status', 'override_location', 'override_online_url',
            'override_max_participants', 'notes'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'override_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Laisser vide pour utiliser le lieu par défaut')
            }),
            'override_online_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('Laisser vide pour utiliser l\'URL par défaut')
            }),
            'override_max_participants': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Préremplir les champs date/heure depuis l'instance
        if self.instance and self.instance.pk:
            self.fields['start_date'].initial = self.instance.start_datetime.date()
            self.fields['start_time'].initial = self.instance.start_datetime.time()
            self.fields['end_time'].initial = self.instance.end_datetime.time()

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', _("L'heure de fin doit être après l'heure de début."))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Marquer comme exception si des modifications ont été faites
        if any([
            instance.override_location,
            instance.override_online_url,
            instance.override_max_participants,
        ]):
            instance.is_exception = True

        # Mettre à jour les datetime
        start_date = self.cleaned_data.get('start_date')
        start_time = self.cleaned_data.get('start_time')
        end_time = self.cleaned_data.get('end_time')

        if start_date and start_time:
            from datetime import datetime
            start_dt = datetime.combine(start_date, start_time)
            if timezone.is_naive(start_dt):
                start_dt = timezone.make_aware(start_dt)
            instance.start_datetime = start_dt

            if end_time:
                end_dt = datetime.combine(start_date, end_time)
                if timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt)
                instance.end_datetime = end_dt

        if commit:
            instance.save()

        return instance


class OccurrenceCancelForm(forms.Form):
    """
    Formulaire pour annuler une occurrence avec une raison.
    """
    cancellation_reason = forms.CharField(
        label=_("Raison de l'annulation"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Ex: Jour férié, absence du professeur, etc.")
        })
    )
    notify_participants = forms.BooleanField(
        label=_("Notifier les participants"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class OccurrenceAttendanceForm(forms.Form):
    """
    Formulaire pour le pointage des présences à une occurrence.
    """

    def __init__(self, *args, **kwargs):
        self.occurrence = kwargs.pop('occurrence', None)
        super().__init__(*args, **kwargs)

        if self.occurrence:
            # Récupérer tous les participants de l'événement parent
            for participant in self.occurrence.event.participants.all():
                field_name = f"attendance_{participant.id}"

                # Récupérer le statut actuel si existe
                try:
                    attendance = EventOccurrenceAttendance.objects.get(
                        occurrence=self.occurrence,
                        participant=participant
                    )
                    initial = attendance.status
                except EventOccurrenceAttendance.DoesNotExist:
                    initial = AttendanceStatus.REGISTERED

                self.fields[field_name] = forms.ChoiceField(
                    label=participant.display_name,
                    choices=AttendanceStatus.choices,
                    initial=initial,
                    widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
                )

    def save(self, checked_by=None):
        """Enregistre les présences."""
        if not self.occurrence:
            return

        for field_name, status in self.cleaned_data.items():
            if field_name.startswith('attendance_'):
                participant_id = int(field_name.replace('attendance_', ''))

                attendance, created = EventOccurrenceAttendance.objects.get_or_create(
                    occurrence=self.occurrence,
                    participant_id=participant_id,
                    defaults={'status': status}
                )

                if not created and attendance.status != status:
                    attendance.status = status
                    if status == AttendanceStatus.PRESENT:
                        attendance.check_in_time = timezone.now()
                        attendance.check_in_method = 'manual'
                        attendance.checked_in_by = checked_by
                    attendance.save()

        # Mettre à jour le compteur de présents
        self.occurrence.update_attendees_count()
