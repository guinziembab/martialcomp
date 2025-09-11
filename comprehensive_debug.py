#!/usr/bin/env python3
"""
Script de diagnostic complet pour résoudre le problème BACH_HAC
"""
import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from apps.competitions.models.users import UserProfile
from apps.competitions.models import Practitioner, Club

print("=== DIAGNOSTIC COMPLET BACH_HAC ===")
print(f"Heure: {datetime.now()}")
print(f"Environnement: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Non défini')}")
print()

# 1. Vérifier l'utilisateur
try:
    user = User.objects.get(username='ClaudiuG')
    print(f"✅ Utilisateur trouvé: {user.username} (ID: {user.id})")
    print(f"   Email: {user.email}")
    print(f"   Is Staff: {user.is_staff}")
    print(f"   Is Superuser: {user.is_superuser}")
    print()
except User.DoesNotExist:
    print("❌ Utilisateur ClaudiuG non trouvé")
    exit(1)

# 2. Vérifier le profil utilisateur
try:
    profile = UserProfile.objects.get(user=user)
    print(f"✅ UserProfile trouvé:")
    print(f"   Organisation: {profile.organization}")
    print(f"   Type d'organisation: {profile.organization.__class__.__name__}")
    print(f"   Role: {profile.role}")
    print()
except UserProfile.DoesNotExist:
    print("❌ UserProfile non trouvé pour ClaudiuG")

# 3. Rechercher BACH_HAC partout
print("=== RECHERCHE BACH_HAC ===")

# Dans les Clubs
bach_clubs = Club.objects.filter(name__icontains='BACH').all()
print(f"Clubs avec 'BACH' dans le nom: {bach_clubs.count()}")
for club in bach_clubs:
    print(f"  - {club.name} (ID: {club.id})")

# Chercher dans tous les types d'organisations
from django.apps import apps
Organization = apps.get_model('competitions', 'Organization')
all_orgs_with_bach = Organization.objects.filter(name__icontains='BACH').all()
print(f"Organisations avec 'BACH' dans le nom: {all_orgs_with_bach.count()}")
for org in all_orgs_with_bach:
    print(f"  - {org.name} (Type: {org.__class__.__name__}, ID: {org.id})")
print()

# 4. Vérifier les pratiquants de l'utilisateur
print("=== PRATIQUANTS DE L'UTILISATEUR ===")
user_practitioners = Practitioner.objects.filter(user=user).all()
print(f"Pratiquants liés à ClaudiuG: {user_practitioners.count()}")
for p in user_practitioners:
    print(f"  - {p.first_name} {p.last_name} dans {p.organization}")

practitioner_by_email = Practitioner.objects.filter(email=user.email).all()
print(f"Pratiquants avec email {user.email}: {practitioner_by_email.count()}")
for p in practitioner_by_email:
    print(f"  - {p.first_name} {p.last_name} dans {p.organization}")
print()

# 5. Sessions actives
print("=== SESSIONS ACTIVES ===")
active_sessions = Session.objects.filter(expire_date__gt=datetime.now()).count()
print(f"Sessions actives: {active_sessions}")

# Rechercher des sessions avec référence à BACH_HAC
all_sessions = Session.objects.all()
bach_sessions = 0
for session in all_sessions:
    session_data = session.get_decoded()
    session_str = str(session_data)
    if 'BACH' in session_str or 'bach' in session_str:
        bach_sessions += 1
        print(f"  Session avec BACH: {session.session_key}")
        print(f"    Expire: {session.expire_date}")
        print(f"    Data: {session_data}")

print(f"Sessions contenant 'BACH': {bach_sessions}")
print()

# 6. Organisations disponibles
print("=== ORGANISATIONS DISPONIBLES ===")
all_orgs = Organization.objects.all().order_by('name')
print(f"Total organisations: {all_orgs.count()}")
for org in all_orgs:
    practitioner_count = Practitioner.objects.filter(organization=org).count()
    print(f"  - {org.name} (Type: {org.__class__.__name__}, Pratiquants: {practitioner_count})")
print()

# 7. Test de la fonction get_user_club
print("=== TEST GET_USER_CLUB ===")
try:
    from apps.competitions.views.club.practitioners import get_user_club
    
    class FakeRequest:
        def __init__(self, user):
            self.user = user
            self.user_organization = None
            self.club = None
    
    fake_request = FakeRequest(user)
    club_result = get_user_club(fake_request)
    print(f"Résultat get_user_club: {club_result}")
    
    if club_result:
        practitioner_count = Practitioner.objects.filter(organization=club_result).count()
        print(f"Pratiquants dans ce club: {practitioner_count}")
    
except Exception as e:
    print(f"Erreur get_user_club: {e}")

# 8. Vérifications base de données
print()
print("=== INFORMATIONS BASE DE DONNÉES ===")
from django.conf import settings
print(f"Base de données: {settings.DATABASES['default']['ENGINE']}")
print(f"Nom: {settings.DATABASES['default']['NAME']}")

# Si SQLite, montrer le chemin complet
if 'sqlite' in settings.DATABASES['default']['ENGINE']:
    db_path = settings.DATABASES['default']['NAME']
    if os.path.exists(db_path):
        print(f"Fichier SQLite: {db_path}")
        print(f"Taille: {os.path.getsize(db_path)} bytes")
        print(f"Modifié: {datetime.fromtimestamp(os.path.getmtime(db_path))}")
    else:
        print(f"❌ Fichier SQLite introuvable: {db_path}")

print()
print("=== FIN DU DIAGNOSTIC ===")
print("Instructions pour l'utilisateur Windows:")
print("1. Copiez ce script sur votre machine Windows")
print("2. Exécutez-le avec: python comprehensive_debug.py")
print("3. Envoyez-nous le résultat complet")