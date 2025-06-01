# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import connection, reset_queries
from django.conf import settings
from django.test.utils import override_settings

from competitions.models.event import Event, EventParticipant
from competitions.models.practitioners import Practitioner
from organizations.models import Organization, OrganizationMember

from datetime import timedelta, date
import time
import random
import string


def random_string(length=10):
    """Génère une chaîne aléatoire de caractères."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


@override_settings(DEBUG=True)  # Pour activer le suivi des requêtes SQL
class EventListingPerformanceTest(TestCase):
    """Tests de performance pour la liste des événements avec grande quantité de données."""
    
    def setUp(self):
        # Désactiver temporairement le cache pour les tests
        settings.CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        }
        
        # Créer un utilisateur administrateur
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True
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
        
        # Créer un utilisateur standard
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        # Créer un pratiquant pour l'utilisateur
        self.practitioner = Practitioner.objects.create(
            user=self.regular_user,
            first_name='Regular',
            last_name='User',
            date_of_birth=date(1990, 1, 1),
            gender='M'
        )
        
        # Client pour les requêtes HTTP
        self.client = Client()
    
    def test_event_list_performance_with_large_dataset(self):
        """
        Test de performance pour la liste des événements avec un grand nombre d'événements.
        Cette méthode mesure le temps d'exécution et le nombre de requêtes SQL.
        """
        # Nombre d'événements à créer pour le test
        num_events = 100
        
        # Créer les événements
        print(f"\nCréation de {num_events} événements pour le test de performance...")
        start_time = time.time()
        
        events = []
        for i in range(num_events):
            event_type = random.choice(['training', 'competition', 'seminar', 'meeting', 'social', 'other'])
            start_date = date.today() + timedelta(days=random.randint(-30, 30))
            end_date = start_date + timedelta(days=random.randint(0, 3))
            
            event = Event(
                title=f"Test Event {i+1} - {random_string(5)}",
                description=f"Description for test event {i+1}",
                event_type=event_type,
                organization=self.organization,
                start_date=start_date,
                end_date=end_date,
                location=f"Location {random_string(8)}",
                created_by=self.admin_user
            )
            events.append(event)
        
        # Utiliser bulk_create pour optimiser la création en masse
        Event.objects.bulk_create(events)
        
        creation_time = time.time() - start_time
        print(f"Création terminée en {creation_time:.2f} secondes")
        
        # Vérifier que tous les événements ont été créés
        self.assertEqual(Event.objects.count(), num_events)
        
        # Créer des inscriptions pour certains événements
        events = Event.objects.all()[:20]  # Prendre les 20 premiers événements
        
        participants = []
        for event in events:
            # Créer 5 inscriptions par événement
            for i in range(5):
                if i == 0:
                    # Inscrire l'utilisateur régulier au premier événement
                    participant = EventParticipant(
                        event=event,
                        practitioner=self.practitioner,
                        registered_by=self.regular_user,
                        status='confirmed'
                    )
                else:
                    # Créer un nouvel utilisateur et pratiquant pour chaque inscription
                    username = f"user_{random_string(8)}"
                    user = User.objects.create_user(
                        username=username,
                        email=f"{username}@example.com",
                        password="password"
                    )
                    
                    practitioner = Practitioner.objects.create(
                        user=user,
                        first_name=f"FirstName_{random_string(5)}",
                        last_name=f"LastName_{random_string(5)}",
                        date_of_birth=date(random.randint(1970, 2000), random.randint(1, 12), random.randint(1, 28)),
                        gender=random.choice(['M', 'F'])
                    )
                    
                    participant = EventParticipant(
                        event=event,
                        practitioner=practitioner,
                        registered_by=user,
                        status=random.choice(['registered', 'confirmed', 'waitlist'])
                    )
                
                participants.append(participant)
        
        # Utiliser bulk_create pour optimiser la création en masse
        EventParticipant.objects.bulk_create(participants)
        
        # Se connecter en tant qu'utilisateur régulier
        self.client.login(username='user', password='userpassword')
        
        # Mesurer les performances de la page de liste des événements
        reset_queries()  # Réinitialiser le compteur de requêtes
        
        print("\nTest de performance pour l'affichage de la liste des événements...")
        start_time = time.time()
        
        response = self.client.get(reverse('competitions:events:event_list'))
        
        execution_time = time.time() - start_time
        query_count = len(connection.queries)
        
        print(f"Temps d'exécution: {execution_time:.2f} secondes")
        print(f"Nombre de requêtes SQL: {query_count}")
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        # Analyser les requêtes pour identifier les optimisations possibles
        total_query_time = sum(float(q['time']) for q in connection.queries)
        print(f"Temps total des requêtes SQL: {total_query_time:.4f} secondes")
        
        # Lister les requêtes les plus lentes (top 5)
        sorted_queries = sorted(connection.queries, key=lambda q: float(q['time']), reverse=True)[:5]
        print("\nTop 5 des requêtes les plus lentes:")
        for i, query in enumerate(sorted_queries):
            print(f"{i+1}. {float(query['time']):.4f}s: {query['sql'][:100]}...")
        
        # Assertions pour les seuils de performance
        # Ces seuils peuvent être ajustés en fonction des attentes et du matériel
        self.assertLess(execution_time, 1.0, "La page met trop de temps à s'afficher")
        self.assertLess(query_count, 20, "Trop de requêtes SQL sont exécutées")
    
    def test_event_detail_performance(self):
        """
        Test de performance pour la vue détaillée d'un événement avec de nombreux participants.
        """
        # Créer un événement avec beaucoup de participants
        event = Event.objects.create(
            title="Large Event",
            description="An event with many participants",
            event_type='competition',
            organization=self.organization,
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=14),
            location="Test Venue",
            created_by=self.admin_user
        )
        
        # Nombre de participants à créer
        num_participants = 100
        
        print(f"\nCréation de {num_participants} participants pour le test de performance...")
        start_time = time.time()
        
        participants = []
        for i in range(num_participants):
            # Créer un nouvel utilisateur et pratiquant pour chaque inscription
            username = f"participant_{random_string(8)}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password="password"
            )
            
            practitioner = Practitioner.objects.create(
                user=user,
                first_name=f"FirstName_{random_string(5)}",
                last_name=f"LastName_{random_string(5)}",
                date_of_birth=date(random.randint(1970, 2000), random.randint(1, 12), random.randint(1, 28)),
                gender=random.choice(['M', 'F'])
            )
            
            participant = EventParticipant(
                event=event,
                practitioner=practitioner,
                registered_by=user,
                status=random.choice(['registered', 'confirmed', 'waitlist'])
            )
            
            participants.append(participant)
        
        # Utiliser bulk_create pour optimiser la création en masse
        EventParticipant.objects.bulk_create(participants)
        
        creation_time = time.time() - start_time
        print(f"Création terminée en {creation_time:.2f} secondes")
        
        # Vérifier que tous les participants ont été créés
        self.assertEqual(EventParticipant.objects.filter(event=event).count(), num_participants)
        
        # Se connecter en tant qu'administrateur
        self.client.login(username='admin', password='adminpassword')
        
        # Mesurer les performances de la page de détail de l'événement
        reset_queries()  # Réinitialiser le compteur de requêtes
        
        print("\nTest de performance pour l'affichage de la page détaillée de l'événement...")
        start_time = time.time()
        
        response = self.client.get(
            reverse('competitions:events:event_detail', kwargs={'event_id': event.id})
        )
        
        execution_time = time.time() - start_time
        query_count = len(connection.queries)
        
        print(f"Temps d'exécution: {execution_time:.2f} secondes")
        print(f"Nombre de requêtes SQL: {query_count}")
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        # Mesurer les performances de la page de gestion des participants
        reset_queries()  # Réinitialiser le compteur de requêtes
        
        print("\nTest de performance pour l'affichage de la liste des participants...")
        start_time = time.time()
        
        response = self.client.get(
            reverse('competitions:events:event_participants', kwargs={'event_id': event.id})
        )
        
        execution_time = time.time() - start_time
        query_count = len(connection.queries)
        
        print(f"Temps d'exécution: {execution_time:.2f} secondes")
        print(f"Nombre de requêtes SQL: {query_count}")
        
        # Vérifier que la page s'affiche correctement
        self.assertEqual(response.status_code, 200)
        
        # Assertions pour les seuils de performance
        self.assertLess(execution_time, 1.0, "La page des participants met trop de temps à s'afficher")
        self.assertLess(query_count, 10, "Trop de requêtes SQL sont exécutées pour la page des participants")