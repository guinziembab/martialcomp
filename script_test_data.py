# script_test_data.py

import os
import sys
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

# Configurer le chemin pour trouver le module settings
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Définir le module settings correct
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialisation de Django
try:
    django.setup()
    print("Django initialisé avec succès!")
except Exception as e:
    print(f"ERREUR lors de l'initialisation de Django: {e}")
    sys.exit(1)

# Imports après l'initialisation
from competitions.models import (
    Federation, Club, Discipline, Practitioner, UserProfile, 
    FederationAdministrator, ClubAdministrator, Judge, JudgeQualification,
    Grade  # Ajout de l'import manquant
)
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

print("Début de la création des données de test...")

# Fonction pour générer un email unique
def generate_email(name, domain="testmail.com"):
    timestamp = int(datetime.now().timestamp())
    return f"{slugify(name)}_{timestamp}@{domain}"

# Fonction pour générer une date de naissance aléatoire
def random_birth_date(min_age=7, max_age=17):
    today = timezone.now().date()
    days = random.randint(min_age * 365, max_age * 365)
    return today - timedelta(days=days)

# Fonction pour créer un utilisateur unique avec profil
def create_user(username, email, role, password="Test1234!"):
    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        print(f"Utilisateur {username} existe déjà, réutilisation.")
    else:
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=username.split('_')[0] if '_' in username else username,
            last_name='Test'
        )
        print(f"Utilisateur {username} créé.")
    
    # S'assurer que le profil existe avec le bon rôle
    if hasattr(user, 'profile'):
        profile = user.profile
        profile.role = role
        profile.save()
    else:
        profile = UserProfile.objects.create(user=user, role=role)
    
    return user

@transaction.atomic
def create_test_data():
    # 1. Récupération de la discipline Qwan Ki Do existante
    try:
        discipline = Discipline.objects.get(name="Qwan Ki Do")
        print(f"Discipline {discipline.name} trouvée et réutilisée.")
    except Discipline.DoesNotExist:
        print("ERREUR: La discipline Qwan Ki Do n'existe pas dans la base de données.")
        print("Veuillez créer cette discipline dans l'administration avant d'exécuter ce script.")
        return
    
    # 2. Création de l'utilisateur admin fédération
    fed_admin = create_user(
        username="qwankido_admin",
        email=generate_email("qwankido_admin"),
        role="federation_admin"
    )

    # 3. Création de la fédération
    federation, created = Federation.objects.get_or_create(
        name="Fédération Qwan Ki Do Test",
        defaults={
            "owner": fed_admin,
            "description": "Fédération de test pour Qwan Ki Do",
            "country": "France",
            "address": "123 Rue de Test",
            "city": "Paris",
            "postal_code": "75001",
            "contact_email": "contact@qwankido-test.fr",
            "contact_phone": "+33123456789",
            "is_active": True
        }
    )
    if created:
        # Slug generation
        federation.slug = slugify(federation.name)
        federation.save()
        print(f"Fédération {federation.name} créée.")
    else:
        print(f"Fédération {federation.name} existe déjà, réutilisation.")

    # Créer l'association administrateur de fédération
    FederationAdministrator.objects.get_or_create(
        user=fed_admin,
        federation=federation,
        defaults={
            "role": "owner",
            "is_primary": True
        }
    )
    print(f"Association admin fédération créée pour {fed_admin.username}.")

    # 4. Création des clubs
    club_names = ["Club Qwan Ki Do Paris", "École Qwan Ki Do Lyon", "Académie Qwan Ki Do Bordeaux"]
    clubs = []

    for idx, club_name in enumerate(club_names):
        club_admin = create_user(
            username=f"club_admin_{idx+1}",
            email=generate_email(f"club_admin_{idx+1}"),
            role="club_manager"
        )
        
        club, created = Club.objects.get_or_create(
            name=club_name,
            defaults={
                "owner": club_admin,
                "federation": federation,
                "address": f"{100+idx} Avenue Test",
                "city": club_name.split()[-1],
                "contact_email": f"contact@{slugify(club_name)}.fr",
                "contact_phone": f"+3312345{idx}789",
                "description": f"Club de test {idx+1} pour Qwan Ki Do",
                "is_active": True
            }
        )
        
        if created:
            print(f"Club {club.name} créé.")
        else:
            print(f"Club {club.name} existe déjà, réutilisation.")
        
        # Ajouter la discipline au club
        club.disciplines.add(discipline)
        club.main_discipline = discipline
        club.save()
        
        # Créer l'association administrateur de club
        ClubAdministrator.objects.get_or_create(
            user=club_admin,
            club=club,
            defaults={
                "role": "owner",
                "is_primary": True
            }
        )
        
        clubs.append(club)
    
    # 5. Création des pratiquants (5 par club)
    practitioners_count = 0
    grade_names = ["Débutant", "1er Cap Jaune", "2ème Cap Jaune", "3ème Cap Jaune", "1er Cap Rouge"]

    # Récupération des instances de Grade depuis la base de données
    all_grades = list(Grade.objects.filter(discipline=discipline))
    if not all_grades:
        print("ATTENTION: Aucun grade trouvé pour la discipline Qwan Ki Do. Les pratiquants n'auront pas de grade.")

    # Création d'un dictionnaire pour associer les noms de grades aux instances
    grade_dict = {}
    for grade_obj in all_grades:
        grade_dict[grade_obj.name] = grade_obj

    print(f"Grades disponibles: {', '.join(grade_dict.keys())}")

    for club in clubs:
        for i in range(5):
            # Âge aléatoire entre 7 et 17 ans
            birth_date = random_birth_date(7, 17)
            
            # Déterminer un genre aléatoire
            gender = random.choice(['male', 'female'])
            
            # Prénom selon le genre
            first_names_male = ["Thomas", "Lucas", "Hugo", "Nathan", "Enzo", "Louis", "Mathis", "Jules", "Gabriel", "Adam"]
            first_names_female = ["Emma", "Jade", "Louise", "Alice", "Chloé", "Lina", "Léa", "Rose", "Anna", "Inès"]
            
            first_name = random.choice(first_names_male if gender == 'male' else first_names_female)
            last_names = ["Martin", "Bernard", "Thomas", "Petit", "Robert", "Richard", "Durand", "Dubois", "Moreau", "Simon"]
            last_name = random.choice(last_names)
            
            # Génération d'un email
            email = generate_email(f"{first_name.lower()}_{last_name.lower()}")
            
            # Préparation des données pour la création du pratiquant
            practitioner_data = {
                "email": email,
                "gender": gender,
                "weight": random.randint(30, 70),  # Poids en kg
                "height": random.randint(130, 175),  # Taille en cm
                "is_active": True
            }
            
            # Si nous avons des grades disponibles, en attribuer un aléatoirement
            grade_name = random.choice(grade_names)
            if grade_name in grade_dict:
                practitioner_data["grade"] = grade_dict[grade_name]
            
            try:
                # Création du pratiquant
                practitioner, created = Practitioner.objects.get_or_create(
                    first_name=first_name,
                    last_name=last_name,
                    birth_date=birth_date,
                    club=club,
                    defaults=practitioner_data
                )
                
                if created:
                    # Ajouter la discipline au pratiquant
                    practitioner.disciplines.add(discipline)
                    practitioners_count += 1
                
                # Création d'un utilisateur lié pour 1 pratiquant sur 3
                if created and i % 3 == 0:
                    user = create_user(
                        username=f"{first_name.lower()}_{last_name.lower()}",
                        email=email,
                        role="participant"
                    )
                    practitioner.user = user
                    practitioner.save()
            except Exception as e:
                print(f"Erreur lors de la création du pratiquant {first_name} {last_name}: {str(e)}")
                continue
    
    # 6. Création des juges
    judges_count = 0
    qualification_levels = ["novice", "regional", "national"]
    
    # Trouver un grade élevé pour les juges (comme "Ceinture Noire 1er Dang")
    judge_grade = None
    for grade_obj in all_grades:
        if "Dang" in grade_obj.name or "noir" in grade_obj.name.lower() or "black" in grade_obj.name.lower():
            judge_grade = grade_obj
            break

    if not judge_grade and all_grades:
        # Si pas de grade noir trouvé, utiliser le grade le plus élevé disponible
        try:
            judge_grade = sorted(all_grades, key=lambda g: g.level, reverse=True)[0]
        except (AttributeError, IndexError):
            print("ATTENTION: Impossible de déterminer un grade pour les juges.")
    
    for i in range(3):
        # Créer l'utilisateur du juge
        judge_user = create_user(
            username=f"juge_test_{i+1}",
            email=generate_email(f"juge_test_{i+1}"),
            role="judge"
        )
        
        # Préparation des données pour la création du pratiquant-juge
        judge_practitioner_data = {
            "email": judge_user.email,
            "gender": random.choice(['male', 'female']),
            "is_active": True,
            "user": judge_user
        }
        
        if judge_grade:
            judge_practitioner_data["grade"] = judge_grade
        
        try:
            # Créer un pratiquant pour ce juge (utilisé pour stocker les informations personnelles)
            judge_practitioner, created = Practitioner.objects.get_or_create(
                first_name=f"Juge{i+1}",
                last_name="Test",
                birth_date=random_birth_date(25, 50),  # Âge entre 25 et 50 ans
                club=random.choice(clubs),
                defaults=judge_practitioner_data
            )
            
            if created:
                judge_practitioner.disciplines.add(discipline)
            
            # Créer le profil juge
            judge, created = Judge.objects.get_or_create(
                practitioner=judge_practitioner,
                defaults={
                    "user": judge_user,
                    "qualification_level": random.choice(qualification_levels),
                    "years_experience": random.randint(1, 10),
                    "is_technical_judge": True,
                    "is_combat_referee": random.choice([True, False]),
                    "federation": federation,
                    "active": True
                }
            )
            
            if created:
                judges_count += 1
            
            # Ajouter une qualification pour Qwan Ki Do
            JudgeQualification.objects.get_or_create(
                practitioner=judge_practitioner,
                qualification_type="technical_judge",
                discipline=discipline,
                defaults={
                    "level": judge.qualification_level,
                    "certified_date": timezone.now().date() - timedelta(days=random.randint(30, 365*3))
                }
            )
        except Exception as e:
            print(f"Erreur lors de la création du juge {i+1}: {str(e)}")
            continue
    
    print(f"{practitioners_count} pratiquants créés ou mis à jour.")
    print(f"{judges_count} juges créés ou mis à jour.")
    
    # Résumé final
    print("\n--- RÉSUMÉ DES DONNÉES DE TEST ---")
    print(f"1 Fédération: {federation.name}")
    print(f"1 Discipline: {discipline.name} (existante)")
    print(f"{len(clubs)} Clubs créés")
    print(f"{practitioners_count} Pratiquants (7-17 ans)")
    print(f"{judges_count} Juges techniques")
    print("\nToutes les données de test ont été créées avec succès!")
    print("\nInformations de connexion:")
    print(f"- Admin Fédération: qwankido_admin / Test1234!")
    for i, club in enumerate(clubs):
        print(f"- Admin Club {i+1}: club_admin_{i+1} / Test1234!")
    for i in range(3):  # Toujours afficher 3 juges même si création échouée
        print(f"- Juge {i+1}: juge_test_{i+1} / Test1234!")
    print("\nVous pouvez maintenant tester la feuille de notation!")

if __name__ == "__main__":
    create_test_data()