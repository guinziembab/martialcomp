#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour mettre à jour tous les fichiers PO de toutes les langues
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Liste des langues à mettre à jour (exclure Test)
LANGUAGES = [
    'am', 'ar', 'de', 'en', 'es', 'fr', 'hi', 'it', 'ja', 
    'ko', 'no', 'pt', 'ru', 'sw', 'vi', 'yo', 'zh', 'zu'
]

def update_po_file(language):
    """Met à jour le fichier PO pour une langue donnée"""
    print(f"\n{'='*80}")
    print(f"🌍 Mise à jour du fichier PO pour la langue: {language.upper()}")
    print(f"{'='*80}")
    
    try:
        # Exécuter makemessages pour cette langue
        cmd = [
            'python3', 'manage.py', 'makemessages',
            '-l', language,
            '--no-obsolete',
            '--no-wrap'
        ]
        
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode == 0:
            print(f"✅ Fichier PO mis à jour avec succès pour {language.upper()}")
            # Afficher les dernières lignes de sortie pour voir les statistiques
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:  # Dernières 10 lignes
                    if line.strip():
                        print(f"   {line}")
            return True
        else:
            print(f"⚠️  Avertissements lors de la mise à jour pour {language.upper()}")
            if result.stderr:
                # Filtrer les erreurs non critiques
                error_lines = result.stderr.strip().split('\n')
                for line in error_lines:
                    if 'UnicodeDecodeError' in line or 'CommandError' in line:
                        if 'skipped file' not in line.lower():
                            print(f"   ⚠️  {line}")
            # Chercher les statistiques dans stdout même si returncode != 0
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[-10:]:
                    if 'processing' in line.lower() or 'fuzzy' in line.lower() or 'untranslated' in line.lower():
                        print(f"   {line}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ Timeout lors de la mise à jour pour {language.upper()}")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour pour {language.upper()}: {e}")
        return False

def update_all_po_files():
    """Met à jour tous les fichiers PO de toutes les langues"""
    print("="*80)
    print("📝 MISE À JOUR DE TOUS LES FICHIERS PO")
    print("="*80)
    print(f"\nLangues à traiter: {', '.join(LANGUAGES)}")
    print(f"Total: {len(LANGUAGES)} langues\n")
    
    results = {}
    success_count = 0
    warning_count = 0
    error_count = 0
    
    for language in LANGUAGES:
        success = update_po_file(language)
        if success:
            results[language] = 'success'
            success_count += 1
        else:
            results[language] = 'warning'
            warning_count += 1
    
    # Résumé final
    print("\n" + "="*80)
    print("📊 RÉSUMÉ DE LA MISE À JOUR")
    print("="*80)
    print(f"\n✅ Succès: {success_count}/{len(LANGUAGES)}")
    print(f"⚠️  Avertissements: {warning_count}/{len(LANGUAGES)}")
    
    if warning_count > 0:
        print("\n⚠️  Langues avec avertissements:")
        for lang, status in results.items():
            if status == 'warning':
                print(f"   - {lang.upper()}")
    
    print("\n✅ Mise à jour terminée !")
    print("\n💡 Prochaine étape: Compiler les traductions avec")
    print("   python3 manage.py compilemessages")
    
    return results

if __name__ == "__main__":
    update_all_po_files()
