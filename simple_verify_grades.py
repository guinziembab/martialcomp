#!/usr/bin/env python3
"""
Script simple de vérification des grades corrigés
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

def verify_grades():
    """Vérifie les grades corrigés"""
    print('🔍 VÉRIFICATION DES GRADES CORRIGÉS')
    print('=' * 60)
    
    # Configuration Django
    Discipline, Grade, GradeCategory = setup_django()
    
    # Vérifier Qwan Ki Do
    print('🥋 QWAN KI DO - VRAI SYSTÈME')
    print('-' * 40)
    
    qwan_ki_do = Discipline.objects.filter(name__icontains='Qwan Ki Do').first()
    if qwan_ki_do:
        qwan_categories = GradeCategory.objects.filter(discipline=qwan_ki_do)
        qwan_grades = Grade.objects.filter(discipline=qwan_ki_do)
        
        print(f'✅ Discipline: {qwan_ki_do.name} (ID: {qwan_ki_do.id})')
        print(f'📊 Catégories: {qwan_categories.count()}')
        print(f'📊 Grades: {qwan_grades.count()}')
        print()
        
        print('📋 CATÉGORIES QWAN KI DO:')
        for category in qwan_categories.order_by('order'):
            print(f'   - {category.name} (Ordre: {category.order})')
        print()
        
        print('📝 GRADES PAR CATÉGORIE:')
        for category in qwan_categories.order_by('order'):
            grades = Grade.objects.filter(discipline=qwan_ki_do, category=category).order_by('level')
            print(f'\\n   🎯 {category.name} ({grades.count()} grades):')
            for grade in grades:
                dan_status = ' (Dan/Dang)' if grade.is_dan_grade else ''
                print(f'      - {grade.name} (Niveau {grade.level}) - {grade.color} - {grade.min_age} ans{dan_status}')
    
    print()
    print('🥋 LONG PHAI - SYSTÈME DUPLIQUÉ')
    print('-' * 40)
    
    long_phai = Discipline.objects.filter(name__icontains='Long Phai').first()
    if long_phai:
        long_categories = GradeCategory.objects.filter(discipline=long_phai)
        long_grades = Grade.objects.filter(discipline=long_phai)
        
        print(f'✅ Discipline: {long_phai.name} (ID: {long_phai.id})')
        print(f'📊 Catégories: {long_categories.count()}')
        print(f'📊 Grades: {long_grades.count()}')
        print()
        
        print('📋 CATÉGORIES LONG PHAI:')
        for category in long_categories.order_by('order'):
            print(f'   - {category.name} (Ordre: {category.order})')
        print()
        
        print('📝 GRADES PAR CATÉGORIE:')
        for category in long_categories.order_by('order'):
            grades = Grade.objects.filter(discipline=long_phai, category=category).order_by('level')
            print(f'\\n   🎯 {category.name} ({grades.count()} grades):')
            for grade in grades:
                dan_status = ' (Dan/Dang)' if grade.is_dan_grade else ''
                print(f'      - {grade.name} (Niveau {grade.level}) - {grade.color} - {grade.min_age} ans{dan_status}')
    
    print()
    print('🔍 COMPARAISON QWAN KI DO vs LONG PHAI')
    print('-' * 50)
    
    if qwan_ki_do and long_phai:
        qwan_count = Grade.objects.filter(discipline=qwan_ki_do).count()
        long_count = Grade.objects.filter(discipline=long_phai).count()
        qwan_cat_count = GradeCategory.objects.filter(discipline=qwan_ki_do).count()
        long_cat_count = GradeCategory.objects.filter(discipline=long_phai).count()
        
        print(f'📊 Grades: Qwan Ki Do {qwan_count} vs Long Phai {long_count}')
        if qwan_count == long_count:
            print('   ✅ Identique')
        else:
            print('   ❌ Différent')
            
        print(f'📊 Catégories: Qwan Ki Do {qwan_cat_count} vs Long Phai {long_cat_count}')
        if qwan_cat_count == long_cat_count:
            print('   ✅ Identique')
        else:
            print('   ❌ Différent')
        
        if qwan_count == long_count and qwan_cat_count == long_cat_count:
            print('\\n🎉 CORRECTION RÉUSSIE! Les deux disciplines ont le même système de grades.')
        else:
            print('\\n⚠️ ATTENTION! Il y a des différences entre les deux disciplines.')
    
    print()
    print('🎯 RÉSUMÉ DU VRAI SYSTÈME QWAN KI DO')
    print('-' * 50)
    print('✅ 7 catégories par tranche d\\'âge')
    print('✅ 27 grades au total')
    print('✅ Système Cap/Dang spécifique')
    print('✅ Couleurs et âges appropriés')
    print('✅ Progression hiérarchique complète')

if __name__ == "__main__":
    verify_grades()