# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.utils import timezone
from django.db import transaction

from competitions.models.event import Event, EventParticipant, EventSurvey, SurveyQuestion, SurveyResponse, QuestionResponse
from competitions.models.event_planning import EventPoll, PollOption, PollResponse, EventReminder, EventStatistics
from competitions.models.practitioners import Practitioner
from competitions.services.event_reminder_service import ReminderService
from organizations.models import Organization, OrganizationMember

from datetime import timedelta, date, datetime
import json
import uuid


class EventCreationAndRegistrationTest(TestCase):
    """Test d'intégration pour la création d'événements et l'inscription."""
    
    def setUp(self):
        # Créer des utilisateurs
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        # Créer une organisation
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Ajouter l'admin comme membre de l'organisation
        OrganizationMember.objects.create(
            organization=self.organization,
            user=self.admin_user,
            role='admin'
        )
        
        # Créer des pratiquants pour les deux utilisateurs
        self.admin_practitioner = Practitioner.objects.create(
            user=self.admin_user,
            first_name='Admin',
            last_name='User',
            date_of_birth=date(1980, 1, 1),
            gender='M'
        )
        
        self.user_practitioner = Practitioner.objects.create(
            user=self.regular_user,
            first_name='Regular',
            last_name='User',
            date_of_birth=date(1990, 1, 1),
            gender='F'
        )
        
        # Client pour les requêtes HTTP
        self.client = Client()
    
    def test_event_creation_and_registration_flow(self):
        """
        Test du flux complet de création d'événement et d'inscription :
        1. L'admin crée un événement
        2. Un utilisateur régulier s'inscrit à l'événement
        3. L'admin consulte la liste des participants
        """
        # 1. Login en tant qu'admin
        self.client.login(username='admin', password='adminpassword')
        
        # Créer un événement via l'API
        event_data = {
            'title': 'Test Training Session',
            'description': 'A training session for testing',
            'event_type': 'training',
            'organization': self.organization.id,
            'start_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'end_date': (date.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
            'start_time': '14:00',
            'end_time': '16:00',
            'location': 'Test Dojo',
            'capacity': 20,
            'registration_required': True
        }
        
        response = self.client.post(
            reverse('competitions:events:create_event'),
            data=event_data,
            follow=True
        )
        
        # Vérifier que la création a réussi
        self.assertEqual(response.status_code, 200)
        
        # Récupérer l'événement créé
        event = Event.objects.filter(title='Test Training Session').first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, 'Test Training Session')
        self.assertEqual(event.organization, self.organization)
        self.assertEqual(event.created_by, self.admin_user)
        
        # Déconnexion de l'admin
        self.client.logout()
        
        # 2. Login en tant qu'utilisateur régulier
        self.client.login(username='user', password='userpassword')
        
        # L'utilisateur consulte la page de détails de l'événement
        response = self.client.get(
            reverse('competitions:events:event_detail', kwargs={'event_id': event.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # L'utilisateur s'inscrit à l'événement
        registration_data = {
            'status': 'registered',
            'notes': 'Looking forward to this event!'
        }
        
        response = self.client.post(
            reverse('competitions:events:register_for_event', kwargs={'event_id': event.id}),
            data=registration_data,
            follow=True
        )
        
        # Vérifier que l'inscription a réussi
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'utilisateur est bien inscrit
        registration = EventParticipant.objects.filter(
            event=event,
            practitioner=self.user_practitioner
        ).first()
        
        self.assertIsNotNone(registration)
        self.assertEqual(registration.status, 'registered')
        self.assertEqual(registration.notes, 'Looking forward to this event!')
        
        # Déconnexion de l'utilisateur
        self.client.logout()
        
        # 3. L'admin se reconnecte pour consulter les participants
        self.client.login(username='admin', password='adminpassword')
        
        # L'admin consulte la liste des participants
        response = self.client.get(
            reverse('competitions:events:event_participants', kwargs={'event_id': event.id})
        )
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que l'utilisateur apparaît dans la liste des participants
        self.assertContains(response, self.user_practitioner.full_name)
        
        # Bonus: L'admin change le statut de l'inscription de l'utilisateur en "confirmé"
        response = self.client.post(
            reverse('competitions:events:edit_participant', kwargs={
                'event_id': event.id,
                'participant_id': registration.id
            }),
            data={
                'status': 'confirmed',
                'notes': 'Registration confirmed for testing'
            },
            follow=True
        )
        
        # Vérifier que la mise à jour a réussi
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le statut a bien été mis à jour
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'confirmed')
        self.assertEqual(registration.notes, 'Registration confirmed for testing')


class SurveyCreationAndResponseTest(TestCase):
    """Test d'intégration pour la création et réponse aux sondages."""
    
    def setUp(self):
        # Créer des utilisateurs
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        # Créer une organisation
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Ajouter l'admin comme membre de l'organisation
        OrganizationMember.objects.create(
            organization=self.organization,
            user=self.admin_user,
            role='admin'
        )
        
        # Créer un événement
        self.event = Event.objects.create(
            title='Event with Survey',
            description='An event with a survey',
            event_type='seminar',
            organization=self.organization,
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() - timedelta(days=1),
            start_time=datetime.now().time(),
            end_time=(datetime.now() + timedelta(hours=2)).time(),
            location='Test Location',
            created_by=self.admin_user
        )
        
        # Client pour les requêtes HTTP
        self.client = Client()
    
    def test_survey_creation_and_response_flow(self):
        """
        Test du flux complet de sondage :
        1. L'admin crée un sondage pour l'événement
        2. L'admin ajoute des questions au sondage
        3. Un utilisateur répond au sondage
        4. L'admin consulte les résultats
        """
        # 1. Login en tant qu'admin
        self.client.login(username='admin', password='adminpassword')
        
        # Créer un sondage pour l'événement
        survey_data = {
            'title': 'Event Feedback Survey',
            'description': 'Please provide your feedback on the event',
            'event': self.event.id,
            'is_anonymous': False,
            'is_active': True,
            'allow_multiple_submissions': False
        }
        
        response = self.client.post(
            reverse('competitions:events:surveys:create_event_survey', kwargs={'event_id': self.event.id}),
            data=survey_data,
            follow=True
        )
        
        # Vérifier que la création a réussi
        self.assertEqual(response.status_code, 200)
        
        # Récupérer le sondage créé
        survey = EventSurvey.objects.filter(title='Event Feedback Survey').first()
        self.assertIsNotNone(survey)
        self.assertEqual(survey.title, 'Event Feedback Survey')
        self.assertEqual(survey.event, self.event)
        self.assertEqual(survey.created_by, self.admin_user)
        
        # 2. Ajouter des questions au sondage
        questions_data = [
            {
                'question_text': 'How would you rate the event overall?',
                'question_type': 'rating',
                'is_required': True,
                'min_value': 1,
                'max_value': 5,
                'order': 1
            },
            {
                'question_text': 'What did you like most about the event?',
                'question_type': 'text',
                'is_required': True,
                'help_text': 'Please be specific',
                'order': 2
            },
            {
                'question_text': 'Would you attend a similar event in the future?',
                'question_type': 'single_choice',
                'is_required': True,
                'choices_text': 'Yes, definitely\nProbably\nNot sure\nProbably not\nNo, definitely not',
                'order': 3
            }
        ]
        
        # Construire les données du formulaire pour les questions
        formset_data = {
            'questions-TOTAL_FORMS': '3',
            'questions-INITIAL_FORMS': '0',
            'questions-MIN_NUM_FORMS': '1',
            'questions-MAX_NUM_FORMS': '1000',
        }
        
        for i, question in enumerate(questions_data):
            for key, value in question.items():
                formset_data[f'questions-{i}-{key}'] = value
            formset_data[f'questions-{i}-survey'] = survey.id
        
        response = self.client.post(
            reverse('competitions:events:surveys:edit_survey', kwargs={'survey_id': survey.id}),
            data=formset_data,
            follow=True
        )
        
        # Vérifier que l'ajout des questions a réussi
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que les questions ont bien été créées
        questions = SurveyQuestion.objects.filter(survey=survey).order_by('order')
        self.assertEqual(questions.count(), 3)
        self.assertEqual(questions[0].question_text, 'How would you rate the event overall?')
        self.assertEqual(questions[1].question_text, 'What did you like most about the event?')
        self.assertEqual(questions[2].question_text, 'Would you attend a similar event in the future?')
        
        # Déconnexion de l'admin
        self.client.logout()
        
        # 3. Login en tant qu'utilisateur régulier
        self.client.login(username='user', password='userpassword')
        
        # L'utilisateur consulte le sondage
        response = self.client.get(
            reverse('competitions:events:surveys:survey_detail', kwargs={'survey_id': survey.id})
        )
        self.assertEqual(response.status_code, 200)
        
        # L'utilisateur répond au sondage
        response_data = {
            'respondent_name': 'Regular User',
            'respondent_email': 'user@example.com',
            'is_anonymous': False,
            f'question_{questions[0].id}': '4',  # Rating question
            f'question_{questions[1].id}': 'The content was great and the instructor was knowledgeable.',  # Text question
            f'question_{questions[2].id}': 'Yes, definitely'  # Choice question
        }
        
        response = self.client.post(
            reverse('competitions:events:surveys:survey_detail', kwargs={'survey_id': survey.id}),
            data=response_data,
            follow=True
        )
        
        # Vérifier que la soumission a réussi
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que la réponse a bien été enregistrée
        survey_response = SurveyResponse.objects.filter(
            survey=survey,
            participant=self.regular_user
        ).first()
        
        self.assertIsNotNone(survey_response)
        self.assertFalse(survey_response.is_anonymous)
        
        # Vérifier les réponses aux questions
        question_responses = QuestionResponse.objects.filter(response=survey_response)
        self.assertEqual(question_responses.count(), 3)
        
        # Trouver la réponse à la question de notation
        rating_response = question_responses.filter(question=questions[0]).first()
        self.assertEqual(rating_response.numeric_response, 4)
        
        # Trouver la réponse à la question de texte
        text_response = question_responses.filter(question=questions[1]).first()
        self.assertEqual(text_response.text_response, 'The content was great and the instructor was knowledgeable.')
        
        # Trouver la réponse à la question à choix
        choice_response = question_responses.filter(question=questions[2]).first()
        self.assertEqual(choice_response.choice_response, ['Yes, definitely'])
        
        # Déconnexion de l'utilisateur
        self.client.logout()
        
        # 4. L'admin se reconnecte pour consulter les résultats
        self.client.login(username='admin', password='adminpassword')
        
        # L'admin consulte les résultats du sondage
        response = self.client.get(
            reverse('competitions:events:surveys:survey_results', kwargs={'survey_id': survey.id})
        )
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que les résultats incluent la réponse de l'utilisateur
        self.assertContains(response, 'Regular User')
        self.assertContains(response, '4')  # Rating value
        self.assertContains(response, 'The content was great')  # Part of text response
        self.assertContains(response, 'Yes, definitely')  # Choice response


class EventReminderServiceTest(TestCase):
    """Test d'intégration pour le service de rappels d'événements."""
    
    def setUp(self):
        # Créer des utilisateurs
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
        )
        
        self.participant1 = User.objects.create_user(
            username='participant1',
            email='participant1@example.com',
            password='password'
        )
        
        self.participant2 = User.objects.create_user(
            username='participant2',
            email='participant2@example.com',
            password='password'
        )
        
        # Créer une organisation
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Créer un événement
        self.future_event = Event.objects.create(
            title='Future Event',
            description='An event in the future',
            event_type='seminar',
            organization=self.organization,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=7),
            start_time=datetime.now().time(),
            end_time=(datetime.now() + timedelta(hours=2)).time(),
            location='Test Location',
            created_by=self.admin_user
        )
        
        # Inscrire les participants à l'événement
        p1 = Practitioner.objects.create(
            user=self.participant1,
            first_name='Participant',
            last_name='One',
            date_of_birth=date(1990, 1, 1),
            gender='M'
        )
        
        p2 = Practitioner.objects.create(
            user=self.participant2,
            first_name='Participant',
            last_name='Two',
            date_of_birth=date(1992, 5, 15),
            gender='F'
        )
        
        # Inscriptions
        EventParticipant.objects.create(
            event=self.future_event,
            practitioner=p1,
            registered_by=self.participant1,
            status='confirmed'
        )
        
        EventParticipant.objects.create(
            event=self.future_event,
            practitioner=p2,
            registered_by=self.participant2,
            status='registered'
        )
        
        # Client pour les requêtes HTTP
        self.client = Client()
    
    def test_reminder_creation_and_sending(self):
        """
        Test du flux de rappels d'événements :
        1. L'admin crée des rappels pour l'événement
        2. Vérification que les rappels sont correctement programmés
        3. Simulation de l'envoi des rappels dus
        """
        # 1. Login en tant qu'admin
        self.client.login(username='admin', password='adminpassword')
        
        # Créer un rappel à envoyer maintenant
        now_reminder_data = {
            'title': 'Test Reminder - Now',
            'message': 'This is a test reminder that should be sent immediately.',
            'reminder_type': 'email',
            'send_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'send_to': 'all'
        }
        
        response = self.client.post(
            reverse('competitions:events:planning:create_reminder', kwargs={'event_id': self.future_event.id}),
            data=now_reminder_data,
            follow=True
        )
        
        # Vérifier que la création a réussi
        self.assertEqual(response.status_code, 200)
        
        # Créer un rappel à envoyer juste avant l'événement
        pre_event_reminder_data = {
            'title': 'Test Reminder - Before Event',
            'message': 'This is a test reminder to be sent before the event.',
            'reminder_type': 'email',
            'time_before_event': '86400',  # 1 jour en secondes
            'send_to': 'confirmed'
        }
        
        response = self.client.post(
            reverse('competitions:events:planning:create_reminder', kwargs={'event_id': self.future_event.id}),
            data=pre_event_reminder_data,
            follow=True
        )
        
        # Vérifier que la création a réussi
        self.assertEqual(response.status_code, 200)
        
        # 2. Vérifier que les rappels ont été créés
        reminders = EventReminder.objects.filter(event=self.future_event)
        self.assertEqual(reminders.count(), 2)
        
        now_reminder = reminders.filter(title='Test Reminder - Now').first()
        pre_event_reminder = reminders.filter(title='Test Reminder - Before Event').first()
        
        self.assertIsNotNone(now_reminder)
        self.assertIsNotNone(pre_event_reminder)
        
        # Vérifier que le premier rappel est dû
        self.assertTrue(now_reminder.is_due)
        
        # Vérifier que le deuxième rappel n'est pas encore dû
        self.assertFalse(pre_event_reminder.is_due)
        
        # 3. Simuler l'envoi du rappel dû
        due_reminders = ReminderService.get_due_reminders()
        self.assertIn(now_reminder, due_reminders)
        self.assertNotIn(pre_event_reminder, due_reminders)
        
        # Envoyer le rappel dû
        result = ReminderService.send_reminder(now_reminder)
        
        # Vérifier que l'envoi a réussi
        self.assertTrue(result['success'])
        
        # Vérifier que le rappel a été marqué comme envoyé
        now_reminder.refresh_from_db()
        self.assertTrue(now_reminder.is_sent)
        self.assertIsNotNone(now_reminder.sent_at)
        
        # Vérifier les statistiques d'envoi
        self.assertEqual(result['delivery_status']['total'], 2)  # Les deux participants
        
        # 4. Tester l'envoi programmé
        # On simule que la date de l'événement est plus proche pour que le rappel soit dû
        with transaction.atomic():
            self.future_event.start_date = date.today() + timedelta(days=1)
            self.future_event.save()
            
            # Vérifier que le deuxième rappel est maintenant dû
            pre_event_reminder.refresh_from_db()
            self.assertTrue(pre_event_reminder.is_due)
            
            # Récupérer les rappels dus
            due_reminders = ReminderService.get_due_reminders()
            self.assertIn(pre_event_reminder, due_reminders)
            
            # Envoyer tous les rappels dus
            results = ReminderService.process_all_due_reminders()
            
            # Vérifier que l'envoi groupé a réussi
            self.assertEqual(results['total'], 1)
            self.assertEqual(results['successful'], 1)
            self.assertEqual(results['failed'], 0)
            
            # Vérifier que le rappel a été marqué comme envoyé
            pre_event_reminder.refresh_from_db()
            self.assertTrue(pre_event_reminder.is_sent)
            
            # Restaurer la date de l'événement
            self.future_event.start_date = date.today() + timedelta(days=7)
            self.future_event.save()