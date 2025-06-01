# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import IntegrityError

from competitions.models.event import Event, EventParticipant, EventSurvey, SurveyQuestion, SurveyResponse, QuestionResponse
from competitions.models.event_planning import EventPoll, PollOption, PollResponse
from competitions.models.practitioners import Practitioner
from organizations.models import Organization

from datetime import timedelta, date


class EventModelTest(TestCase):
    """Tests pour le modèle Event."""
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer une organisation pour les tests
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Créer un événement de base pour les tests
        self.event = Event.objects.create(
            title='Test Event',
            description='This is a test event',
            event_type='training',
            organization=self.organization,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            created_by=self.user
        )
    
    def test_event_creation(self):
        """Tester la création d'un événement."""
        self.assertEqual(self.event.title, 'Test Event')
        self.assertEqual(self.event.description, 'This is a test event')
        self.assertEqual(self.event.event_type, 'training')
        self.assertEqual(self.event.organization, self.organization)
        self.assertEqual(self.event.created_by, self.user)
    
    def test_event_string_representation(self):
        """Tester la représentation en chaîne de caractères d'un événement."""
        expected_string = f"{self.event.title} - {self.event.start_date}"
        self.assertEqual(str(self.event), expected_string)
    
    def test_is_upcoming_property(self):
        """Tester la propriété is_upcoming."""
        # Événement dans le futur
        future_event = Event.objects.create(
            title='Future Event',
            description='This is a future event',
            event_type='competition',
            organization=self.organization,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=8),
            created_by=self.user
        )
        self.assertTrue(future_event.is_upcoming)
        
        # Événement aujourd'hui
        today_event = Event.objects.create(
            title='Today Event',
            description='This is today\'s event',
            event_type='training',
            organization=self.organization,
            start_date=date.today(),
            end_date=date.today(),
            created_by=self.user
        )
        self.assertTrue(today_event.is_upcoming)
        
        # Événement passé
        past_event = Event.objects.create(
            title='Past Event',
            description='This is a past event',
            event_type='seminar',
            organization=self.organization,
            start_date=date.today() - timedelta(days=8),
            end_date=date.today() - timedelta(days=7),
            created_by=self.user
        )
        self.assertFalse(past_event.is_upcoming)
    
    def test_is_past_property(self):
        """Tester la propriété is_past."""
        # Événement passé
        past_event = Event.objects.create(
            title='Past Event',
            description='This is a past event',
            event_type='seminar',
            organization=self.organization,
            start_date=date.today() - timedelta(days=8),
            end_date=date.today() - timedelta(days=7),
            created_by=self.user
        )
        self.assertTrue(past_event.is_past)
        
        # Événement en cours
        current_event = Event.objects.create(
            title='Current Event',
            description='This is a current event',
            event_type='meeting',
            organization=self.organization,
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=1),
            created_by=self.user
        )
        self.assertFalse(current_event.is_past)
        
        # Événement futur
        future_event = Event.objects.create(
            title='Future Event',
            description='This is a future event',
            event_type='competition',
            organization=self.organization,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=8),
            created_by=self.user
        )
        self.assertFalse(future_event.is_past)
    
    def test_is_ongoing_property(self):
        """Tester la propriété is_ongoing."""
        # Événement en cours
        current_event = Event.objects.create(
            title='Current Event',
            description='This is a current event',
            event_type='meeting',
            organization=self.organization,
            start_date=date.today() - timedelta(days=1),
            end_date=date.today() + timedelta(days=1),
            created_by=self.user
        )
        self.assertTrue(current_event.is_ongoing)
        
        # Événement aujourd'hui
        today_event = Event.objects.create(
            title='Today Event',
            description='This is today\'s event',
            event_type='training',
            organization=self.organization,
            start_date=date.today(),
            end_date=date.today(),
            created_by=self.user
        )
        self.assertTrue(today_event.is_ongoing)
        
        # Événement passé
        past_event = Event.objects.create(
            title='Past Event',
            description='This is a past event',
            event_type='seminar',
            organization=self.organization,
            start_date=date.today() - timedelta(days=8),
            end_date=date.today() - timedelta(days=7),
            created_by=self.user
        )
        self.assertFalse(past_event.is_ongoing)
        
        # Événement futur
        future_event = Event.objects.create(
            title='Future Event',
            description='This is a future event',
            event_type='competition',
            organization=self.organization,
            start_date=date.today() + timedelta(days=7),
            end_date=date.today() + timedelta(days=8),
            created_by=self.user
        )
        self.assertFalse(future_event.is_ongoing)


class EventParticipantModelTest(TestCase):
    """Tests pour le modèle EventParticipant."""
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer une organisation pour les tests
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Créer un événement pour les tests
        self.event = Event.objects.create(
            title='Test Event',
            description='This is a test event',
            event_type='training',
            organization=self.organization,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            created_by=self.user
        )
        
        # Créer un pratiquant pour les tests
        self.practitioner = Practitioner.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            date_of_birth=date(1990, 1, 1),
            gender='M'
        )
    
    def test_event_participant_creation(self):
        """Tester la création d'un participant à un événement."""
        participant = EventParticipant.objects.create(
            event=self.event,
            practitioner=self.practitioner,
            registered_by=self.user,
            status='registered'
        )
        
        self.assertEqual(participant.event, self.event)
        self.assertEqual(participant.practitioner, self.practitioner)
        self.assertEqual(participant.registered_by, self.user)
        self.assertEqual(participant.status, 'registered')
        self.assertFalse(participant.attended)
    
    def test_event_participant_string_representation(self):
        """Tester la représentation en chaîne de caractères d'un participant."""
        participant = EventParticipant.objects.create(
            event=self.event,
            practitioner=self.practitioner,
            registered_by=self.user,
            status='registered'
        )
        
        expected_string = f"{self.practitioner.full_name} - {self.event.title}"
        self.assertEqual(str(participant), expected_string)
    
    def test_unique_participant_per_event(self):
        """Tester qu'un pratiquant ne peut s'inscrire qu'une seule fois à un événement."""
        # Première inscription - doit réussir
        EventParticipant.objects.create(
            event=self.event,
            practitioner=self.practitioner,
            registered_by=self.user,
            status='registered'
        )
        
        # Deuxième inscription - doit échouer avec IntegrityError
        with self.assertRaises(IntegrityError):
            EventParticipant.objects.create(
                event=self.event,
                practitioner=self.practitioner,
                registered_by=self.user,
                status='confirmed'
            )


class EventSurveyModelTest(TestCase):
    """Tests pour le modèle EventSurvey."""
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer une organisation pour les tests
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Créer un événement pour les tests
        self.event = Event.objects.create(
            title='Test Event',
            description='This is a test event',
            event_type='training',
            organization=self.organization,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            created_by=self.user
        )
        
        # Créer un sondage pour les tests
        self.survey = EventSurvey.objects.create(
            title='Test Survey',
            description='This is a test survey',
            event=self.event,
            is_anonymous=False,
            is_active=True,
            created_by=self.user
        )
    
    def test_event_survey_creation(self):
        """Tester la création d'un sondage d'événement."""
        self.assertEqual(self.survey.title, 'Test Survey')
        self.assertEqual(self.survey.description, 'This is a test survey')
        self.assertEqual(self.survey.event, self.event)
        self.assertFalse(self.survey.is_anonymous)
        self.assertTrue(self.survey.is_active)
        self.assertEqual(self.survey.created_by, self.user)
    
    def test_event_survey_string_representation(self):
        """Tester la représentation en chaîne de caractères d'un sondage."""
        expected_string = f"{self.survey.title} - {self.event.title}"
        self.assertEqual(str(self.survey), expected_string)
    
    def test_is_open_property_with_dates(self):
        """Tester la propriété is_open avec des dates définies."""
        now = timezone.now()
        
        # Sondage actif et dans la période de dates
        active_survey = EventSurvey.objects.create(
            title='Active Survey',
            description='This is an active survey',
            event=self.event,
            is_active=True,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            created_by=self.user
        )
        self.assertTrue(active_survey.is_open)
        
        # Sondage actif mais pas encore commencé
        future_survey = EventSurvey.objects.create(
            title='Future Survey',
            description='This is a future survey',
            event=self.event,
            is_active=True,
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=2),
            created_by=self.user
        )
        self.assertFalse(future_survey.is_open)
        
        # Sondage actif mais déjà terminé
        past_survey = EventSurvey.objects.create(
            title='Past Survey',
            description='This is a past survey',
            event=self.event,
            is_active=True,
            start_date=now - timedelta(days=2),
            end_date=now - timedelta(days=1),
            created_by=self.user
        )
        self.assertFalse(past_survey.is_open)
        
        # Sondage inactif même dans la période de dates
        inactive_survey = EventSurvey.objects.create(
            title='Inactive Survey',
            description='This is an inactive survey',
            event=self.event,
            is_active=False,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=1),
            created_by=self.user
        )
        self.assertFalse(inactive_survey.is_open)
    
    def test_is_open_property_without_dates(self):
        """Tester la propriété is_open sans dates définies."""
        # Sondage actif sans dates
        active_survey = EventSurvey.objects.create(
            title='Active Survey',
            description='This is an active survey',
            event=self.event,
            is_active=True,
            created_by=self.user
        )
        self.assertTrue(active_survey.is_open)
        
        # Sondage inactif sans dates
        inactive_survey = EventSurvey.objects.create(
            title='Inactive Survey',
            description='This is an inactive survey',
            event=self.event,
            is_active=False,
            created_by=self.user
        )
        self.assertFalse(inactive_survey.is_open)


class SurveyQuestionModelTest(TestCase):
    """Tests pour le modèle SurveyQuestion."""
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer une organisation pour les tests
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Créer un événement pour les tests
        self.event = Event.objects.create(
            title='Test Event',
            description='This is a test event',
            event_type='training',
            organization=self.organization,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            created_by=self.user
        )
        
        # Créer un sondage pour les tests
        self.survey = EventSurvey.objects.create(
            title='Test Survey',
            description='This is a test survey',
            event=self.event,
            is_anonymous=False,
            is_active=True,
            created_by=self.user
        )
    
    def test_survey_question_creation(self):
        """Tester la création d'une question de sondage."""
        # Question à texte
        text_question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='What did you think of the event?',
            question_type='text',
            is_required=True,
            help_text='Please provide your honest feedback',
            order=1
        )
        self.assertEqual(text_question.survey, self.survey)
        self.assertEqual(text_question.question_text, 'What did you think of the event?')
        self.assertEqual(text_question.question_type, 'text')
        self.assertTrue(text_question.is_required)
        self.assertEqual(text_question.help_text, 'Please provide your honest feedback')
        self.assertEqual(text_question.order, 1)
        
        # Question à choix unique
        single_choice_question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='How would you rate the event?',
            question_type='single_choice',
            is_required=True,
            choices=['Excellent', 'Good', 'Average', 'Poor', 'Very Poor'],
            order=2
        )
        self.assertEqual(single_choice_question.question_type, 'single_choice')
        self.assertEqual(single_choice_question.choices, ['Excellent', 'Good', 'Average', 'Poor', 'Very Poor'])
        
        # Question de notation
        rating_question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='Rate the event organization',
            question_type='rating',
            is_required=False,
            min_value=1,
            max_value=5,
            order=3
        )
        self.assertEqual(rating_question.question_type, 'rating')
        self.assertEqual(rating_question.min_value, 1)
        self.assertEqual(rating_question.max_value, 5)
    
    def test_survey_question_string_representation(self):
        """Tester la représentation en chaîne de caractères d'une question."""
        question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='What did you think of the event?',
            question_type='text',
            is_required=True,
            order=1
        )
        
        self.assertEqual(str(question), 'What did you think of the event?')
        
        # Test avec une question longue
        long_question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='This is a very long question that should be truncated in the string representation because it is over fifty characters long',
            question_type='text',
            is_required=True,
            order=2
        )
        
        expected_string = 'This is a very long question that should be truncate...'
        self.assertEqual(str(long_question), expected_string)


class SurveyResponseModelTest(TestCase):
    """Tests pour les modèles SurveyResponse et QuestionResponse."""
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer une organisation pour les tests
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
        
        # Créer un événement pour les tests
        self.event = Event.objects.create(
            title='Test Event',
            description='This is a test event',
            event_type='training',
            organization=self.organization,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            created_by=self.user
        )
        
        # Créer un sondage pour les tests
        self.survey = EventSurvey.objects.create(
            title='Test Survey',
            description='This is a test survey',
            event=self.event,
            is_anonymous=False,
            is_active=True,
            created_by=self.user
        )
        
        # Créer des questions pour les tests
        self.text_question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='What did you think of the event?',
            question_type='text',
            is_required=True,
            order=1
        )
        
        self.choice_question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='How would you rate the event?',
            question_type='single_choice',
            is_required=True,
            choices=['Excellent', 'Good', 'Average', 'Poor', 'Very Poor'],
            order=2
        )
        
        self.rating_question = SurveyQuestion.objects.create(
            survey=self.survey,
            question_text='Rate the event organization',
            question_type='rating',
            is_required=False,
            min_value=1,
            max_value=5,
            order=3
        )
    
    def test_survey_response_creation(self):
        """Tester la création d'une réponse de sondage."""
        # Réponse anonyme
        anonymous_response = SurveyResponse.objects.create(
            survey=self.survey,
            is_anonymous=True,
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(anonymous_response.survey, self.survey)
        self.assertTrue(anonymous_response.is_anonymous)
        self.assertEqual(anonymous_response.ip_address, '127.0.0.1')
        self.assertIsNone(anonymous_response.participant)
        
        # Réponse identifiée
        identified_response = SurveyResponse.objects.create(
            survey=self.survey,
            participant=self.user,
            is_anonymous=False,
            ip_address='127.0.0.2'
        )
        
        self.assertEqual(identified_response.survey, self.survey)
        self.assertFalse(identified_response.is_anonymous)
        self.assertEqual(identified_response.participant, self.user)
        
        # Réponse avec nom/email mais sans compte
        named_response = SurveyResponse.objects.create(
            survey=self.survey,
            respondent_name='John Doe',
            respondent_email='john@example.com',
            is_anonymous=False,
            ip_address='127.0.0.3'
        )
        
        self.assertEqual(named_response.respondent_name, 'John Doe')
        self.assertEqual(named_response.respondent_email, 'john@example.com')
    
    def test_survey_response_string_representation(self):
        """Tester la représentation en chaîne de caractères d'une réponse de sondage."""
        # Réponse anonyme
        anonymous_response = SurveyResponse.objects.create(
            survey=self.survey,
            is_anonymous=True
        )
        
        self.assertEqual(str(anonymous_response), f"Réponse anonyme - {self.survey.title}")
        
        # Réponse identifiée
        identified_response = SurveyResponse.objects.create(
            survey=self.survey,
            participant=self.user,
            is_anonymous=False
        )
        
        self.assertEqual(str(identified_response), f"Réponse de {self.user.get_full_name()} - {self.survey.title}")
        
        # Réponse avec nom mais sans compte
        named_response = SurveyResponse.objects.create(
            survey=self.survey,
            respondent_name='John Doe',
            is_anonymous=False
        )
        
        self.assertEqual(str(named_response), f"Réponse de John Doe - {self.survey.title}")
    
    def test_question_response_creation(self):
        """Tester la création de réponses aux questions."""
        # Créer une réponse de sondage
        response = SurveyResponse.objects.create(
            survey=self.survey,
            participant=self.user,
            is_anonymous=False
        )
        
        # Réponse textuelle
        text_response = QuestionResponse.objects.create(
            response=response,
            question=self.text_question,
            text_response="I really enjoyed the event. It was well organized and informative."
        )
        
        self.assertEqual(text_response.response, response)
        self.assertEqual(text_response.question, self.text_question)
        self.assertEqual(text_response.text_response, "I really enjoyed the event. It was well organized and informative.")
        
        # Réponse à choix
        choice_response = QuestionResponse.objects.create(
            response=response,
            question=self.choice_question,
            choice_response=["Excellent"]
        )
        
        self.assertEqual(choice_response.choice_response, ["Excellent"])
        
        # Réponse de notation
        rating_response = QuestionResponse.objects.create(
            response=response,
            question=self.rating_question,
            numeric_response=4
        )
        
        self.assertEqual(rating_response.numeric_response, 4)
    
    def test_question_response_string_representation(self):
        """Tester la représentation en chaîne de caractères d'une réponse à une question."""
        # Créer une réponse de sondage
        response = SurveyResponse.objects.create(
            survey=self.survey,
            participant=self.user,
            is_anonymous=False
        )
        
        # Réponse à une question
        question_response = QuestionResponse.objects.create(
            response=response,
            question=self.text_question,
            text_response="It was great!"
        )
        
        self.assertEqual(str(question_response), f"Réponse à {self.text_question}")


class EventPlanningIntegrationTest(TestCase):
    """Tests d'intégration pour les modèles liés à la planification d'événements."""
    
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer une organisation pour les tests
        self.organization = Organization.objects.create(
            name='Test Organization',
            code='TEST'
        )
    
    def test_event_creation_from_poll(self):
        """
        Tester le flux complet : création d'un sondage → votes → finalisation → création d'un événement.
        """
        # 1. Créer un sondage de planification
        poll = EventPoll.objects.create(
            title='Planning Poll',
            description='When should we hold the meeting?',
            organization=self.organization,
            status='active',
            created_by=self.user,
            event_type='meeting'
        )
        
        # 2. Ajouter des options de date
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)
        
        option1 = PollOption.objects.create(
            poll=poll,
            date=tomorrow,
            start_time=timezone.datetime.time(timezone.datetime(2000, 1, 1, 14, 0)),
            end_time=timezone.datetime.time(timezone.datetime(2000, 1, 1, 16, 0)),
            order=1
        )
        
        option2 = PollOption.objects.create(
            poll=poll,
            date=next_week,
            start_time=timezone.datetime.time(timezone.datetime(2000, 1, 1, 10, 0)),
            end_time=timezone.datetime.time(timezone.datetime(2000, 1, 1, 12, 0)),
            order=2
        )
        
        # 3. Créer quelques utilisateurs et leur faire voter
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='password')
        user3 = User.objects.create_user(username='user3', email='user3@example.com', password='password')
        
        # Votes pour la première option
        PollResponse.objects.create(option=option1, user=self.user, response='yes')
        PollResponse.objects.create(option=option1, user=user2, response='yes')
        PollResponse.objects.create(option=option1, user=user3, response='maybe')
        
        # Votes pour la deuxième option
        PollResponse.objects.create(option=option2, user=self.user, response='no')
        PollResponse.objects.create(option=option2, user=user2, response='maybe')
        PollResponse.objects.create(option=option2, user=user3, response='yes')
        
        # 4. Vérifier les scores
        self.assertEqual(option1.yes_count, 2)
        self.assertEqual(option1.maybe_count, 1)
        self.assertEqual(option1.no_count, 0)
        self.assertEqual(option1.score, 5)  # 2 yes (2 points chacun) + 1 maybe (1 point)
        
        self.assertEqual(option2.yes_count, 1)
        self.assertEqual(option2.maybe_count, 1)
        self.assertEqual(option2.no_count, 1)
        self.assertEqual(option2.score, 3)  # 1 yes (2 points) + 1 maybe (1 point) + 0 pour le no
        
        # 5. Finaliser le sondage avec l'option la plus populaire
        event = poll.finalize_with_option(option1)
        
        # 6. Vérifier que l'événement a été créé correctement
        self.assertIsNotNone(event)
        self.assertEqual(event.title, poll.title)
        self.assertEqual(event.description, poll.description)
        self.assertEqual(event.event_type, poll.event_type)
        self.assertEqual(event.organization, poll.organization)
        self.assertEqual(event.start_date, option1.date)
        self.assertEqual(event.end_date, option1.date)
        self.assertEqual(event.start_time, option1.start_time)
        self.assertEqual(event.end_time, option1.end_time)
        self.assertEqual(event.created_by, poll.created_by)
        
        # 7. Vérifier que le sondage a été correctement mis à jour
        poll.refresh_from_db()
        self.assertEqual(poll.status, 'finalized')
        self.assertIsNotNone(poll.finalized_at)
        self.assertEqual(poll.event, event)
        self.assertEqual(poll.selected_option, option1)
        
        # 8. Vérifier que l'option a été marquée comme sélectionnée
        option1.refresh_from_db()
        self.assertTrue(option1.is_selected)
        option2.refresh_from_db()
        self.assertFalse(option2.is_selected)