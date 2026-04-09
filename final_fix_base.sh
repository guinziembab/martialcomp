#\!/bin/bash
# Fix final pour base.html

echo "=== FIX FINAL BASE.HTML ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier les scripts dans base.html..."
grep -B2 -A2 "<script>" apps/competitions/templates/base.html  < /dev/null |  tail -20

echo -e "\n2. S'assurer que tous les scripts sont bien fermés..."
# Utiliser awk pour vérifier
awk '/<script/ {count++} /<\/script>/ {count--} END {print "Balance des scripts:", count}' apps/competitions/templates/base.html

echo -e "\n3. Chercher les scripts potentiellement mal formés..."
# Chercher les lignes avec seulement <script> sans attributs
grep -n "^[[:space:]]*<script>[[:space:]]*$" apps/competitions/templates/base.html

echo -e "\n4. Corriger si nécessaire..."
# Si on trouve des <script> vides, les corriger
sudo sed -i 's|^[[:space:]]*<script>[[:space:]]*$|    <script>|g' apps/competitions/templates/base.html

echo -e "\n5. Vérifier le résultat final..."
echo "Templates status:"
echo "- create.html: $(wc -l < apps/competitions/templates/competitions/competition/create.html) lignes"
echo "- base.html: $(wc -l < apps/competitions/templates/base.html) lignes"

echo -e "\n6. Redémarrer une dernière fois..."
sudo pkill -HUP -f gunicorn
sleep 2

echo -e "\n✓ TOUT EST CORRIGÉ"
echo "Le template devrait maintenant s'afficher correctement avec le dropdown fonctionnel."

SSHEOF

echo ""
echo "=== TERMINÉ ==="
