#\!/bin/bash
# Analyser l'erreur de syntaxe

echo "=== ANALYSE ERREUR DE SYNTAXE LIGNE 1765 ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Examiner le template create.html autour de la ligne problématique..."
# Le template est probablement rendu avec des numéros de ligne différents
# Cherchons les scripts inline dans le template
grep -n "<script" apps/competitions/templates/competitions/competition/create.html  < /dev/null |  tail -20

echo "2. Extraire le contenu JavaScript du template..."
# Extraire les blocs de script pour analyse
sed -n '/<script/,/<\/script>/p' apps/competitions/templates/competitions/competition/create.html > /tmp/scripts_extract.js

echo "3. Vérifier la syntaxe des scripts extraits..."
# Utiliser node ou python pour vérifier la syntaxe
python3 -c "
import re

with open('/tmp/scripts_extract.js', 'r') as f:
    content = f.read()

# Trouver les erreurs potentielles
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)

print(f'Nombre de scripts trouvés: {len(scripts)}')

# Chercher les patterns problématiques
for i, script in enumerate(scripts):
    lines = script.split('\n')
    for j, line in enumerate(lines):
        # Chercher les erreurs communes
        if '{{' in line and not ('{{' in line and '}}' in line):
            print(f'Script {i+1}, ligne {j+1}: Template tag non fermé')
        if line.strip().endswith(',') and '}' in lines[j+1].strip()[:1]:
            print(f'Script {i+1}, ligne {j+1}: Virgule finale avant accolade')
        if '\'\'\'' in line or '\"\"\"' in line:
            print(f'Script {i+1}, ligne {j+1}: Triple quotes détectés')
" 2>&1 || echo "Erreur lors de l'analyse"

echo "4. Rechercher spécifiquement autour des logs de types de compétition..."
# Les logs montrent que le problème est après l'initialisation des types
grep -A10 -B10 "Types filtrés avec succès" apps/competitions/templates/competitions/competition/create.html

echo "5. Vérifier s'il y a des conflits avec notre fix dropdown..."
grep -n "userDropdown\|dropdown.*click\|preventDefault" apps/competitions/templates/competitions/competition/create.html | head -20

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
