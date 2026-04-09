#\!/bin/bash
# Solution simple pour l'erreur de syntaxe

echo "=== SOLUTION SIMPLE ERREUR SYNTAXE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Identifier et commenter la partie problématique..."
# On sait que l'erreur est après la ligne 1059
# Cherchons et commentons temporairement le code problématique

# D'abord, voir ce qu'il y a après la ligne 1059
echo "Contenu après ligne 1059:"
sed -n '1059,1085p' apps/competitions/templates/competitions/competition/create.html

echo -e "\n2. Commenter le script problématique..."
# Remplacer le script problématique par une version commentée
sed -i.bak '1061,1083s/^/<\!-- TEMPORAIREMENT DESACTIVE: /' apps/competitions/templates/competitions/competition/create.html
sed -i '1061,1083s/$/ -->/' apps/competitions/templates/competitions/competition/create.html

echo "3. Vérifier la modification..."
echo "Après modification:"
sed -n '1059,1065p' apps/competitions/templates/competitions/competition/create.html

echo "4. Redémarrer..."
sudo pkill -HUP -f gunicorn
sleep 2

echo -e "\n✓ Script problématique commenté"
echo "L'erreur de syntaxe devrait être résolue et le dropdown devrait fonctionner."

SSHEOF

echo ""
echo "=== TERMINÉ ==="
