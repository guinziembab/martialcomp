#\!/bin/bash
# Trouver l'erreur exacte à la ligne 1780

echo "=== RECHERCHE ERREUR LIGNE 1780 ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Extraire le contexte autour de la ligne problématique..."
# Le numéro de ligne dans le navigateur correspond au HTML rendu
# Cherchons dans le template autour du code JavaScript

echo "2. Rechercher dans le template create.html..."
# Compter les lignes pour trouver approximativement où se trouve l'erreur
awk 'NR >= 1000 && NR <= 1100 {print NR ": " $0}' apps/competitions/templates/competitions/competition/create.html  < /dev/null |  grep -A5 -B5 "Types filtrés"

echo "3. Chercher spécifiquement après 'Types filtrés avec succès'..."
grep -A50 "Types filtrés avec succès" apps/competitions/templates/competitions/competition/create.html | cat -n

echo "4. Analyser la structure du JavaScript..."
# Extraire tout le bloc script contenant le code des types
sed -n '/competitionTypesSelect/,/}<\/script>/p' apps/competitions/templates/competitions/competition/create.html > /tmp/script_block.js

echo "5. Vérifier la syntaxe du bloc extrait..."
python3 -c "
with open('/tmp/script_block.js', 'r') as f:
    content = f.read()
    
# Chercher les problèmes potentiels
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    # Chercher les caractères suspects
    if any(ord(c) > 127 for c in line) and 'console.log' in line:
        print(f'Ligne {i}: Caractères non-ASCII détectés')
    # Chercher les guillemets mal fermés
    if line.count('\"') % 2 \!= 0:
        print(f'Ligne {i}: Nombre impair de guillemets doubles')
    if line.count(\"'\") % 2 \!= 0:
        print(f'Ligne {i}: Nombre impair de guillemets simples')
    # Chercher les template tags Django dans le JS
    if '{{' in line or '{%' in line:
        print(f'Ligne {i}: Template tag Django dans JavaScript: {line.strip()}')
"

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
