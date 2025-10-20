#!/usr/bin/env python3
"""
Script pour analyser le statut complet des langues en développement
"""

import os
import glob
from collections import defaultdict

def analyze_languages():
    """Analyse le statut de toutes les langues"""
    
    print("🌍 STATUT COMPLET DES LANGUES EN DÉVELOPPEMENT")
    print("=" * 50)
    
    # Langues traduites par l'utilisateur
    translated_languages = {
        'ja': 'Japonais',
        'zh': 'Chinois',
        'hi': 'Hindi', 
        'am': 'Amharique',
        'vi': 'Vietnamien',
        'ko': 'Coréen'
    }
    
    # Langues existantes
    existing_languages = {
        'fr': 'Français',
        'en': 'Anglais',
        'es': 'Espagnol',
        'de': 'Allemand',
        'it': 'Italien',
        'pt': 'Portugais',
        'ru': 'Russe',
        'ar': 'Arabe',
        'no': 'Norvégien',
        'sw': 'Swahili',
        'yo': 'Yoruba',
        'zu': 'Zoulou',
        'ja': 'Japonais',
        'zh': 'Chinois',
        'hi': 'Hindi',
        'am': 'Amharique',
        'vi': 'Vietnamien',
        'ko': 'Coréen'
    }
    
    # Analyser chaque langue
    results = {}
    
    for lang_code, lang_name in existing_languages.items():
        lang_dir = f"locale/{lang_code}"
        lc_messages_dir = f"{lang_dir}/LC_MESSAGES"
        po_file = f"{lc_messages_dir}/django.po"
        mo_file = f"{lc_messages_dir}/django.mo"
        
        result = {
            'name': lang_name,
            'code': lang_code,
            'directory_exists': os.path.exists(lang_dir),
            'lc_messages_exists': os.path.exists(lc_messages_dir),
            'po_exists': os.path.exists(po_file),
            'mo_exists': os.path.exists(mo_file),
            'message_count': 0,
            'is_translated': lang_code in translated_languages
        }
        
        # Compter les messages si le fichier .po existe
        if result['po_exists']:
            try:
                with open(po_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    result['message_count'] = content.count('msgid "')
            except Exception as e:
                result['message_count'] = f"Erreur: {e}"
        
        results[lang_code] = result
    
    # Afficher les résultats
    print("\n📊 LANGUES TRADUITES PAR L'UTILISATEUR:")
    print("-" * 40)
    
    for lang_code in translated_languages.keys():
        if lang_code in results:
            result = results[lang_code]
            status = "✅ COMPLET" if result['po_exists'] and result['mo_exists'] else "❌ INCOMPLET"
            print(f"🔤 {result['name']} ({lang_code}): {status}")
            print(f"   📁 Dossier: {'✅' if result['directory_exists'] else '❌'}")
            print(f"   📄 Fichier .po: {'✅' if result['po_exists'] else '❌'}")
            print(f"   📦 Fichier .mo: {'✅' if result['mo_exists'] else '❌'}")
            print(f"   📊 Messages: {result['message_count']}")
            print()
    
    print("\n📊 TOUTES LES LANGUES DISPONIBLES:")
    print("-" * 40)
    
    # Grouper par statut
    complete_languages = []
    incomplete_languages = []
    missing_languages = []
    
    for lang_code, result in results.items():
        if result['directory_exists'] and result['po_exists'] and result['mo_exists']:
            complete_languages.append(result)
        elif result['directory_exists'] or result['po_exists']:
            incomplete_languages.append(result)
        else:
            missing_languages.append(result)
    
    print(f"\n✅ LANGUES COMPLÈTES ({len(complete_languages)}):")
    for result in complete_languages:
        translated_mark = " 🌟" if result['is_translated'] else ""
        print(f"   {result['name']} ({result['code']}) - {result['message_count']} messages{translated_mark}")
    
    print(f"\n⚠️  LANGUES INCOMPLÈTES ({len(incomplete_languages)}):")
    for result in incomplete_languages:
        issues = []
        if not result['directory_exists']:
            issues.append("Dossier manquant")
        if not result['po_exists']:
            issues.append("Fichier .po manquant")
        if not result['mo_exists']:
            issues.append("Fichier .mo manquant")
        
        translated_mark = " 🌟" if result['is_translated'] else ""
        print(f"   {result['name']} ({result['code']}) - {', '.join(issues)}{translated_mark}")
    
    if missing_languages:
        print(f"\n❌ LANGUES MANQUANTES ({len(missing_languages)}):")
        for result in missing_languages:
            print(f"   {result['name']} ({result['code']})")
    
    # Statistiques globales
    print(f"\n📈 STATISTIQUES GLOBALES:")
    print("-" * 30)
    print(f"   Total langues configurées: {len(existing_languages)}")
    print(f"   Langues complètes: {len(complete_languages)}")
    print(f"   Langues incomplètes: {len(incomplete_languages)}")
    print(f"   Langues traduites par l'utilisateur: {len(translated_languages)}")
    
    # Vérifier la cohérence des messages
    if complete_languages:
        message_counts = [r['message_count'] for r in complete_languages if isinstance(r['message_count'], int)]
        if message_counts:
            min_count = min(message_counts)
            max_count = max(message_counts)
            if min_count == max_count:
                print(f"   Messages par langue: {min_count} (cohérent)")
            else:
                print(f"   Messages par langue: {min_count}-{max_count} (incohérent)")
    
    return results

if __name__ == "__main__":
    analyze_languages()