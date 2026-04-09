#\!/bin/bash
# Recherche directe de l'erreur

echo "=== RECHERCHE DIRECTE ERREUR ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Chercher dans le template autour du code problématique..."
# Ligne 1780 dans le navigateur = environ ligne 1040+ dans le template
sed -n '1040,1060p' apps/competitions/templates/competitions/competition/create.html

echo -e "\n2. Rechercher les fins de script et début suivants..."
grep -n -A5 -B5 "</script>" apps/competitions/templates/competitions/competition/create.html  < /dev/null |  grep -A10 -B10 "1040\|1050\|1060"

echo -e "\n3. Vérifier s'il y a un problème de fermeture de balise..."
# Compter les balises script
echo "Nombre de <script>: $(grep -c "<script" apps/competitions/templates/competitions/competition/create.html)"
echo "Nombre de </script>: $(grep -c "</script>" apps/competitions/templates/competitions/competition/create.html)"

echo -e "\n4. Examiner la ligne exacte 1055 (approximation de 1780 dans le rendu)..."
sed -n '1055p' apps/competitions/templates/competitions/competition/create.html

echo -e "\n5. Chercher des caractères invisibles ou mal encodés..."
# Utiliser od pour voir les bytes
sed -n '1055p' apps/competitions/templates/competitions/competition/create.html | od -c

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
