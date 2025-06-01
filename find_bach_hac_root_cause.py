#!/usr/bin/env python3
"""
Script pour trouver la cause racine du problème BACH HAC
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import *
from django.db import connection
import traceback

def find_root_cause():
    """Trouve la cause racine exacte du problème"""
    print("=== Recherche de la cause racine du problème 'BACH HAC' ===\n")
    
    # 1. Vérifier la ligne exacte qui cause l'erreur
    print("1. Simulation de l'erreur dans la vue technical_scoring")
    
    try:
        # Obtenir un club pour tester
        test_club = Club.objects.first()
        print(f"Test avec le club: {test_club.name}")
        
        # Tester la requête des juges  
        print("\n2. Test de la requête des juges...")
        try:
            judges_query = Judge.objects.filter(
                practitioner__club=test_club,
                is_technical_judge=True
            )
            print(f"   SQL: {judges_query.query}")
            judges_count = judges_query.count()
            print(f"   Résultat: {judges_count} juges")
        except Exception as e:
            print(f"   ERREUR: {e}")
            traceback.print_exc()
        
        # Test des performances
        print("\n3. Test de différentes requêtes de performances...")
        
        # Test 1: Filtre direct
        try:
            print("   Test 1: Filtre direct par club")
            perf1 = TechnicalPerformance.objects.filter(
                practitioner__club=test_club
            )
            print(f"   SQL: {perf1.query}")
            count = perf1.count()
            print(f"   Résultat: {count} performances")
        except Exception as e:
            print(f"   ERREUR: {e}")
            print(f"   Type d'erreur: {type(e)}")
            traceback.print_exc()
        
        # Test 2: Filtre par ID 
        try:
            print("\n   Test 2: Filtre par IDs de pratiquants")
            practitioner_ids = Practitioner.objects.filter(club=test_club).values_list('id', flat=True)
            perf2 = TechnicalPerformance.objects.filter(
                practitioner_id__in=practitioner_ids
            )
            count = perf2.count()
            print(f"   Résultat: {count} performances")
        except Exception as e:
            print(f"   ERREUR: {e}")
            traceback.print_exc()
        
    except Exception as e:
        print(f"Erreur générale: {e}")
        traceback.print_exc()
    
    # 4. Recherche de données corrompues
    print("\n4. Recherche de données potentiellement corrompues...")
    
    with connection.cursor() as cursor:
        # Vérifier les performances avec practitioner_id invalides
        cursor.execute("""
            SELECT tp.id, tp.practitioner_id
            FROM competitions_technicalperformance tp
            LEFT JOIN competitions_practitioner p ON tp.practitioner_id = p.id
            WHERE p.id IS NULL
        """)
        invalid_performances = cursor.fetchall()
        
        if invalid_performances:
            print(f"   Performances avec practitioner_id invalide: {len(invalid_performances)}")
            for perf_id, pract_id in invalid_performances[:5]:
                print(f"     - Performance {perf_id}: practitioner_id={pract_id}")
        
        # Rechercher des valeurs textuelles dans practitioner_id
        try:
            cursor.execute("""
                SELECT id, practitioner_id::text
                FROM competitions_technicalperformance
                WHERE practitioner_id::text NOT SIMILAR TO '[0-9]+'
                LIMIT 10
            """)
            text_ids = cursor.fetchall()
            
            if text_ids:
                print(f"\n   Performances avec practitioner_id non numérique: {len(text_ids)}")
                for perf_id, pract_id in text_ids:
                    print(f"     - Performance {perf_id}: practitioner_id='{pract_id}'")
        except:
            # Essayer une autre approche
            try:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM competitions_technicalperformance
                    WHERE practitioner_id < 0
                """)
                negative_count = cursor.fetchone()[0]
                print(f"\n   Performances avec practitioner_id négatif: {negative_count}")
            except:
                pass
    
    # 5. Vérifier si le problème est dans le decorator @club_required
    print("\n5. Vérification du décorateur @club_required...")
    try:
        from competitions.utils.decorators import club_required
        import inspect
        print(f"   Code du décorateur:")
        print(inspect.getsource(club_required))
    except Exception as e:
        print(f"   Erreur lors de l'inspection du décorateur: {e}")

def create_clean_test():
    """Crée un test propre pour isoler le problème"""
    print("\n=== Test propre pour isoler le problème ===")
    
    test_code = '''
# Test isolé du problème
from competitions.models import Club, TechnicalPerformance, Judge

# Test 1: Obtenir un club
try:
    club = Club.objects.get(name__icontains="BACH HAC")
    print(f"Club trouvé: {club.name} (ID: {club.id})")
except Club.DoesNotExist:
    print("Aucun club 'BACH HAC' trouvé")
    club = Club.objects.first()
    print(f"Utilisation du club: {club.name}")

# Test 2: Requête problématique 
try:
    performances = TechnicalPerformance.objects.filter(
        practitioner__club=club
    )
    print(f"Performances trouvées: {performances.count()}")
except Exception as e:
    print(f"ERREUR DÉTECTÉE: {e}")
    print(f"Type d'erreur: {type(e)}")
    
    # Essayer de comprendre pourquoi
    import traceback
    traceback.print_exc()
    
    # Vérifier le type de 'club'
    print(f"\\nType de 'club': {type(club)}")
    print(f"Valeur de 'club': {club}")
    
    # Vérifier si club a un attribut étrange
    for attr in dir(club):
        if not attr.startswith('_'):
            try:
                value = getattr(club, attr)
                if isinstance(value, str) and "BACH HAC" in value:
                    print(f"Attribut '{attr}' contient 'BACH HAC': {value}")
            except:
                pass
'''
    
    with open('test_bach_hac_isolated.py', 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    print("Test isolé créé: test_bach_hac_isolated.py")

if __name__ == "__main__":
    find_root_cause()
    create_clean_test()
    
    print("\n=== CONCLUSION ===")
    print("1. L'erreur indique qu'une chaîne 'BACH HAC' est utilisée là où un objet Practitioner est attendu")
    print("2. Le problème peut venir:")
    print("   - D'un club mal configuré avec le nom 'BACH HAC'")
    print("   - D'un décorateur @club_required qui assigne incorrectement request.club")
    print("   - De données corrompues dans la base de données")
    print("\n3. Solution temporaire:")
    print("   - Utilisez /competitions/club/technical-scoring/ (avec le hotfix)")
    print("   - Ou examinez les résultats des scripts de diagnostic")
    print("   - Vérifiez si request.club est bien un objet Club et non une chaîne")