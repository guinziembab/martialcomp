#\!/bin/bash
# Analyser le problème de l'icône profil

echo "=== ANALYSE ICÔNE PROFIL ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Recherche du template de mise à jour..."
find apps -name "*.html" -type f  < /dev/null |  xargs grep -l "competition.*update" | grep -E "(form|update)" | head -5

echo "2. Vérification du template de base..."
# L'icône profil est probablement dans base.html
grep -A10 -B5 "notification.*icon\|profile.*icon\|dropdown.*user" apps/competitions/templates/base.html | head -30

echo "3. Recherche des fichiers JavaScript associés..."
find apps/competitions/static -name "*.js" -type f | xargs grep -l "dropdown\|profile\|user.*menu" | head -5

echo "4. Vérification des erreurs JavaScript côté client..."
# Créer un script de test pour vérifier les erreurs JS
cat > /tmp/check_js_errors.html << 'HTML'
<script>
// Script pour détecter les erreurs JS sur la page
console.log("Vérification des erreurs JavaScript...");
// Ce script sera exécuté côté client
</script>
HTML

echo "5. Analyse du HTML de l'icône profil..."
# Chercher spécifiquement le code de l'icône profil/dropdown
grep -r "dropdown.*toggle\|user.*dropdown\|profile.*dropdown" apps/competitions/templates/ | grep -v ".py" | head -10

echo "6. Vérifier si le JavaScript nécessaire est chargé..."
# Chercher les imports de JS dans le template
grep -r "bootstrap.*dropdown\|dropdown.*js" apps/competitions/templates/ | head -5

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
