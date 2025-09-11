# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils import timezone
from django.contrib.auth.models import User

from competitions.models.event import EventSurvey, SurveyQuestion, SurveyResponse, QuestionResponse
from competitions.models.event import Event

import json
from datetime import date, datetime


class EventSurveyForm(forms.ModelForm):
    """Formulaire pour la création et modification de sondages d'événements."""
    
    class Meta:
        model = EventSurvey
        fields = [
            'title', 'description', 'event', 'is_anonymous', 'is_active',
            'start_date', 'end_date', 'is_required', 'allow_multiple_submissions'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les événements disponibles à ceux créés par l'utilisateur
        # ou dans les organisations où il est admin/manager
        if user:
            events = Event.objects.filter(created_by=user)
            if hasattr(user, 'userprofile') and user.userprofile.role in ['club_admin', 'federation_admin']:
                events = events | Event.objects.filter(club=user.userprofile.club)
            
            self.fields['event'].queryset = events
        
        # Rendre certains champs optionnels
        self.fields['event'].required = False
        
        # Ajouter des classes CSS pour le style
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Vérifier que la date de fin est après la date de début
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', _("La date de fin doit être postérieure à la date de début."))
        
        return cleaned_data


class SurveyQuestionForm(forms.ModelForm):
    """Formulaire pour les questions de sondage."""
    
    choices_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text=_("Pour les questions à choix, entrez une option par ligne.")
    )
    
    class Meta:
        model = SurveyQuestion
        fields = [
            'question_text', 'question_type', 'is_required',
            'help_text', 'min_value', 'max_value', 'order'
        ]
        widgets = {
            'question_text': forms.TextInput(attrs={'class': 'form-control'}),
            'help_text': forms.TextInput(attrs={'class': 'form-control'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # Initialiser le champ de choix depuis l'instance
        if instance and instance.pk and instance.choices:
            if isinstance(instance.choices, list):
                self.fields['choices_text'].initial = '\n'.join(instance.choices)
            elif isinstance(instance.choices, dict):
                # Si les choix sont stockés sous forme de dict
                choices_lines = []
                for key, value in instance.choices.items():
                    choices_lines.append(f"{key}:{value}")
                self.fields['choices_text'].initial = '\n'.join(choices_lines)
    
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        choices_text = cleaned_data.get('choices_text')
        min_value = cleaned_data.get('min_value')
        max_value = cleaned_data.get('max_value')
        
        # Valider selon le type de question
        if question_type in ['single_choice', 'multiple_choice']:
            if not choices_text:
                self.add_error('choices_text', _("Veuillez fournir des options pour cette question à choix."))
        
        if question_type in ['rating', 'scale']:
            if min_value is None:
                self.add_error('min_value', _("Veuillez spécifier une valeur minimale."))
            if max_value is None:
                self.add_error('max_value', _("Veuillez spécifier une valeur maximale."))
            if min_value is not None and max_value is not None and min_value >= max_value:
                self.add_error('max_value', _("La valeur maximale doit être supérieure à la valeur minimale."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Traiter les choix
        choices_text = self.cleaned_data.get('choices_text')
        if choices_text and instance.question_type in ['single_choice', 'multiple_choice']:
            choices_lines = choices_text.split('\n')
            choices = []
            for line in choices_lines:
                line = line.strip()
                if line:
                    choices.append(line)
            instance.choices = choices
        
        if commit:
            instance.save()
        
        return instance


class BaseSurveyQuestionFormSet(BaseInlineFormSet):
    """Formset de base pour les questions de sondage."""
    
    def clean(self):
        """Validation globale du formset."""
        super().clean()
        
        # Vérifier qu'il y a au moins une question
        if any(self.errors):
            return
        
        if not any(form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                  for form in self.forms):
            raise forms.ValidationError(_("Au moins une question est requise."))
        
        # Vérifier les numéros d'ordre
        orders = {}
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            
            order = form.cleaned_data.get('order')
            if order in orders:
                form.add_error('order', _("Ce numéro d'ordre est déjà utilisé."))
            orders[order] = True


# Créer le formset pour les questions de sondage
SurveyQuestionFormSet = inlineformset_factory(
    EventSurvey,
    SurveyQuestion,
    form=SurveyQuestionForm,
    formset=BaseSurveyQuestionFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class SurveyResponseForm(forms.Form):
    """Formulaire dynamique pour répondre à un sondage."""
    
    respondent_name = forms.CharField(
        label=_("Votre nom"),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    respondent_email = forms.EmailField(
        label=_("Votre email"),
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    is_anonymous = forms.BooleanField(
        label=_("Soumettre anonymement"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey')
        self.survey = survey
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Ajouter dynamiquement les champs pour chaque question
        questions = SurveyQuestion.objects.filter(survey=survey).order_by('order')
        
        for question in questions:
            field_name = f'question_{question.id}'
            
            # Créer le champ en fonction du type de question
            if question.question_type == 'text':
                self.fields[field_name] = forms.CharField(
                    label=question.question_text,
                    help_text=question.help_text,
                    required=question.is_required,
                    widget=forms.TextInput(attrs={'class': 'form-control'})
                )
            
            elif question.question_type == 'textarea':
                self.fields[field_name] = forms.CharField(
                    label=question.question_text,
                    help_text=question.help_text,
                    required=question.is_required,
                    widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
                )
            
            elif question.question_type == 'single_choice':
                choices = [(choice, choice) for choice in question.choices]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.question_text,
                    help_text=question.help_text,
                    required=question.is_required,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                )
            
            elif question.question_type == 'multiple_choice':
                choices = [(choice, choice) for choice in question.choices]
                self.fields[field_name] = forms.MultipleChoiceField(
                    label=question.question_text,
                    help_text=question.help_text,
                    required=question.is_required,
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
                )
            
            elif question.question_type == 'rating':
                choices = [(i, str(i)) for i in range(question.min_value, question.max_value + 1)]
                self.fields[field_name] = forms.ChoiceField(
                    label=question.question_text,
                    help_text=question.help_text,
                    required=question.is_required,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-check-input rating-input'})
                )
            
            elif question.question_type == 'scale':
                self.fields[field_name] = forms.IntegerField(
                    label=question.question_text,
                    help_text=question.help_text,
                    required=question.is_required,
                    min_value=question.min_value,
                    max_value=question.max_value,
                    widget=forms.NumberInput(attrs={'class': 'form-control', 'type': 'range', 'min': question.min_value, 'max': question.max_value})
                )
            
            elif question.question_type == 'date':
                self.fields[field_name] = forms.DateField(
                    label=question.question_text,
                    help_text=question.help_text,
                    required=question.is_required,
                    widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
                )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Si le sondage est anonyme, l'utilisateur ne peut pas être identifié
        is_anonymous = cleaned_data.get('is_anonymous')
        
        if is_anonymous:
            # Si anonyme, enlever les informations d'identification
            cleaned_data['respondent_name'] = ''
            cleaned_data['respondent_email'] = ''
        elif not self.user and not (cleaned_data.get('respondent_name') and cleaned_data.get('respondent_email')):
            # Si pas anonyme et pas d'utilisateur connecté, exiger nom et email
            if not cleaned_data.get('respondent_name'):
                self.add_error('respondent_name', _("Ce champ est requis pour les réponses non anonymes."))
            if not cleaned_data.get('respondent_email'):
                self.add_error('respondent_email', _("Ce champ est requis pour les réponses non anonymes."))
        
        return cleaned_data
    
    def save(self):
        """Sauvegarde la réponse au sondage et ses questions associées."""
        # Créer la réponse principale
        response = SurveyResponse(
            survey=self.survey,
            participant=self.user,
            respondent_name=self.cleaned_data.get('respondent_name', ''),
            respondent_email=self.cleaned_data.get('respondent_email', ''),
            is_anonymous=self.cleaned_data.get('is_anonymous', False),
            ip_address=self.request.META.get('REMOTE_ADDR') if hasattr(self, 'request') else None,
        )
        
        # Calculer le temps de complétion si disponible
        start_time = self.request.session.get('survey_start_time') if hasattr(self, 'request') else None
        if start_time:
            try:
                start_time = datetime.fromisoformat(start_time)
                end_time = timezone.now()
                response.completion_time = end_time - start_time
            except (ValueError, TypeError):
                pass
        
        response.save()
        
        # Enregistrer les réponses aux questions individuelles
        questions = SurveyQuestion.objects.filter(survey=self.survey)
        
        for question in questions:
            field_name = f'question_{question.id}'
            
            if field_name in self.cleaned_data:
                answer = self.cleaned_data[field_name]
                
                # Créer l'instance de réponse à la question
                question_response = QuestionResponse(
                    response=response,
                    question=question
                )
                
                # Enregistrer la réponse selon le type de question
                if question.question_type in ['text', 'textarea']:
                    question_response.text_response = answer
                elif question.question_type == 'single_choice':
                    question_response.choice_response = [answer]
                elif question.question_type == 'multiple_choice':
                    question_response.choice_response = answer
                elif question.question_type in ['rating', 'scale']:
                    question_response.numeric_response = int(answer)
                elif question.question_type == 'date':
                    question_response.date_response = answer
                
                question_response.save()
        
        return response