#\!/bin/bash
# Analyser les champs désactivés sur le formulaire de combat

echo "=== ANALYSE CHAMPS COMBAT ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Rechercher le formulaire de combat..."
find apps -name "*combat*" -path "*/forms/*" -type f  < /dev/null |  grep -E "(form|combat)" | head -10

echo -e "\n2. Rechercher le template de création de combat..."
find apps -name "*creer*" -path "*/templates/*" -type f | grep -i combat | head -10
find apps -name "*create*" -path "*/templates/*" -type f | grep -i combat | head -10

echo -e "\n3. Rechercher les vues de combat..."
grep -r "def.*creer\|def.*create" apps/competitions/views/ | grep -i combat | head -10

echo -e "\n4. Vérifier le modèle Combat pour voir les champs..."
grep -A20 "class Combat" apps/competitions/models/combat.py | head -30

echo -e "\n5. Rechercher CombatConfiguration et referee..."
grep -r "CombatConfiguration\|configuration\|referee\|arbitre" apps/competitions/models/ | grep -v ".pyc" | head -20

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
