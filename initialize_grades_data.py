#!/usr/bin/env python3
"""
Script pour initialiser les données de grades pour toutes les disciplines d'arts martiaux.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/mnt/c/martial_hub_django/martialcomp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from django.utils.translation import gettext_lazy as _
from competitions.models import Discipline
from grades.models import Grade, GradeCategory

def initialize_grades():
    """Initialise les systèmes de grades pour toutes les disciplines."""
    
    # Définition des systèmes de grades par discipline
    grade_systems = {
        'Qwan Ki Do': {
            'grades': [
                {'name': 'Ceinture blanche', 'color': 'Blanc', 'level': 1},
                {'name': 'Ceinture jaune', 'color': 'Jaune', 'level': 2},
                {'name': 'Ceinture orange', 'color': 'Orange', 'level': 3},
                {'name': 'Ceinture verte', 'color': 'Vert', 'level': 4},
                {'name': 'Ceinture bleue', 'color': 'Bleu', 'level': 5},
                {'name': 'Ceinture violette', 'color': 'Violet', 'level': 6},
                {'name': 'Ceinture marron', 'color': 'Marron', 'level': 7},
                {'name': 'Ceinture rouge', 'color': 'Rouge', 'level': 8},
                {'name': 'Ceinture noire 1er Dang', 'color': 'Noir', 'level': 9, 'is_dan': True},
                {'name': 'Ceinture noire 2ème Dang', 'color': 'Noir', 'level': 10, 'is_dan': True},
                {'name': 'Ceinture noire 3ème Dang', 'color': 'Noir', 'level': 11, 'is_dan': True},
                {'name': 'Ceinture noire 4ème Dang', 'color': 'Noir', 'level': 12, 'is_dan': True},
                {'name': 'Ceinture noire 5ème Dang', 'color': 'Noir', 'level': 13, 'is_dan': True},
                {'name': 'Ceinture noire 6ème Dang', 'color': 'Noir', 'level': 14, 'is_dan': True},
                {'name': 'Ceinture noire 7ème Dang', 'color': 'Noir', 'level': 15, 'is_dan': True},
                {'name': 'Ceinture noire 8ème Dang', 'color': 'Noir', 'level': 16, 'is_dan': True},
                {'name': 'Ceinture noire 9ème Dang', 'color': 'Noir', 'level': 17, 'is_dan': True},
                {'name': 'Ceinture noire 10ème Dang', 'color': 'Noir', 'level': 18, 'is_dan': True},
            ]
        },
        'Karaté': {
            'grades': [
                {'name': 'Ceinture blanche', 'color': 'Blanc', 'level': 1},
                {'name': 'Ceinture jaune', 'color': 'Jaune', 'level': 2},
                {'name': 'Ceinture orange', 'color': 'Orange', 'level': 3},
                {'name': 'Ceinture verte', 'color': 'Vert', 'level': 4},
                {'name': 'Ceinture bleue', 'color': 'Bleu', 'level': 5},
                {'name': 'Ceinture marron', 'color': 'Marron', 'level': 6},
                {'name': 'Ceinture noire 1er Dan', 'color': 'Noir', 'level': 7, 'is_dan': True},
                {'name': 'Ceinture noire 2ème Dan', 'color': 'Noir', 'level': 8, 'is_dan': True},
                {'name': 'Ceinture noire 3ème Dan', 'color': 'Noir', 'level': 9, 'is_dan': True},
                {'name': 'Ceinture noire 4ème Dan', 'color': 'Noir', 'level': 10, 'is_dan': True},
                {'name': 'Ceinture noire 5ème Dan', 'color': 'Noir', 'level': 11, 'is_dan': True},
                {'name': 'Ceinture noire 6ème Dan', 'color': 'Noir', 'level': 12, 'is_dan': True},
                {'name': 'Ceinture noire 7ème Dan', 'color': 'Noir', 'level': 13, 'is_dan': True},
                {'name': 'Ceinture noire 8ème Dan', 'color': 'Noir', 'level': 14, 'is_dan': True},
                {'name': 'Ceinture noire 9ème Dan', 'color': 'Noir', 'level': 15, 'is_dan': True},
                {'name': 'Ceinture noire 10ème Dan', 'color': 'Noir', 'level': 16, 'is_dan': True},
            ]
        },
        'Judo': {
            'grades': [
                {'name': 'Ceinture blanche', 'color': 'Blanc', 'level': 1},
                {'name': 'Ceinture blanche-jaune', 'color': 'Blanc-Jaune', 'level': 2},
                {'name': 'Ceinture jaune', 'color': 'Jaune', 'level': 3},
                {'name': 'Ceinture jaune-orange', 'color': 'Jaune-Orange', 'level': 4},
                {'name': 'Ceinture orange', 'color': 'Orange', 'level': 5},
                {'name': 'Ceinture orange-verte', 'color': 'Orange-Vert', 'level': 6},
                {'name': 'Ceinture verte', 'color': 'Vert', 'level': 7},
                {'name': 'Ceinture bleue', 'color': 'Bleu', 'level': 8},
                {'name': 'Ceinture marron', 'color': 'Marron', 'level': 9},
                {'name': 'Ceinture noire 1er Dan', 'color': 'Noir', 'level': 10, 'is_dan': True},
                {'name': 'Ceinture noire 2ème Dan', 'color': 'Noir', 'level': 11, 'is_dan': True},
                {'name': 'Ceinture noire 3ème Dan', 'color': 'Noir', 'level': 12, 'is_dan': True},
                {'name': 'Ceinture noire 4ème Dan', 'color': 'Noir', 'level': 13, 'is_dan': True},
                {'name': 'Ceinture noire 5ème Dan', 'color': 'Noir', 'level': 14, 'is_dan': True},
                {'name': 'Ceinture rouge-blanc 6ème Dan', 'color': 'Rouge-Blanc', 'level': 15, 'is_dan': True},
                {'name': 'Ceinture rouge-blanc 7ème Dan', 'color': 'Rouge-Blanc', 'level': 16, 'is_dan': True},
                {'name': 'Ceinture rouge-blanc 8ème Dan', 'color': 'Rouge-Blanc', 'level': 17, 'is_dan': True},
                {'name': 'Ceinture rouge 9ème Dan', 'color': 'Rouge', 'level': 18, 'is_dan': True},
                {'name': 'Ceinture rouge 10ème Dan', 'color': 'Rouge', 'level': 19, 'is_dan': True},
            ]
        },
        'Taekwondo': {
            'grades': [
                {'name': 'Ceinture blanche (10ème Keup)', 'color': 'Blanc', 'level': 1},
                {'name': 'Ceinture blanche-jaune (9ème Keup)', 'color': 'Blanc-Jaune', 'level': 2},
                {'name': 'Ceinture jaune (8ème Keup)', 'color': 'Jaune', 'level': 3},
                {'name': 'Ceinture jaune-verte (7ème Keup)', 'color': 'Jaune-Vert', 'level': 4},
                {'name': 'Ceinture verte (6ème Keup)', 'color': 'Vert', 'level': 5},
                {'name': 'Ceinture verte-bleue (5ème Keup)', 'color': 'Vert-Bleu', 'level': 6},
                {'name': 'Ceinture bleue (4ème Keup)', 'color': 'Bleu', 'level': 7},
                {'name': 'Ceinture bleue-rouge (3ème Keup)', 'color': 'Bleu-Rouge', 'level': 8},
                {'name': 'Ceinture rouge (2ème Keup)', 'color': 'Rouge', 'level': 9},
                {'name': 'Ceinture rouge-noire (1er Keup)', 'color': 'Rouge-Noir', 'level': 10},
                {'name': 'Ceinture noire 1er Dan', 'color': 'Noir', 'level': 11, 'is_dan': True},
                {'name': 'Ceinture noire 2ème Dan', 'color': 'Noir', 'level': 12, 'is_dan': True},
                {'name': 'Ceinture noire 3ème Dan', 'color': 'Noir', 'level': 13, 'is_dan': True},
                {'name': 'Ceinture noire 4ème Dan', 'color': 'Noir', 'level': 14, 'is_dan': True},
                {'name': 'Ceinture noire 5ème Dan', 'color': 'Noir', 'level': 15, 'is_dan': True},
                {'name': 'Ceinture noire 6ème Dan', 'color': 'Noir', 'level': 16, 'is_dan': True},
                {'name': 'Ceinture noire 7ème Dan', 'color': 'Noir', 'level': 17, 'is_dan': True},
                {'name': 'Ceinture noire 8ème Dan', 'color': 'Noir', 'level': 18, 'is_dan': True},
                {'name': 'Ceinture noire 9ème Dan', 'color': 'Noir', 'level': 19, 'is_dan': True},
            ]
        },
        'Aikido': {
            'grades': [
                {'name': 'Ceinture blanche', 'color': 'Blanc', 'level': 1},
                {'name': 'Ceinture jaune', 'color': 'Jaune', 'level': 2},
                {'name': 'Ceinture orange', 'color': 'Orange', 'level': 3},
                {'name': 'Ceinture verte', 'color': 'Vert', 'level': 4},
                {'name': 'Ceinture bleue', 'color': 'Bleu', 'level': 5},
                {'name': 'Ceinture marron', 'color': 'Marron', 'level': 6},
                {'name': 'Ceinture noire 1er Dan', 'color': 'Noir', 'level': 7, 'is_dan': True},
                {'name': 'Ceinture noire 2ème Dan', 'color': 'Noir', 'level': 8, 'is_dan': True},
                {'name': 'Ceinture noire 3ème Dan', 'color': 'Noir', 'level': 9, 'is_dan': True},
                {'name': 'Ceinture noire 4ème Dan', 'color': 'Noir', 'level': 10, 'is_dan': True},
                {'name': 'Ceinture noire 5ème Dan', 'color': 'Noir', 'level': 11, 'is_dan': True},
            ]
        },
        'Kung Fu': {
            'grades': [
                {'name': 'Ceinture blanche', 'color': 'Blanc', 'level': 1},
                {'name': 'Ceinture jaune', 'color': 'Jaune', 'level': 2},
                {'name': 'Ceinture orange', 'color': 'Orange', 'level': 3},
                {'name': 'Ceinture verte', 'color': 'Vert', 'level': 4},
                {'name': 'Ceinture bleue', 'color': 'Bleu', 'level': 5},
                {'name': 'Ceinture marron', 'color': 'Marron', 'level': 6},
                {'name': 'Ceinture noire 1er Dan', 'color': 'Noir', 'level': 7, 'is_dan': True},
                {'name': 'Ceinture noire 2ème Dan', 'color': 'Noir', 'level': 8, 'is_dan': True},
                {'name': 'Ceinture noire 3ème Dan', 'color': 'Noir', 'level': 9, 'is_dan': True},
                {'name': 'Ceinture noire 4ème Dan', 'color': 'Noir', 'level': 10, 'is_dan': True},
                {'name': 'Ceinture noire 5ème Dan', 'color': 'Noir', 'level': 11, 'is_dan': True},
            ]
        },
        'Vovinam': {
            'grades': [
                {'name': 'Ceinture blanche', 'color': 'Blanc', 'level': 1},
                {'name': 'Ceinture jaune', 'color': 'Jaune', 'level': 2},
                {'name': 'Ceinture orange', 'color': 'Orange', 'level': 3},
                {'name': 'Ceinture verte', 'color': 'Vert', 'level': 4},
                {'name': 'Ceinture bleue', 'color': 'Bleu', 'level': 5},
                {'name': 'Ceinture marron', 'color': 'Marron', 'level': 6},
                {'name': 'Ceinture noire 1er Cap', 'color': 'Noir', 'level': 7, 'is_dan': True},
                {'name': 'Ceinture noire 2ème Cap', 'color': 'Noir', 'level': 8, 'is_dan': True},
                {'name': 'Ceinture noire 3ème Cap', 'color': 'Noir', 'level': 9, 'is_dan': True},
                {'name': 'Ceinture noire 4ème Cap', 'color': 'Noir', 'level': 10, 'is_dan': True},
                {'name': 'Ceinture noire 5ème Cap', 'color': 'Noir', 'level': 11, 'is_dan': True},
            ]
        },
        'Krav Maga': {
            'grades': [
                {'name': 'Niveau Débutant P1', 'color': 'Blanc', 'level': 1},
                {'name': 'Niveau Débutant P2', 'color': 'Jaune', 'level': 2},
                {'name': 'Niveau Débutant P3', 'color': 'Orange', 'level': 3},
                {'name': 'Niveau Débutant P4', 'color': 'Vert', 'level': 4},
                {'name': 'Niveau Débutant P5', 'color': 'Bleu', 'level': 5},
                {'name': 'Niveau Gradé G1', 'color': 'Marron', 'level': 6},
                {'name': 'Niveau Gradé G2', 'color': 'Marron', 'level': 7},
                {'name': 'Niveau Gradé G3', 'color': 'Marron', 'level': 8},
                {'name': 'Niveau Gradé G4', 'color': 'Marron', 'level': 9},
                {'name': 'Niveau Gradé G5', 'color': 'Marron', 'level': 10},
                {'name': 'Expert E1', 'color': 'Noir', 'level': 11, 'is_dan': True},
                {'name': 'Expert E2', 'color': 'Noir', 'level': 12, 'is_dan': True},
                {'name': 'Expert E3', 'color': 'Noir', 'level': 13, 'is_dan': True},
                {'name': 'Expert E4', 'color': 'Noir', 'level': 14, 'is_dan': True},
                {'name': 'Expert E5', 'color': 'Noir', 'level': 15, 'is_dan': True},
            ]
        }
    }
    
    # Compteurs pour les statistiques
    created_grades = 0
    updated_grades = 0
    failed_grades = 0
    
    print("🚀 Début de l'initialisation des grades...")
    
    # Pour chaque discipline, créer les grades
    for discipline_name, system_data in grade_systems.items():
        try:
            # Récupérer la discipline
            try:
                discipline = Discipline.objects.get(name=discipline_name)
                print(f"📋 Traitement de {discipline_name}...")
            except Discipline.DoesNotExist:
                print(f"⚠️  La discipline {discipline_name} n'existe pas, création ignorée")
                continue
            
            # Créer les grades dans une transaction
            with transaction.atomic():
                for grade_data in system_data['grades']:
                    grade, created = Grade.objects.update_or_create(
                        name=grade_data['name'],
                        discipline=discipline,
                        defaults={
                            'color': grade_data.get('color', ''),
                            'level': grade_data.get('level', 0),
                            'is_dan_grade': grade_data.get('is_dan', False),
                            'is_active': True,
                            'order': grade_data.get('level', 0),
                        }
                    )
                    
                    if created:
                        created_grades += 1
                        print(f"  ✅ Créé: {grade.name}")
                    else:
                        updated_grades += 1
                        print(f"  🔄 Mis à jour: {grade.name}")
                        
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {discipline_name}: {e}")
            failed_grades += 1
            continue
    
    # Afficher le résumé
    print("\n" + "="*60)
    print("✨ Initialisation des grades terminée!")
    print("📊 Bilan:")
    print(f"   - Grades créés: {created_grades}")
    print(f"   - Grades mis à jour: {updated_grades}")
    print(f"   - Échecs: {failed_grades}")
    print("="*60)

if __name__ == "__main__":
    initialize_grades()