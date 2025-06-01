"""
Tests complets pour l'application grades
À exécuter avec: python manage.py test grades
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from competitions.models import Discipline, Practitioner, Club
from grades.models import (
    Grade, 
    GradeCategory, 
    PractitionerGrade, 
    GradeRequirement,
    GradeExam, 
    GradeExamRegistration
)

import datetime
import json


class GradeModelTestCase(TestCase):
    """Tests pour le modèle Grade"""
    
    def setUp(self):
        # Créer une discipline
        self.discipline = Discipline.objects.create(
            name="Karaté",
            description="Art martial japonais",
            country_origin="Japon",
            is_active=True
        )
        
        # Créer une catégorie de grade
        self.category = GradeCategory.objects.create(
            name="Débutant",
            description="Grades débutants",
            discipline=self.discipline,
            order=1,
            is_active=True
        )
        
        # Créer un grade
        self.grade = Grade.objects.create(
            name="Ceinture Jaune",
            discipline=self.discipline,
            category=self.category,
            color="Jaune",
            color_code="#FFFF00",
            level=2,
            min_age=8,
            min_time_in_previous_grade=6,
            requirements="Maîtrise des positions de base",
            is_active=True,
            is_dan_grade=False
        )
        
        # Créer un autre grade (grade précédent)
        self.previous_grade = Grade.objects.create(
            name="Ceinture Blanche",
            discipline=self.discipline,
            category=self.category,
            color="Blanche",
            color_code="#FFFFFF",
            level=1,
            min_age=6,
            min_time_in_previous_grade=0,
            is_active=True,
            is_dan_grade=False
        )
        
        # Créer un grade suivant
        self.next_grade = Grade.objects.create(
            name="Ceinture Orange",
            discipline=self.discipline,
            category=self.category,
            color="Orange",
            color_code="#FFA500",
            level=3,
            min_age=9,
            min_time_in_previous_grade=6,
            is_active=True,
            is_dan_grade=False
        )
    
    def test_grade_creation(self):
        """Tester la création d'un grade"""
        self.assertEqual(self.grade.name, "Ceinture Jaune")
        self.assertEqual(self.grade.discipline, self.discipline)
        self.assertEqual(self.grade.category, self.category)
        self.assertEqual(self.grade.level, 2)
        self.assertEqual(self.grade.min_age, 8)
        self.assertEqual(self.grade.min_time_in_previous_grade, 6)
        self.assertTrue(self.grade.is_active)
        self.assertFalse(self.grade.is_dan_grade)
    
    def test_grade_string_representation(self):
        """Tester la représentation en chaîne d'un grade"""
        self.assertEqual(str(self.grade), f"Ceinture Jaune ({self.discipline.name})")
    
    def test_is_black_belt_property(self):
        """Tester la propriété is_black_belt"""
        self.assertFalse(self.grade.is_black_belt)
        
        # Créer un grade ceinture noire
        black_belt = Grade.objects.create(
            name="Ceinture Noire 1er Dan",
            discipline=self.discipline,
            color="Noire",
            color_code="#000000",
            level=10,
            min_age=16,
            min_time_in_previous_grade=12,
            is_active=True,
            is_dan_grade=True
        )
        
        self.assertTrue(black_belt.is_black_belt)
    
    def test_next_grade_property(self):
        """Tester la propriété next_grade"""
        self.assertEqual(self.grade.next_grade, self.next_grade)
        self.assertIsNone(self.next_grade.next_grade)  # Pas de grade suivant
    
    def test_previous_grade_property(self):
        """Tester la propriété previous_grade"""
        self.assertEqual(self.grade.previous_grade, self.previous_grade)
        self.assertIsNone(self.previous_grade.previous_grade)  # Pas de grade précédent


class PractitionerGradeModelTestCase(TestCase):
    """Tests pour le modèle PractitionerGrade"""
    
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer un club
        self.club = Club.objects.create(
            name="Club de Test",
            city="Test City"
        )
        
        # Créer une discipline
        self.discipline = Discipline.objects.create(
            name="Karaté",
            description="Art martial japonais",
            country_origin="Japon",
            is_active=True
        )
        
        # Créer un grade
        self.grade = Grade.objects.create(
            name="Ceinture Jaune",
            discipline=self.discipline,
            color="Jaune",
            color_code="#FFFF00",
            level=2,
            min_age=8,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        # Créer un pratiquant
        self.practitioner = Practitioner.objects.create(
            first_name="John",
            last_name="Doe",
            birth_date=timezone.now().date() - datetime.timedelta(days=365*15),  # 15 ans
            grade="Ceinture Jaune",
            club=self.club,
            user=self.user
        )
        
        # Ajouter la discipline au pratiquant
        self.practitioner.disciplines.add(self.discipline)
        
        # Créer un grade attribué au pratiquant
        self.practitioner_grade = PractitionerGrade.objects.create(
            practitioner=self.practitioner,
            grade=self.grade,
            discipline=self.discipline,
            date_obtained=timezone.now().date() - datetime.timedelta(days=180),  # 6 mois
            awarded_by="Sensei Test",
            location="Dojo Test",
            certificate_number="123456",
            notes="Très bon passage de grade",
            is_current=True
        )
    
    def test_practitioner_grade_creation(self):
        """Tester la création d'un grade de pratiquant"""
        self.assertEqual(self.practitioner_grade.practitioner, self.practitioner)
        self.assertEqual(self.practitioner_grade.grade, self.grade)
        self.assertEqual(self.practitioner_grade.discipline, self.discipline)
        self.assertEqual(self.practitioner_grade.awarded_by, "Sensei Test")
        self.assertTrue(self.practitioner_grade.is_current)
    
    def test_practitioner_grade_string_representation(self):
        """Tester la représentation en chaîne d'un grade de pratiquant"""
        expected = f"{self.practitioner.full_name} - {self.grade.name} ({self.discipline.name}) - {self.practitioner_grade.date_obtained}"
        self.assertEqual(str(self.practitioner_grade), expected)
    
    def test_is_current_auto_update(self):
        """Tester que is_current est automatiquement mis à jour"""
        # Créer un autre grade
        new_grade = Grade.objects.create(
            name="Ceinture Orange",
            discipline=self.discipline,
            color="Orange",
            color_code="#FFA500",
            level=3,
            min_age=9,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        # Attribuer le nouveau grade au pratiquant
        new_practitioner_grade = PractitionerGrade.objects.create(
            practitioner=self.practitioner,
            grade=new_grade,
            discipline=self.discipline,
            date_obtained=timezone.now().date(),
            is_current=True
        )
        
        # Vérifier que l'ancien grade n'est plus courant
        self.practitioner_grade.refresh_from_db()
        self.assertFalse(self.practitioner_grade.is_current)
        self.assertTrue(new_practitioner_grade.is_current)


class GradeViewsTestCase(TestCase):
    """Tests pour les vues de l'application grades"""
    
    def setUp(self):
        # Créer un utilisateur d'administrateur
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True,
            is_superuser=True
        )
        
        # Créer un utilisateur normal
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='userpassword'
        )
        
        # Créer un utilisateur responsable de club
        self.club_manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='managerpassword'
        )
        
        # Créer un club
        self.club = Club.objects.create(
            name="Club de Test",
            city="Test City",
            owner=self.club_manager
        )
        
        # Créer une discipline
        self.discipline = Discipline.objects.create(
            name="Karaté",
            description="Art martial japonais",
            country_origin="Japon",
            is_active=True
        )
        
        # Créer une catégorie de grade
        self.category = GradeCategory.objects.create(
            name="Débutant",
            description="Grades débutants",
            discipline=self.discipline,
            order=1,
            is_active=True
        )
        
        # Créer un grade
        self.grade = Grade.objects.create(
            name="Ceinture Jaune",
            discipline=self.discipline,
            category=self.category,
            color="Jaune",
            color_code="#FFFF00",
            level=2,
            min_age=8,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        # Créer un pratiquant
        self.practitioner = Practitioner.objects.create(
            first_name="John",
            last_name="Doe",
            birth_date=timezone.now().date() - datetime.timedelta(days=365*15),  # 15 ans
            grade="Ceinture Jaune",
            club=self.club,
            user=self.normal_user
        )
        
        # Ajouter la discipline au pratiquant
        self.practitioner.disciplines.add(self.discipline)
        
        # Créer un grade attribué au pratiquant
        self.practitioner_grade = PractitionerGrade.objects.create(
            practitioner=self.practitioner,
            grade=self.grade,
            discipline=self.discipline,
            date_obtained=timezone.now().date() - datetime.timedelta(days=180),  # 6 mois
            awarded_by="Sensei Test",
            location="Dojo Test",
            certificate_number="123456",
            notes="Très bon passage de grade",
            is_current=True
        )
        
        # Client pour les requêtes
        self.client = Client()
    
    def test_grade_list_view(self):
        """Tester la vue de liste des grades"""
        # Se connecter en tant qu'admin
        self.client.login(username='admin', password='adminpassword')
        
        # Accéder à la liste des grades
        url = reverse('grades:grade_list')
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grades/grade_list.html')
        self.assertContains(response, "Ceinture Jaune")
        self.assertContains(response, "Karaté")
    
    def test_grade_detail_view(self):
        """Tester la vue de détail d'un grade"""
        # Se connecter en tant qu'admin
        self.client.login(username='admin', password='adminpassword')
        
        # Accéder au détail d'un grade
        url = reverse('grades:grade_detail', kwargs={'pk': self.grade.pk})
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grades/grade_detail.html')
        self.assertContains(response, "Ceinture Jaune")
        self.assertContains(response, "Karaté")
    
    def test_grade_create_view(self):
        """Tester la vue de création d'un grade"""
        # Se connecter en tant qu'admin
        self.client.login(username='admin', password='adminpassword')
        
        # Accéder au formulaire de création
        url = reverse('grades:grade_create')
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grades/grade_form.html')
        
        # Créer un nouveau grade
        data = {
            'name': 'Ceinture Verte',
            'discipline': self.discipline.pk,
            'category': self.category.pk,
            'color': 'Verte',
            'color_code': '#008000',
            'level': 4,
            'min_age': 10,
            'min_time_in_previous_grade': 6,
            'is_active': True,
            'is_dan_grade': False
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Vérifier la redirection et la création du grade
        self.assertRedirects(response, reverse('grades:grade_list'))
        self.assertTrue(Grade.objects.filter(name='Ceinture Verte').exists())
    
    def test_practitioner_grades_view(self):
        """Tester la vue des grades d'un pratiquant"""
        # Se connecter en tant que responsable de club
        self.client.login(username='manager', password='managerpassword')
        
        # Accéder aux grades d'un pratiquant
        url = reverse('grades:practitioner_grades', kwargs={'practitioner_id': self.practitioner.pk})
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grades/practitioner_grades.html')
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Ceinture Jaune")
    
    def test_add_practitioner_grade_view(self):
        """Tester l'ajout d'un grade à un pratiquant"""
        # Se connecter en tant que responsable de club
        self.client.login(username='manager', password='managerpassword')
        
        # Créer un nouveau grade
        orange_grade = Grade.objects.create(
            name="Ceinture Orange",
            discipline=self.discipline,
            category=self.category,
            color="Orange",
            color_code="#FFA500",
            level=3,
            min_age=9,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        # Accéder au formulaire d'ajout de grade
        url = reverse('grades:add_practitioner_grade', kwargs={'practitioner_id': self.practitioner.pk})
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grades/assign_grade.html')
        
        # Ajouter un nouveau grade au pratiquant
        data = {
            'grade': orange_grade.pk,
            'discipline': self.discipline.pk,
            'date_obtained': timezone.now().date().isoformat(),
            'awarded_by': 'Sensei Master',
            'location': 'Dojo Central',
            'is_current': True
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Vérifier la redirection et l'ajout du grade
        self.assertRedirects(response, reverse('grades:practitioner_grades', kwargs={'practitioner_id': self.practitioner.pk}))
        self.assertTrue(PractitionerGrade.objects.filter(practitioner=self.practitioner, grade=orange_grade).exists())
        
        # Vérifier que l'ancien grade n'est plus courant
        self.practitioner_grade.refresh_from_db()
        self.assertFalse(self.practitioner_grade.is_current)


class GradeAPITestCase(TestCase):
    """Tests pour les API AJAX de l'application grades"""
    
    def setUp(self):
        # Créer un utilisateur
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Créer un club
        self.club = Club.objects.create(
            name="Club de Test",
            city="Test City",
            owner=self.user
        )
        
        # Créer deux disciplines
        self.karate = Discipline.objects.create(
            name="Karaté",
            description="Art martial japonais",
            country_origin="Japon",
            is_active=True
        )
        
        self.judo = Discipline.objects.create(
            name="Judo",
            description="Art martial japonais",
            country_origin="Japon",
            is_active=True
        )
        
        # Créer des grades pour le karaté
        self.white_belt_karate = Grade.objects.create(
            name="Ceinture Blanche",
            discipline=self.karate,
            color="Blanche",
            color_code="#FFFFFF",
            level=1,
            min_age=6,
            is_active=True
        )
        
        self.yellow_belt_karate = Grade.objects.create(
            name="Ceinture Jaune",
            discipline=self.karate,
            color="Jaune",
            color_code="#FFFF00",
            level=2,
            min_age=8,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        # Créer des grades pour le judo
        self.white_belt_judo = Grade.objects.create(
            name="Ceinture Blanche",
            discipline=self.judo,
            color="Blanche",
            color_code="#FFFFFF",
            level=1,
            min_age=6,
            is_active=True
        )
        
        self.yellow_belt_judo = Grade.objects.create(
            name="Ceinture Jaune",
            discipline=self.judo,
            color="Jaune",
            color_code="#FFFF00",
            level=2,
            min_age=8,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        # Créer des pratiquants
        self.practitioner1 = Practitioner.objects.create(
            first_name="John",
            last_name="Doe",
            birth_date=timezone.now().date() - datetime.timedelta(days=365*10),  # 10 ans
            grade="Ceinture Blanche",
            club=self.club
        )
        
        self.practitioner2 = Practitioner.objects.create(
            first_name="Jane",
            last_name="Smith",
            birth_date=timezone.now().date() - datetime.timedelta(days=365*8),  # 8 ans
            grade="Ceinture Blanche",
            club=self.club
        )
        
        # Client pour les requêtes
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')
    
    def test_get_grades_by_discipline(self):
        """Tester l'API pour récupérer les grades par discipline"""
        url = reverse('grades:get_grades_by_discipline')
        response = self.client.get(url, {'discipline_id': self.karate.pk})
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('grades', data)
        self.assertEqual(len(data['grades']), 2)  # 2 grades de karaté
        
        # Vérifier les noms des grades
        grade_names = [grade['name'] for grade in data['grades']]
        self.assertIn('Ceinture Blanche', grade_names)
        self.assertIn('Ceinture Jaune', grade_names)
    
    def test_get_eligible_practitioners(self):
        """Tester l'API pour récupérer les pratiquants éligibles"""
        url = reverse('grades:get_eligible_practitioners')
        response = self.client.get(url, {
            'grade_id': self.yellow_belt_karate.pk,
            'club_id': self.club.pk
        })
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertIn('practitioners', data)
        
        # Seul le pratiquant de 10 ans devrait être éligible (âge minimum 8 ans)
        eligible_ids = [p['id'] for p in data['practitioners']]
        self.assertIn(self.practitioner1.pk, eligible_ids)
        self.assertIn(self.practitioner2.pk, eligible_ids)  # 8 ans = éligible


class GradeIntegrationTestCase(TestCase):
    """Tests d'intégration pour l'application grades"""
    
    def setUp(self):
        # Créer un utilisateur responsable de club
        self.club_manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='managerpassword'
        )
        
        # Créer un club
        self.club = Club.objects.create(
            name="Club de Test",
            city="Test City",
            owner=self.club_manager
        )
        
        # Créer une discipline
        self.discipline = Discipline.objects.create(
            name="Karaté",
            description="Art martial japonais",
            country_origin="Japon",
            is_active=True
        )
        
        # Associer la discipline au club
        self.club.disciplines.add(self.discipline)
        
        # Créer une catégorie de grade
        self.category = GradeCategory.objects.create(
            name="Débutant",
            description="Grades débutants",
            discipline=self.discipline,
            order=1,
            is_active=True
        )
        
        # Créer des grades
        self.white_belt = Grade.objects.create(
            name="Ceinture Blanche",
            discipline=self.discipline,
            category=self.category,
            color="Blanche",
            color_code="#FFFFFF",
            level=1,
            min_age=6,
            is_active=True
        )
        
        self.yellow_belt = Grade.objects.create(
            name="Ceinture Jaune",
            discipline=self.discipline,
            category=self.category,
            color="Jaune",
            color_code="#FFFF00",
            level=2,
            min_age=8,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        self.orange_belt = Grade.objects.create(
            name="Ceinture Orange",
            discipline=self.discipline,
            category=self.category,
            color="Orange",
            color_code="#FFA500",
            level=3,
            min_age=9,
            min_time_in_previous_grade=6,
            is_active=True
        )
        
        # Créer des pratiquants
        self.practitioner1 = Practitioner.objects.create(
            first_name="John",
            last_name="Doe",
            birth_date=timezone.now().date() - datetime.timedelta(days=365*10),  # 10 ans
            grade="Ceinture Blanche",
            club=self.club
        )
        
        self.practitioner2 = Practitioner.objects.create(
            first_name="Jane",
            last_name="Smith",
            birth_date=timezone.now().date() - datetime.timedelta(days=365*8),  # 8 ans
            grade="Ceinture Blanche",
            club=self.club
        )
        
        # Associer la discipline aux pratiquants
        self.practitioner1.disciplines.add(self.discipline)
        self.practitioner2.disciplines.add(self.discipline)
        
        # Créer un grade attribué au pratiquant 1
        self.practitioner1_grade = PractitionerGrade.objects.create(
            practitioner=self.practitioner1,
            grade=self.white_belt,
            discipline=self.discipline,
            date_obtained=timezone.now().date() - datetime.timedelta(days=365),  # 1 an
            is_current=True
        )
        
        # Client pour les requêtes
        self.client = Client()
        self.client.login(username='manager', password='managerpassword')
    
    def test_full_grade_progression(self):
        """Tester une progression complète des grades pour un pratiquant"""
        # 1. Attribuer le grade ceinture jaune au pratiquant 1
        url = reverse('grades:add_practitioner_grade', kwargs={'practitioner_id': self.practitioner1.pk})
        data = {
            'grade': self.yellow_belt.pk,
            'discipline': self.discipline.pk,
            'date_obtained': timezone.now().date().isoformat(),
            'awarded_by': 'Sensei Master',
            'location': 'Dojo Central',
            'is_current': True
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Vérifier que le grade a été attribué
        self.assertRedirects(response, reverse('grades:practitioner_grades', kwargs={'practitioner_id': self.practitioner1.pk}))
        self.assertTrue(PractitionerGrade.objects.filter(practitioner=self.practitioner1, grade=self.yellow_belt).exists())
        
        # Vérifier que l'ancien grade n'est plus courant
        self.practitioner1_grade.refresh_from_db()
        self.assertFalse(self.practitioner1_grade.is_current)
        
        # 2. Créer un examen de passage de grade
        exam_date = timezone.now().date() + datetime.timedelta(days=30)
        exam = GradeExam.objects.create(
            title="Examen de passage de grade",
            description="Passage de grade pour ceinture orange",
            date=exam_date,
            location="Dojo Central",
            discipline=self.discipline,
            max_participants=20,
            registration_deadline=timezone.now().date() + datetime.timedelta(days=15),
            examiners="Sensei Master",
            status='scheduled'
        )
        
        # Ajouter les grades disponibles
        exam.available_grades.add(self.orange_belt)
        
        # 3. Inscrire le pratiquant à l'examen
        url = reverse('grades:register_for_exam', kwargs={'exam_id': exam.pk})
        data = {
            'practitioner': self.practitioner1.pk,
            'target_grade': self.orange_belt.pk,
            'payment_confirmed': True
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Vérifier que l'inscription a été créée
        self.assertRedirects(response, reverse('grades:exam_detail', kwargs={'pk': exam.pk}))
        self.assertTrue(GradeExamRegistration.objects.filter(practitioner=self.practitioner1, exam=exam).exists())
        
        # 4. Mettre à jour le statut de l'inscription
        registration = GradeExamRegistration.objects.get(practitioner=self.practitioner1, exam=exam)
        url = reverse('grades:update_exam_registration_status', kwargs={'registration_id': registration.pk})
        data = {
            'status': 'passed'
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Vérifier que le statut a été mis à jour
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'passed')
        
        # Vérifier que le grade a été attribué automatiquement
        self.assertTrue(PractitionerGrade.objects.filter(
            practitioner=self.practitioner1,
            grade=self.orange_belt,
            is_current=True
        ).exists())
        
        # Vérifier que le précédent grade n'est plus courant
        yellow_belt_grade = PractitionerGrade.objects.get(practitioner=self.practitioner1, grade=self.yellow_belt)
        self.assertFalse(yellow_belt_grade.is_current)
        
        # 5. Vérifier l'historique des grades du pratiquant
        url = reverse('grades:practitioner_grades', kwargs={'practitioner_id': self.practitioner1.pk})
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ceinture Blanche")
        self.assertContains(response, "Ceinture Jaune")
        self.assertContains(response, "Ceinture Orange")


class GradeRequirementTestCase(TestCase):
    """Tests pour les exigences de grade"""
    
    def setUp(self):
        # Créer une discipline
        self.discipline = Discipline.objects.create(
            name="Karaté",
            description="Art martial japonais",
            country_origin="Japon",
            is_active=True
        )
        
        # Créer un grade
        self.grade = Grade.objects.create(
            name="Ceinture Noire 1er Dan",
            discipline=self.discipline,
            color="Noire",
            color_code="#000000",
            level=10,
            min_age=16,
            min_time_in_previous_grade=12,
            is_active=True,
            is_dan_grade=True
        )
        
        # Créer une exigence de grade
        self.requirement = GradeRequirement.objects.create(
            grade=self.grade,
            name="Kata avancé",
            description="Maîtrise d'un kata avancé",
            is_mandatory=True,
            min_age=16,
            min_time_in_previous_grade=12,
            required_points=10,
            order=1
        )
        
        # Client pour les requêtes
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            is_staff=True,
            is_superuser=True
        )
        self.client.login(username='admin', password='adminpassword')
    
    def test_requirement_creation(self):
        """Tester la création d'une exigence de grade"""
        self.assertEqual(self.requirement.name, "Kata avancé")
        self.assertEqual(self.requirement.grade, self.grade)
        self.assertTrue(self.requirement.is_mandatory)
        self.assertEqual(self.requirement.required_points, 10)
    
    def test_requirement_string_representation(self):
        """Tester la représentation en chaîne d'une exigence de grade"""
        expected = f"Kata avancé ({self.grade.name})"
        self.assertEqual(str(self.requirement), expected)
    
    def test_requirement_list_view(self):
        """Tester la vue de liste des exigences de grade"""
        url = reverse('grades:requirement_list')
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kata avancé")
    
    def test_requirement_create_view(self):
        """Tester la vue de création d'une exigence de grade"""
        url = reverse('grades:requirement_create')
        response = self.client.get(url)
        
        # Vérifier la réponse
        self.assertEqual(response.status_code, 200)
        
        # Créer une nouvelle exigence
        data = {
            'grade': self.grade.pk,
            'name': 'Combat libre',
            'description': 'Démonstration de combat libre',
            'is_mandatory': True,
            'min_age': 16,
            'min_time_in_previous_grade': 12,
            'required_points': 8,
            'order': 2
        }
        
        response = self.client.post(url, data, follow=True)
        
        # Vérifier la redirection et la création de l'exigence
        self.assertRedirects(response, reverse('grades:grade_detail', kwargs={'pk': self.grade.pk}))
        self.assertTrue(GradeRequirement.objects.filter(name='Combat libre').exists())