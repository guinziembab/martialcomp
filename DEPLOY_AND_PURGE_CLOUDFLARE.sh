#!/bin/bash
# =============================================================================
# DÉPLOIEMENT FINAL + PURGE CLOUDFLARE
# =============================================================================
# Ce script déploie les fichiers mis à jour et rappelle de purger le cache Cloudflare
#
# Date: 2025-12-13
# =============================================================================

set -e

echo "=============================================="
echo "=== DÉPLOIEMENT FINAL - Liste Poules ==="
echo "=============================================="
echo ""

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à déployer
FILES=(
    "apps/competitions/views/combat.py"
    "apps/competitions/urls/combat.py"
    "apps/competitions/templates/competitions/combat/liste_poules.html"
)

echo "=== ÉTAPE 1: Déploiement des fichiers ==="
for file in "${FILES[@]}"; do
    echo "  Déploiement: $file"
    scp "$file" "${REMOTE_HOST}:${REMOTE_PATH}/${file}"
done

echo ""
echo "=== ÉTAPE 2: Nettoyage des caches serveur ==="
ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Supprimer __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "  Cache Python supprimé"

# Vider le cache Django
source /var/www/vhosts/martialcomp.com/venv/bin/activate
python3 manage.py shell -c "from django.core.cache import cache; cache.clear(); print('  Cache Django vidé')" 2>/dev/null || echo "  Cache Django: commande exécutée"
deactivate 2>/dev/null || true

# Redémarrer Apache
touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py
sudo systemctl restart apache2 2>/dev/null || echo "  Redémarrage Apache via sudo non disponible"
echo "  Apache redémarré (wsgi.py touché)"
EOF

echo ""
echo "=== ÉTAPE 3: Vérification du déploiement ==="
ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "  Recherche 'never_cache' dans combat.py:"
grep -c "never_cache" apps/competitions/views/combat.py && echo "    OK: never_cache trouvé" || echo "    ERREUR"

echo "  Recherche 'fa-magic' dans liste_poules.html:"
grep -c "fa-magic" apps/competitions/templates/competitions/combat/liste_poules.html && echo "    OK: fa-magic trouvé" || echo "    ERREUR"

echo "  Recherche 'generatePoolsModal' dans liste_poules.html:"
grep -c "generatePoolsModal" apps/competitions/templates/competitions/combat/liste_poules.html && echo "    OK: modal trouvé" || echo "    ERREUR"
EOF

echo ""
echo "=============================================="
echo "=== DÉPLOIEMENT SERVEUR TERMINÉ ==="
echo "=============================================="
echo ""
echo "!!! IMPORTANT - ACTION MANUELLE REQUISE !!!"
echo ""
echo "Le cache CLOUDFLARE doit être purgé manuellement:"
echo ""
echo "1. Allez sur https://dash.cloudflare.com/"
echo "2. Sélectionnez le domaine: martialcomp.com"
echo "3. Allez dans: Caching → Configuration"
echo "4. Cliquez sur: 'Purge Everything'"
echo "5. Confirmez la purge"
echo ""
echo "Ensuite:"
echo "- Ouvrez un navigateur en mode INCOGNITO (Ctrl+Shift+N)"
echo "- Accédez à la page des poules"
echo "- Vérifiez que le modal s'ouvre (pas un confirm JavaScript)"
echo ""
