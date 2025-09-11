#!/usr/bin/env python3
"""
Script pour investiguer le problème de traduction Django.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import Discipline
from django.db import connection

def investigate_translation_system():
    """Investigate le système de traduction."""
    
    print("🔍 INVESTIGATION DU SYSTÈME DE TRADUCTION")
    print("=" * 60)
    
    # 1. Vérification de la langue active
    from django.utils import translation
    from django.conf import settings
    print(f"🌍 Langue active: {translation.get_language()}")
    print(f"🌍 Langues configurées: {[lang[0] for lang in settings.LANGUAGES]}")
    
    # 2. Test avec activation de langue française
    print("\n📋 TEST AVEC LANGUE FRANÇAISE FORCÉE:")
    print("-" * 40)
    
    with translation.override('fr'):
        discipline = Discipline.objects.first()
        if discipline:
            print(f"Discipline (FR): '{discipline.name}'")
            print(f"Discipline name_fr: '{getattr(discipline, 'name_fr', 'N/A')}'")
            
            # Accès direct aux champs
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT name, name_fr FROM competitions_discipline WHERE id = %s", [discipline.id])
                row = cursor.fetchone()
                print(f"DB direct (name, name_fr): {row}")
    
    # 3. Test sans système de traduction
    print("\n📋 TEST SANS SYSTÈME DE TRADUCTION:")
    print("-" * 40)
    
    # Désactiver temporairement modeltranslation
    try:
        # Accès direct au modèle original
        original_discipline = Discipline._base_manager.defer().get(id=1)
        print(f"Modèle original: '{original_discipline.name}'")
    except:
        print("Impossible d'accéder au modèle original")
    
    # 4. Requête SQL brute pour voir les vraies données
    print("\n💾 DONNÉES SQL BRUTES:")
    print("-" * 40)
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, name_fr, name_en FROM competitions_discipline WHERE name != '' AND name IS NOT NULL LIMIT 3")
        rows = cursor.fetchall()
        print("Disciplines avec nom non vide:")
        for row in rows:
            print(f"  ID {row[0]}: '{row[1]}' (FR: '{row[2]}', EN: '{row[3]}')")
    
    print()
    
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, name_fr, color, color_fr, discipline_id FROM grades_grade WHERE name != '' AND name IS NOT NULL LIMIT 5")
        rows = cursor.fetchall()
        print("Grades avec nom non vide:")
        for row in rows:
            print(f"  ID {row[0]}: '{row[1]}' (FR: '{row[2]}') - Couleur: '{row[3]}' (FR: '{row[4]}') - Discipline: {row[5]}")
    
    # 5. Test de mise à jour directe
    print("\n🔧 TEST DE MISE À JOUR DIRECTE:")
    print("-" * 40)
    
    try:
        # Mise à jour d'une discipline
        with connection.cursor() as cursor:
            cursor.execute("UPDATE competitions_discipline SET name_fr = name WHERE id = 1 AND name != ''")
            cursor.execute("UPDATE grades_grade SET name_fr = name, color_fr = color WHERE discipline_id = 1 AND name != ''")
            
        print("✅ Mise à jour SQL directe effectuée")
        
        # Test du résultat
        discipline = Discipline.objects.get(id=1)
        print(f"Après mise à jour - Discipline: '{discipline.name}'")
        print(f"name_fr: '{getattr(discipline, 'name_fr', 'N/A')}'")
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")

def test_manual_fix():
    """Test une correction manuelle des données."""
    
    print("\n🛠️ CORRECTION MANUELLE DES DONNÉES")
    print("=" * 50)
    
    with connection.cursor() as cursor:
        # Correction disciplines
        cursor.execute("""
            UPDATE competitions_discipline 
            SET name_fr = name, name_en = name, 
                description_fr = description, description_en = description
            WHERE name != '' AND name IS NOT NULL
        """)
        disciplines_updated = cursor.rowcount
        
        # Correction grades
        cursor.execute("""
            UPDATE grades_grade 
            SET name_fr = name, name_en = name,
                color_fr = color, color_en = color
            WHERE name != '' AND name IS NOT NULL
        """)
        grades_updated = cursor.rowcount
        
    print(f"✅ {disciplines_updated} disciplines mises à jour")
    print(f"✅ {grades_updated} grades mis à jour")
    
    # Test final
    print("\n🧪 TEST FINAL:")
    print("-" * 20)
    
    discipline = Discipline.objects.first()
    if discipline:
        print(f"Discipline: '{discipline.name}'")
        print(f"name_fr: '{getattr(discipline, 'name_fr', 'N/A')}'")
        
        grade = Grade.objects.filter(discipline=discipline).first()
        if grade:
            print(f"Grade: '{grade.name}' - '{grade.color}'")
            print(f"name_fr: '{getattr(grade, 'name_fr', 'N/A')}' - color_fr: '{getattr(grade, 'color_fr', 'N/A')}'")

if __name__ == "__main__":
    from grades.models import Grade  # Import local pour éviter les problèmes d'ordre d'import
    try:
        investigate_translation_system()
        test_manual_fix()
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()