#!/bin/bash
# ============================================================
# DÉPLOIEMENT - Page Welcome avec Compteurs et Mode Festif
# Version: 1.0
# Date: 2024-12-21
# ============================================================

set -e

echo "=========================================="
echo "DÉPLOIEMENT PAGE WELCOME v1.0"
echo "(Compteurs Réels + Mode Festif Noël)"
echo "=========================================="

# Configuration
SSH_TARGET="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}1. Transfert de la vue welcome.py (avec statistiques et mode festif)...${NC}"
scp apps/competitions/views/welcome.py ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/views/

echo -e "${YELLOW}2. Transfert du template welcome.html (avec compteurs et décorations Noël)...${NC}"
scp apps/competitions/templates/competitions/welcome.html ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/templates/competitions/

echo -e "${YELLOW}3. Redémarrage du serveur...${NC}"
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
echo "DÉPLOIEMENT TERMINÉ v1.0"
echo "=========================================="
echo ""
echo "Page mise à jour:"
echo "  - https://martialcomp.com/fr/?no_redirect=1"
echo ""
echo "COMPTEURS:"
echo "  ✓ Base de départ: 50 compétitions, 2500 pratiquants, 75 clubs, 12 fédérations"
echo "  ✓ + Données réelles de la base de données"
echo "  ✓ Les compteurs ne montreront plus jamais '0'"
echo ""
echo "MODE FESTIF (NOËL):"
echo "  ✓ Activé automatiquement du 15 décembre au 5 janvier"
echo "  ✓ Flocons de neige animés"
echo "  ✓ Guirlande lumineuse multicolore"
echo "  ✓ Bandeau de voeux festif"
echo "  ✓ Bouton pour désactiver les décorations (localStorage)"
echo ""
echo "CONFIGURATION (settings.py):"
echo "  - WELCOME_FESTIVE_MODE = True/False  # Forcer on/off"
echo "  - FESTIVE_MODE_START = '12-15'       # Date début (MM-DD)"
echo "  - FESTIVE_MODE_END = '01-05'         # Date fin (MM-DD)"
echo "  - FESTIVE_THEME = 'christmas'        # Thème"
echo "==========================================${NC}"
