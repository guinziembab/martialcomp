#!/usr/bin/env python
"""
Script pour lister les IDs des pratiquants, disciplines et grades dans la base de données.
"""

import os
import sys
import django

# Configuration Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import Practitioner, Discipline
from grades.models import Grade, PractitionerGrade

def list_practitioners():
    """Liste tous les pratiquants avec leurs IDs."""
    print("\n=== PRATIQUANTS ===")
    print(f"{'ID':<5} | {'Nom':<30} | {'Club':<20} | {'Discipline':<15}")
    print("-" * 75)
    
    for p in Practitioner.objects.all().order_by('last_name', 'first_name'):
        club = p.club.name if p.club else "Aucun club"
        disciplines = ", ".join([d.name for d in p.disciplines.all()]) if hasattr(p, 'disciplines') else "N/A"
        print(f"{p.id:<5} | {p.full_name:<30} | {club:<20} | {disciplines:<15}")

def list_disciplines():
    """Liste toutes les disciplines avec leurs IDs."""
    print("\n=== DISCIPLINES ===")
    print(f"{'ID':<5} | {'Nom':<30} | {'Origine':<20} | {'Actif':<5}")
    print("-" * 65)
    
    for d in Discipline.objects.all().order_by('name'):
        origin = d.country_origin if hasattr(d, 'country_origin') else "N/A"
        print(f"{d.id:<5} | {d.name:<30} | {origin:<20} | {'Oui' if d.is_active else 'Non':<5}")

def list_grades():
    """Liste tous les grades avec leurs IDs."""
    print("\n=== GRADES ===")
    print(f"{'ID':<5} | {'Nom':<30} | {'Discipline':<20} | {'Niveau':<6} | {'Dan/Dang':<7}")
    print("-" * 75)
    
    for g in Grade.objects.all().order_by('discipline__name', 'level'):
        discipline = g.discipline.name if hasattr(g, 'discipline') and g.discipline else "N/A"
        level = g.level if hasattr(g, 'level') else "N/A"
        is_dan = "Oui" if hasattr(g, 'is_dan_grade') and g.is_dan_grade else "Non"
        print(f"{g.id:<5} | {g.name:<30} | {discipline:<20} | {level:<6} | {is_dan:<7}")

def list_practitioner_grades():
    """Liste les grades attribués aux pratiquants."""
    print("\n=== GRADES DES PRATIQUANTS ===")
    print(f"{'ID':<5} | {'Pratiquant':<30} | {'Grade':<30} | {'Discipline':<20} | {'Actuel':<6}")
    print("-" * 95)
    
    for pg in PractitionerGrade.objects.all().order_by('practitioner__last_name', 'practitioner__first_name'):
        practitioner = pg.practitioner.full_name if hasattr(pg, 'practitioner') else "N/A"
        grade = pg.grade.name if hasattr(pg, 'grade') else "N/A"
        discipline = pg.discipline.name if hasattr(pg, 'discipline') else "N/A"
        is_current = "Oui" if pg.is_current else "Non"
        print(f"{pg.id:<5} | {practitioner:<30} | {grade:<30} | {discipline:<20} | {is_current:<6}")

if __name__ == "__main__":
    list_practitioners()
    list_disciplines()
    list_grades()
    list_practitioner_grades()
    
def list_qwan_ki_do_elements():
    """Liste les éléments spécifiques au Qwan Ki Do."""
    print("\n=== QWAN KI DO ===")
    
    # Trouver la discipline Qwan Ki Do
    try:
        qkd = Discipline.objects.get(name__icontains="Qwan Ki Do")
        print(f"Discipline Qwan Ki Do trouvée (ID: {qkd.id})")
        
        # Afficher les pratiquants
        print("\nPratiquants de Qwan Ki Do:")
        for p in Practitioner.objects.filter(disciplines=qkd):
            print(f"ID: {p.id}, Nom: {p.full_name}")
        
        # Afficher les grades
        print("\nGrades de Qwan Ki Do:")
        for g in Grade.objects.filter(discipline=qkd):
            print(f"ID: {g.id}, Nom: {g.name}, Niveau: {g.level}")
        
        # Afficher les catégories de grades
        from grades.models import GradeCategory
        print("\nCatégories de grades de Qwan Ki Do:")
        for c in GradeCategory.objects.filter(discipline=qkd):
            print(f"ID: {c.id}, Nom: {c.name}, Ordre: {c.order}")
        
    except Discipline.DoesNotExist:
        print("Discipline Qwan Ki Do non trouvée dans la base de données.")