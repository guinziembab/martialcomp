#!/bin/bash
# DIAGNOSTIC URGENT - Trouver pourquoi l'ancien template est servi

echo "=== DIAGNOSTIC TEMPLATE liste_poules.html ==="
echo ""

REMOTE="martialcomp-production"
TEMPLATE_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_poules.html"

echo "1. Vérifier le contenu EXACT du bouton Générer (lignes autour de 'Générer automatiquement'):"
ssh $REMOTE "grep -n -B2 -A2 'Générer automatiquement' $TEMPLATE_PATH | head -30"

echo ""
echo "2. Vérifier si c'est un bouton ou un lien:"
ssh $REMOTE "grep -c 'data-bs-toggle=\"modal\"' $TEMPLATE_PATH && echo 'Modal trouvé' || echo 'PAS de modal'"
ssh $REMOTE "grep -c 'onclick=\"return confirm' $TEMPLATE_PATH && echo 'Ancien confirm() trouvé' || echo 'Pas de confirm()'"

echo ""
echo "3. Vérifier la date de modification du fichier:"
ssh $REMOTE "ls -la $TEMPLATE_PATH"
ssh $REMOTE "stat $TEMPLATE_PATH | grep -i modify"

echo ""
echo "4. Chercher TOUS les fichiers liste_poules.html sur le serveur:"
ssh $REMOTE "find /var/www/vhosts/martialcomp.com -name 'liste_poules.html' -type f 2>/dev/null"

echo ""
echo "5. Vérifier la config Django TEMPLATES pour voir les DIRS:"
ssh $REMOTE "grep -A 10 'TEMPLATES = \[' /var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py 2>/dev/null || grep -A 10 'TEMPLATES = \[' /var/www/vhosts/martialcomp.com/httpdocs/config/settings/base.py"

echo ""
echo "6. Afficher les 50 premières lignes du template pour vérifier:"
ssh $REMOTE "head -50 $TEMPLATE_PATH"

echo ""
echo "7. Vérifier le hash MD5 du fichier local vs serveur:"
echo "Local:"
md5sum apps/competitions/templates/competitions/combat/liste_poules.html 2>/dev/null || md5 apps/competitions/templates/competitions/combat/liste_poules.html 2>/dev/null || echo "md5 non dispo"
echo "Serveur:"
ssh $REMOTE "md5sum $TEMPLATE_PATH"
