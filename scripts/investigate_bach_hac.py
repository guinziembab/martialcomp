#!/usr/bin/env python3
"""
Script pour investiguer le problème "BACH HAC"
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import TechnicalPerformance, Practitioner, Club
from django.db import connection

def investigate_bach_hac():
    """Recherche l'origine du problème "BACH HAC" """
    print("=== Investigation du problème 'BACH HAC' ===\n")
    
    # 1. Vérifier s'il y a un club nommé "BACH HAC"
    clubs = Club.objects.filter(name__icontains="BACH HAC")
    if clubs.exists():
        print(f"Clubs trouvés avec 'BACH HAC': {clubs.count()}")
        for club in clubs:
            print(f"- Club {club.id}: {club.name}")
            practitioner_count = Practitioner.objects.filter(club=club).count()
            print(f"  Nombre de pratiquants: {practitioner_count}")
    else:
        print("Aucun club trouvé avec 'BACH HAC'")
    
    # 2. Vérifier s'il y a des pratiquants nommés "BACH HAC"
    practitioners = Practitioner.objects.filter(full_name__icontains="BACH HAC")
    if practitioners.exists():
        print(f"\nPratiquants trouvés avec 'BACH HAC': {practitioners.count()}")
        for p in practitioners:
            print(f"- Practitioner {p.id}: {p.full_name} (club: {p.club})")
    else:
        print("\nAucun pratiquant trouvé avec 'BACH HAC'")
    
    # 3. Vérifier la structure de la base de données
    print("\n=== Structure de la table TechnicalPerformance ===")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'competitions_technicalperformance'
            ORDER BY ordinal_position
        """)
        columns = cursor.fetchall()
        for col in columns:
            print(f"- {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
    
    # 4. Vérifier s'il y a des performances avec des références incorrectes
    print("\n=== Vérification des performances techniques ===")
    with connection.cursor() as cursor:
        # Requête pour voir les données brutes
        cursor.execute("""
            SELECT 
                tp.id,
                tp.practitioner_id,
                p.full_name,
                p.club_id,
                c.name as club_name
            FROM competitions_technicalperformance tp
            LEFT JOIN competitions_practitioner p ON tp.practitioner_id = p.id
            LEFT JOIN competitions_club c ON p.club_id = c.id
            WHERE p.id IS NULL
            OR p.full_name LIKE '%BACH HAC%'
            OR c.name LIKE '%BACH HAC%'
            LIMIT 10
        """)
        results = cursor.fetchall()
        
        if results:
            print("Performances avec références potentiellement problématiques:")
            for row in results:
                print(f"- Performance {row[0]}: practitioner_id={row[1]}, practitioner={row[2]}, club={row[4]}")
        else:
            print("Aucune performance problématique trouvée")
    
    # 5. Recherche d'erreurs de données spécifiques
    print("\n=== Recherche d'erreurs de données ===")
    try:
        # Essayer de voir si on peut récupérer toutes les performances
        all_performances = TechnicalPerformance.objects.all()
        problematic_count = 0
        
        for perf in all_performances:
            try:
                # Accéder au practitioner pour forcer le chargement
                practitioner_name = perf.practitioner.full_name if perf.practitioner else "None"
            except Exception as e:
                problematic_count += 1
                print(f"Erreur avec performance {perf.id}: {str(e)}")
        
        print(f"Total de performances: {all_performances.count()}")
        print(f"Performances problématiques: {problematic_count}")
        
    except Exception as e:
        print(f"Erreur lors de la vérification des performances: {str(e)}")

def suggest_fixes():
    """Suggère des corrections possibles"""
    print("\n=== Suggestions de correction ===")
    print("1. Si 'BACH HAC' est un club et non un pratiquant:")
    print("   - Identifier les performances qui ont été mal assignées")
    print("   - Créer un script de migration pour corriger les références")
    print("\n2. Vérifier les contraintes de clé étrangère:")
    print("   - S'assurer que toutes les performances ont un practitioner_id valide")
    print("   - Supprimer ou corriger les performances orphelines")
    print("\n3. Modifier la vue pour gérer les cas d'erreur:")
    print("   - Utiliser la vue technical_scoring_fixed qui gère mieux les erreurs")
    print("   - Ajouter plus de logging pour identifier l'origine du problème")

def create_data_fix_script():
    """Crée un script pour corriger les données"""
    script_content = '''#!/usr/bin/env python3
"""
Script pour corriger les données TechnicalPerformance problématiques
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models import TechnicalPerformance, Practitioner, Club
from django.db import transaction

@transaction.atomic
def fix_technical_performances():
    """Corrige les performances avec des références invalides"""
    
    # 1. Identifier les performances problématiques
    problematic_performances = []
    
    for perf in TechnicalPerformance.objects.all():
        try:
            if not perf.practitioner or not isinstance(perf.practitioner, Practitioner):
                problematic_performances.append(perf)
        except:
            problematic_performances.append(perf)
    
    print(f"Performances problématiques trouvées: {len(problematic_performances)}")
    
    # 2. Essayer de corriger chaque performance
    for perf in problematic_performances:
        print(f"\\nCorrection de la performance {perf.id}")
        
        # Obtenir des informations de contexte
        try:
            # Si on a un practitioner_id, essayer de le charger
            if hasattr(perf, 'practitioner_id') and perf.practitioner_id:
                practitioner = Practitioner.objects.filter(id=perf.practitioner_id).first()
                if practitioner:
                    perf.practitioner = practitioner
                    perf.save()
                    print(f"  Practitioner corrigé: {practitioner.full_name}")
                else:
                    print(f"  Practitioner ID {perf.practitioner_id} introuvable")
            else:
                print("  Pas de practitioner_id valide")
        except Exception as e:
            print(f"  Erreur: {str(e)}")
    
    print("\\nCorrection terminée")

if __name__ == "__main__":
    fix_technical_performances()
'''
    
    with open('fix_technical_performance_data.py', 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print("Script de correction créé: fix_technical_performance_data.py")

def main():
    """Fonction principale"""
    investigate_bach_hac()
    suggest_fixes()
    create_data_fix_script()

if __name__ == "__main__":
    main()