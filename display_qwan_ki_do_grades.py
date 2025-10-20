#!/usr/bin/env python3
"""
Script pour afficher tous les grades de Qwan Ki Do
"""

import os
import sys
import django

def setup_django():
    """Configure Django pour la production"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()
    
    from apps.competitions.models import Discipline
    from apps.grades.models import Grade, GradeCategory
    return Discipline, Grade, GradeCategory

def display_grades():
    """Affiche tous les grades de Qwan Ki Do"""
    print('🥋 GRADES DE LA DISCIPLINE QWAN KI DO')
    print('=' * 60)
    
    # Configuration Django
    Discipline, Grade, GradeCategory = setup_django()
    
    # Trouver la discipline Qwan Ki Do
    qwan_ki_do = Discipline.objects.filter(name__icontains='Qwan Ki Do').first()
    if qwan_ki_do:
        print(f'✅ Discipline: {qwan_ki_do.name} (ID: {qwan_ki_do.id})')
        print(f'   Description: {qwan_ki_do.description}')
        print(f'   Pays d\'origine: {qwan_ki_do.country_origin}')
        print(f'   Active: {qwan_ki_do.is_active}')
        print()
        
        # Afficher les catégories
        categories = GradeCategory.objects.filter(discipline=qwan_ki_do)
        print(f'📊 Catégories de grades: {categories.count()}')
        for category in categories:
            print(f'   - {category.name}')
        print()
        
        # Afficher tous les grades
        grades = Grade.objects.filter(discipline=qwan_ki_do)
        print(f'📊 Total des grades: {grades.count()}')
        print()
        print('📝 TOUS LES GRADES QWAN KI DO:')
        print('-' * 60)
        
        for i, grade in enumerate(grades.order_by('level'), 1):
            print(f'{i:2d}. {grade.name}')
            print(f'    Niveau: {grade.level}')
            if grade.category:
                print(f'    Catégorie: {grade.category.name}')
            else:
                print(f'    Catégorie: Aucune')
            
            color = grade.color_code or grade.color or "Non définie"
            print(f'    Couleur: {color}')
            print(f'    Âge minimum: {grade.min_age} ans')
            print(f'    Temps min. grade précédent: {grade.min_time_in_previous_grade} mois')
            
            dan_status = "Oui" if grade.is_dan_grade else "Non"
            print(f'    Dan/Dang: {dan_status}')
            
            active_status = "Oui" if grade.is_active else "Non"
            print(f'    Actif: {active_status}')
            print(f'    Ordre: {grade.order}')
            
            if grade.requirements_text:
                print(f'    Exigences: {grade.requirements_text}')
            print()
    else:
        print('❌ Discipline Qwan Ki Do non trouvée')
        print()
        print('📋 Disciplines disponibles:')
        for discipline in Discipline.objects.all().order_by('name'):
            print(f'   - {discipline.name} (ID: {discipline.id})')

if __name__ == "__main__":
    display_grades()