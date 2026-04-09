#\!/bin/bash
# Vérifier les besoins d'authentification

echo "=== VÉRIFICATION AUTHENTIFICATION ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier la vue creer_combat..."
grep -A10 "@login_required\ < /dev/null | LoginRequired\|permission_required" apps/competitions/views/combat.py | grep -B5 "def creer_combat"

echo -e "\n2. Vérifier les URLs de combat..."
grep -A5 -B5 "creer.*combat\|combat.*creer" apps/competitions/urls/combat.py 2>/dev/null || echo "Pas de urls/combat.py"

echo -e "\n3. Chercher dans toutes les URLs..."
find apps/competitions/urls -name "*.py" -exec grep -l "combat" {} \; | head -5

echo -e "\n4. Vérifier le décorateur sur la vue..."
sed -n '/def creer_combat/,/def [a-zA-Z]/p' apps/competitions/views/combat.py | head -20

echo -e "\n5. Solution: s'assurer que l'utilisateur est connecté"
echo ""
echo "SOLUTION:"
echo "========="
echo "L'utilisateur doit être connecté pour accéder à cette page."
echo ""
echo "1. Connectez-vous d'abord sur: https://martialcomp.com/fr/accounts/login/"
echo "2. Puis accédez à: https://martialcomp.com/fr/competitions/combat/combats/creer/competition/4/"
echo ""
echo "Ou utilisez ce lien direct après connexion:"
echo "https://martialcomp.com/fr/accounts/login/?next=/fr/competitions/combat/combats/creer/competition/4/"

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
