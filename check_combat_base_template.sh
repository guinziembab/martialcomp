#\!/bin/bash
# Vérifier le template de base pour combat

echo "=== VÉRIFICATION TEMPLATE BASE COMBAT ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier le template de base combat..."
if [ -f "apps/competitions/templates/competitions/combat/base.html" ]; then
    echo "Template base.html trouvé"
    grep -n "<script\ < /dev/null | </script>" apps/competitions/templates/competitions/combat/base.html
    
    echo -e "\n2. Vérifier les blocks JavaScript..."
    grep -A5 -B5 "block.*js\|block.*script" apps/competitions/templates/competitions/combat/base.html
else
    echo "Pas de template combat/base.html, recherche d'autres bases..."
    find apps/competitions/templates -name "base*.html" | head -10
fi

echo -e "\n3. Vérifier s'il y a des URLs ou des includes mal formés..."
grep -n "{% url\|{% include" apps/competitions/templates/competitions/combat/form_combat.html

echo -e "\n4. Tester la page directement avec curl pour voir l'erreur..."
# Capturer le HTML rendu pour voir où est l'erreur
curl -s "https://martialcomp.com/fr/competitions/combat/combats/creer/competition/4/" | grep -A10 -B10 -i "script" | grep -v "^$" | head -50

echo -e "\n5. Vérifier les fichiers JavaScript statiques..."
find apps/competitions/static -name "*.js" | xargs grep -l "combat" | head -10

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
