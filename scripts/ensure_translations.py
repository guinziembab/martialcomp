#!/usr/bin/env python3
"""
Script pour s'assurer que toutes les langues ont au moins un ensemble minimal
de traductions pour les textes les plus courants.
"""
import os
import re
import sys
from collections import defaultdict

# Textes essentiels à traduire dans toutes les langues
ESSENTIAL_STRINGS = [
    "Accueil",
    "Tableau de bord",
    "Connexion",
    "Déconnexion",
    "Administration",
    "Tous droits réservés.",
    "Plateforme de gestion de compétitions d'arts martiaux",
    "MartialComp - Gestion de Compétitions d'Arts Martiaux",
    "Fonctionnalités",
    "Compétitions",
    "À propos",
    "Contact",
    "Se connecter",
    "S'inscrire",
    "Nom d'utilisateur",
    "Mot de passe",
    "La plateforme ultime de gestion des compétitions d'arts martiaux"
]

def parse_po_file(file_path):
    """Parse un fichier .po et renvoie un dictionnaire des traductions"""
    translations = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraire les paires msgid/msgstr
    pattern = r'msgid "(.*?)"\nmsgstr "(.*?)"'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for msgid, msgstr in matches:
        # Remplacer les sauts de ligne échappés
        msgid = msgid.replace('\\n', '\n')
        msgstr = msgstr.replace('\\n', '\n')
        
        # Nettoyer les guillemets échappés
        msgid = msgid.replace('\\"', '"')
        msgstr = msgstr.replace('\\"', '"')
        
        translations[msgid] = msgstr
    
    return translations

def write_po_file(file_path, translations, language_code):
    """Écrit un fichier .po avec les traductions données"""
    # En-tête du fichier .po
    header = f"""# Translations for martialcomp project.
# Copyright (C) 2025 martialcomp
# This file is distributed under the same license as the martialcomp package.
msgid ""
msgstr ""
"Project-Id-Version: martialcomp 1.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-05-13 18:00+0200\\n"
"PO-Revision-Date: 2025-05-13 18:00+0200\\n"
"Last-Translator: Claude <assistant@anthropic.com>\\n"
"Language-Team: {language_code} <{language_code}@li.org>\\n"
"Language: {language_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"""
    
    # Ajouter les règles de pluralisation selon la langue
    if language_code == 'en':
        header += '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n'
    elif language_code == 'fr':
        header += '"Plural-Forms: nplurals=2; plural=(n > 1);\\n"\n'
    elif language_code == 'ar':
        header += '"Plural-Forms: nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5);\\n"\n'
    else:
        # Pour les autres langues, utiliser la forme anglaise par défaut
        header += '"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n'
    
    # Corps du fichier avec les traductions
    body = ""
    for msgid, msgstr in translations.items():
        # Échapper les guillemets et les sauts de ligne
        msgid_escaped = msgid.replace('"', '\\"').replace('\n', '\\n')
        msgstr_escaped = msgstr.replace('"', '\\"').replace('\n', '\\n')
        
        body += f'\nmsgid "{msgid_escaped}"\nmsgstr "{msgstr_escaped}"\n'
    
    # Écrire le fichier
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(header + body)

def ensure_essential_translations():
    """S'assure que toutes les langues ont les traductions essentielles"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    locale_dir = os.path.join(base_dir, 'locale')
    
    # Obtenir la liste des répertoires de langues
    lang_dirs = [d for d in os.listdir(locale_dir) 
                if os.path.isdir(os.path.join(locale_dir, d)) and d != 'LC_MESSAGES']
    
    print(f"Langues trouvées: {', '.join(lang_dirs)}")
    
    # Charger les traductions de référence depuis l'anglais
    reference_file = os.path.join(locale_dir, 'en', 'LC_MESSAGES', 'django.po')
    reference_translations = {}
    if os.path.exists(reference_file):
        reference_translations = parse_po_file(reference_file)
        print(f"Chargement des traductions de référence (anglais): {len(reference_translations)} entrées")
    else:
        print("ERREUR: Fichier de référence en anglais non trouvé!")
        return
    
    # Nombre de traductions ajoutées par langue
    additions = defaultdict(int)
    
    # Parcourir chaque langue
    for lang in lang_dirs:
        po_file = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.po')
        if not os.path.exists(po_file):
            print(f"ERREUR: {lang} n'a pas de fichier django.po")
            continue
        
        # Charger les traductions existantes
        translations = parse_po_file(po_file)
        print(f"{lang}: {len(translations)} traductions existantes", end="")
        
        # Ajouter les traductions essentielles manquantes
        initial_count = len(translations)
        for text in ESSENTIAL_STRINGS:
            if text not in translations and text in reference_translations:
                if lang == 'fr':
                    # Pour le français, utiliser le texte original (déjà en français)
                    translations[text] = text
                else:
                    # Pour les autres langues, utiliser la traduction anglaise si disponible
                    translations[text] = reference_translations.get(text, text)
                additions[lang] += 1
        
        # Si des traductions ont été ajoutées, mettre à jour le fichier .po
        if len(translations) > initial_count:
            write_po_file(po_file, translations, lang)
            print(f" -> {additions[lang]} traductions essentielles ajoutées")
        else:
            print(" -> Toutes les traductions essentielles sont présentes")
    
    # Résumé
    print("\nRésumé des traductions ajoutées:")
    for lang, count in additions.items():
        print(f"{lang}: +{count} traductions")
    
    if sum(additions.values()) > 0:
        print("\nN'oubliez pas de compiler les fichiers .po en .mo avec recompile_translations.py")

if __name__ == "__main__":
    ensure_essential_translations()