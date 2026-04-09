#!/bin/bash
# ============================================================
# DÉPLOIEMENT - Système d'Analyse de Neutralité des Juges
# Version: 2.3 (avec Thème Sombre)
# Date: 2024-12-21
# ============================================================

set -e

echo "=========================================="
echo "DÉPLOIEMENT ANALYSE NEUTRALITÉ JUGES v2.3"
echo "(Thème Sombre + Podium des Juges)"
echo "=========================================="

# Configuration
SSH_TARGET="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}1. Transfert du service de neutralité...${NC}"
scp apps/competitions/services/judge_neutrality_service.py ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/services/

echo -e "${YELLOW}2. Transfert du template neutralité (avec Podium)...${NC}"
scp apps/competitions/templates/competitions/technical_scoring/judge_neutrality.html ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/templates/competitions/technical_scoring/

echo -e "${YELLOW}3. Transfert de la vue mise à jour...${NC}"
scp apps/competitions/views/technical_scoring.py ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/views/

echo -e "${YELLOW}4. Transfert des URLs mises à jour...${NC}"
scp apps/competitions/urls/technical_scoring.py ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/urls/

echo -e "${YELLOW}5. Transfert des templates avec lien Neutralité dans sidebar...${NC}"
scp apps/competitions/templates/competitions/technical_scoring/scoring_history.html ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/templates/competitions/technical_scoring/
scp apps/competitions/templates/competitions/technical_scoring/judge_dashboard.html ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/templates/competitions/technical_scoring/
scp apps/competitions/templates/competitions/technical_scoring/categories.html ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/templates/competitions/technical_scoring/

echo -e "${YELLOW}6. Redémarrage du serveur...${NC}"
ssh ${SSH_TARGET} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Vider le cache Django
python manage.py clear_cache 2>/dev/null || echo "Cache vidé manuellement"

# Nettoyer les fichiers .pyc
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Redémarrer Gunicorn
sudo systemctl restart gunicorn 2>/dev/null || pkill -HUP gunicorn || echo "Redémarrage manuel nécessaire"

echo "Serveur redémarré"
EOF

echo ""
echo -e "${GREEN}=========================================="
echo "DÉPLOIEMENT TERMINÉ v2.3"
echo "=========================================="
echo ""
echo "Fonctionnalités déployées:"
echo "  - /fr/competitions/technical-scoring/neutrality/"
echo "  - /fr/competitions/technical-scoring/neutrality/<competition_id>/"
echo ""
echo "Nouveautés v2.3:"
echo "  ✓ THÈME SOMBRE complet pour toute la page"
echo "  ✓ Couleurs adaptées (fond #1a1d24, cartes #2a2f3a)"
echo "  ✓ Contrastes optimisés pour la lisibilité"
echo "  ✓ Graphique radar et podium en thème sombre"
echo ""
echo "Fonctionnalités v2.2:"
echo "  ✓ PODIUM DES JUGES les plus impartiaux (Or, Argent, Bronze)"
echo "  ✓ Affichage visuel avec médailles et scores"
echo ""
echo "Fonctionnalités v2.1:"
echo "  ✓ SÉCURITÉ RGPD: Segmentation stricte des compétitions"
echo ""
echo "Cette page analyse:"
echo "  ✓ Biais de club (favoritisme même club)"
echo "  ✓ Biais de nationalité"
echo "  ✓ Biais de position (sévérité/générosité)"
echo "  ✓ Corrélation avec autres juges"
echo "==========================================${NC}"
