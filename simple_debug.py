#!/usr/bin/env python3
"""
Script de diagnostic simple pour BACH_HAC
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User
from apps.competitions.models.users import UserProfile
from apps.competitions.models import Practitioner, Club

print("=== DIAGNOSTIC SIMPLE BACH_HAC ===")

# 1. Vérifier l'utilisateur ClaudiuG
user = User.objects.get(username='ClaudiuG')
print(f"User: {user.username} (ID: {user.id})")

# 2. Vérifier le UserProfile
profile = UserProfile.objects.get(user=user)
print(f"UserProfile organisation: {profile.organization}")

# 3. Chercher BACH_HAC
print("\n=== RECHERCHE BACH_HAC ===")
bach_clubs = Club.objects.filter(name__icontains='BACH')
print(f"Clubs avec BACH: {bach_clubs.count()}")
for club in bach_clubs:
    print(f"  - {club.name}")

# Chercher dans tous les objets avec "bach" ou "hac"
all_clubs = Club.objects.all()
print(f"\nTous les clubs ({all_clubs.count()}):")
for club in all_clubs:
    if 'bach' in club.name.lower() or 'hac' in club.name.lower():
        print(f"  BACH/HAC trouvé: {club.name}")
    else:
        print(f"  - {club.name}")

# 4. Vérifier tous les practiquants de ClaudiuG
print(f"\n=== PRACTIQUANTS DE {user.username} ===")
practitioners = Practitioner.objects.filter(user=user)
print(f"Practiquants: {practitioners.count()}")
for p in practitioners:
    print(f"  - {p.first_name} {p.last_name} -> {p.organization}")

# 5. Test direct de la vue
print(f"\n=== TEST DIRECT ===")
try:
    from apps.competitions.views.club.practitioners import get_user_club, manual_permission_check
    
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    mock_request = MockRequest(user)
    club = get_user_club(mock_request)
    print(f"get_user_club result: {club}")
    
    if club:
        permission = manual_permission_check(user, club)
        print(f"Permission check: {permission}")
        
        practitioner_count = Practitioner.objects.filter(organization=club).count()
        print(f"Practitioners in club: {practitioner_count}")
    
except Exception as e:
    print(f"Erreur: {e}")
    import traceback
    traceback.print_exc()

print(f"\n=== INFO BASE DE DONNÉES ===")
from django.conf import settings
print(f"Database: {settings.DATABASES['default']['NAME']}")

print(f"\n=== SOLUTION RECOMMANDÉE ===")
print("Si vous voyez encore BACH_HAC sur Windows:")
print("1. Vérifiez que vous utilisez la même base de données")
print("2. Redémarrez complètement le serveur Django")  
print("3. Effacez le cache du navigateur et les cookies")
print("4. Utilisez un navigateur privé/incognito")
print("5. Vérifiez qu'il n'y a pas plusieurs serveurs Django qui tournent")