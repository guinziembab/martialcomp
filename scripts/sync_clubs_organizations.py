#!/usr/bin/env python3
"""Script pour synchroniser les clubs avec leurs organisations"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_minimal')
django.setup()

from competitions.models import Club
from organizations.models import Organization
from django.db import transaction

def sync_clubs_organizations():
    """Synchronise tous les clubs avec leurs organisations"""
    
    print("=== Synchronisation Clubs → Organizations ===")
    
    clubs = Club.objects.all()
    print(f"Clubs à synchroniser: {clubs.count()}")
    
    synced_count = 0
    created_count = 0
    
    for club in clubs:
        print(f"\n📋 Traitement du club: {club.name}")
        
        try:
            with transaction.atomic():
                # Vérifier si une organisation existe déjà
                organization = club.organization or club.as_organization
                
                if organization:
                    print(f"  ✅ Organisation existante: {organization.name}")
                    synced_count += 1
                else:
                    # Créer une nouvelle organisation
                    organization = Organization.objects.create(
                        name=club.name,
                        organization_type='club',
                        description=getattr(club, 'description', ''),
                        email=getattr(club, 'contact_email', ''),
                        phone=getattr(club, 'contact_phone', ''),
                        website=getattr(club, 'website', ''),
                        address=getattr(club, 'address', ''),
                        city=getattr(club, 'city', ''),
                        postal_code=getattr(club, 'postal_code', ''),
                        is_active=getattr(club, 'is_active', True),
                        created_by=getattr(club, 'owner', None),
                        old_club_id=club.id  # Liaison importante
                    )
                    
                    # Lier le club à l'organisation
                    club.organization = organization
                    club.save(update_fields=['organization'])
                    
                    print(f"  ✅ Organisation créée: {organization.name}")
                    created_count += 1
                
                # Synchroniser les disciplines
                if hasattr(club, 'disciplines') and hasattr(organization, 'disciplines'):
                    club_disciplines = club.disciplines.all()
                    if club_disciplines.exists():
                        # Copier les disciplines du club vers l'organisation
                        for discipline in club_disciplines:
                            organization.disciplines.add(discipline)
                        print(f"  🥋 Synchronisé {club_disciplines.count()} disciplines")
                    else:
                        print(f"  ⚠️  Aucune discipline assignée au club")
                
        except Exception as e:
            print(f"  ❌ Erreur lors de la synchronisation: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 Résumé:")
    print(f"  - {synced_count} clubs déjà synchronisés")
    print(f"  - {created_count} organisations créées")
    print(f"  - {synced_count + created_count} clubs traités au total")
    
    # Vérification finale
    print(f"\n🔍 Vérification finale:")
    for club in Club.objects.all():
        organization = club.organization or club.as_organization
        if organization:
            print(f"  ✅ {club.name} → {organization.name}")
        else:
            print(f"  ❌ {club.name} → Aucune organisation")

def add_disciplines_to_clubs():
    """Ajoute des disciplines aux clubs qui n'en ont pas"""
    print(f"\n=== Ajout de Disciplines aux Clubs ===")
    
    from competitions.models import Discipline
    
    # Récupérer les disciplines disponibles
    disciplines = Discipline.objects.filter(is_active=True)
    if not disciplines.exists():
        print("❌ Aucune discipline disponible")
        return
    
    # Assigner au moins une discipline à chaque club
    clubs_without_disciplines = Club.objects.filter(disciplines__isnull=True)
    print(f"Clubs sans disciplines: {clubs_without_disciplines.count()}")
    
    for club in clubs_without_disciplines:
        # Assigner la première discipline disponible (par exemple Karaté)
        first_discipline = disciplines.first()
        club.disciplines.add(first_discipline)
        club.main_discipline = first_discipline
        club.save()
        print(f"  ✅ {club.name} → {first_discipline.name}")

if __name__ == "__main__":
    sync_clubs_organizations()
    add_disciplines_to_clubs()
    print("\n🎉 Synchronisation terminée!")