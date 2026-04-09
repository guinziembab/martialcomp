#\!/bin/bash
# Vérifier le dropdown profil

echo "=== VÉRIFICATION DROPDOWN PROFIL ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Recherche du code exact du dropdown profil dans base.html..."
grep -n -A20 "userDropdown\ < /dev/null | user.*dropdown\|nav-item.*dropdown" apps/competitions/templates/base.html | grep -A20 -B5 "dropdown"

echo "2. Vérification des attributs data-toggle vs data-bs-toggle..."
# Bootstrap 5 utilise data-bs-toggle au lieu de data-toggle
grep -r "data-toggle=\"dropdown\"\|data-bs-toggle=\"dropdown\"" apps/competitions/templates/base.html

echo "3. Vérifier quel template est utilisé pour la page update..."
grep -r "extends.*base\|extends.*layout" apps/competitions/templates/competitions/competition/ | grep -v ".py"

echo "4. Recherche du template spécifique pour update..."
find apps/competitions/templates -name "*update*.html" -o -name "*form*.html" | grep competition | head -10

echo "5. Vérifier les scripts Bootstrap chargés..."
grep -A5 -B5 "bootstrap.*js\|popper.*js" apps/competitions/templates/base.html

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
