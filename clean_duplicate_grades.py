#!/usr/bin/env python3
"""
Script pour nettoyer les grades en doublon, en gardant les grades avec catégories.
"""

import os
import sys
import django

# Setup Django
sys.path.append('/mnt/c/martial_hub_django/martialcomp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from grades.models import Grade

def clean_duplicate_grades():
    """Nettoie les grades en doublon en gardant ceux avec catégories."""
    
    print("🧹 Nettoyage des grades en doublon...")
    
    # Récupérer tous les grades groupés par discipline et nom
    from collections import defaultdict
    grade_groups = defaultdict(list)
    
    for grade in Grade.objects.all().order_by('id'):
        key = (grade.discipline.name, grade.name.lower().strip())
        grade_groups[key].append(grade)
    
    deleted_count = 0
    kept_count = 0
    
    for (discipline_name, grade_name), grades in grade_groups.items():
        if len(grades) > 1:
            print(f"\n📋 Doublons trouvés pour '{grade_name}' ({discipline_name}):")
            
            # Trier les grades : priorité à ceux avec catégorie, puis par ID décroissant
            grades_sorted = sorted(grades, key=lambda x: (
                x.category is not None,  # True first (avec catégorie)
                x.id  # Plus récent (ID plus élevé)
            ), reverse=True)
            
            # Garder le premier (meilleur) et supprimer les autres
            grade_to_keep = grades_sorted[0]
            grades_to_delete = grades_sorted[1:]
            
            print(f"  ✅ Garde: {grade_to_keep.name} (ID: {grade_to_keep.id}) - Catégorie: {grade_to_keep.category or 'Aucune'}")
            
            for grade_to_delete in grades_to_delete:
                print(f"  🗑️  Supprime: {grade_to_delete.name} (ID: {grade_to_delete.id}) - Catégorie: {grade_to_delete.category or 'Aucune'}")
                try:
                    grade_to_delete.delete()
                    deleted_count += 1
                except Exception as e:
                    print(f"    ❌ Erreur lors de la suppression: {e}")
            
            kept_count += 1
        else:
            kept_count += 1
    
    print(f"\n" + "="*60)
    print(f"✨ Nettoyage terminé!")
    print(f"📊 Bilan:")
    print(f"   - Grades supprimés: {deleted_count}")
    print(f"   - Grades conservés: {kept_count}")
    print("="*60)
    
    # Vérification finale
    print("\n🔍 Vérification finale par discipline:")
    from competitions.models import Discipline
    for discipline in Discipline.objects.filter(is_active=True):
        count = Grade.objects.filter(discipline=discipline, is_active=True).count()
        print(f"   - {discipline.name}: {count} grades")

if __name__ == "__main__":
    clean_duplicate_grades()