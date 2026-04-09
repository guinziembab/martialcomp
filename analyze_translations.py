#!/usr/bin/env python
"""
Analyse des traductions manquantes dans le projet MartialComp.
Vérifie les templates HTML pour les chaînes en dur non traduites.
"""
import os
import re
from pathlib import Path
from collections import defaultdict

# Patterns pour détecter les chaînes traduisibles
TRANS_PATTERNS = [
    r'{%\s*trans\s+"([^"]+)"\s*%}',
    r'{%\s*trans\s+\'([^\']+)\'\s*%}',
    r'{%\s*blocktrans[^%]*%}(.*?){%\s*endblocktrans\s*%}',
    r'_\(\s*["\']([^"\']+)["\']\s*\)',
    r'gettext\(\s*["\']([^"\']+)["\']\s*\)',
    r'gettext_lazy\(\s*["\']([^"\']+)["\']\s*\)',
]

# Patterns pour détecter les chaînes en dur potentiellement non traduites
HARDCODED_PATTERNS = [
    # Texte dans les balises HTML courantes
    r'<button[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</button>',
    r'<a[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</a>',
    r'<h[1-6][^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</h[1-6]>',
    r'<label[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</label>',
    r'<th[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</th>',
    r'<td[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</td>',
    r'<span[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</span>',
    r'<p[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</p>',
    r'<div[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</div>',
    r'<li[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</li>',
    r'<option[^>]*>([A-Z][a-zA-Zéèàùâêîôûç\s]+)</option>',
    # Attributs title et placeholder
    r'title="([A-Z][a-zA-Zéèàùâêîôûç\s]+)"',
    r'placeholder="([A-Z][a-zA-Zéèàùâêîôûç\s]+)"',
    r'alt="([A-Z][a-zA-Zéèàùâêîôûç\s]+)"',
]

# Mots à ignorer (noms propres, variables, etc.)
IGNORE_WORDS = {
    'Django', 'Python', 'JavaScript', 'CSS', 'HTML', 'API', 'URL', 'ID',
    'MartialComp', 'Bootstrap', 'Chart', 'Font', 'Awesome', 'Icon',
    'True', 'False', 'None', 'null', 'undefined',
    'GET', 'POST', 'PUT', 'DELETE', 'PATCH',
    'OK', 'Cancel', 'Submit', 'Reset',
}

def is_likely_translatable(text):
    """Vérifie si le texte devrait être traduit."""
    text = text.strip()

    # Ignorer les textes trop courts
    if len(text) < 3:
        return False

    # Ignorer les textes qui sont juste des nombres
    if text.isdigit():
        return False

    # Ignorer les mots connus
    if text in IGNORE_WORDS:
        return False

    # Ignorer les variables Django
    if '{{' in text or '{%' in text:
        return False

    # Ignorer les classes CSS ou IDs
    if text.startswith('.') or text.startswith('#'):
        return False

    return True

def analyze_template(filepath):
    """Analyse un fichier template pour les chaînes en dur."""
    hardcoded = []
    translated = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return hardcoded, translated

    # Trouver les chaînes traduites
    for pattern in TRANS_PATTERNS:
        matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            translated.append(match.strip())

    # Trouver les chaînes potentiellement en dur
    for pattern in HARDCODED_PATTERNS:
        for match in re.finditer(pattern, content, re.DOTALL):
            text = match.group(1).strip()
            # Vérifier que ce n'est pas déjà traduit
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_end = content.find('\n', match.end())
            line = content[line_start:line_end]

            # Si la ligne contient {% trans ou blocktrans, c'est traduit
            if '{% trans' in line or '{% blocktrans' in line or 'trans ' in line:
                continue

            if is_likely_translatable(text) and text not in translated:
                hardcoded.append({
                    'text': text,
                    'line': content[:match.start()].count('\n') + 1,
                    'context': line.strip()[:100]
                })

    return hardcoded, translated

def analyze_python_file(filepath):
    """Analyse un fichier Python pour les chaînes en dur."""
    hardcoded = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return hardcoded

    # Patterns pour les chaînes en dur dans Python
    py_patterns = [
        # messages.error/success/info/warning
        r'messages\.\w+\([^,]+,\s*["\']([^"\']+)["\']',
        # raise ValidationError
        r'ValidationError\(["\']([^"\']+)["\']',
        # Textes dans les vues
        r'context\[["\'][^"\']+["\']\]\s*=\s*["\']([A-Z][^"\']+)["\']',
    ]

    for pattern in py_patterns:
        for match in re.finditer(pattern, content):
            text = match.group(1).strip()
            # Vérifier que ce n'est pas déjà dans _() ou gettext
            line_start = content.rfind('\n', 0, match.start()) + 1
            line_end = content.find('\n', match.end())
            line = content[line_start:line_end]

            if '_(' not in line and 'gettext' not in line:
                if is_likely_translatable(text):
                    hardcoded.append({
                        'text': text,
                        'line': content[:match.start()].count('\n') + 1,
                        'context': line.strip()[:100]
                    })

    return hardcoded

def main():
    base_dir = Path('.')

    # Dossiers à analyser
    template_dirs = [
        'apps/competitions/templates',
        'apps/grades/templates',
        'apps/finances/templates',
        'apps/organizations/templates',
        'templates',
    ]

    python_dirs = [
        'apps/competitions/views',
        'apps/competitions/forms',
        'apps/grades/views',
        'apps/finances/views',
    ]

    all_hardcoded = defaultdict(list)
    total_translated = set()

    print("=" * 80)
    print("ANALYSE DES TRADUCTIONS MANQUANTES")
    print("=" * 80)

    # Analyser les templates
    print("\n--- Analyse des templates HTML ---\n")
    for template_dir in template_dirs:
        dir_path = base_dir / template_dir
        if not dir_path.exists():
            continue

        for filepath in dir_path.rglob('*.html'):
            hardcoded, translated = analyze_template(filepath)
            total_translated.update(translated)

            if hardcoded:
                rel_path = str(filepath.relative_to(base_dir))
                all_hardcoded[rel_path].extend(hardcoded)

    # Analyser les fichiers Python
    print("\n--- Analyse des fichiers Python ---\n")
    for py_dir in python_dirs:
        dir_path = base_dir / py_dir
        if not dir_path.exists():
            continue

        for filepath in dir_path.rglob('*.py'):
            hardcoded = analyze_python_file(filepath)
            if hardcoded:
                rel_path = str(filepath.relative_to(base_dir))
                all_hardcoded[rel_path].extend(hardcoded)

    # Afficher les résultats
    print("\n" + "=" * 80)
    print("CHAÎNES EN DUR POTENTIELLEMENT NON TRADUITES")
    print("=" * 80)

    total_issues = 0
    for filepath, issues in sorted(all_hardcoded.items()):
        if issues:
            print(f"\n[FILE] {filepath}")
            for issue in issues[:10]:  # Limiter à 10 par fichier
                print(f"   Ligne {issue['line']}: \"{issue['text']}\"")
                total_issues += 1
            if len(issues) > 10:
                print(f"   ... et {len(issues) - 10} autres")
                total_issues += len(issues) - 10

    print("\n" + "=" * 80)
    print(f"RÉSUMÉ: {total_issues} chaînes potentiellement non traduites")
    print(f"        {len(total_translated)} chaînes déjà traduites trouvées")
    print("=" * 80)

    # Sauvegarder dans un fichier
    with open('translation_analysis_report.txt', 'w', encoding='utf-8') as f:
        f.write("RAPPORT D'ANALYSE DES TRADUCTIONS\n")
        f.write("=" * 80 + "\n\n")

        for filepath, issues in sorted(all_hardcoded.items()):
            if issues:
                f.write(f"\n{filepath}\n")
                f.write("-" * 40 + "\n")
                for issue in issues:
                    f.write(f"  Ligne {issue['line']}: \"{issue['text']}\"\n")

    print("\nRapport sauvegardé dans: translation_analysis_report.txt")

if __name__ == '__main__':
    main()
