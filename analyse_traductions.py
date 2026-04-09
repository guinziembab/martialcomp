#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse complète des traductions Django
Identifie les textes hardcodés non traduits dans les templates HTML et les fichiers Python
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Set

# Configuration
BASE_DIR = Path(__file__).parent
APPS_DIR = BASE_DIR / 'apps'
LOCALE_DIR = BASE_DIR / 'locale'
REPORT_DIR = BASE_DIR / 'rapports_traductions'

# Patterns pour identifier les textes à traduire
FRENCH_PATTERNS = [
    r'\b(?:Date|Heure|Nom|Prénom|Email|Téléphone|Adresse|Ville|Code postal|Pays)\b',
    r'\b(?:Équipe|Rouge|Bleue|Blanche|Noire|Verte|Jaune)\b',
    r'\b(?:Compétition|Catégorie|Participant|Juge|Club|Fédération)\b',
    r'\b(?:Non défini|À définir|Validé|En attente|Annulé|Terminé)\b',
    r'\b(?:Date non définie|Heure non définie|Non disponible)\b',
    r'\b(?:Voir|Modifier|Supprimer|Ajouter|Enregistrer|Annuler|Valider)\b',
    r'\b(?:Détails|Liste|Tableau|Formulaire|Recherche|Filtre)\b',
    r'[ÀàÂâÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿÇç]',  # Caractères accentués français
]

# Mots à ignorer (trop courts ou trop communs)
IGNORE_WORDS = {
    'de', 'du', 'la', 'le', 'les', 'un', 'une', 'des', 'et', 'ou', 'à', 'en', 'par',
    'pour', 'avec', 'sans', 'sur', 'sous', 'dans', 'est', 'sont', 'a', 'as', 'ont',
    'id', 'url', 'css', 'js', 'html', 'xml', 'json', 'api', 'http', 'https', 'www',
    'com', 'org', 'net', 'fr', 'en', 'es', 'it', 'de', 'pt', 'ru', 'vi', 'no', 'ja',
    'zh', 'hi', 'ar', 'sw', 'am', 'zu', 'yo', 'ko',
}

# Patterns pour détecter les traductions existantes dans les templates
TEMPLATE_TRANS_PATTERNS = [
    r'\{%\s*trans\s+["\']([^"\']+)["\']\s*%\}',
    r'\{%\s*blocktrans\s+[^%]*%\}',
    r'default:\s*_\("([^"]+)"\)',
    r'default:\s*_\(\'([^\']+)\'\)',
]

# Patterns pour détecter les traductions existantes dans Python
PYTHON_TRANS_PATTERNS = [
    r'_\("([^"]+)"\)',
    r'_\'([^\']+)\'',
    r'gettext\("([^"]+)"\)',
    r'gettext\(\'([^\']+)\'\)',
    r'ugettext\("([^"]+)"\)',
    r'ugettext\(\'([^\']+)\'\)',
    r'pgettext\(',
    r'ngettext\(',
]

# Patterns pour identifier les chaînes de caractères dans les templates
TEMPLATE_STRING_PATTERNS = [
    r'>([^<>{}\n]+[ÀàÂâÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿÇç][^<>{}\n]*)<',  # Texte avec accents entre balises
    r'["\']([^"\']*[ÀàÂâÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿÇç][^"\']*)["\']',  # Chaînes avec accents
]

# Patterns pour identifier les chaînes de caractères dans Python
PYTHON_STRING_PATTERNS = [
    r'["\']([^"\']*[ÀàÂâÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿÇç][^"\']*)["\']',
    r'f["\']([^"\']*[ÀàÂâÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿÇç][^"\']*)["\']',
]

# Fichiers à ignorer
IGNORE_PATTERNS = [
    r'.*\.pyc$',
    r'.*\.pyo$',
    r'.*\.mo$',
    r'.*\.po$',
    r'.*__pycache__.*',
    r'.*\.backup.*',
    r'.*\.old.*',
    r'.*_OLD.*',
    r'.*\.new.*',
    r'.*migrations.*',
    r'.*venv.*',
    r'.*env.*',
    r'.*node_modules.*',
    r'.*\.git.*',
    r'.*staticfiles.*',
    r'.*media.*',
    r'.*Cache.*',
    r'.*backup.*',
    r'.*Backup.*',
]


class TranslationAnalyzer:
    """Analyseur de traductions Django"""
    
    def __init__(self):
        self.issues = defaultdict(list)
        self.translated_strings = set()
        self.po_strings = set()
        self.stats = {
            'html_files_scanned': 0,
            'py_files_scanned': 0,
            'html_issues_found': 0,
            'py_issues_found': 0,
            'po_files_loaded': 0,
        }
        
    def should_ignore_file(self, filepath: Path) -> bool:
        """Vérifie si un fichier doit être ignoré"""
        filepath_str = str(filepath)
        for pattern in IGNORE_PATTERNS:
            if re.search(pattern, filepath_str, re.IGNORECASE):
                return True
        return False
    
    def parse_po_string(self, s: str) -> str:
        """Parse une chaîne .po en décodant les séquences d'échappement"""
        # Remplacer les séquences d'échappement courantes
        s = s.replace('\\n', '\n')
        s = s.replace('\\t', '\t')
        s = s.replace('\\"', '"')
        s = s.replace("\\'", "'")
        s = s.replace('\\\\', '\\')
        return s
    
    def load_po_files(self):
        """Charge tous les msgid des fichiers .po"""
        print("📖 Chargement des fichiers de traduction (.po)...")
        po_files = list(LOCALE_DIR.rglob('*.po'))
        
        for po_file in po_files:
            try:
                with open(po_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # Chercher msgid
                    if line.startswith('msgid '):
                        msgid_parts = []
                        
                        # Cas 1: msgid "texte" (une ligne)
                        match = re.match(r'msgid\s+"(.+)"', line)
                        if match:
                            msgid_parts.append(match.group(1))
                        # Cas 2: msgid "" (multiligne)
                        elif re.match(r'msgid\s+""', line):
                            # Lire les lignes suivantes jusqu'à msgstr
                            i += 1
                            while i < len(lines):
                                next_line = lines[i].strip()
                                if next_line.startswith('msgstr'):
                                    break
                                # Extraire le contenu entre guillemets
                                match = re.match(r'"(.+)"', next_line)
                                if match:
                                    msgid_parts.append(match.group(1))
                                i += 1
                        
                        if msgid_parts:
                            # Concaténer et parser
                            msgid = ''.join(msgid_parts)
                            msgid = self.parse_po_string(msgid)
                            # Normaliser (enlever espaces multiples)
                            normalized = ' '.join(msgid.split())
                            if normalized and len(normalized) > 2 and normalized != 'Project-Id-Version':
                                self.po_strings.add(normalized)
                    
                    i += 1
                
                self.stats['po_files_loaded'] += 1
            except Exception as e:
                print(f"⚠️  Erreur lors du chargement de {po_file}: {e}")
        
        print(f"✅ {len(self.po_strings)} chaînes de traduction chargées depuis {self.stats['po_files_loaded']} fichiers .po")
    
    def extract_translated_strings_from_template(self, content: str) -> Set[str]:
        """Extrait les chaînes déjà traduites d'un template"""
        translated = set()
        
        # Extraire les chaînes dans {% trans %}
        for pattern in TEMPLATE_TRANS_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                if match.groups():
                    translated.add(match.group(1).strip())
        
        return translated
    
    def extract_translated_strings_from_python(self, content: str) -> Set[str]:
        """Extrait les chaînes déjà traduites d'un fichier Python"""
        translated = set()
        
        for pattern in PYTHON_TRANS_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                if match.groups():
                    translated.add(match.group(1).strip())
        
        return translated
    
    def find_french_strings_in_template(self, content: str, filepath: Path) -> List[Dict]:
        """Trouve les chaînes françaises non traduites dans un template"""
        issues = []
        translated = self.extract_translated_strings_from_template(content)
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Ignorer les lignes de commentaires
            if line.strip().startswith('{#') or line.strip().startswith('<!--'):
                continue
            
            # Chercher les chaînes avec caractères français
            for pattern in TEMPLATE_STRING_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    if match.groups():
                        text = match.group(1).strip()
                        if not text or len(text) < 3:
                            continue
                        
                        # Vérifier si c'est du français
                        has_french_chars = bool(re.search(r'[ÀàÂâÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿÇç]', text))
                        has_french_words = any(re.search(pattern, text, re.IGNORECASE) for pattern in FRENCH_PATTERNS[:5])
                        
                        if has_french_chars or has_french_words:
                            # Vérifier si déjà traduit
                            if text not in translated and text not in self.po_strings:
                                # Vérifier si ce n'est pas un mot à ignorer
                                words = text.split()
                                if not all(word.lower() in IGNORE_WORDS for word in words):
                                    issues.append({
                                        'line': line_num,
                                        'text': text,
                                        'context': line.strip()[:100],
                                        'type': 'template_hardcoded_french'
                                    })
        
        return issues
    
    def find_french_strings_in_python(self, content: str, filepath: Path) -> List[Dict]:
        """Trouve les chaînes françaises non traduites dans un fichier Python"""
        issues = []
        translated = self.extract_translated_strings_from_python(content)
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            # Ignorer les commentaires
            if line.strip().startswith('#'):
                continue
            
            # Ignorer les docstrings
            if '"""' in line or "'''" in line:
                continue
            
            # Chercher les chaînes avec caractères français
            for pattern in PYTHON_STRING_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    if match.groups():
                        text = match.group(1).strip()
                        if not text or len(text) < 3:
                            continue
                        
                        # Vérifier si c'est du français
                        has_french_chars = bool(re.search(r'[ÀàÂâÉéÈèÊêËëÎîÏïÔôÙùÛûÜüŸÿÇç]', text))
                        has_french_words = any(re.search(pattern, text, re.IGNORECASE) for pattern in FRENCH_PATTERNS[:5])
                        
                        if has_french_chars or has_french_words:
                            # Vérifier si déjà traduit
                            if text not in translated and text not in self.po_strings:
                                # Vérifier si ce n'est pas un mot à ignorer
                                words = text.split()
                                if not all(word.lower() in IGNORE_WORDS for word in words):
                                    issues.append({
                                        'line': line_num,
                                        'text': text,
                                        'context': line.strip()[:100],
                                        'type': 'python_hardcoded_french'
                                    })
        
        return issues
    
    def scan_html_files(self):
        """Scanne tous les fichiers HTML"""
        print("\n🔍 Scan des fichiers HTML...")
        html_files = list(APPS_DIR.rglob('*.html'))
        
        for html_file in html_files:
            if self.should_ignore_file(html_file):
                continue
            
            try:
                with open(html_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                issues = self.find_french_strings_in_template(content, html_file)
                if issues:
                    rel_path = html_file.relative_to(BASE_DIR)
                    self.issues[str(rel_path)].extend(issues)
                    self.stats['html_issues_found'] += len(issues)
                
                self.stats['html_files_scanned'] += 1
                
            except Exception as e:
                print(f"⚠️  Erreur lors du scan de {html_file}: {e}")
        
        print(f"✅ {self.stats['html_files_scanned']} fichiers HTML scannés, {self.stats['html_issues_found']} problèmes trouvés")
    
    def scan_python_files(self):
        """Scanne tous les fichiers Python"""
        print("\n🔍 Scan des fichiers Python...")
        py_files = list(APPS_DIR.rglob('*.py'))
        
        for py_file in py_files:
            if self.should_ignore_file(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                issues = self.find_french_strings_in_python(content, py_file)
                if issues:
                    rel_path = py_file.relative_to(BASE_DIR)
                    self.issues[str(rel_path)].extend(issues)
                    self.stats['py_issues_found'] += len(issues)
                
                self.stats['py_files_scanned'] += 1
                
            except Exception as e:
                print(f"⚠️  Erreur lors du scan de {py_file}: {e}")
        
        print(f"✅ {self.stats['py_files_scanned']} fichiers Python scannés, {self.stats['py_issues_found']} problèmes trouvés")
    
    def generate_report(self):
        """Génère un rapport détaillé"""
        REPORT_DIR.mkdir(exist_ok=True)
        
        report_file = REPORT_DIR / 'rapport_traductions_complet.md'
        json_file = REPORT_DIR / 'rapport_traductions_complet.json'
        
        # Générer le rapport Markdown
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Rapport d'Analyse des Traductions\n\n")
            f.write(f"**Date:** {Path(__file__).stat().st_mtime}\n\n")
            f.write("## Statistiques\n\n")
            f.write(f"- Fichiers HTML scannés: {self.stats['html_files_scanned']}\n")
            f.write(f"- Fichiers Python scannés: {self.stats['py_files_scanned']}\n")
            f.write(f"- Fichiers .po chargés: {self.stats['po_files_loaded']}\n")
            f.write(f"- Chaînes dans .po: {len(self.po_strings)}\n")
            f.write(f"- Problèmes HTML trouvés: {self.stats['html_issues_found']}\n")
            f.write(f"- Problèmes Python trouvés: {self.stats['py_issues_found']}\n")
            f.write(f"- **Total problèmes:** {self.stats['html_issues_found'] + self.stats['py_issues_found']}\n\n")
            
            f.write("## Problèmes identifiés\n\n")
            
            if not self.issues:
                f.write("✅ **Aucun problème trouvé ! Tous les textes semblent être traduits.**\n\n")
            else:
                for filepath, file_issues in sorted(self.issues.items()):
                    f.write(f"### {filepath}\n\n")
                    f.write(f"**{len(file_issues)} problème(s) trouvé(s)**\n\n")
                    
                    for issue in file_issues:
                        f.write(f"- **Ligne {issue['line']}:** `{issue['text']}`\n")
                        f.write(f"  - Type: {issue['type']}\n")
                        f.write(f"  - Contexte: `{issue['context']}`\n\n")
                    
                    f.write("\n")
            
            f.write("## Recommandations\n\n")
            f.write("1. Utiliser `{% trans \"texte\" %}` pour les textes dans les templates\n")
            f.write("2. Utiliser `_(\"texte\")` ou `gettext(\"texte\")` pour les chaînes dans Python\n")
            f.write("3. Utiliser `default:_(\"texte\")` pour les valeurs par défaut dans les filtres\n")
            f.write("4. Exécuter `python manage.py makemessages -l en` pour mettre à jour les fichiers de traduction\n")
            f.write("5. Exécuter `python manage.py compilemessages` pour compiler les traductions\n\n")
        
        # Générer le rapport JSON
        report_data = {
            'stats': self.stats,
            'po_strings_count': len(self.po_strings),
            'issues': {k: v for k, v in self.issues.items()},
            'total_issues': self.stats['html_issues_found'] + self.stats['py_issues_found']
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Rapport généré:")
        print(f"   - Markdown: {report_file}")
        print(f"   - JSON: {json_file}")
    
    def run(self):
        """Exécute l'analyse complète"""
        print("=" * 60)
        print("🔍 ANALYSE COMPLÈTE DES TRADUCTIONS")
        print("=" * 60)
        
        self.load_po_files()
        self.scan_html_files()
        self.scan_python_files()
        self.generate_report()
        
        print("\n" + "=" * 60)
        print("✅ ANALYSE TERMINÉE")
        print("=" * 60)
        print(f"\n📊 Résumé:")
        print(f"   - {self.stats['html_files_scanned']} fichiers HTML scannés")
        print(f"   - {self.stats['py_files_scanned']} fichiers Python scannés")
        print(f"   - {self.stats['html_issues_found'] + self.stats['py_issues_found']} problèmes trouvés")
        print(f"\n📁 Consultez le rapport dans: {REPORT_DIR}/")


if __name__ == '__main__':
    try:
        analyzer = TranslationAnalyzer()
        analyzer.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
