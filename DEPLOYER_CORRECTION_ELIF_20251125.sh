#!/bin/bash
# Script pour déployer la correction du {% elif currentValue %} en production
# Date: 25 novembre 2024
#
# CAUSE DE L'ERREUR:
# {% elif currentValue %} utilisait une variable JavaScript (currentValue)
# comme si c'était une variable Django, ce qui générait du code JavaScript invalide
#
# CORRECTION APPLIQUÉE:
# Remplacé par {% else %} + if (currentValue) { ... } en JavaScript pur
# Ajouté |escapejs au filtre Django pour échapper correctement la valeur

echo "=================================================="
echo "DÉPLOIEMENT DE LA CORRECTION - {% elif currentValue %}"
echo "=================================================="
echo ""

# Chemin du fichier à déployer
LOCAL_FILE="apps/competitions/templates/competitions/club/practitioner_form.html"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/practitioner_form.html"

echo "=== 1. Vérification de la correction locale ==="
echo ""
echo "Recherche de {% elif currentValue %} (NE DEVRAIT PAS EXISTER):"
grep -n "{% elif currentValue %}" "$LOCAL_FILE" && echo "❌ ERREUR: Le tag problématique existe encore!" && exit 1
echo "✅ Le tag problématique a été corrigé"
echo ""

echo "Vérification de la nouvelle syntaxe (DEVRAIT EXISTER):"
grep -n "{% else %}" "$LOCAL_FILE" | grep -A 2 "Si une valeur"
echo ""

echo "=== 2. Transfert du fichier vers la production ==="
echo "Commande: scp $LOCAL_FILE pierrep99@martialcomp.com:$REMOTE_PATH"
echo ""

# Le transfert SCP - à décommenter pour exécuter
# scp "$LOCAL_FILE" "pierrep99@martialcomp.com:$REMOTE_PATH"

echo "⚠️  COMMANDE SCP À EXÉCUTER MANUELLEMENT:"
echo ""
echo "scp \"$LOCAL_FILE\" \"pierrep99@martialcomp.com:$REMOTE_PATH\""
echo ""

echo "=== 3. Après le transfert, vider le cache sur le serveur ==="
echo ""
echo "Commandes à exécuter sur le serveur:"
echo ""
cat << 'EOF'
ssh pierrep99@martialcomp.com << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Vérifier que la correction est bien présente
echo "=== Vérification de la correction ==="
grep -n "{% elif currentValue %}" apps/competitions/templates/competitions/club/practitioner_form.html && echo "❌ ERREUR: Le tag problématique existe encore!" && exit 1
echo "✅ Correction vérifiée"

# Vider les caches
echo ""
echo "=== Vidage des caches ==="
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "✅ Cache Python vidé"

# Vider le cache Django si disponible
source /var/www/vhosts/martialcomp.com/venv/bin/activate
python3 manage.py shell -c "from django.core.cache import cache; cache.clear(); print('✅ Cache Django vidé')" 2>/dev/null || echo "Cache Django: commande non disponible"

# Redémarrer Passenger
mkdir -p tmp
touch tmp/restart.txt
echo "✅ Passenger redémarré"

echo ""
echo "=== Vérification finale ==="
ls -lh apps/competitions/templates/competitions/club/practitioner_form.html
echo ""
echo "Correction déployée avec succès!"
ENDSSH
EOF

echo ""
echo "=================================================="
echo "INSTRUCTIONS"
echo "=================================================="
echo ""
echo "1. Exécutez la commande SCP ci-dessus pour transférer le fichier"
echo "2. Connectez-vous au serveur: ssh pierrep99@martialcomp.com"
echo "3. Exécutez les commandes de vidage de cache"
echo "4. Testez la page: https://martialcomp.com/fr/competitions/club/practitioners/88/edit/"
echo "5. Vérifiez la console (F12) - l'erreur JavaScript devrait avoir disparu"
echo ""
