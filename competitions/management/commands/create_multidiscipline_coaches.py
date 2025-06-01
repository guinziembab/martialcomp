import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from competitions.models import (
    Practitioner, 
    CoachProfile, 
    DisciplineExpertise, 
    Discipline,
    UserProfile,
    Federation
)

class Command(BaseCommand):
    help = 'Creates sample multi-discipline coaches for testing and demonstration'
    
    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of coaches to create')
        
    @transaction.atomic
    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create disciplines
        disciplines = list(Discipline.objects.all())
        if not disciplines:
            self.stdout.write('No disciplines found. Creating sample disciplines...')
            disciplines = self._create_sample_disciplines()
        
        # Get or create federations
        federations = list(Federation.objects.all())
        if not federations:
            self.stdout.write('No federations found. Creating sample federations...')
            federations = self._create_sample_federations()
        
        # Create the coaches
        for i in range(count):
            self._create_coach(i, disciplines, federations)
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} multi-discipline coaches'))
    
    def _create_sample_disciplines(self):
        """Create a variety of martial arts disciplines"""
        disciplines_data = [
            {'name': 'Karate', 'description': 'Japanese martial art focusing on striking techniques'},
            {'name': 'Judo', 'description': 'Japanese martial art focusing on throws and grappling'},
            {'name': 'Taekwondo', 'description': 'Korean martial art emphasizing high kicks and striking'},
            {'name': 'Brazilian Jiu-Jitsu', 'description': 'Ground-based grappling martial art'},
            {'name': 'Kung Fu', 'description': 'Chinese martial arts systems'},
            {'name': 'Muay Thai', 'description': 'Thai boxing using the eight limbs'},
            {'name': 'Boxing', 'description': 'Western combat sport focused on punching'},
            {'name': 'Wrestling', 'description': 'Grappling sport with various styles'},
            {'name': 'Aikido', 'description': 'Japanese martial art focusing on redirecting energy'},
            {'name': 'Capoeira', 'description': 'Brazilian martial art combining dance, acrobatics, and music'}
        ]
        
        created_disciplines = []
        for data in disciplines_data:
            discipline, created = Discipline.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            created_disciplines.append(discipline)
            if created:
                self.stdout.write(f'Created discipline: {discipline.name}')
                
        return created_disciplines
    
    def _create_sample_federations(self):
        """Create sample federations"""
        federation_data = [
            {'name': 'World Karate Federation', 'country': 'International'},
            {'name': 'International Judo Federation', 'country': 'International'},
            {'name': 'World Taekwondo Federation', 'country': 'International'},
            {'name': 'International Brazilian Jiu-Jitsu Federation', 'country': 'International'},
            {'name': 'World Kung Fu Federation', 'country': 'China'},
            {'name': 'World Muaythai Council', 'country': 'Thailand'},
            {'name': 'International Boxing Association', 'country': 'International'},
            {'name': 'United World Wrestling', 'country': 'International'},
            {'name': 'International Aikido Federation', 'country': 'Japan'},
            {'name': 'World Capoeira Federation', 'country': 'Brazil'}
        ]
        
        created_federations = []
        for data in federation_data:
            federation, created = Federation.objects.get_or_create(
                name=data['name'],
                defaults={'country': data['country']}
            )
            created_federations.append(federation)
            if created:
                self.stdout.write(f'Created federation: {federation.name}')
                
        return created_federations
    
    def _create_coach(self, index, disciplines, federations):
        """Create a multi-discipline coach with associated profiles"""
        # Random data for variety
        first_names = ['Jean', 'Marie', 'Pierre', 'Sophie', 'Thomas', 'Laura', 'Michel', 'Claire', 'Jacques', 'Anne']
        last_names = ['Martin', 'Bernard', 'Dubois', 'Thomas', 'Robert', 'Richard', 'Petit', 'Durand', 'Leroy', 'Moreau']
        profile_types = ['traditional', 'competitive', 'wellness', 'children', 'master', 'multidisciplinary']
        expertise_levels = ['beginner', 'intermediate', 'advanced', 'expert', 'master']
        
        # Select 2-4 disciplines
        num_disciplines = random.randint(2, min(4, len(disciplines)))
        selected_disciplines = random.sample(disciplines, num_disciplines)
        
        # Create user
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"coach_{first_name.lower()}{last_name.lower()}_{index}"
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'User {username} already exists. Skipping.')
            return
        
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="password123",
            first_name=first_name,
            last_name=last_name
        )
        
        # Create user profile
        user_profile = UserProfile.objects.create(
            user=user,
            role="coach",
            onboarding_completed=True
        )
        
        # Choose primary discipline
        primary_discipline = selected_disciplines[0]
        
        # Create practitioner
        practitioner = Practitioner.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            email=f"{username}@example.com",
            phone=f"0{random.randint(100000000, 999999999)}",
            primary_discipline=primary_discipline,
            is_coach=True
        )
        
        # Create coach profile
        years_teaching = random.randint(3, 20)
        coach_profile = CoachProfile.objects.create(
            practitioner=practitioner,
            profile_type=random.choice(profile_types),
            years_teaching=years_teaching,
            teaching_place_name=f"{first_name}'s Martial Arts Academy",
            teaching_philosophy=f"My philosophy is to help students develop physically, mentally, and spiritually through martial arts training.",
            available_for_seminars=random.choice([True, True, False]),
            available_for_private_lessons=random.choice([True, True, False]),
            available_for_online_coaching=random.choice([True, False]),
            hourly_rate_range=f"{random.randint(30, 60)}-{random.randint(70, 100)}€"
        )
        
        # Create expertise for each discipline
        for i, discipline in enumerate(selected_disciplines):
            is_primary = (i == 0)  # First discipline is primary
            years_experience = years_teaching + random.randint(0, 10)
            discipline_years_teaching = years_teaching if is_primary else random.randint(1, years_teaching)
            
            # Select a federation related to this discipline if possible
            matching_federations = [f for f in federations if discipline.name in f.name]
            federation = random.choice(matching_federations) if matching_federations else random.choice(federations)
            
            expertise = DisciplineExpertise.objects.create(
                coach_profile=coach_profile,
                discipline=discipline,
                is_primary=is_primary,
                level=random.choice(expertise_levels),
                years_experience=years_experience,
                years_teaching=discipline_years_teaching,
                current_grade=f"{random.randint(1, 5)}ème Dan" if random.random() > 0.2 else "Expert",
                teaching_certification=random.choice(["Instructeur Fédéral", "DEJEPS", "BEES", "Master Coach", ""]),
                federation=federation,
                public_description=f"Experienced in {discipline.name} with {years_experience} years of practice."
            )
        
        self.stdout.write(f'Created multi-discipline coach: {first_name} {last_name} with {num_disciplines} disciplines')