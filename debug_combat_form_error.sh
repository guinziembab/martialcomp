#\!/bin/bash
# Debug de l'erreur JavaScript sur le formulaire de combat

echo "=== DEBUG ERREUR FORMULAIRE COMBAT ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Examiner le template du formulaire de combat..."
echo "Vérification du template form_combat.html:"
grep -n "<script\ < /dev/null | </script>" apps/competitions/templates/competitions/combat/form_combat.html

echo -e "\n2. Afficher le contenu complet du template..."
cat apps/competitions/templates/competitions/combat/form_combat.html

echo -e "\n3. Vérifier s'il y a des scripts inline mal formés..."
grep -A5 -B5 "script" apps/competitions/templates/competitions/combat/form_combat.html | grep -v "^--$"

echo -e "\n4. Chercher les erreurs de syntaxe courantes..."
# Chercher les balises HTML dans du JavaScript
grep -E "<[^>]+>" apps/competitions/templates/competitions/combat/form_combat.html | grep -v "{% \|{{ \|<\!--" | tail -20

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
