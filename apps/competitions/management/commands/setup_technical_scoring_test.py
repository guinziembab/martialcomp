# -*- coding: utf-8 -*-
"""
Script de création d'environnement de test pour le système de notation technique MartialComp
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal

try:
    from apps.organizations.models import Organization, OrganizationMember, OrganizationType
    from apps.competitions.models import (
        Federation, Club, Discipline, Practitioner, Competition, 
        CompetitionCategory, CompetitionType, CompetitionRegistration
    )
    from apps.grades.models import Grade, GradeCategory
    from apps.competitions.models.technical_scoring import (
        ScoringCriterion, Performance, Score
    )
    from apps.competitions.models.judges import Judge, JudgeAssignment
except ImportError as e:
    print(f"Erreur d'importation: {e}")


class Command(BaseCommand):
    help = 'Crée un environnement de test complet pour la notation technique'
    
    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', 
                          help='Supprime les données de test existantes avant création')
        parser.add_argument('--verbose', action='store_true', 
                          help='Affichage détaillé des opérations')
    
    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        
        if options.get('reset'):
            self.cleanup_test_data()
        
        self.stdout.write(self.style.SUCCESS('🏆 CRÉATION ENVIRONNEMENT TEST NOTATION TECHNIQUE'))
        self.stdout.write('=' * 70)
        
        # Étapes de création
        try:
            # Désactiver temporairement les signaux pour éviter les erreurs de sous-domaines
            from django.db.models.signals import post_save
            from django.dispatch import receiver
            from apps.competitions.signals import create_organization_tenant_and_qr
            from apps.organizations.models import Organization
            
            # Déconnecter le signal temporairement
            post_save.disconnect(create_organization_tenant_and_qr, sender=Organization)
            
            try:
                self.federation = self.create_federation()
                self.discipline = self.create_discipline()
                self.clubs = self.create_clubs()
                self.grade_categories = self.create_grade_system()
                self.judges = self.create_judges()
                self.practitioners = self.create_practitioners()
                self.competition = self.create_competition()
                self.categories = self.create_competition_categories()
                self.configure_scoring_system()
                self.register_participants()
                self.assign_judges()
                self.create_performances()
                
                # Lancer les tests automatiques
                self.run_scoring_simulation()
                
            finally:
                # Reconnecter le signal
                post_save.connect(create_organization_tenant_and_qr, sender=Organization)
            
            self.stdout.write(self.style.SUCCESS('\n🎯 ENVIRONNEMENT TEST CRÉÉ AVEC SUCCÈS'))
            self.print_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erreur lors de la création: {e}'))
            import traceback
            traceback.print_exc()
    
    def cleanup_test_data(self):
        """Nettoie les données de test existantes."""
        self.log('🧹 Nettoyage des données de test...')
        
        try:
            # Supprimer dans l'ordre inverse des dépendances
            Performance.objects.filter(category__competition__title__icontains='Test').delete()
            Score.objects.filter(performance__category__competition__title__icontains='Test').delete()
            JudgeAssignment.objects.filter(category__competition__title__icontains='Test').delete()
            CompetitionRegistration.objects.filter(competition__title__icontains='Test').delete()
            Competition.objects.filter(title__icontains='Test').delete()
            Judge.objects.filter(user__username__startswith='judge_test_').delete()
            Judge.objects.filter(user__username__startswith='test_').delete()
            Practitioner.objects.filter(first_name__startswith='Pratiquant').delete()
            Practitioner.objects.filter(user__username__startswith='judge_test_').delete()
            Practitioner.objects.filter(user__username__startswith='test_').delete()
            Club.objects.filter(name__icontains='Club Test').delete()
            Organization.objects.filter(name__icontains='Club Test').delete()
            Organization.objects.filter(name__icontains='Compétition Test').delete()
            Federation.objects.filter(name__icontains='Fédération Test').delete()
            User.objects.filter(username__startswith='test_').delete()
            User.objects.filter(username__startswith='judge_test_').delete()
            
            # Supprimer les grades de test
            from apps.grades.models import Grade, GradeCategory
            Grade.objects.filter(discipline__name__icontains='Test').delete()
            GradeCategory.objects.filter(discipline__name__icontains='Test').delete()
            
            # Supprimer les disciplines de test
            from apps.competitions.models import Discipline
            Discipline.objects.filter(name__icontains='Test').delete()
            
            self.log('  ✅ Données de test supprimées')
        except Exception as e:
            self.log(f'  ⚠️ Erreur lors du nettoyage: {e}')
    
    def create_federation(self):
        """Crée la fédération de test."""
        self.log('🏛️  Création de la fédération...')
        
        # Créer l'utilisateur président
        president_user, created = User.objects.get_or_create(
            username='test_president_federation',
            defaults={
                'email': 'president@federation-test.com',
                'first_name': 'Jean',
                'last_name': 'Président'
            }
        )
        if created:
            president_user.set_password('testpass123')
            president_user.save()
        
        federation = Federation.objects.create(
            name='Fédération Test Arts Martiaux',
            description='Fédération créée pour les tests de notation technique',
            owner=president_user,
            contact_email='contact@federation-test.com',
            is_active=True
        )
        
        self.log(f'  ✅ Fédération créée: {federation.name}')
        return federation
    
    def create_discipline(self):
        """Crée la discipline de test."""
        self.log('🥋 Création de la discipline...')
        
        discipline = Discipline.objects.create(
            name='Karaté Technique Test',
            description='Discipline pour tests de notation technique',
            is_active=True
        )
        
        self.federation.disciplines.add(discipline)
        
        self.log(f'  ✅ Discipline créée: {discipline.name}')
        return discipline
    
    def create_clubs(self):
        """Crée les 3 clubs de test."""
        self.log('🏢 Création des clubs...')
        
        clubs = []
        club_names = ['Dojo du Levant', 'Club des Guerriers', 'École du Dragon']
        
        for i, club_name in enumerate(club_names, 1):
            # Créer l'utilisateur responsable du club
            owner_user, created = User.objects.get_or_create(
                username=f'test_owner_club_{i}',
                defaults={
                    'email': f'owner.club{i}@test.com',
                    'first_name': 'Responsable',
                    'last_name': f'Club{i}'
                }
            )
            if created:
                owner_user.set_password('testpass123')
                owner_user.save()
            
            # Créer l'organisation pour le club
            organization = Organization.objects.create(
                name=f'Organisation Club Test {club_name}',
                short_name=f'OCT{i}',
                organization_type=OrganizationType.CLUB,
                description=f'Organisation pour le club de test {club_name}',
                created_by=owner_user,
                is_active=True
            )
            
            club = Club.objects.create(
                name=f'Club Test {club_name}',
                description=f'Club de test numéro {i}',
                owner=owner_user,
                organization=organization,
                contact_email=f'contact.club{i}@test.com',
                city=f'Ville{i}',
                is_active=True
            )
            
            club.disciplines.add(self.discipline)
            clubs.append(club)
            
            self.log(f'  ✅ Club créé: {club.name}')
        
        return clubs
    
    def create_grade_system(self):
        """Crée le système de grades."""
        self.log('🎖️  Création du système de grades...')
        
        # Créer les catégories de grades
        categories = []
        for i, cat_name in enumerate(['Kyu', 'Dan'], 1):
            category = GradeCategory.objects.create(
                name=cat_name,
                discipline=self.discipline,
                order=i
            )
            categories.append(category)
            self.log(f'  ✅ Catégorie de grade: {cat_name}')
        
        # Créer les grades
        grades = []
        
        # Grades Kyu (ceintures colorées)
        kyu_grades = [
            ('6ème Kyu - Ceinture Blanche', 1, '#FFFFFF'),
            ('5ème Kyu - Ceinture Jaune', 2, '#FFFF00'),
            ('4ème Kyu - Ceinture Orange', 3, '#FFA500'),
            ('3ème Kyu - Ceinture Verte', 4, '#00FF00'),
            ('2ème Kyu - Ceinture Bleue', 5, '#0000FF'),
            ('1er Kyu - Ceinture Marron', 6, '#8B4513'),
        ]
        
        for grade_name, level, color in kyu_grades:
            grade = Grade.objects.create(
                name=grade_name,
                discipline=self.discipline,
                category=categories[0],  # Kyu
                level=level,
                color_code=color,
                min_age=12,
                is_active=True
            )
            grades.append(grade)
        
        # Grades Dan (ceintures noires)
        dan_grades = [
            ('1er Dan - Ceinture Noire', 7, '#000000'),
            ('2ème Dan - Ceinture Noire', 8, '#000000'),
            ('3ème Dan - Ceinture Noire', 9, '#000000'),
        ]
        
        for grade_name, level, color in dan_grades:
            grade = Grade.objects.create(
                name=grade_name,
                discipline=self.discipline,
                category=categories[1],  # Dan
                level=level,
                color_code=color,
                min_age=16,
                is_active=True,
                is_dan_grade=True
            )
            grades.append(grade)
        
        self.log(f'  ✅ {len(grades)} grades créés')
        return categories
    
    def create_judges(self):
        """Crée 2 juges par club (6 juges total)."""
        self.log('👨‍⚖️ Création des juges techniques...')
        
        judges = []
        for i, club in enumerate(self.clubs, 1):
            for j in range(1, 3):  # 2 juges par club
                # Créer l'utilisateur juge
                user, created = User.objects.get_or_create(
                    username=f'judge_test_club{i}_{j}',
                    defaults={
                        'email': f'juge{j}.club{i}@test.com',
                        'first_name': f'Juge{j}',
                        'last_name': f'Club{i}'
                    }
                )
                if created:
                    user.set_password('testpass123')
                    user.save()
                
                # Créer le pratiquant associé
                practitioner, created = Practitioner.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'birth_date': timezone.now().date() - timedelta(days=365*30),  # 30 ans
                        'email': user.email,
                        'organization': club.organization,
                        'grade': Grade.objects.filter(level__gte=7).first(),  # Au moins 1er Dan
                        'is_active': True
                    }
                )
                
                # Créer le juge technique
                judge, created = Judge.objects.get_or_create(
                    user=user,
                    defaults={
                        'practitioner': practitioner,
                        'certification_number': f'JT{i:02d}{j:02d}2024',
                        'active': True,
                        'is_technical_judge': True
                    }
                )
                judges.append(judge)
                
                self.log(f'  ✅ Juge créé: {judge.practitioner.full_name} ({club.name})')
        
        return judges
    
    def create_practitioners(self):
        """Crée 5 pratiquants de différents grades."""
        self.log('🥷 Création des pratiquants compétiteurs...')
        
        practitioners = []
        grades = Grade.objects.filter(discipline=self.discipline).order_by('level')
        
        practitioner_data = [
            ('Pratiquant', 'Alpha', 'alpha@test.com', 20),
            ('Pratiquant', 'Beta', 'beta@test.com', 22),
            ('Pratiquant', 'Gamma', 'gamma@test.com', 19),
            ('Pratiquant', 'Delta', 'delta@test.com', 25),
            ('Pratiquant', 'Epsilon', 'epsilon@test.com', 21),
        ]
        
        for i, (first_name, last_name, email, age) in enumerate(practitioner_data):
            # Répartir les pratiquants dans les clubs
            club = self.clubs[i % len(self.clubs)]
            
            # Créer l'utilisateur
            user, created = User.objects.get_or_create(
                username=f'test_practitioner_{i+1}',
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
            
            # Sélectionner un grade aléatoire
            grade = random.choice(grades)
            
            # Créer le pratiquant
            practitioner, created = Practitioner.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'birth_date': timezone.now().date() - timedelta(days=365*age),
                    'email': email,
                    'organization': club.organization,
                    'grade': grade,
                    'is_active': True
                }
            )
            
            practitioners.append(practitioner)
            self.log(f'  ✅ Pratiquant créé: {practitioner.full_name} - {grade.name} ({club.name})')
        
        return practitioners
    
    def create_competition(self):
        """Crée la compétition de test."""
        self.log('🏆 Création de la compétition...')
        
        # Créer une organisation pour la compétition
        competition_org = Organization.objects.create(
            name='Organisation Compétition Test',
            short_name='OCT',
            organization_type=OrganizationType.CLUB,
            description='Organisation pour la compétition de test',
            created_by=User.objects.get(username='test_president_federation'),
            is_active=True
        )
        
        competition = Competition.objects.create(
            title='Compétition Test Notation Technique 2024',
            description='Compétition de test pour valider le système de notation technique',
            organizing_organization=competition_org,
            start_date=timezone.now().date() + timedelta(days=7),
            end_date=timezone.now().date() + timedelta(days=7),
            registration_deadline=timezone.now().date() + timedelta(days=5),
            venue_name='Centre Test MartialComp',
            max_participants=50,
            status='published',
            is_published=True
        )
        
        competition.discipline = self.discipline
        competition.save()
        
        self.log(f'  ✅ Compétition créée: {competition.title}')
        return competition
    
    def create_competition_categories(self):
        """Crée 2 catégories de compétition."""
        self.log('📋 Création des catégories...')
        
        # Créer le type de compétition technique
        comp_type, created = CompetitionType.objects.get_or_create(
            name='Technique Kata',
            discipline=self.discipline,
            defaults={
                'description': 'Compétition technique de kata'
            }
        )
        
        categories = []
        
        # Catégorie 1: Jeunes (Kyu)
        category1 = CompetitionCategory.objects.create(
            name='Kata Jeunes (Kyu)',
            competition=self.competition,
            competition_type=comp_type,
            min_age=16,
            max_age=25,
            min_grade='6ème Kyu',
            max_grade='1er Kyu',
            max_participants=10
        )
        categories.append(category1)
        
        # Catégorie 2: Experts (Dan)
        category2 = CompetitionCategory.objects.create(
            name='Kata Experts (Dan)',
            competition=self.competition,
            competition_type=comp_type,
            min_age=18,
            max_age=50,
            min_grade='1er Dan',
            max_grade='3ème Dan',
            max_participants=10
        )
        categories.append(category2)
        
        for category in categories:
            self.log(f'  ✅ Catégorie créée: {category.name}')
        
        return categories
    
    def configure_scoring_system(self):
        """Configure le système de notation pour chaque catégorie."""
        self.log('⚙️  Configuration du système de notation...')
        
        for category in self.categories:
            # Critères de notation
            criteria_data = [
                ('Technique', 'Qualité technique des mouvements', 3.0, 1),
                ('Puissance', 'Puissance et impact des techniques', 2.5, 2),
                ('Stabilité', 'Équilibre et stabilité', 2.0, 3),
                ('Rythme', 'Respect du rythme et timing', 1.5, 4),
                ('Expression', 'Expression martiale et regard', 1.0, 5),
            ]
            
            for name, description, weight, order in criteria_data:
                ScoringCriterion.objects.create(
                    name=name,
                    description=description,
                    weight=weight,
                    min_score=4.0,
                    max_score=7.0,
                    step=0.25,
                    category=category,
                    order=order,
                    is_active=True
                )
            
            self.log(f'  ✅ Configuration créée pour: {category.name}')
    
    def register_participants(self):
        """Inscrit les pratiquants aux catégories appropriées."""
        self.log('📝 Inscription des participants...')
        
        for practitioner in self.practitioners:
            # Déterminer la catégorie appropriée selon le grade
            if practitioner.grade.level <= 6:  # Kyu
                category = self.categories[0]  # Jeunes
            else:  # Dan
                category = self.categories[1]  # Experts
            
            # Créer l'inscription
            registration = CompetitionRegistration.objects.create(
                practitioner=practitioner,
                competition=self.competition,
                is_competitor=True,
                status='approved'
            )
            
            registration.categories.add(category)
            
            self.log(f'  ✅ {practitioner.full_name} inscrit en {category.name}')
    
    def assign_judges(self):
        """Affecte les juges aux catégories."""
        self.log('👨‍⚖️ Affectation des juges...')
        
        # Répartir les juges équitablement
        judges_per_category = 3  # 3 juges par catégorie
        
        for i, category in enumerate(self.categories):
            # Sélectionner 3 juges pour cette catégorie
            start_idx = i * judges_per_category
            category_judges = self.judges[start_idx:start_idx + judges_per_category]
            
            for judge in category_judges:
                # Créer l'inscription du juge
                registration = CompetitionRegistration.objects.create(
                    practitioner=judge.practitioner,
                    competition=self.competition,
                    is_technical_judge=True,
                    status='approved'
                )
                
                # Créer l'affectation
                assignment = JudgeAssignment.objects.create(
                    registration=registration,
                    category=category,
                    assignment_type='technical_judge',
                    status='confirmed',
                    start_time=timezone.now()
                )
                
                self.log(f'  ✅ {judge.practitioner.full_name} affecté à {category.name}')
    
    def create_performances(self):
        """Crée les performances à évaluer."""
        self.log('🎭 Création des performances...')
        
        for category in self.categories:
            # Récupérer les pratiquants de cette catégorie
            registrations = CompetitionRegistration.objects.filter(
                competition=self.competition,
                categories=category,
                is_competitor=True
            )
            
            for order, registration in enumerate(registrations, 1):
                performance = Performance.objects.create(
                    practitioner=registration.practitioner,
                    category=category,
                    status='ready',
                    scheduled_time=timezone.now() + timedelta(hours=order),
                    order=order
                )
                
                self.log(f'  ✅ Performance créée: {performance.practitioner.full_name} (ordre {order})')
    
    def run_scoring_simulation(self):
        """Simule le processus de notation complet."""
        self.log('🎯 SIMULATION DU PROCESSUS DE NOTATION')
        self.log('-' * 50)
        
        for category in self.categories:
            self.log(f'\n🏷️  Notation catégorie: {category.name}')
            
            # Récupérer les performances et les juges
            performances = Performance.objects.filter(category=category).order_by('order')
            assignments = JudgeAssignment.objects.filter(category=category, status='confirmed')
            criteria = ScoringCriterion.objects.filter(category=category, is_active=True)
            
            for performance in performances:
                self.log(f'\n  🎭 Performance: {performance.practitioner.full_name}')
                
                # Chaque juge note selon tous les critères
                for assignment in assignments:
                    # Récupérer le juge depuis l'inscription
                    judge = Judge.objects.get(practitioner=assignment.registration.practitioner)
                    
                    # Simuler des notes réalistes (entre 4.0 et 7.0)
                    for criterion in criteria:
                        # Générer une note réaliste avec variation selon le critère
                        base_score = random.uniform(5.0, 6.5)
                        
                        # Variation selon le critère (certains juges préfèrent certains aspects)
                        if criterion.name == 'Technique':
                            base_score += random.uniform(-0.5, 0.5)
                        elif criterion.name == 'Puissance':
                            base_score += random.uniform(-0.3, 0.7)
                        
                        # Arrondir selon le pas de notation (0.25)
                        score_value = round(base_score * 4) / 4
                        score_value = max(4.0, min(7.0, score_value))  # Borner entre 4 et 7
                        
                        # Créer le score
                        Score.objects.create(
                            performance=performance,
                            judge=judge,
                            criterion=criterion,
                            value=score_value,
                            comments=f'Note simulée pour test'
                        )
                        
                        self.log(f'    {judge.practitioner.full_name}: {criterion.name} = {score_value}')
                
                # Calculer le score total de la performance
                total_score = performance.calculate_total_score()
                performance.total_score = total_score
                performance.status = 'completed'
                performance.completion_time = timezone.now()
                performance.save()
                
                self.log(f'    💯 Score total: {total_score:.2f}')
            
            # Calculer les classements
            self.calculate_rankings(category)
    
    def calculate_rankings(self, category):
        """Calcule et affiche les classements d'une catégorie."""
        self.log(f'\n🏆 CLASSEMENT - {category.name}')
        
        performances = Performance.objects.filter(
            category=category, 
            status='completed'
        ).order_by('-total_score')
        
        for rank, performance in enumerate(performances, 1):
            performance.ranking = rank
            performance.save()
            
            self.log(f'  {rank}. {performance.practitioner.full_name} - {performance.total_score:.2f} pts')
    
    def print_summary(self):
        """Affiche un résumé de l'environnement créé."""
        self.log('\n📊 RÉSUMÉ DE L\'ENVIRONNEMENT TEST')
        self.log('=' * 50)
        
        self.log(f'🏛️  Fédération: {self.federation.name}')
        self.log(f'🏢 Clubs: {len(self.clubs)}')
        self.log(f'👨‍⚖️ Juges: {len(self.judges)}')
        self.log(f'🥷 Pratiquants: {len(self.practitioners)}')
        self.log(f'🏆 Compétition: {self.competition.title}')
        self.log(f'📋 Catégories: {len(self.categories)}')
        
        # Statistiques de notation
        total_scores = Score.objects.filter(
            performance__category__in=self.categories
        ).count()
        self.log(f'🎯 Scores générés: {total_scores}')
        
        # Afficher les classements finaux
        for category in self.categories:
            self.log(f'\n🏆 PODIUM - {category.name}')
            performances = Performance.objects.filter(
                category=category,
                ranking__isnull=False
            ).order_by('ranking')[:3]
            
            for performance in performances:
                medal = ['🥇', '🥈', '🥉'][performance.ranking - 1]
                self.log(f'  {medal} {performance.practitioner.full_name} - {performance.total_score:.2f} pts')
        
        # Instructions de test manuel
        self.log('\n🔧 PROCHAINES ÉTAPES DE TEST MANUEL')
        self.log('-' * 40)
        self.log('1. Accéder au dashboard juge avec les comptes créés')
        self.log('2. Tester la modification de scores (si autorisée)')
        self.log('3. Vérifier l\'affichage temps réel des résultats')
        self.log('4. Tester l\'export des résultats')
        self.log('5. Valider la segmentation entre organisations')
        
        # Informations de connexion
        self.log('\n🔑 COMPTES DE TEST CRÉÉS')
        self.log('-' * 30)
        self.log('📧 Format email: juge{N}.club{C}@test.com')
        self.log('🔐 Mot de passe: testpass123')
        self.log('👤 Usernames: judge_test_club{C}_{N}')
    
    def log(self, message):
        """Affiche un message si le mode verbose est activé."""
        if self.verbose:
            self.stdout.write(message)
        else:
            self.stdout.write(message)  # Pour cette directive, toujours afficher