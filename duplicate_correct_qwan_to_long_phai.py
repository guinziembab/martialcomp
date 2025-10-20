#!/usr/bin/env python3
"""
Script de duplication du vrai système Qwan Ki Do vers Long Phai
"""

import os
import sys
import django
from datetime import datetime

def setup_django():
    """Configure Django pour la production"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()
    
    from apps.competitions.models import Discipline
    from apps.grades.models import Grade, GradeCategory
    return Discipline, Grade, GradeCategory

def duplicate_correct_system():
    """Duplique le vrai système Qwan Ki Do vers Long Phai"""
    print("🔄 DUPLICATION DU VRAI SYSTÈME QWAN KI DO VERS LONG PHAI")
    print("=" * 70)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configuration Django
    Discipline, Grade, GradeCategory = setup_django()
    
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
    
    # Supprimer l'ancien système incorrect de Long Phai
    print("2️⃣ Suppression de l'ancien système Long Phai...")
    
    old_grades = Grade.objects.filter(discipline=long_phai)
    old_categories = GradeCategory.objects.filter(discipline=long_phai)
    
    grades_deleted = old_grades.count()
    categories_deleted = old_categories.count()
    
    old_grades.delete()
    old_categories.delete()
    
    print(f"   ✅ {grades_deleted} anciens grades supprimés")
    print(f"   ✅ {categories_deleted} anciennes catégories supprimées")
    print()
    
    # Récupérer le vrai système Qwan Ki Do
    print("3️⃣ Récupération du vrai système Qwan Ki Do...")
    
    qwan_categories = GradeCategory.objects.filter(discipline=qwan_ki_do)
    qwan_grades = Grade.objects.filter(discipline=qwan_ki_do)
    
    print(f"   📊 Catégories Qwan Ki Do: {qwan_categories.count()}")
    print(f"   📊 Grades Qwan Ki Do: {qwan_grades.count()}")
    print()
    
    # Dupliquer les catégories
    print("4️⃣ Duplication des catégories...")
    
    category_mapping = {}
    categories_duplicated = 0
    
    for qwan_category in qwan_categories:
        new_category = GradeCategory.objects.create(
            name=qwan_category.name,
            description=qwan_category.description,
            discipline=long_phai,
            order=qwan_category.order,
            is_active=qwan_category.is_active
        )
        category_mapping[qwan_category.id] = new_category
        categories_duplicated += 1
        print(f"   ✅ Catégorie dupliquée: {qwan_category.name}")
    
    print(f"   📊 {categories_duplicated} catégories dupliquées")
    print()
    
    # Dupliquer les grades
    print("5️⃣ Duplication des grades...")
    
    grades_duplicated = 0
    
    for qwan_grade in qwan_grades:
        # Trouver la catégorie correspondante
        category = None
        if qwan_grade.category and qwan_grade.category.id in category_mapping:
            category = category_mapping[qwan_grade.category.id]
        
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
        print(f"   ✅ Grade dupliqué: {qwan_grade.name} (Niveau {qwan_grade.level})")
    
    print(f"   📊 {grades_duplicated} grades dupliqués")
    print()
    
    # Vérification finale
    print("6️⃣ Vérification finale...")
    
    final_long_phai_categories = GradeCategory.objects.filter(discipline=long_phai).count()
    final_long_phai_grades = Grade.objects.filter(discipline=long_phai).count()
    
    print(f"✅ Catégories Long Phai: {final_long_phai_categories}")
    print(f"✅ Grades Long Phai: {final_long_phai_grades}")
    
    # Afficher quelques exemples
    print()
    print("📝 EXEMPLES DE GRADES LONG PHAI:")
    for i, grade in enumerate(Grade.objects.filter(discipline=long_phai).order_by('level')[:10], 1):
        print(f"   {i:2d}. {grade.name} - Niveau {grade.level} - {grade.color}")
    
    print()
    print("🎉 Duplication du vrai système terminée avec succès!")
    print(f"✅ {grades_duplicated} grades dupliqués vers Long Phai")
    print(f"✅ {categories_duplicated} catégories dupliquées vers Long Phai")
    
    return True

def main():
    """Fonction principale"""
    try:
        success = duplicate_correct_system()
        if success:
            print("\n✅ Long Phai dispose maintenant du vrai système Qwan Ki Do")
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