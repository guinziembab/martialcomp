# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone

from apps.competitions.models.event import Event, EventParticipant


class EventNotificationForm(forms.Form):
    """
    Formulaire pour envoyer des notifications aux participants d'un événement.
    """
    RECIPIENT_CHOICES = [
        ('all', _('Tous les participants')),
        ('confirmed', _('Participants confirmés uniquement')),
        ('waitlist', _("Participants sur liste d'attente")),
        ('not_responded', _("Participants n'ayant pas répondu")),
        ('custom', _('Sélection personnalisée')),
    ]
    
    subject = forms.CharField(
        label=_("Sujet"),
        max_length=200,
        required=True
    )
    
    message = forms.CharField(
        label=_("Message"),
        widget=forms.Textarea(attrs={'rows': 5}),
        required=True
    )
    
    recipient_type = forms.ChoiceField(
        label=_("Destinataires"),
        choices=RECIPIENT_CHOICES,
        initial='all',
        widget=forms.RadioSelect
    )
    
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        label=_("Sélectionner des destinataires"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("Sélectionnez les participants spécifiques Ã  qui envoyer cette notification.")
    )
    
    notification_method = forms.MultipleChoiceField(
        label=_("Méthode de notification"),
        choices=[
            ('email', _('Email')),
            ('sms', _('SMS')),
            ('app', _("Notification dans l'application")),
        ],
        initial=['email', 'app'],
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    send_immediately = forms.BooleanField(
        label=_("Envoyer immédiatement"),
        initial=True,
        required=False
    )
    
    scheduled_date = forms.DateField(
        label=_("Date d'envoi programmée"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    scheduled_time = forms.TimeField(
        label=_("Heure d'envoi programmée"),
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Charger les participants de l'événement si disponible
        if self.event:
            # Récupérer tous les participants
            participants = EventParticipant.objects.filter(event=self.event)
            
            # Récupérer les utilisateurs correspondants
            participant_users = User.objects.filter(
                id__in=participants.values_list('user_id', flat=True)
            ).order_by('last_name', 'first_name')
            
            self.fields['recipients'].queryset = participant_users
            
            # Pré-remplir le sujet avec le titre de l'événement
            self.fields['subject'].initial = f"{_('Information')}: {self.event.title}"
    
    def clean(self):
        cleaned_data = super().clean()
        recipient_type = cleaned_data.get('recipient_type')
        recipients = cleaned_data.get('recipients')
        send_immediately = cleaned_data.get('send_immediately')
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        
        # Vérifier que des destinataires sont sélectionnés si le type est 'custom'
        if recipient_type == 'custom' and not recipients:
            self.add_error('recipients', _("Veuillez sélectionner au moins un destinataire."))
        
        # Vérifier que la date et l'heure sont fournies si l'envoi n'est pas immédiat
        if not send_immediately:
            if not scheduled_date:
                self.add_error('scheduled_date', _("Veuillez spécifier une date d'envoi."))
            
            if not scheduled_time:
                self.add_error('scheduled_time', _("Veuillez spécifier une heure d'envoi."))
            
            # Vérifier que la date/heure programmée est dans le futur
            if scheduled_date and scheduled_time:
                scheduled_datetime = timezone.datetime.combine(scheduled_date, scheduled_time)
                scheduled_datetime = timezone.make_aware(scheduled_datetime)
                
                if scheduled_datetime <= timezone.now():
                    self.add_error('scheduled_date', _("La date et l'heure programmées doivent Ãªtre dans le futur."))
        
        return cleaned_data
    
    def get_recipients(self):
        """
        Retourne la liste des utilisateurs destinataires en fonction du type sélectionné.
        """
        if not self.event or not hasattr(self, 'cleaned_data'):
            return []
        
        recipient_type = self.cleaned_data.get('recipient_type')
        
        if recipient_type == 'custom':
            return list(self.cleaned_data.get('recipients', []))
        
        # Filtrer les participants selon le type sélectionné
        participants = EventParticipant.objects.filter(event=self.event)
        
        if recipient_type == 'confirmed':
            participants = participants.filter(status='confirmed')
        elif recipient_type == 'waitlist':
            participants = participants.filter(status='waitlist')
        elif recipient_type == 'not_responded':
            # Cette logique dépend de l'implémentation exacte du suivi des réponses
            # Par exemple, si vous utilisez un statut 'pending' ou un champ has_responded
            participants = participants.filter(status='registered')
        
        # Récupérer les utilisateurs correspondants
        user_ids = participants.values_list('user_id', flat=True)
        return list(User.objects.filter(id__in=user_ids))
    
    def save_notification(self):
        """
        Enregistre la notification et la programme pour envoi.
        Retourne l'objet notification créé.
        """
        if not self.event or not hasattr(self, 'cleaned_data'):
            return None
        
        recipients = self.get_recipients()
        
        if not recipients:
            return None
        
        # Créer un objet de notification (Ã  adapter selon votre modèle)
        from apps.competitions.models.notifications import EventNotification
        
        notification = EventNotification(
            event=self.event,
            subject=self.cleaned_data['subject'],
            message=self.cleaned_data['message'],
            created_by=self.user,
            notification_type='custom',
            methods=self.cleaned_data.get('notification_method', []),
        )
        
        # Gérer la programmation
        if not self.cleaned_data.get('send_immediately'):
            scheduled_date = self.cleaned_data.get('scheduled_date')
            scheduled_time = self.cleaned_data.get('scheduled_time')
            
            if scheduled_date and scheduled_time:
                scheduled_datetime = timezone.datetime.combine(scheduled_date, scheduled_time)
                notification.scheduled_for = timezone.make_aware(scheduled_datetime)
        
        # Enregistrer la notification
        notification.save()
        
        # Associer les destinataires
        notification.recipients.set(recipients)
        
        # Si l'envoi est immédiat, déclencher l'envoi
        if self.cleaned_data.get('send_immediately'):
            notification.send()
        
        return notification


class EventInvitationForm(forms.Form):
    """
    Formulaire pour inviter des personnes Ã  un événement.
    """
    INVITATION_TYPE_CHOICES = [
        ('email', _('Par adresse email')),
        ('users', _('Utilisateurs existants')),
        ('groups', _("Groupes d'utilisateurs")),
    ]
    
    invitation_type = forms.ChoiceField(
        label=_("Type d'invitation"),
        choices=INVITATION_TYPE_CHOICES,
        initial='email',
        widget=forms.RadioSelect
    )
    
    # Pour les invitations par email
    emails = forms.CharField(
        label=_("Adresses email"),
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'placeholder': _("Entrez les adresses email séparées par des virgules ou des sauts de ligne")
        }),
        help_text=_("Plusieurs adresses peuvent Ãªtre séparées par des virgules ou des sauts de ligne.")
    )
    
    # Pour les invitations d'utilisateurs existants
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all().order_by('last_name', 'first_name'),
        label=_("Sélectionner des utilisateurs"),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2-widget'})
    )
    
    # Pour les invitations de groupes
    groups = forms.MultipleChoiceField(
        choices=[],  # Sera rempli dynamiquement
        label=_("Sélectionner des groupes"),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2-widget'})
    )
    
    message = forms.CharField(
        label=_("Message personnel"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        help_text=_("Un message personnel Ã  inclure dans l'invitation.")
    )
    
    send_reminder = forms.BooleanField(
        label=_("Envoyer un rappel"),
        required=False,
        initial=True,
        help_text=_("Envoyer un rappel 24 heures avant l'événement.")
    )
    
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les utilisateurs aux membres de l'organisation si applicable
        if self.event and self.event.organization:
            org_members = self.event.organization.members.all()
            self.fields['users'].queryset = org_members.order_by('last_name', 'first_name')
        
        # Charger les groupes disponibles (adapter selon votre structure)
        group_choices = []
        
        if self.event and self.event.organization:
            # Exemple : récupérer les groupes de l'organisation
            from django.contrib.auth.models import Group
            
            # Adapter cette logique selon votre modèle de données
            # Par exemple, si vous avez un modèle OrganizationGroup lié Ã  Organization
            group_choices = [
                ('all_members', _('Tous les membres')),
                ('administrators', _('Administrateurs')),
            ]
            
            # Si vous utilisez des groupes standards Django
            all_groups = Group.objects.all().values_list('id', 'name')
            group_choices.extend([(str(g_id), name) for g_id, name in all_groups])
        
        self.fields['groups'].choices = group_choices
    
    def clean_emails(self):
        emails = self.cleaned_data.get('emails', '')
        if not emails:
            return []
        
        # Diviser et nettoyer les emails
        email_list = []
        for line in emails.split('\n'):
            # Diviser par virgules et traiter chaque email
            for email in line.split(','):
                email = email.strip()
                if email:
                    email_list.append(email)
        
        # Valider le format de chaque email
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        invalid_emails = []
        valid_emails = []
        
        for email in email_list:
            try:
                validate_email(email)
                valid_emails.append(email)
            except ValidationError:
                invalid_emails.append(email)
        
        if invalid_emails:
            raise forms.ValidationError(
                _("Les adresses email suivantes ne sont pas valides: %(emails)s"),
                params={'emails': ', '.join(invalid_emails)}
            )
        
        return valid_emails
    
    def clean(self):
        cleaned_data = super().clean()
        invitation_type = cleaned_data.get('invitation_type')
        
        # Vérifier que les champs appropriés sont remplis selon le type d'invitation
        if invitation_type == 'email' and not cleaned_data.get('emails'):
            self.add_error('emails', _("Veuillez entrer au moins une adresse email."))
        
        elif invitation_type == 'users' and not cleaned_data.get('users'):
            self.add_error('users', _("Veuillez sélectionner au moins un utilisateur."))
        
        elif invitation_type == 'groups' and not cleaned_data.get('groups'):
            self.add_error('groups', _("Veuillez sélectionner au moins un groupe."))
        
        return cleaned_data
    
    def get_recipients(self):
        """
        Retourne la liste des destinataires d'invitation.
        Pour le type 'email', retourne une liste de dictionnaires avec les emails.
        Pour les autres types, retourne une liste d'objets User.
        """
        if not hasattr(self, 'cleaned_data'):
            return []
        
        invitation_type = self.cleaned_data.get('invitation_type')
        
        if invitation_type == 'email':
            # Pour les emails, retourner une liste de dictionnaires
            emails = self.cleaned_data.get('emails', [])
            return [{'email': email} for email in emails]
        
        elif invitation_type == 'users':
            # Pour les utilisateurs, retourner la liste des utilisateurs sélectionnés
            return list(self.cleaned_data.get('users', []))
        
        elif invitation_type == 'groups':
            # Pour les groupes, récupérer tous les utilisateurs des groupes sélectionnés
            users = set()
            groups = self.cleaned_data.get('groups', [])
            
            for group_id in groups:
                if group_id == 'all_members' and self.event and self.event.organization:
                    # Tous les membres de l'organisation
                    users.update(self.event.organization.members.all())
                elif group_id == 'administrators' and self.event and self.event.organization:
                    # Administrateurs de l'organisation
                    users.update(self.event.organization.admins.all())
                else:
                    # Groupes standards Django
                    try:
                        from django.contrib.auth.models import Group
                        group = Group.objects.get(pk=int(group_id))
                        users.update(group.user_set.all())
                    except (ValueError, Group.DoesNotExist):
                        pass
            
            return list(users)
        
        return []
    
    def send_invitations(self):
        """
        Envoie les invitations aux destinataires.
        Retourne un tuple (success_count, error_count, errors_list).
        """
        if not self.event or not hasattr(self, 'cleaned_data'):
            return 0, 0, ["Formulaire invalide"]
        
        recipients = self.get_recipients()
        
        if not recipients:
            return 0, 0, ["Aucun destinataire valide"]
        
        success_count = 0
        error_count = 0
        errors = []
        
        # Logique d'envoi d'invitation (adapter selon votre implémentation)
        from apps.competitions.models.notifications import EventInvitation
        
        for recipient in recipients:
            try:
                if isinstance(recipient, dict) and 'email' in recipient:
                    # Invitation par email pour un nouvel utilisateur
                    invitation = EventInvitation(
                        event=self.event,
                        email=recipient['email'],
                        message=self.cleaned_data.get('message', ''),
                        created_by=self.user
                    )
                    invitation.save()
                    invitation.send_email_invitation()
                else:
                    # Invitation pour un utilisateur existant
                    invitation = EventInvitation(
                        event=self.event,
                        user=recipient,
                        message=self.cleaned_data.get('message', ''),
                        created_by=self.user
                    )
                    invitation.save()
                    invitation.send_notification()
                
                success_count += 1
                
                # Créer un rappel si demandé
                if self.cleaned_data.get('send_reminder') and self.event.start_date:
                    from datetime import timedelta
                    from apps.competitions.models.event_planning import EventReminder
                    
                    reminder = EventReminder(
                        event=self.event,
                        title=_("Rappel: {title}").format(title=self.event.title),
                        message=_("Rappel: l'événement {title} aura lieu demain.").format(
                            title=self.event.title
                        ),
                        reminder_type='all',
                        time_before_event=timedelta(days=1),
                        is_enabled=True,
                        created_by=self.user
                    )
                    reminder.save()
                    
                    # Ajouter le destinataire au rappel
                    if isinstance(recipient, dict) and 'email' in recipient:
                        # Pour les invitations par email, les rappels seront envoyés 
                        # uniquement après inscription
                        pass
                    else:
                        reminder.recipients.add(recipient)
                
            except Exception as e:
                error_count += 1
                recipient_str = recipient.get_full_name() if hasattr(recipient, 'get_full_name') else str(recipient)
                errors.append(f"{recipient_str}: {str(e)}")
        
        return success_count, error_count, errors

