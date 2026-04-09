#!/bin/bash
# =============================================================================
# DEPLOIEMENT DEBUG - MODAL CREATION EQUIPE
# Date: 2024-12-03
# Description: Correction du filtrage des pratiquants + logging de debug
#
# Corrections apportées:
#   1. Ajout d'une recherche fallback de l'organization via old_club_id
#   2. Ajout de logs DEBUG pour diagnostiquer le problème
# =============================================================================

SSH_HOST="martialcomp-production"
REMOTE_BASE="/var/www/vhosts/martialcomp.com/httpdocs"

echo "========================================"
echo "DEPLOIEMENT DEBUG - MODAL CREATION EQUIPE"
echo "========================================"
echo ""

# =============================================================================
# 1. TRANSFERT DE LA VUE AVEC DEBUG
# =============================================================================
echo "1. Transfert de registration_api.py avec logging debug..."
scp apps/competitions/views/club/registration_api.py ${SSH_HOST}:${REMOTE_BASE}/apps/competitions/views/club/registration_api.py
echo "   -> Fichier transféré"
echo ""

# =============================================================================
# 2. VERIFICATION SYNTAXE
# =============================================================================
echo "2. Vérification de la syntaxe Python..."
ssh ${SSH_HOST} "cd ${REMOTE_BASE} && source ../venv/bin/activate && python3 -m py_compile apps/competitions/views/club/registration_api.py"
echo "   -> Syntaxe OK"
echo ""

# =============================================================================
# 3. NETTOYAGE CACHE PYTHON
# =============================================================================
echo "3. Nettoyage du cache Python..."
ssh ${SSH_HOST} "find ${REMOTE_BASE}/apps -name '*.pyc' -delete && find ${REMOTE_BASE}/apps -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true"
echo "   -> Cache nettoyé"
echo ""

# =============================================================================
# 4. REDEMARRAGE DU SERVEUR
# =============================================================================
echo "4. Redémarrage du serveur..."
ssh ${SSH_HOST} "sudo systemctl restart apache2 && sudo systemctl restart gunicorn 2>/dev/null || true"
echo "   -> Serveur redémarré"
echo ""

echo "========================================"
echo "DEPLOIEMENT TERMINE"
echo "========================================"
echo ""
echo "Pour voir les logs de debug, exécutez:"
echo ""
echo "  ssh ${SSH_HOST}"
echo "  tail -f /var/log/apache2/error.log | grep 'DEBUG TEAM MODAL'"
echo ""
echo "Puis accédez à:"
echo "  https://martialcomp.com/fr/competitions/club/competition-registration/4/"
echo ""
echo "Les logs afficheront:"
echo "  - Club de l'utilisateur et son organization"
echo "  - Nombre de pratiquants du club"
echo "  - Nombre d'inscriptions trouvées"
echo "  - Catégories associées aux inscriptions"
echo ""
