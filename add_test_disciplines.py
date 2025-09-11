#!/usr/bin/env python3
"""
Add test disciplines to CHUATAO organization
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth.models import User
from apps.competitions.models.users import UserProfile
from apps.competitions.models.discipline import Discipline

print("=== ADDING TEST DISCIPLINES ===")

# Get ClaudiuG's organization
user = User.objects.get(username='ClaudiuG')
profile = UserProfile.objects.get(user=user)
organization = profile.organization

print(f"Organization: {organization}")

# Check existing disciplines
existing_disciplines = organization.disciplines.all()
print(f"Existing disciplines: {existing_disciplines.count()}")

# Create some test disciplines if none exist
if existing_disciplines.count() == 0:
    disciplines_to_create = [
        {
            'name': 'Karaté',
            'description': 'Art martial traditionnel japonais'
        },
        {
            'name': 'Taekwondo',
            'description': 'Art martial coréen axé sur les coups de pied'
        },
        {
            'name': 'Judo',
            'description': 'Art martial japonais de projection et contrôle'
        },
        {
            'name': 'Qwan Ki Do',
            'description': 'Art martial vietnamien'
        }
    ]
    
    created_count = 0
    for disc_data in disciplines_to_create:
        # Check if discipline already exists globally
        existing = Discipline.objects.filter(name=disc_data['name']).first()
        
        if existing:
            # Add existing discipline to organization
            organization.disciplines.add(existing)
            print(f"✅ Added existing discipline: {existing.name}")
        else:
            # Create new discipline
            discipline = Discipline.objects.create(
                name=disc_data['name'],
                description=disc_data['description'],
                organization=organization  # Set as primary federation
            )
            # Also add to organization's disciplines
            organization.disciplines.add(discipline)
            print(f"✅ Created and added discipline: {discipline.name}")
        
        created_count += 1
    
    print(f"\n✅ Added {created_count} disciplines to {organization}")
    
else:
    print(f"✅ Organization already has {existing_disciplines.count()} disciplines:")
    for disc in existing_disciplines:
        print(f"  - {disc.name}")

# Final verification
final_count = organization.disciplines.count()
print(f"\nFinal discipline count: {final_count}")

print(f"\n🎯 Training forms should now show {final_count} available disciplines!")