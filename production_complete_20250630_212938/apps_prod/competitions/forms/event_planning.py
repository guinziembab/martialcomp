# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.forms import inlineformset_factory, BaseInlineFormSet

from competitions.models.event_planning import (
    EventPoll, PollOption, PollResponse, EventReminder, EventStatistics, PollQuestion, PollQuestionResponse
)


class EventPollForm(forms.ModelForm):
    """
    Formulaire pour la création/édition d'un sondage d'événement.
    """
    expires_at_date = forms.DateField(
        label=_("Date d'expiration"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    expires_at_time = forms.TimeField(
        label=_("Heure d'expiration"),
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    class Meta:
        model = EventPoll
        fields = [
            'title', 'description', 'event_type', 'response_type',
            'allow_comments', 'allow_multiple_votes', 'show_participants',
            'show_vote_counts', 'organization'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'organization': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Si nous avons une instance existante et une date d'expiration
        if self.instance and self.instance.pk and self.instance.expires_at:
            self.fields['expires_at_date'].initial = self.instance.expires_at.date()
            self.fields['expires_at_time'].initial = self.instance.expires_at.time()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Vérifier et convertir les champs date/time en un seul champ datetime
        expires_at_date = cleaned_data.get('expires_at_date')
        expires_at_time = cleaned_data.get('expires_at_time')
        
        if expires_at_date:
            # Si seulement la date est fournie, on utilise minuit comme heure par défaut
            if not expires_at_time:
                expires_at_time = timezone.datetime.min.time()
            
            # Combiner date et heure dans un objet datetime
            expires_at = timezone.datetime.combine(expires_at_date, expires_at_time)
            
            # Rendre le datetime aware avant la comparaison
            expires_at_aware = timezone.make_aware(expires_at)
            
            # Vérifier que la date d'expiration est future
            if expires_at_aware <= timezone.now():
                self.add_error('expires_at_date', _("La date d'expiration doit être dans le futur."))
            
            # Stocker dans le format attendu par le modèle
            cleaned_data['expires_at'] = expires_at_aware
        else:
            cleaned_data['expires_at'] = None
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir le créateur si nous avons un utilisateur
        if self.user and not instance.created_by:
            instance.created_by = self.user
        
        # Enregistrer l'instance si commit est True
        if commit:
            instance.save()
        
        return instance


class PollOptionForm(forms.ModelForm):
    """
    Formulaire pour l'ajout d'options de date/heure à un sondage.
    """
    class Meta:
        model = PollOption
        fields = ['date', 'start_time', 'end_time', 'all_day', 'location']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        all_day = cleaned_data.get('all_day')
        
        # Si c'est toute la journée, on ignore les heures
        if all_day:
            cleaned_data['start_time'] = None
            cleaned_data['end_time'] = None
        # Sinon, on valide que l'heure de fin est après l'heure de début
        elif start_time and end_time and start_time >= end_time:
            self.add_error('end_time', _("L'heure de fin doit être postérieure à l'heure de début."))
        
        return cleaned_data


class BasePollOptionFormSet(BaseInlineFormSet):
    """
    FormSet de base pour les options de sondage avec validation améliorée.
    """
    def clean(self):
        super().clean()
        
        # Vérifier qu'au moins une option a été fournie
        if not any(form.cleaned_data and not form.cleaned_data.get('DELETE', False) 
                    for form in self.forms):
            raise forms.ValidationError(_("Vous devez fournir au moins une option de date/heure."))
        
        # Vérifier qu'il n'y a pas de doublons
        seen_dates = {}
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                date = form.cleaned_data.get('date')
                start_time = form.cleaned_data.get('start_time')
                all_day = form.cleaned_data.get('all_day')
                
                # Créer une clé unique pour chaque combinaison date/heure
                if all_day:
                    key = (date, None)
                else:
                    key = (date, start_time)
                
                if key in seen_dates:
                    form.add_error('date', _("Cette combinaison date/heure est déjà proposée."))
                else:
                    seen_dates[key] = True


# Création du FormSet pour les options de sondage
PollOptionFormSet = inlineformset_factory(
    EventPoll, 
    PollOption,
    form=PollOptionForm,
    formset=BasePollOptionFormSet,
    extra=3,  # Nombre de formulaires vides à afficher
    can_delete=True,
    min_num=1,  # Nombre minimum de formulaires
    validate_min=True
)


class PollResponseForm(forms.ModelForm):
    """
    Formulaire pour répondre à une option de sondage.
    """
    class Meta:
        model = PollResponse
        fields = ['response', 'comment', 'is_anonymous']
        widgets = {
            'response': forms.RadioSelect(),
            'comment': forms.Textarea(attrs={'rows': 2, 'placeholder': _("Commentaire (optionnel)")}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.option = kwargs.pop('option', None)
        super().__init__(*args, **kwargs)
        
        # Adapter les choix selon le type de réponse du sondage
        if self.option and self.option.poll.response_type == 'yes_no':
            self.fields['response'].choices = [
                ('yes', _('Oui')),
                ('no', _('Non')),
            ]
        
        # Cacher l'option anonyme si le sondage ne montre pas les participants
        if self.option and not self.option.poll.show_participants:
            self.fields['is_anonymous'].widget = forms.HiddenInput()
            self.fields['is_anonymous'].initial = True
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir l'utilisateur et l'option si fournis
        if self.user:
            instance.user = self.user
        if self.option:
            instance.option = self.option
        
        # Enregistrer l'instance si commit est True
        if commit:
            instance.save()
        
        return instance


class BulkPollResponseForm(forms.Form):
    """
    Formulaire pour répondre à toutes les options d'un sondage en une fois.
    """
    def __init__(self, *args, **kwargs):
        self.poll = kwargs.pop('poll', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if not self.poll:
            return
        
        # Ajouter dynamiquement un champ pour chaque option du sondage
        for option in self.poll.options.all().order_by('date', 'start_time'):
            field_name = f'option_{option.id}'
            
            # Adapter les choix selon le type de réponse
            if self.poll.response_type == 'yes_no':
                choices = [
                    ('', _('Choisir...')),
                    ('yes', _('Oui')),
                    ('no', _('Non')),
                ]
            else:  # yes_maybe_no
                choices = [
                    ('', _('Choisir...')),
                    ('yes', _('Oui')),
                    ('maybe', _('Peut-être')),
                    ('no', _('Non')),
                ]
            
            self.fields[field_name] = forms.ChoiceField(
                label=str(option),
                choices=choices,
                required=False,
                widget=forms.RadioSelect()
            )
            
            # Ajouter un champ de commentaire pour chaque option
            if self.poll.allow_comments:
                comment_field_name = f'comment_{option.id}'
                self.fields[comment_field_name] = forms.CharField(
                    label=_("Commentaire"),
                    required=False,
                    widget=forms.Textarea(attrs={'rows': 2, 'placeholder': _("Commentaire (optionnel)")})
                )
        
        # Champ pour l'anonymat global
        if self.poll.show_participants:
            self.fields['is_anonymous'] = forms.BooleanField(
                label=_("Répondre anonymement"),
                required=False
            )
    
    def save(self):
        """Enregistre toutes les réponses du formulaire."""
        if not self.poll or not self.user:
            return []
        
        responses = []
        is_anonymous = self.cleaned_data.get('is_anonymous', False)
        
        for option in self.poll.options.all():
            field_name = f'option_{option.id}'
            comment_field_name = f'comment_{option.id}'
            
            # Vérifier si une réponse a été donnée pour cette option
            response_value = self.cleaned_data.get(field_name)
            if response_value:
                # Vérifier si une réponse existe déjà pour cette option et cet utilisateur
                try:
                    response = PollResponse.objects.get(
                        option=option,
                        user=self.user
                    )
                    # Mettre à jour la réponse existante
                    response.response = response_value
                    if comment_field_name in self.cleaned_data:
                        response.comment = self.cleaned_data[comment_field_name]
                    response.is_anonymous = is_anonymous
                    response.save()
                except PollResponse.DoesNotExist:
                    # Créer une nouvelle réponse
                    response = PollResponse(
                        option=option,
                        user=self.user,
                        response=response_value,
                        comment=self.cleaned_data.get(comment_field_name, ''),
                        is_anonymous=is_anonymous
                    )
                    response.save()
                
                responses.append(response)
        
        return responses


class EventReminderForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un rappel d'événement.
    """
    # Champs pour faciliter la gestion de la durée
    days = forms.IntegerField(
        label=_("Jours"),
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'min': '0'})
    )
    hours = forms.IntegerField(
        label=_("Heures"),
        required=False,
        min_value=0,
        max_value=23,
        initial=1,
        widget=forms.NumberInput(attrs={'min': '0', 'max': '23'})
    )
    minutes = forms.IntegerField(
        label=_("Minutes"),
        required=False,
        min_value=0,
        max_value=59,
        initial=0,
        widget=forms.NumberInput(attrs={'min': '0', 'max': '59'})
    )
    
    # Date et heure précises pour l'envoi
    send_at_date = forms.DateField(
        label=_("Date d'envoi"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    send_at_time = forms.TimeField(
        label=_("Heure d'envoi"),
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    class Meta:
        model = EventReminder
        fields = [
            'title', 'message', 'reminder_type', 'is_enabled', 'recipients'
        ]
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4}),
            'recipients': forms.SelectMultiple(attrs={'class': 'select2-widget'})
        }
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pré-remplir les champs de durée si nous avons une instance
        if self.instance and self.instance.pk and self.instance.time_before_event:
            total_seconds = self.instance.time_before_event.total_seconds()
            days = int(total_seconds // (24 * 3600))
            hours = int((total_seconds % (24 * 3600)) // 3600)
            minutes = int((total_seconds % 3600) // 60)
            
            self.fields['days'].initial = days
            self.fields['hours'].initial = hours
            self.fields['minutes'].initial = minutes
        
        # Pré-remplir la date et l'heure d'envoi si définies
        if self.instance and self.instance.pk and self.instance.send_at:
            self.fields['send_at_date'].initial = self.instance.send_at.date()
            self.fields['send_at_time'].initial = self.instance.send_at.time()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Gérer la date/heure d'envoi précise
        send_at_date = cleaned_data.get('send_at_date')
        send_at_time = cleaned_data.get('send_at_time')
        
        # Gérer les champs de durée
        days = cleaned_data.get('days') or 0
        hours = cleaned_data.get('hours') or 0
        minutes = cleaned_data.get('minutes') or 0
        
        # Vérifier qu'au moins une méthode d'envoi est spécifiée
        if not send_at_date and days == 0 and hours == 0 and minutes == 0:
            self.add_error(None, _("Vous devez spécifier soit une date d'envoi précise, soit un délai avant l'événement."))
        
        # Convertir les champs de durée en un objet timedelta pour time_before_event
        if days > 0 or hours > 0 or minutes > 0:
            from datetime import timedelta
            cleaned_data['time_before_event'] = timedelta(
                days=days,
                hours=hours,
                minutes=minutes
            )
        
        # Convertir date et heure en un objet datetime pour send_at
        if send_at_date:
            # Si seulement la date est fournie, on utilise midi comme heure par défaut
            if not send_at_time:
                send_at_time = timezone.datetime.min.time().replace(hour=12)
            
            # Combiner date et heure
            send_at = timezone.datetime.combine(send_at_date, send_at_time)
            cleaned_data['send_at'] = timezone.make_aware(send_at)
            
            # Vérifier que la date d'envoi est future
            if cleaned_data['send_at'] <= timezone.now():
                self.add_error('send_at_date', _("La date d'envoi doit être dans le futur."))
            
            # Vérifier que la date d'envoi est avant la date de l'événement
            if self.event and self.event.start_date:
                event_datetime = timezone.datetime.combine(self.event.start_date, self.event.start_time or timezone.datetime.min.time())
                event_datetime = timezone.make_aware(event_datetime)
                
                if cleaned_data['send_at'] >= event_datetime:
                    self.add_error('send_at_date', _("La date d'envoi doit être antérieure à la date de l'événement."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir l'événement si fourni
        if self.event and not instance.event_id:
            instance.event = self.event
        
        # Définir le créateur si nous avons un utilisateur
        if self.user and not instance.created_by:
            instance.created_by = self.user
        
        # Enregistrer l'instance si commit est True
        if commit:
            instance.save()
            # Pour enregistrer la relation many-to-many
            self.save_m2m()
        
        return instance


class PollQuestionForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une question personnalisée de sondage.
    """
    choices_text = forms.CharField(
        label=_("Options de choix"),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': _("Une option par ligne (pour les questions à choix multiple)")
        }),
        help_text=_("Saisissez une option par ligne pour les questions à choix multiple")
    )
    
    class Meta:
        model = PollQuestion
        fields = [
            'question_text', 'question_type', 'is_required', 'order'
        ]
        widgets = {
            'question_text': forms.TextInput(attrs={
                'placeholder': _("Saisissez votre question...")
            }),
            'question_type': forms.Select(),
            'order': forms.NumberInput(attrs={'min': '0'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pré-remplir le champ choices_text si nous avons une instance
        if self.instance and self.instance.pk and self.instance.choices:
            self.fields['choices_text'].initial = '\n'.join(self.instance.choices)
    
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        choices_text = cleaned_data.get('choices_text', '').strip()
        
        # Vérifier que les options sont fournies pour les questions à choix
        if question_type == 'choice' and not choices_text:
            self.add_error('choices_text', _("Vous devez fournir des options pour les questions à choix multiple."))
        
        # Convertir le texte des choix en liste
        if choices_text:
            choices = [choice.strip() for choice in choices_text.split('\n') if choice.strip()]
            if question_type == 'choice' and len(choices) < 2:
                self.add_error('choices_text', _("Vous devez fournir au moins 2 options pour les questions à choix multiple."))
            cleaned_data['choices'] = choices
        else:
            cleaned_data['choices'] = []
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir les choix depuis le champ choices
        choices = self.cleaned_data.get('choices', [])
        instance.choices = choices
        
        if commit:
            instance.save()
        
        return instance


class BasePollQuestionFormSet(BaseInlineFormSet):
    """
    FormSet de base pour les questions personnalisées avec validation.
    """
    def clean(self):
        super().clean()
        
        # Vérifier l'ordre des questions (pas de doublons)
        orders = []
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                order = form.cleaned_data.get('order', 0)
                if order in orders:
                    form.add_error('order', _("Plusieurs questions ont le même ordre."))
                orders.append(order)


# Création du FormSet pour les questions personnalisées
PollQuestionFormSet = inlineformset_factory(
    EventPoll,
    PollQuestion,
    form=PollQuestionForm,
    formset=BasePollQuestionFormSet,
    extra=2,  # Nombre de formulaires vides à afficher
    can_delete=True,
    min_num=0,  # Pas de minimum requis
    validate_min=False
)


class PollQuestionResponseForm(forms.ModelForm):
    """
    Formulaire pour répondre à une question personnalisée.
    """
    class Meta:
        model = PollQuestionResponse
        fields = [
            'response_text', 'response_number', 'response_date', 
            'response_time', 'response_choice'
        ]
        widgets = {
            'response_text': forms.Textarea(attrs={'rows': 3}),
            'response_number': forms.NumberInput(),
            'response_date': forms.DateInput(attrs={'type': 'date'}),
            'response_time': forms.TimeInput(attrs={'type': 'time'}),
            'response_choice': forms.Select()
        }
    
    def __init__(self, *args, **kwargs):
        self.question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)
        
        if not self.question:
            return
        
        # Adapter les champs selon le type de question
        question_type = self.question.question_type
        
        # Cacher tous les champs par défaut
        for field_name in self.fields:
            self.fields[field_name].widget = forms.HiddenInput()
            self.fields[field_name].required = False
        
        # Afficher seulement le champ approprié selon le type
        if question_type == 'text':
            self.fields['response_text'].widget = forms.Textarea(attrs={'rows': 3})
            self.fields['response_text'].required = self.question.is_required
            
        elif question_type == 'choice':
            # Utiliser un ChoiceField dynamique pour les choix multiples
            choices = [('', _('Choisir...'))] + [(choice, choice) for choice in self.question.choices]
            self.fields['response_choice'] = forms.ChoiceField(
                choices=choices,
                required=self.question.is_required,
                widget=forms.Select()
            )
            
        elif question_type == 'rating':
            choices = [('', _('Choisir...'))] + [(str(i), str(i)) for i in range(1, 6)]
            self.fields['response_number'] = forms.ChoiceField(
                choices=choices,
                required=self.question.is_required,
                widget=forms.Select()
            )
            
        elif question_type == 'yes_no':
            self.fields['response_choice'].widget = forms.RadioSelect(choices=[
                ('yes', _('Oui')),
                ('no', _('Non'))
            ])
            self.fields['response_choice'].required = self.question.is_required
            
        elif question_type == 'date':
            self.fields['response_date'].widget = forms.DateInput(attrs={'type': 'date'})
            self.fields['response_date'].required = self.question.is_required
            
        elif question_type == 'time':
            self.fields['response_time'].widget = forms.TimeInput(attrs={'type': 'time'})
            self.fields['response_time'].required = self.question.is_required
            
        elif question_type == 'number':
            self.fields['response_number'].widget = forms.NumberInput()
            self.fields['response_number'].required = self.question.is_required
    
    def clean(self):
        cleaned_data = super().clean()
        
        if not self.question:
            return cleaned_data
        
        question_type = self.question.question_type
        
        # Vérifier qu'une réponse est fournie si la question est requise
        if self.question.is_required:
            response_provided = False
            
            if question_type == 'text' and cleaned_data.get('response_text'):
                response_provided = True
            elif question_type in ['choice', 'yes_no'] and cleaned_data.get('response_choice'):
                response_provided = True
            elif question_type in ['rating', 'number'] and cleaned_data.get('response_number') is not None:
                response_provided = True
            elif question_type == 'date' and cleaned_data.get('response_date'):
                response_provided = True
            elif question_type == 'time' and cleaned_data.get('response_time'):
                response_provided = True
            
            if not response_provided:
                raise forms.ValidationError(_("Cette question est obligatoire."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir la question si fournie
        if self.question:
            instance.question = self.question
        
        if commit:
            instance.save()
        
        return instance