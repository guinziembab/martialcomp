#\!/bin/bash
# Débugger l'erreur à la ligne 1215

echo "=== DEBUG ERREUR LIGNE 1215 ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Capturer le HTML rendu de la page..."
# Utiliser curl avec authentification pour voir le HTML complet
curl -s -L "https://martialcomp.com/fr/competitions/combat/combats/creer/competition/4/" > /tmp/combat_page.html

echo "2. Examiner autour de la ligne 1215..."
# Afficher les lignes 1210-1220
sed -n '1210,1220p' /tmp/combat_page.html

echo -e "\n3. Chercher les balises <script> mal fermées ou du HTML dans du JS..."
# Chercher les patterns problématiques
grep -n -A5 -B5 "<script" /tmp/combat_page.html  < /dev/null |  grep -A10 -B10 "1215" | head -30

echo -e "\n4. Vérifier s'il y a des erreurs 404 ou des redirections..."
# Chercher les erreurs dans le HTML
grep -i "error\|404\|not found" /tmp/combat_page.html | head -10

echo -e "\n5. Analyser le contenu JavaScript inline..."
# Extraire tous les blocs script
awk '/<script/{p=1} p{print NR ": " $0} /<\/script/{p=0}' /tmp/combat_page.html | grep -A5 -B5 "1215"

echo -e "\n6. Vérifier si c'est une erreur d'authentification..."
# Si la page redirige vers login
grep -i "login\|authentification\|connexion" /tmp/combat_page.html | head -5

echo -e "\n7. Alternative: obtenir directement le contenu de la ligne problématique..."
awk 'NR==1215 {print "Ligne 1215: " $0}' /tmp/combat_page.html

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
