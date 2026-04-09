#\!/bin/bash
# Trouver le template de mise à jour

echo "=== RECHERCHE TEMPLATE UPDATE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Recherche dans la vue competition_update..."
grep -A10 "def competition_update" apps/competitions/views/competitions.py  < /dev/null |  grep -E "render|template"

echo "2. Recherche des templates form pour competition..."
find apps/competitions/templates -path "*/competition/*" -name "*form*.html" -o -name "*update*.html" | head -10

echo "3. Vérifier le contenu du template utilisé..."
# D'abord trouver quel template est utilisé
template=$(grep -A20 "def competition_update" apps/competitions/views/competitions.py | grep -o "render.*\.html" | grep -o "'[^']*\.html'" | tr -d "'")
echo "Template trouvé: $template"

if [ \! -z "$template" ]; then
    echo "4. Vérification du template $template..."
    # Vérifier s'il étend bien base.html
    grep -n "extends\|block extra_js\|block content" "apps/competitions/templates/$template" | head -10
    
    echo "5. Vérifier les scripts JS dans ce template..."
    grep -n "script\|bootstrap\|dropdown" "apps/competitions/templates/$template" | head -20
fi

echo "6. Test d'un fix rapide - Ajout d'un script d'initialisation..."
# Créer un petit script pour réinitialiser les dropdowns
cat > /tmp/fix_dropdown.js << 'JS'
// Fix pour les dropdowns Bootstrap 5
document.addEventListener('DOMContentLoaded', function() {
    // Réinitialiser tous les dropdowns
    var dropdownElementList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl);
    });
    
    console.log('Dropdowns réinitialisés:', dropdownList.length);
});
JS

echo "Script de fix créé dans /tmp/fix_dropdown.js"

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
