#!/bin/bash
# =============================================================================
# DÉPLOIEMENT - CORRECTIONS INTERFACE COMBAT V2
# =============================================================================
# Ce script déploie les corrections pour l'interface de combat v2:
# 1. Scroll et adaptation responsive pour tous les écrans
# 2. Configuration du timer visible directement (1min, 1:30, 2min, 3min, 4min, 5min)
# 3. Boutons de prolongation en cas d'égalité (30s et 1min)
#
# Date: 2025-12-14
# =============================================================================

set -e

echo "=============================================="
echo "=== DÉPLOIEMENT - Interface Combat V2 Fix ==="
echo "=============================================="
echo ""

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichier à déployer
FILE="apps/competitions/templates/competitions/combat/interface_combat_v2.html"

echo "=== ÉTAPE 1: Sauvegarde de l'ancien fichier ==="
ssh ${REMOTE_HOST} "cd ${REMOTE_PATH} && cp ${FILE} ${FILE}.backup_\$(date +%Y%m%d_%H%M%S)"
echo "  Sauvegarde créée"

echo ""
echo "=== ÉTAPE 2: Déploiement du nouveau fichier ==="
scp "${FILE}" "${REMOTE_HOST}:${REMOTE_PATH}/${FILE}"
echo "  Fichier déployé: ${FILE}"

echo ""
echo "=== ÉTAPE 3: Nettoyage des caches serveur ==="
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

# Redémarrer Apache/Gunicorn
touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py
sudo systemctl restart apache2 2>/dev/null || echo "  Redémarrage Apache via sudo non disponible"
echo "  Apache redémarré (wsgi.py touché)"
EOF

echo ""
echo "=== ÉTAPE 4: Vérification du déploiement ==="
ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "  Recherche 'timer-config' dans interface_combat_v2.html:"
grep -c "timer-config" apps/competitions/templates/competitions/combat/interface_combat_v2.html && echo "    OK: Configuration timer trouvée" || echo "    ERREUR"

echo "  Recherche 'startProlongation' dans interface_combat_v2.html:"
grep -c "startProlongation" apps/competitions/templates/competitions/combat/interface_combat_v2.html && echo "    OK: Fonction prolongation trouvée" || echo "    ERREUR"

echo "  Recherche 'equality-alert' dans interface_combat_v2.html:"
grep -c "equality-alert" apps/competitions/templates/competitions/combat/interface_combat_v2.html && echo "    OK: Alerte égalité trouvée" || echo "    ERREUR"
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
echo "- Accédez à l'interface combat: /competitions/combat/combats/XXX/interface-v2/"
echo "- Vérifiez:"
echo "  1. Le scroll fonctionne sur tous les écrans"
echo "  2. Les boutons de durée (1min, 1:30, 2min...) sont visibles"
echo "  3. Quand le timer atteint 0 avec égalité, les boutons 30s/1min apparaissent"
echo ""
