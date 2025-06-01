from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import (
    Practitioner, 
    CoachProfile, 
    DisciplineExpertise, 
    Discipline, 
    Federation, 
    UserProfile
)

class CoachMultiDisciplineTest(TestCase):
    def setUp(self):
        # Create test disciplines
        self.discipline1 = Discipline.objects.create(name="Karate", description="Japanese martial art")
        self.discipline2 = Discipline.objects.create(name="Judo", description="Japanese grappling martial art")
        self.discipline3 = Discipline.objects.create(name="Taekwondo", description="Korean martial art")
        
        # Create test federation
        self.federation = Federation.objects.create(name="World Karate Federation", country="International")
        
        # Create test user
        self.user = User.objects.create_user(
            username="testcoach", 
            email="testcoach@example.com",
            password="testpassword"
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role="coach"
        )
        
        # Create test practitioner
        self.practitioner = Practitioner.objects.create(
            user=self.user,
            first_name="Test",
            last_name="Coach",
            email="testcoach@example.com",
            primary_discipline=self.discipline1,
            is_coach=True
        )
        
        # Create coach profile
        self.coach_profile = CoachProfile.objects.create(
            practitioner=self.practitioner,
            profile_type="traditional",
            years_teaching=5,
            teaching_place_name="Test Dojo"
        )
        
        # Add expertise
        self.expertise1 = DisciplineExpertise.objects.create(
            coach_profile=self.coach_profile,
            discipline=self.discipline1,
            is_primary=True,
            level="advanced",
            years_experience=10,
            years_teaching=5,
            current_grade="3rd Dan",
            federation=self.federation
        )
        
        # Login client
        self.client = Client()
        self.client.login(username="testcoach", password="testpassword")
    
    def test_dashboard_view(self):
        """Test that the coach multi-discipline dashboard loads correctly"""
        response = self.client.get(reverse("dashboard:coach_multidiscipline"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "competitions/dashboard/coach_multidiscipline.html")
        self.assertContains(response, self.discipline1.name)
        
    def test_add_secondary_discipline(self):
        """Test adding a secondary discipline to the coach profile"""
        # Add a second discipline expertise
        expertise2 = DisciplineExpertise.objects.create(
            coach_profile=self.coach_profile,
            discipline=self.discipline2,
            is_primary=False,
            level="intermediate",
            years_experience=5,
            years_teaching=2,
            current_grade="1st Dan"
        )
        
        # Check that the dashboard displays both disciplines
        response = self.client.get(reverse("dashboard:coach_multidiscipline"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.discipline1.name)  # Primary discipline
        self.assertContains(response, self.discipline2.name)  # Secondary discipline
    
    def test_primary_discipline_restriction(self):
        """Test that only one discipline can be set as primary"""
        # Add a second discipline, also marked as primary
        expertise2 = DisciplineExpertise.objects.create(
            coach_profile=self.coach_profile,
            discipline=self.discipline2,
            is_primary=True,  # This should override the primary status of the first
            level="advanced",
            years_experience=8,
            years_teaching=4
        )
        
        # Refresh the first expertise from database
        self.expertise1.refresh_from_db()
        
        # Check that the first expertise is no longer primary
        self.assertFalse(self.expertise1.is_primary)
        self.assertTrue(expertise2.is_primary)
    
    def test_coach_onboarding(self):
        """Test the coach onboarding process with multiple disciplines"""
        # Create a new user for onboarding
        new_user = User.objects.create_user(
            username="newcoach", 
            email="newcoach@example.com",
            password="newpassword"
        )
        UserProfile.objects.create(
            user=new_user,
            role="user",  # Will be updated to coach
            onboarding_completed=False
        )
        
        # Login with the new user
        self.client.login(username="newcoach", password="newpassword")
        
        # Submit the onboarding form with multi-discipline data
        response = self.client.post(reverse("onboarding:coach_simplified"), {
            'first_name': 'New',
            'last_name': 'Coach',
            'email': 'newcoach@example.com',
            'phone': '1234567890',
            'profile_type': 'multidisciplinary',
            'years_teaching': '7',
            'teaching_place_name': 'Multi-Arts Academy',
            'primary_discipline': str(self.discipline1.id),
            'current_grade': '4th Dan',
            'teaching_certification': 'Master Instructor',
            'secondary_disciplines': [str(self.discipline2.id), str(self.discipline3.id)],
            'available_for_seminars': 'on',
            'available_for_private_lessons': 'on'
        })
        
        # Check redirection to dashboard
        self.assertRedirects(response, reverse("dashboard:index"))
        
        # Verify the coach profile was created with the primary discipline
        new_profile = UserProfile.objects.get(user=new_user)
        self.assertEqual(new_profile.role, "coach")
        self.assertTrue(new_profile.onboarding_completed)
        
        # Verify the practitioner record
        new_practitioner = Practitioner.objects.get(user=new_user)
        self.assertEqual(new_practitioner.primary_discipline, self.discipline1)
        self.assertTrue(new_practitioner.is_coach)
        
        # Verify the coach profile record
        new_coach = CoachProfile.objects.get(practitioner=new_practitioner)
        self.assertEqual(new_coach.profile_type, "multidisciplinary")
        self.assertEqual(new_coach.years_teaching, 7)
        
        # Verify the discipline expertise records
        expertise_records = DisciplineExpertise.objects.filter(coach_profile=new_coach)
        self.assertEqual(expertise_records.count(), 3)  # Primary + 2 secondary
        
        # Verify primary discipline expertise
        primary_expertise = expertise_records.get(is_primary=True)
        self.assertEqual(primary_expertise.discipline, self.discipline1)
        self.assertEqual(primary_expertise.current_grade, "4th Dan")
        
        # Verify secondary disciplines were added
        secondary_disciplines = [e.discipline for e in expertise_records.filter(is_primary=False)]
        self.assertIn(self.discipline2, secondary_disciplines)
        self.assertIn(self.discipline3, secondary_disciplines)