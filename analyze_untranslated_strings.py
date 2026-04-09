#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'analyse des chaînes de texte non traduites
Analyse le code et les templates pour identifier les chaînes manquantes dans le fichier PO
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Configuration
PROJECT_ROOT = Path(__file__).parent
APPS_DIR = PROJECT_ROOT / "apps"
TEMPLATES_DIR = PROJECT_ROOT / "apps" / "competitions" / "templates"
LOCALE_DIR = PROJECT_ROOT / "locale" / "fr" / "LC_MESSAGES"
PO_FILE = LOCALE_DIR / "django.po"

# Patterns pour extraire les chaînes traduites
PYTHON_PATTERNS = [
    r'_\(["\']([^"\']+)["\']\)',  # _("text")
    r'_\(["\']([^"\']+)["\']\)',  # _('text')
    r'gettext\(["\']([^"\']+)["\']\)',  # gettext("text")
    r'gettext_lazy\(["\']([^"\']+)["\']\)',  # gettext_lazy("text")
    r'\.format\(_\(["\']([^"\']+)["\']\)\)',  # .format(_("text"))
]

TEMPLATE_PATTERNS = [
    r'{%\s*trans\s+["\']([^"\']+)["\']\s*%}',  # {% trans "text" %}
    r'{%\s*translate\s+["\']([^"\']+)["\']\s*%}',  # {% translate "text" %}
    r'{%\s*blocktrans\s+%}(.*?){%\s*endblocktrans\s*%}',  # {% blocktrans %}...{% endblocktrans %}
]

def extract_po_strings():
    """Extrait toutes les chaînes msgid du fichier PO"""
    if not PO_FILE.exists():
        print(f"⚠️  Fichier PO non trouvé: {PO_FILE}")
        return set()
    
    strings = set()
    current_msgid = None
    current_msgid_multiline = False
    
    with open(PO_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # msgid simple
            if line.startswith('msgid "'):
                match = re.match(r'msgid\s+"(.*)"', line)
                if match:
                    current_msgid = match.group(1)
                    current_msgid_multiline = current_msgid.endswith('\\n')
                    if current_msgid and not current_msgid_multiline:
                        strings.add(current_msgid)
                    elif not current_msgid:
                        strings.add("")
            
            # msgid multiligne
            elif line.startswith('"') and current_msgid is not None:
                if line.endswith('\\n"'):
                    current_msgid += line[1:-3]  # Enlever les guillemets et \n
                    current_msgid_multiline = True
                elif line.endswith('"'):
                    current_msgid += line[1:-1]
                    strings.add(current_msgid)
                    current_msgid = None
                    current_msgid_multiline = False
            
            # Fin de msgid
            elif line == '' and current_msgid is not None:
                if current_msgid:
                    strings.add(current_msgid)
                current_msgid = None
                current_msgid_multiline = False
    
    return strings

def extract_python_strings():
    """Extrait toutes les chaînes traduites des fichiers Python"""
    strings = defaultdict(list)
    
    if not APPS_DIR.exists():
        print(f"⚠️  Dossier apps non trouvé: {APPS_DIR}")
        return strings
    
    # Fichiers à ignorer
    ignore_dirs = {'__pycache__', 'migrations', 'tests', '.git'}
    ignore_files = {'.pyc', '.pyo'}
    
    for root, dirs, files in os.walk(APPS_DIR):
        # Ignorer certains dossiers
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            if not file.endswith('.py'):
                continue
            
            file_path = Path(root) / file
            relative_path = file_path.relative_to(PROJECT_ROOT)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        # Chercher toutes les patterns
                        for pattern in PYTHON_PATTERNS:
                            matches = re.finditer(pattern, line)
                            for match in matches:
                                string = match.group(1)
                                if string and string.strip():
                                    strings[string].append({
                                        'file': str(relative_path),
                                        'line': i,
                                        'type': 'python'
                                    })
            except Exception as e:
                print(f"⚠️  Erreur lecture {file_path}: {e}")
    
    return strings

def extract_template_strings():
    """Extrait toutes les chaînes traduites des templates"""
    strings = defaultdict(list)
    
    if not TEMPLATES_DIR.exists():
        print(f"⚠️  Dossier templates non trouvé: {TEMPLATES_DIR}")
        return strings
    
    for root, dirs, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if not file.endswith('.html'):
                continue
            
            file_path = Path(root) / file
            relative_path = file_path.relative_to(PROJECT_ROOT)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        # Pattern pour {% trans %}
                        for pattern in TEMPLATE_PATTERNS[:2]:
                            matches = re.finditer(pattern, line)
                            for match in matches:
                                string = match.group(1)
                                if string and string.strip():
                                    strings[string].append({
                                        'file': str(relative_path),
                                        'line': i,
                                        'type': 'template'
                                    })
                        
                        # Pattern pour {% blocktrans %}
                        blocktrans_pattern = r'{%\s*blocktrans\s+%}(.*?){%\s*endblocktrans\s*%}'
                        matches = re.finditer(blocktrans_pattern, line, re.DOTALL)
                        for match in matches:
                            string = match.group(1).strip()
                            if string:
                                strings[string].append({
                                    'file': str(relative_path),
                                    'line': i,
                                    'type': 'template_blocktrans'
                                })
            except Exception as e:
                print(f"⚠️  Erreur lecture {file_path}: {e}")
    
    return strings

def analyze_strings():
    """Analyse principale"""
    print("🔍 Analyse des chaînes de traduction...")
    print("=" * 80)
    
    # Extraire les chaînes du PO
    print("\n1. Extraction des chaînes du fichier PO...")
    po_strings = extract_po_strings()
    print(f"   ✅ {len(po_strings)} chaînes trouvées dans le fichier PO")
    
    # Extraire les chaînes du code Python
    print("\n2. Extraction des chaînes du code Python...")
    python_strings = extract_python_strings()
    print(f"   ✅ {len(python_strings)} chaînes uniques trouvées dans le code Python")
    
    # Extraire les chaînes des templates
    print("\n3. Extraction des chaînes des templates...")
    template_strings = extract_template_strings()
    print(f"   ✅ {len(template_strings)} chaînes uniques trouvées dans les templates")
    
    # Fusionner toutes les chaînes trouvées dans le code
    all_code_strings = defaultdict(list)
    for string, locations in python_strings.items():
        all_code_strings[string].extend(locations)
    for string, locations in template_strings.items():
        all_code_strings[string].extend(locations)
    
    # Identifier les chaînes manquantes
    print("\n4. Identification des chaînes manquantes...")
    missing_strings = {}
    for string, locations in all_code_strings.items():
        if string not in po_strings:
            missing_strings[string] = locations
    
    # Statistiques
    print("\n" + "=" * 80)
    print("📊 RÉSULTATS DE L'ANALYSE")
    print("=" * 80)
    print(f"\n📝 Total chaînes dans le PO: {len(po_strings)}")
    print(f"📝 Total chaînes dans le code: {len(all_code_strings)}")
    print(f"⚠️  Chaînes manquantes: {len(missing_strings)}")
    
    # Grouper par fichier
    if missing_strings:
        print("\n" + "=" * 80)
        print("⚠️  CHAÎNES MANQUANTES DANS LE FICHIER PO")
        print("=" * 80)
        
        by_file = defaultdict(list)
        for string, locations in missing_strings.items():
            for loc in locations:
                by_file[loc['file']].append({
                    'string': string,
                    'line': loc['line'],
                    'type': loc['type']
                })
        
        # Trier par fichier
        for file_path in sorted(by_file.keys()):
            print(f"\n📄 {file_path}")
            print("-" * 80)
            for item in sorted(by_file[file_path], key=lambda x: x['line']):
                print(f"  Ligne {item['line']} ({item['type']}):")
                # Afficher la chaîne avec gestion des caractères spéciaux
                display_string = item['string'].replace('\n', '\\n').replace('\t', '\\t')
                if len(display_string) > 100:
                    display_string = display_string[:100] + "..."
                print(f"    {display_string}")
                print()
        
        # Générer un rapport JSON
        report_file = PROJECT_ROOT / "untranslated_strings_report.json"
        report = {
            'total_po_strings': len(po_strings),
            'total_code_strings': len(all_code_strings),
            'missing_count': len(missing_strings),
            'missing_strings': {
                string: locations 
                for string, locations in missing_strings.items()
            },
            'by_file': {
                file_path: items 
                for file_path, items in by_file.items()
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Rapport JSON généré: {report_file}")
        
        # Générer un rapport texte pour ajout au PO
        po_additions_file = PROJECT_ROOT / "po_additions.txt"
        with open(po_additions_file, 'w', encoding='utf-8') as f:
            f.write("# Chaînes à ajouter au fichier PO\n")
            f.write("# Généré automatiquement par analyze_untranslated_strings.py\n\n")
            
            for string, locations in sorted(missing_strings.items(), key=lambda x: x[1][0]['file']):
                # Écrire les références
                files_lines = set()
                for loc in locations:
                    files_lines.add(f"{loc['file']}:{loc['line']}")
                
                f.write(f"#: {' '.join(sorted(files_lines))}\n")
                f.write(f'msgid "{string}"\n')
                f.write(f'msgstr "{string}"\n')
                f.write("\n")
        
        print(f"✅ Fichier d'additions PO généré: {po_additions_file}")
    else:
        print("\n✅ Toutes les chaînes sont présentes dans le fichier PO!")
    
    return missing_strings

if __name__ == "__main__":
    analyze_strings()
