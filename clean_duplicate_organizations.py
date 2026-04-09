#!/usr/bin/env python
"""Script pour nettoyer les organisations en doublon"""

import os
import sys
import django
from django.db import transaction

# Configuration Django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.organizations.models import Organization
from apps.competitions.models import Club, Practitioner
from apps.competitions.models.users import UserProfile
from collections import defaultdict

print("=== NETTOYAGE DES ORGANISATIONS EN DOUBLON ===\n")

# Mode dry run par défaut
DRY_RUN = False
print(f"MODE: {'DRY RUN (simulation)' if DRY_RUN else 'EXECUTION RÉELLE'}\n")

# Grouper les organisations par nom
org_by_name = defaultdict(list)
for org in Organization.objects.all().order_by('name', 'id'):
    org_by_name[org.name].append(org)

# Traiter les doublons
duplicates_to_delete = []
merge_operations = []

for name, orgs in org_by_name.items():
    if len(orgs) > 1:
        print(f"\nTraitement de '{name}': {len(orgs)} organisations")
        
        # Trouver l'organisation principale (celle avec des associations)
        main_org = None
        for org in orgs:
            clubs_count = Club.objects.filter(organization=org).count()
            practitioners_count = Practitioner.objects.filter(organization=org).count()
            profiles_count = UserProfile.objects.filter(organization=org).count()
            total = clubs_count + practitioners_count + profiles_count
            
            if total > 0:
                if main_org is None or total > main_org['total']:
                    main_org = {
                        'org': org,
                        'total': total,
                        'clubs': clubs_count,
                        'practitioners': practitioners_count,
                        'profiles': profiles_count
                    }
        
        if main_org:
            print(f"  Organisation principale: ID {main_org['org'].id} ({main_org['total']} associations)")
            
            # Marquer les autres pour suppression
            for org in orgs:
                if org.id != main_org['org'].id:
                    clubs_count = Club.objects.filter(organization=org).count()
                    practitioners_count = Practitioner.objects.filter(organization=org).count()
                    profiles_count = UserProfile.objects.filter(organization=org).count()
                    
                    if clubs_count == 0 and practitioners_count == 0 and profiles_count == 0:
                        duplicates_to_delete.append(org)
                        print(f"  - Suppression prévue: ID {org.id} (aucune association)")
                    else:
                        # Si elle a des associations, on devrait fusionner
                        merge_operations.append({
                            'from': org,
                            'to': main_org['org'],
                            'clubs': clubs_count,
                            'practitioners': practitioners_count,
                            'profiles': profiles_count
                        })
                        print(f"  - Fusion nécessaire: ID {org.id} -> ID {main_org['org'].id}")
                        print(f"    ({clubs_count} clubs, {practitioners_count} pratiquants, {profiles_count} profils)")
        else:
            # Toutes sont vides, garder la première
            print(f"  Toutes vides - garder ID {orgs[0].id}")
            for org in orgs[1:]:
                duplicates_to_delete.append(org)

# Résumé
print(f"\n\n=== RÉSUMÉ DES OPÉRATIONS ===")
print(f"Organisations à supprimer: {len(duplicates_to_delete)}")
print(f"Fusions nécessaires: {len(merge_operations)}")

if not DRY_RUN and duplicates_to_delete:
    print("\n=== SUPPRESSION EN COURS ===")
    
    # Auto-confirmation pour l'exécution automatique
    print(f"\nSuppression de {len(duplicates_to_delete)} organisations...")
    if True:  # Auto-confirm
        with transaction.atomic():
            count = 0
            for org in duplicates_to_delete:
                print(f"Suppression de {org.name} (ID: {org.id})...")
                org.delete()
                count += 1
            
            print(f"\n✓ {count} organisations supprimées avec succès!")
    else:
        print("Opération annulée.")
else:
    print("\nPour exécuter réellement les suppressions:")
    print("1. Modifiez DRY_RUN = False dans ce script")
    print("2. Relancez le script")

# Cas spécifique KHIPHAP
print("\n\n=== CAS SPÉCIFIQUE KHIPHAP ===")
khiphap_orgs = Organization.objects.filter(name='KHIPHAP').order_by('id')
print(f"Nombre d'organisations KHIPHAP: {khiphap_orgs.count()}")

main_khiphap = None
for org in khiphap_orgs:
    clubs = Club.objects.filter(organization=org).count()
    practitioners = Practitioner.objects.filter(organization=org).count()
    profiles = UserProfile.objects.filter(organization=org).count()
    total = clubs + practitioners + profiles
    
    print(f"  - ID {org.id}: {clubs} clubs, {practitioners} pratiquants, {profiles} profils")
    
    if total > 0 and (main_khiphap is None or org.id == 146):  # Privilégier ID 146
        main_khiphap = org

if main_khiphap:
    print(f"\nOrganisation KHIPHAP principale: ID {main_khiphap.id}")
    
# Script de nettoyage SQL pour référence
print("\n\n=== SCRIPT SQL DE NETTOYAGE (pour référence) ===")
print("-- Supprimer les organisations sans associations")
print("DELETE FROM organizations_organization")
print("WHERE id NOT IN (")
print("    SELECT DISTINCT organization_id FROM competitions_club WHERE organization_id IS NOT NULL")
print("    UNION")
print("    SELECT DISTINCT organization_id FROM competitions_practitioner WHERE organization_id IS NOT NULL")  
print("    UNION")
print("    SELECT DISTINCT organization_id FROM competitions_userprofile WHERE organization_id IS NOT NULL")
print(");")