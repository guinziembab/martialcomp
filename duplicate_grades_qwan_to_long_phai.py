#!/usr/bin/env python3
"""
Script de duplication des grades Qwan Ki Do vers Long Phai
Duplique tous les grades et catégories de Qwan Ki Do vers la discipline Long Phai
"""

import os
import sys
import django
from datetime import datetime

def setup_django():
    """Configure Django pour la production"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()
    
    from apps.grades.models import Grade, GradeCategory
    from apps.competitions.models import Discipline
    return Grade, GradeCategory, Discipline

def duplicate_grades():
    """Duplique les grades de Qwan Ki Do vers Long Phai"""
    print("🔄 DUPLICATION DES GRADES QWAN KI DO VERS LONG PHAI")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configuration Django
    Grade, GradeCategory, Discipline = setup_django()
    
    # Trouver les disciplines
    print("1️⃣ Recherche des disciplines...")
    
    qwan_ki_do = Discipline.objects.filter(name__icontains='Qwan Ki Do').first()
    long_phai = Discipline.objects.filter(name__icontains='Long Phai').first()
    
    if not qwan_ki_do:
        print("❌ Discipline Qwan Ki Do non trouvée")
        return False
    
    if not long_phai:
        print("❌ Discipline Long Phai non trouvée")
        return False
    
    print(f"✅ Discipline source: {qwan_ki_do.name} (ID: {qwan_ki_do.id})")
    print(f"✅ Discipline cible: {long_phai.name} (ID: {long_phai.id})")
    print()
    
    # Vérifier l'état actuel
    print("2️⃣ Analyse de l'état actuel...")
    
    qwan_grades = Grade.objects.filter(discipline=qwan_ki_do)
    qwan_categories = GradeCategory.objects.filter(discipline=qwan_ki_do)
    long_phai_grades = Grade.objects.filter(discipline=long_phai)
    long_phai_categories = GradeCategory.objects.filter(discipline=long_phai)
    
    print(f"📊 Qwan Ki Do:")
    print(f"   - Catégories: {qwan_categories.count()}")
    print(f"   - Grades: {qwan_grades.count()}")
    print(f"📊 Long Phai (avant duplication):")
    print(f"   - Catégories: {long_phai_categories.count()}")
    print(f"   - Grades: {long_phai_grades.count()}")
    print()
    
    # Dupliquer les catégories
    print("3️⃣ Duplication des catégories de grades...")
    
    categories_duplicated = 0
    category_mapping = {}
    
    for qwan_category in qwan_categories:
        # Vérifier si la catégorie existe déjà
        try:
            existing_category = GradeCategory.objects.get(
                name=qwan_category.name,
                discipline=long_phai
            )
            category_mapping[qwan_category.id] = existing_category
            print(f"   ✅ Catégorie existante: {qwan_category.name}")
        except GradeCategory.DoesNotExist:
            # Créer nouvelle catégorie
            new_category = GradeCategory.objects.create(
                name=qwan_category.name,
                description=qwan_category.description,
                discipline=long_phai,
                order=qwan_category.order,
                is_active=qwan_category.is_active
            )
            category_mapping[qwan_category.id] = new_category
            categories_duplicated += 1
            print(f"   ✅ Ajoutée: {qwan_category.name}")
    
    print(f"   📊 Catégories dupliquées: {categories_duplicated}")
    print()
    
    # Dupliquer les grades
    print("4️⃣ Duplication des grades...")
    
    grades_duplicated = 0
    grades_skipped = 0
    
    for qwan_grade in qwan_grades:
        # Vérifier si le grade existe déjà
        try:
            existing_grade = Grade.objects.get(
                name=qwan_grade.name,
                discipline=long_phai
            )
            grades_skipped += 1
            print(f"   ⚠️ Grade existant ignoré: {qwan_grade.name}")
        except Grade.DoesNotExist:
            # Trouver la catégorie correspondante
            category = None
            if qwan_grade.category and qwan_grade.category.id in category_mapping:
                category = category_mapping[qwan_grade.category.id]
            
            # Créer nouveau grade
            new_grade = Grade.objects.create(
                name=qwan_grade.name,
                discipline=long_phai,
                category=category,
                color=qwan_grade.color,
                color_code=qwan_grade.color_code,
                level=qwan_grade.level,
                min_age=qwan_grade.min_age,
                min_time_in_previous_grade=qwan_grade.min_time_in_previous_grade,
                requirements_text=qwan_grade.requirements_text,
                is_active=qwan_grade.is_active,
                is_dan_grade=qwan_grade.is_dan_grade,
                order=qwan_grade.order
            )
            grades_duplicated += 1
            print(f"   ✅ Ajouté: {qwan_grade.name} - Niveau {qwan_grade.level}")
    
    print(f"   📊 Grades dupliqués: {grades_duplicated}")
    print(f"   📊 Grades ignorés (existants): {grades_skipped}")
    print()
    
    # Vérification finale
    print("5️⃣ Vérification finale...")
    
    final_long_phai_grades = Grade.objects.filter(discipline=long_phai)
    final_long_phai_categories = GradeCategory.objects.filter(discipline=long_phai)
    
    print(f"📊 Long Phai (après duplication):")
    print(f"   - Catégories: {final_long_phai_categories.count()}")
    print(f"   - Grades: {final_long_phai_grades.count()}")
    print()
    
    # Afficher les grades dupliqués
    print("📝 GRADES DISPONIBLES POUR LONG PHAI:")
    for i, grade in enumerate(final_long_phai_grades.order_by('level'), 1):
        print(f"   {i:2d}. {grade.name} - Niveau {grade.level}")
    
    print()
    print("🎉 Duplication des grades terminée avec succès!")
    print(f"✅ {grades_duplicated} grades ajoutés à Long Phai")
    print(f"✅ {categories_duplicated} catégories ajoutées à Long Phai")
    
    return True

def main():
    """Fonction principale"""
    try:
        success = duplicate_grades()
        if success:
            print("\n✅ Les grades Qwan Ki Do ont été dupliqués vers Long Phai")
        else:
            print("\n❌ La duplication a échoué")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors de la duplication: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()