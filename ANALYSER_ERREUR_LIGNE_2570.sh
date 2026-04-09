#!/bin/bash
# Script pour analyser l'erreur JavaScript à la ligne 2570
# Date: 25 novembre 2024

echo "=================================================="
echo "ANALYSE DE L'ERREUR JAVASCRIPT LIGNE 2570"
echo "=================================================="
echo ""

ssh pierrep99@martialcomp.com << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "=== 1. Vérification du fichier base.html actuel ==="
echo "Recherche de {% url dans les blocs <script> :"
echo ""

# Extraire les blocs script de base.html et chercher des {% url %}
python3 << 'ENDPYTHON'
import re

file_path = 'apps/competitions/templates/base.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver tous les blocs <script>
script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)

print(f"Nombre de blocs <script> trouvés: {len(script_blocks)}")
print("")

problematic_tags = []

for i, block in enumerate(script_blocks, 1):
    # Chercher des Django URL tags dans le JavaScript
    url_tags = re.findall(r'\{%\s*url\s+[^%]+%\}', block)
    if url_tags:
        print(f"⚠️  BLOC SCRIPT #{i} - TAGS URL TROUVÉS:")
        for tag in url_tags:
            print(f"    {tag}")
            problematic_tags.append(tag)
        print("")

    # Chercher des variables Django non échappées
    vars_tags = re.findall(r'\{\{\s*[^}]+\s*\}\}', block)
    if vars_tags:
        print(f"📝 BLOC SCRIPT #{i} - VARIABLES DJANGO:")
        for var in vars_tags:
            # Vérifier si c'est échappé correctement
            if '|escapejs' not in var and '|safe' not in var and '|default' not in var:
                print(f"    ⚠️  NON ÉCHAPPÉE: {var}")
                problematic_tags.append(var)
            else:
                print(f"    ✅ Échappée: {var}")
        print("")

if not problematic_tags:
    print("✅ Aucun tag Django problématique trouvé dans les blocs <script> de base.html")
else:
    print(f"❌ {len(problematic_tags)} tag(s) problématique(s) trouvé(s)")

ENDPYTHON

echo ""
echo "=== 2. Vérification de practitioner_form.html ==="
echo ""

python3 << 'ENDPYTHON'
import re

file_path = 'apps/competitions/templates/competitions/club/practitioner_form.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver le bloc extra_js
js_start = content.find('{% block extra_js %}')
js_end = content.find('{% endblock %}', js_start) if js_start != -1 else -1

if js_start == -1:
    print("Bloc extra_js non trouvé!")
    exit(1)

js_block = content[js_start:js_end]
print(f"Bloc extra_js trouvé: {len(js_block)} caractères")
print("")

# Chercher des problèmes potentiels
problems = []

# 1. Django URL tags
url_tags = re.findall(r'\{%\s*url\s+[^%]+%\}', js_block)
if url_tags:
    print("⚠️  TAGS URL DANS LE JAVASCRIPT:")
    for tag in url_tags:
        print(f"    {tag}")
        problems.append(("URL tag", tag))

# 2. Variables Django non échappées
vars_without_escape = re.findall(r'\{\{\s*(?!.*\|escapejs)[^}]+\s*\}\}', js_block)
for var in vars_without_escape:
    if '|default' not in var and '|safe' not in var and '|json_script' not in var:
        print(f"⚠️  VARIABLE NON ÉCHAPPÉE: {var}")
        problems.append(("Variable non échappée", var))

# 3. Chercher des elif avec des variables JavaScript
elif_with_js = re.findall(r'\{%\s*elif\s+[a-z_]+[A-Z][a-zA-Z]*\s*%\}', js_block)
if elif_with_js:
    print("⚠️  ELIF AVEC VARIABLES JAVASCRIPT (camelCase):")
    for tag in elif_with_js:
        print(f"    {tag}")
        problems.append(("elif avec JS var", tag))

# 4. Vérifier les accolades équilibrées
open_braces = js_block.count('{')
close_braces = js_block.count('}')
if open_braces != close_braces:
    print(f"⚠️  ACCOLADES DÉSÉQUILIBRÉES: {{ = {open_braces}, }} = {close_braces}")
    problems.append(("Accolades déséquilibrées", f"{{ = {open_braces}, }} = {close_braces}"))

# 5. Vérifier les parenthèses équilibrées
open_parens = js_block.count('(')
close_parens = js_block.count(')')
if open_parens != close_parens:
    print(f"⚠️  PARENTHÈSES DÉSÉQUILIBRÉES: ( = {open_parens}, ) = {close_parens}")
    problems.append(("Parenthèses déséquilibrées", f"( = {open_parens}, ) = {close_parens}"))

if not problems:
    print("✅ Aucun problème évident trouvé dans le bloc JavaScript")
else:
    print(f"\n❌ {len(problems)} problème(s) trouvé(s)")

print("")
print("=== Vérification de la syntaxe JavaScript ===")

# Extraire le JavaScript pur (sans les tags Django)
js_pure = re.sub(r'\{%.*?%\}', '', js_block)
js_pure = re.sub(r'\{\{.*?\}\}', '""', js_pure)

# Vérifier si le JavaScript résultant a des problèmes évidents
lines = js_pure.split('\n')
for i, line in enumerate(lines, 1):
    # Chercher des patterns problématiques
    if re.search(r'\(\s*,', line):
        print(f"Ligne {i}: Possible erreur - parenthèse suivie de virgule: {line.strip()[:80]}")
    if re.search(r',\s*\)', line):
        print(f"Ligne {i}: Possible erreur - virgule suivie de parenthèse: {line.strip()[:80]}")
    if re.search(r'\)\s*\{', line) and line.strip().endswith('{'):
        # C'est normal pour les fonctions
        pass

ENDPYTHON

echo ""
echo "=== 3. Comptage des lignes jusqu'à la ligne 2570 ==="
echo ""

python3 << 'ENDPYTHON'
# Calculer approximativement où se situe la ligne 2570 dans le HTML rendu
# base.html + practitioner_form.html

base_path = 'apps/competitions/templates/base.html'
form_path = 'apps/competitions/templates/competitions/club/practitioner_form.html'

with open(base_path, 'r', encoding='utf-8') as f:
    base_lines = len(f.readlines())

with open(form_path, 'r', encoding='utf-8') as f:
    form_lines = len(f.readlines())

print(f"base.html: {base_lines} lignes")
print(f"practitioner_form.html: {form_lines} lignes")
print(f"Total approximatif: {base_lines + form_lines} lignes")
print("")

if base_lines + form_lines < 2570:
    print(f"⚠️  La ligne 2570 est au-delà des templates statiques!")
    print(f"    Il y a environ {2570 - base_lines - form_lines} lignes générées dynamiquement")
    print("    L'erreur pourrait venir de:")
    print("    - Contenu généré par Django (listes, boucles for)")
    print("    - JavaScript inline généré")
    print("    - Widgets de formulaire")
else:
    print(f"La ligne 2570 devrait être dans practitioner_form.html")
    print(f"Ligne approximative dans le fichier: {2570 - base_lines}")

ENDPYTHON

echo ""
echo "=== 4. Lignes autour de l'index 2570 dans les templates ==="
echo ""

# Chercher ce qui pourrait être à la ligne 2570 dans le rendu final
python3 << 'ENDPYTHON'
base_path = 'apps/competitions/templates/base.html'
form_path = 'apps/competitions/templates/competitions/club/practitioner_form.html'

# Lire base.html jusqu'au block content
with open(base_path, 'r', encoding='utf-8') as f:
    base_content = f.read()

# Trouver où le block content est inséré
block_content_pos = base_content.find('{% block content %}')
if block_content_pos == -1:
    print("Block content non trouvé dans base.html")
    exit(1)

# Compter les lignes avant le block content
lines_before_content = base_content[:block_content_pos].count('\n')
print(f"Lignes dans base.html avant {{%% block content %%}}: {lines_before_content}")

# Lire practitioner_form.html
with open(form_path, 'r', encoding='utf-8') as f:
    form_content = f.read()

# Le contenu dynamique du formulaire peut ajouter beaucoup de lignes
# Estimer le nombre de lignes du formulaire
form_lines = form_content.count('\n')
print(f"Lignes dans practitioner_form.html: {form_lines}")

# La ligne 2570 dans le rendu final
target_line = 2570

# Estimer où ça tombe
# Le rendu final = base_before_content + practitioner_content + base_after_content
# Mais le formulaire Django génère aussi des lignes (widgets, options, etc.)

print(f"\nSi l'erreur est à la ligne {target_line}, elle est probablement dans:")
if target_line < lines_before_content:
    print(f"  → base.html (partie header/nav)")
elif target_line < lines_before_content + form_lines:
    approx_form_line = target_line - lines_before_content
    print(f"  → practitioner_form.html autour de la ligne {approx_form_line}")

    # Afficher les lignes autour de cette position
    with open(form_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    start = max(0, approx_form_line - 10)
    end = min(len(lines), approx_form_line + 10)
    print(f"\n  Lignes {start+1} à {end} de practitioner_form.html:")
    for i in range(start, end):
        line = lines[i].rstrip()[:100]
        marker = " >>> " if i == approx_form_line - 1 else "     "
        print(f"  {marker}{i+1}: {line}")
else:
    print(f"  → base.html (partie footer/scripts) ou contenu généré dynamiquement")

ENDPYTHON

echo ""
echo "=== 5. Recherche de patterns d'erreur courants ==="
echo ""

# Chercher des patterns qui causent souvent l'erreur "missing ) after argument list"
grep -n "console.log\|alert\|fetch\|JSON.stringify" apps/competitions/templates/competitions/club/practitioner_form.html | head -20

echo ""
echo "=== FIN DE L'ANALYSE ==="

ENDSSH
