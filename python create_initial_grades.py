#!/usr/bin/env python
"""
Script pour initialiser des grades dans la base de données.
"""

import os
import sys
import django

# Ajouter le répertoire parent au chemin Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import Discipline
from grades.models import Grade, GradeCategory

def create_initial_grades():
    print("Création des grades initiaux...")
    
    # Vérifier si des disciplines existent
    if not Discipline.objects.exists():
        print("Aucune discipline trouvée. Création d'une discipline d'exemple...")
        discipline = Discipline.objects.create(
            name="Karaté",
            description="Art martial japonais basé sur des techniques de percussion",
            country_origin="Japon",
            is_active=True
        )
        print(f"Discipline créée: {discipline.name} (ID: {discipline.id})")
    else:
        discipline = Discipline.objects.first()
        print(f"Utilisation de la discipline existante: {discipline.name} (ID: {discipline.id})")
    
    # Créer une catégorie de grade si nécessaire
    category, created = GradeCategory.objects.get_or_create(
        name="Grades Kyu",
        defaults={
            'description': "Grades d'élèves",
            'discipline': discipline,
            'order': 1,
            'is_active': True
        }
    )
    if created:
        print(f"Catégorie de grade créée: {category.name}")
    else:
        print(f"Utilisation de la catégorie existante: {category.name}")
    
    # Définir les grades à créer
    grades_to_create = [
        {"name": "Ceinture blanche", "color": "Blanche", "color_code": "#FFFFFF", "level": 1},
        {"name": "Ceinture jaune", "color": "Jaune", "color_code": "#FFFF00", "level": 2},
        {"name": "Ceinture orange", "color": "Orange", "color_code": "#FFA500", "level": 3},
        {"name": "Ceinture verte", "color": "Verte", "color_code": "#008000", "level": 4},
        {"name": "Ceinture bleue", "color": "Bleue", "color_code": "#0000FF", "level": 5},
        {"name": "Ceinture marron", "color": "Marron", "color_code": "#8B4513", "level": 6},
        {"name": "Ceinture noire 1er dan", "color": "Noire", "color_code": "#000000", "level": 7, "is_dan_grade": True},
        {"name": "Ceinture noire 2e dan", "color": "Noire", "color_code": "#000000", "level": 8, "is_dan_grade": True},
    ]
    
    for grade_data in grades_to_create:
        grade, created = Grade.objects.get_or_create(
            name=grade_data["name"],
            discipline=discipline,
            defaults={
                'category': category,
                'color': grade_data["color"],
                'color_code': grade_data["color_code"],
                'level': grade_data["level"],
                'is_dan_grade': grade_data.get("is_dan_grade", False),
                'is_active': True,
                'order': grade_data["level"]
            }
        )
        
        if created:
            print(f"Grade créé: {grade.name} (ID: {grade.id})")
        else:
            print(f"Le grade existe déjà: {grade.name} (ID: {grade.id})")
    
    print("Initialisation des grades terminée.")

if __name__ == "__main__":
    create_initial_grades()