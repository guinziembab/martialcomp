#!/usr/bin/env python
"""Lister toutes les organisations et leurs associations"""

import os
import sys
import django

# Configuration Django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.organizations.models import Organization
from apps.competitions.models import Club, Practitioner
from apps.competitions.models.users import UserProfile
from django.db.models import Count, Q

print("=== LISTE DES ORGANISATIONS ET LEURS ASSOCIATIONS ===\n")

# Récupérer toutes les organisations
organizations = Organization.objects.all().order_by('name', 'id')

# Grouper par nom pour identifier les doublons
from collections import defaultdict
org_by_name = defaultdict(list)

for org in organizations:
    org_by_name[org.name].append(org)

print(f"Nombre total d'organisations: {organizations.count()}")
print(f"Nombre de noms uniques: {len(org_by_name)}\n")

# Identifier les doublons
print("=== ORGANISATIONS EN DOUBLON ===")
duplicates_found = False
for name, orgs in org_by_name.items():
    if len(orgs) > 1:
        duplicates_found = True
        print(f"\n'{name}': {len(orgs)} organisations")
        for org in orgs:
            # Compter les associations
            clubs_count = Club.objects.filter(organization=org).count()
            practitioners_count = Practitioner.objects.filter(organization=org).count()
            profiles_count = UserProfile.objects.filter(organization=org).count()
            
            print(f"  - ID: {org.id}")
            print(f"    Type: {org.organization_type}")
            print(f"    Active: {org.is_active}")
            print(f"    Créée: {org.created_at.strftime('%Y-%m-%d') if hasattr(org, 'created_at') and org.created_at else 'N/A'}")
            print(f"    Associations:")
            print(f"      - Clubs: {clubs_count}")
            print(f"      - Pratiquants: {practitioners_count}")
            print(f"      - Profils utilisateur: {profiles_count}")
            print(f"    TOTAL: {clubs_count + practitioners_count + profiles_count}")

if not duplicates_found:
    print("Aucun doublon trouvé!")

# Lister toutes les organisations avec leurs statistiques
print("\n\n=== TOUTES LES ORGANISATIONS ===")
print(f"{'Nom':<40} {'ID':<6} {'Type':<15} {'Clubs':<8} {'Prat.':<8} {'Profils':<8} {'Total':<8}")
print("-" * 100)

for org in organizations[:50]:  # Limiter à 50 pour la lisibilité
    clubs_count = Club.objects.filter(organization=org).count()
    practitioners_count = Practitioner.objects.filter(organization=org).count()
    profiles_count = UserProfile.objects.filter(organization=org).count()
    total = clubs_count + practitioners_count + profiles_count
    
    print(f"{org.name[:40]:<40} {org.id:<6} {org.organization_type[:15]:<15} {clubs_count:<8} {practitioners_count:<8} {profiles_count:<8} {total:<8}")

if organizations.count() > 50:
    print(f"\n... et {organizations.count() - 50} autres organisations")

# Identifier les organisations sans aucune association
print("\n\n=== ORGANISATIONS SANS ASSOCIATIONS (candidates à la suppression) ===")
empty_orgs = []
for org in organizations:
    clubs_count = Club.objects.filter(organization=org).count()
    practitioners_count = Practitioner.objects.filter(organization=org).count()
    profiles_count = UserProfile.objects.filter(organization=org).count()
    
    if clubs_count == 0 and practitioners_count == 0 and profiles_count == 0:
        empty_orgs.append(org)

print(f"Nombre d'organisations sans associations: {len(empty_orgs)}")
if empty_orgs:
    print("\nListe des organisations vides:")
    for org in empty_orgs[:20]:
        print(f"  - {org.name} (ID: {org.id}, Type: {org.organization_type})")
    
    if len(empty_orgs) > 20:
        print(f"  ... et {len(empty_orgs) - 20} autres")

# Spécifiquement pour KHIPHAP
print("\n\n=== FOCUS SUR KHIPHAP ===")
khiphap_orgs = Organization.objects.filter(name__icontains='KHIPHAP').order_by('id')
for org in khiphap_orgs:
    clubs = Club.objects.filter(organization=org)
    practitioners = Practitioner.objects.filter(organization=org)[:5]
    profiles = UserProfile.objects.filter(organization=org)
    
    print(f"\nKHIPHAP ID {org.id}:")
    print(f"  - Type: {org.organization_type}")
    print(f"  - Active: {org.is_active}")
    print(f"  - Clubs ({clubs.count()}):")
    for club in clubs:
        print(f"    * {club.name} (ID: {club.id}, Owner: {club.owner.username if club.owner else 'N/A'})")
    print(f"  - Pratiquants ({Practitioner.objects.filter(organization=org).count()}):")
    for p in practitioners:
        print(f"    * {p.full_name}")
    print(f"  - Profils utilisateur ({profiles.count()}):")
    for profile in profiles:
        print(f"    * {profile.user.username}")