#!/usr/bin/env python3
"""
Traduction automatique de toutes les chaînes manquantes
Utilise un dictionnaire de traduction automatique FR->EN
"""

import re

# Charger la liste des chaînes manquantes
with open('missing_translations_full.txt', 'r', encoding='utf-8') as f:
    missing = [line.strip() for line in f if line.strip()]

print(f"Chargement de {len(missing)} chaînes manquantes...")
print()

# Dictionnaire de traduction automatique basique
def auto_translate_fr_to_en(french_text):
    """Traduction automatique basique FR->EN"""
    
    # Dictionnaire de mots communs
    replacements = {
        # Articles
        'le ': 'the ', 'la ': 'the ', 'les ': 'the ', "l'": 'the ',
        'un ': 'a ', 'une ': 'a ', 'des ': 'some ',
        'du ': 'of the ', 'de la ': 'of the ', 'de ': 'of ',
        'au ': 'to the ', 'aux ': 'to the ', 'à ': 'to ',
        
        # Verbes courants
        'créer': 'create', 'modifier': 'modify', 'supprimer': 'delete',
        'ajouter': 'add', 'voir': 'view', 'gérer': 'manage',
        'afficher': 'display', 'fermer': 'close', 'ouvrir': 'open',
        'enregistrer': 'save', 'annuler': 'cancel', 'valider': 'validate',
        
        # Noms communs
        'membre': 'member', 'membres': 'members',
        'pratiquant': 'practitioner', 'pratiquants': 'practitioners',
        'compétition': 'competition', 'compétitions': 'competitions',
        'événement': 'event', 'événements': 'events',
        'document': 'document', 'documents': 'documents',
        'combat': 'fight', 'combats': 'fights',
        'entraînement': 'training', 'entraînements': 'trainings',
        'grade': 'grade', 'grades': 'grades',
        'rôle': 'role', 'rôles': 'roles',
        'permission': 'permission', 'permissions': 'permissions',
        
        # Adjectifs
        'nouveau': 'new', 'nouvelle': 'new', 'nouveaux': 'new', 'nouvelles': 'new',
        'actif': 'active', 'active': 'active', 'actifs': 'active', 'actives': 'active',
        'récent': 'recent', 'récente': 'recent', 'récents': 'recent', 'récentes': 'recent',
        'complet': 'complete', 'complète': 'complete',
        'public': 'public', 'publique': 'public',
        
        # Expressions
        'Aucun': 'No', 'Aucune': 'No',
        'Tous': 'All', 'Toutes': 'All',
        'Total': 'Total',
    }
    
    text = french_text.lower()
    for fr, en in replacements.items():
        text = text.replace(fr, en)
    
    # Capitaliser si nécessaire
    if french_text and french_text[0].isupper():
        text = text.capitalize()
    
    return text

# Traduire automatiquement
translations = {}
for french in missing:
    # Passer les chaînes étranges (fragments HTML, etc.)
    if len(french) < 2 or french in ['%', ';', '&']:
        continue
    
    english = auto_translate_fr_to_en(french)
    translations[french] = english

print(f"Traductions générées: {len(translations)}")
print()

# Exemples
print("Exemples de traductions (10 premières):")
print("-" * 70)
for i, (fr, en) in enumerate(list(translations.items())[:10], 1):
    print(f"{i}. \"{fr[:40]}...\" → \"{en[:40]}...\"" if len(fr) > 40 else f"{i}. \"{fr}\" → \"{en}\"")

print()
print("ATTENTION: Ces traductions sont automatiques et approximatives.")
print("Il faudra les réviser avec Poedit Pro ou utiliser DeepL API.")
print()

response = input("Voulez-vous ajouter ces traductions au fichier .po ? (oui/non): ")

if response.lower() in ['oui', 'yes', 'y', 'o']:
    with open('locale/en/LC_MESSAGES/django.po', 'a', encoding='utf-8') as f:
        f.write('\n# Traductions automatiques - À réviser\n')
        for fr, en in sorted(translations.items()):
            f.write(f'\nmsgid "{fr}"\n')
            f.write(f'msgstr "{en}"\n')
    
    print(f"✅ {len(translations)} traductions ajoutées!")
    print()
    print("IMPORTANT: Révisez ces traductions avec Poedit Pro avant utilisation")
else:
    print("❌ Annulé")
