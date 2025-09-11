# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.competitions.models.event import Event


class EventFeedbackForm(forms.Form):
    """
    Formulaire pour recueillir les commentaires des participants après un événement.
    """
    RATING_CHOICES = [
        (1, _('Très insatisfait')),
        (2, _('Insatisfait')),
        (3, _('Neutre')),
        (4, _('Satisfait')),
        (5, _('Très satisfait')),
    ]
    
    overall_satisfaction = forms.ChoiceField(
        label=_("Satisfaction générale"),
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    organization_rating = forms.ChoiceField(
        label=_("Organisation de l'événement"),
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    content_quality = forms.ChoiceField(
        label=_("Qualité du contenu"),
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    location_rating = forms.ChoiceField(
        label=_("Lieu de l'événement"),
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=True
    )
    
    value_for_money = forms.ChoiceField(
        label=_("Rapport qualité-prix"),
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        required=False
    )
    
    would_recommend = forms.ChoiceField(
        label=_("Recommanderiez-vous cet événement Ã  d'autres personnes?"),
        choices=[
            ('yes', _('Oui, sans hésitation')),
            ('maybe', _('Peut-Ãªtre')),
            ('no', _('Non'))
        ],
        widget=forms.RadioSelect,
        required=True
    )
    
    highlights = forms.CharField(
        label=_("Ce que vous avez le plus apprécié"),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    
    improvements = forms.CharField(
        label=_("Ce qui pourrait Ãªtre amélioré"),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    
    additional_comments = forms.CharField(
        label=_("Commentaires additionnels"),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )
    
    allow_testimonial = forms.BooleanField(
        label=_("J'autorise l'utilisation de mes commentaires comme témoignage"),
        required=False,
        initial=False
    )
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Adapter le formulaire selon les caractéristiques de l'événement
        if self.event:
            # Si l'événement est gratuit, masquer la question sur le rapport qualité-prix
            if not self.event.price or self.event.price == 0:
                self.fields['value_for_money'].widget = forms.HiddenInput()
                self.fields['value_for_money'].required = False
            
            # Ajouter des questions spécifiques selon le type d'événement
            if self.event.event_type == 'competition':
                self.fields['competition_fairness'] = forms.ChoiceField(
                    label=_("Ã‰quité du processus de compétition"),
                    choices=self.RATING_CHOICES,
                    widget=forms.RadioSelect,
                    required=True
                )
            elif self.event.event_type == 'training' or self.event.event_type == 'seminar':
                self.fields['instructor_knowledge'] = forms.ChoiceField(
                    label=_("Connaissance de l'instructeur"),
                    choices=self.RATING_CHOICES,
                    widget=forms.RadioSelect,
                    required=True
                )
                self.fields['material_usefulness'] = forms.ChoiceField(
                    label=_("Utilité du matériel présenté"),
                    choices=self.RATING_CHOICES,
                    widget=forms.RadioSelect,
                    required=True
                )
            elif self.event.event_type == 'exam':
                self.fields['exam_difficulty'] = forms.ChoiceField(
                    label=_("Niveau de difficulté de l'examen"),
                    choices=[
                        (1, _('Trop facile')),
                        (2, _('Facile')),
                        (3, _('Approprié')),
                        (4, _('Difficile')),
                        (5, _('Trop difficile'))
                    ],
                    widget=forms.RadioSelect,
                    required=True
                )
    
    def save_feedback(self):
        """
        Enregistre les commentaires pour l'événement.
        Retourne un dictionnaire avec les données de feedback.
        """
        if not self.event or not self.user:
            return None
        
        # Collecter toutes les données du formulaire
        feedback_data = {
            'event_id': str(self.event.id),
            'user_id': self.user.id,
            'username': self.user.username,
            'full_name': self.user.get_full_name(),
            'timestamp': timezone.now().isoformat(),
            'ratings': {},
            'comments': {},
            'recommendation': self.cleaned_data.get('would_recommend'),
            'allow_testimonial': self.cleaned_data.get('allow_testimonial', False),
        }
        
        # Ajouter les notations
        for field_name in ['overall_satisfaction', 'organization_rating', 
                          'content_quality', 'location_rating', 'value_for_money']:
            if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                feedback_data['ratings'][field_name] = int(self.cleaned_data[field_name])
        
        # Ajouter les questions spécifiques au type d'événement
        for field_name in ['competition_fairness', 'instructor_knowledge', 
                          'material_usefulness', 'exam_difficulty']:
            if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                feedback_data['ratings'][field_name] = int(self.cleaned_data[field_name])
        
        # Ajouter les commentaires textuels
        for field_name in ['highlights', 'improvements', 'additional_comments']:
            if field_name in self.cleaned_data and self.cleaned_data[field_name]:
                feedback_data['comments'][field_name] = self.cleaned_data[field_name]
        
        # Enregistrer ce feedback dans l'événement ou dans un modèle séparé
        # Nous utilisons un champ JSONField pour stocker les feedbacks
        
        # Si l'événement n'a pas encore de feedbacks, initialiser une liste vide
        if not hasattr(self.event, 'feedbacks'):
            from apps.competitions.models.event_feedback import EventFeedback
            feedback = EventFeedback(
                event=self.event,
                feedbacks=[feedback_data]
            )
            feedback.save()
        else:
            # Ajouter le nouveau feedback Ã  la liste existante
            self.event.feedbacks.feedbacks.append(feedback_data)
            self.event.feedbacks.save()
        
        return feedback_data

