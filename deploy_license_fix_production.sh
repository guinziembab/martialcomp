#!/bin/bash

# Script pour déployer la correction de génération de numéro de licence en production
# 8 Octobre 2025

set -e

HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"
API_FILE="${HTTPDOCS}/apps/competitions/api.py"
BACKUP_FILE="${API_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "======================================"
echo "CORRECTION GÉNÉRATION NUMÉRO DE LICENCE"
echo "======================================"
echo

# 1. Backup du fichier original
echo "1️⃣  Création du backup..."
cp "${API_FILE}" "${BACKUP_FILE}"
echo "✅ Backup créé: $(basename ${BACKUP_FILE})"
echo

# 2. Afficher le contenu actuel
echo "2️⃣  Contenu actuel du fichier api.py..."
tail -10 "${API_FILE}"
echo

# 3. Vérifier si la route existe déjà
if grep -q "generate-license-number" "${API_FILE}"; then
    echo "✅ La route generate-license-number existe déjà"
    exit 0
fi

# 4. Ajouter l'import et la route
echo "3️⃣  Ajout de la route generate-license-number..."

# Créer un fichier temporaire avec les modifications
cat > /tmp/api_fix.txt << 'EOF'

from django.urls import path
from apps.competitions.views.api import generate_license_number

urlpatterns = [
    path('upcoming/', CompetitionListView.as_view(), name='competitions_upcoming'),
    path('generate-license-number/', generate_license_number, name='generate_license_number'),
]
EOF

# Remplacer la partie urlpatterns dans le fichier
sed -i.bak '/^from django.urls import path$/,/^]$/c\
from django.urls import path\
from apps.competitions.views.api import generate_license_number\
\
urlpatterns = [\
    path('"'"'upcoming/'"'"', CompetitionListView.as_view(), name='"'"'competitions_upcoming'"'"'),\
    path('"'"'generate-license-number/'"'"', generate_license_number, name='"'"'generate_license_number'"'"'),\
]' "${API_FILE}"

echo "✅ Route ajoutée"
echo

# 5. Vérifier la syntaxe Python
echo "4️⃣  Vérification de la syntaxe Python..."
cd "${HTTPDOCS}"
source /var/www/vhosts/martialcomp.com/venv/bin/activate
python3 -m py_compile "${API_FILE}"

if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python valide"
else
    echo "❌ Erreur de syntaxe Python!"
    echo "Restauration du backup..."
    mv "${BACKUP_FILE}" "${API_FILE}"
    exit 1
fi
echo

# 6. Ajuster les permissions
echo "5️⃣  Ajustement des permissions..."
chown www-data:www-data "${API_FILE}"
chmod 644 "${API_FILE}"
echo "✅ Permissions ajustées"
echo

# 7. Redémarrer le service
echo "6️⃣  Redémarrage du service..."
systemctl restart martialcomp.service
sleep 5

if systemctl is-active --quiet martialcomp.service; then
    echo "✅ Service redémarré avec succès"
else
    echo "❌ Erreur lors du redémarrage du service"
    systemctl status martialcomp.service --no-pager | head -20
    exit 1
fi
echo

# 8. Test de l'API
echo "7️⃣  Test de l'API..."
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/fr/)

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 301 ]; then
    echo "✅ Site accessible (HTTP ${HTTP_CODE})"
else
    echo "⚠️  Code HTTP: ${HTTP_CODE}"
fi
echo

# 9. Afficher le résumé
echo "======================================"
echo "RÉSUMÉ"
echo "======================================"
echo "✅ Backup: $(basename ${BACKUP_FILE})"
echo "✅ Route ajoutée: /fr/competitions/api/generate-license-number/"
echo "✅ Syntaxe validée"
echo "✅ Service redémarré"
echo
echo "📝 INSTRUCTIONS:"
echo "1. Tester la génération de licence: https://martialcomp.com/fr/competitions/club/practitioners/add/"
echo "2. Vérifier dans la console du navigateur (pas d'erreur 404)"
echo "3. Si problème, restaurer avec: cp ${BACKUP_FILE} ${API_FILE} && systemctl restart martialcomp.service"
echo

exit 0
