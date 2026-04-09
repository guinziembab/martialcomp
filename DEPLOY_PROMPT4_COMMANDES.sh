#!/bin/bash
# =============================================================================
# PROMPT 4 - DEPLOIEMENT SECTION COMMANDES
# =============================================================================
# Ce script deploie les fichiers necessaires pour la section Commandes
# dans la fiche pratiquant.
#
# Fichiers deployes:
#   1. apps/shop/services/order_service.py (NOUVEAU)
#   2. apps/competitions/views/club/practitioners.py (MODIFIE)
#   3. apps/competitions/templates/competitions/club/practitioner_detail_modern.html (MODIFIE)
# =============================================================================

echo "=============================================="
echo "PROMPT 4 - DEPLOIEMENT SECTION COMMANDES"
echo "=============================================="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"

# Fichiers a deployer
FILE1="apps/shop/services/order_service.py"
FILE2="apps/competitions/views/club/practitioners.py"
FILE3="apps/competitions/templates/competitions/club/practitioner_detail_modern.html"

echo "Verification des fichiers locaux..."
echo ""

# Verifier que les fichiers existent
for file in "$FILE1" "$FILE2" "$FILE3"; do
    if [ -f "$file" ]; then
        echo "  [OK] $file"
    else
        echo "  [ERREUR] $file n'existe pas!"
        exit 1
    fi
done

echo ""
echo "Verification du contenu..."

# Verifier que OrderService contient les bonnes methodes
if grep -q "class OrderService" "$FILE1"; then
    echo "  [OK] OrderService class trouvee"
else
    echo "  [ERREUR] OrderService class non trouvee dans $FILE1"
    exit 1
fi

if grep -q "get_orders_summary" "$FILE1"; then
    echo "  [OK] get_orders_summary method trouvee"
else
    echo "  [ERREUR] get_orders_summary non trouvee"
    exit 1
fi

# Verifier que la vue charge orders_data
if grep -q "orders_data" "$FILE2"; then
    echo "  [OK] orders_data trouve dans la vue"
else
    echo "  [ERREUR] orders_data non trouve dans $FILE2"
    exit 1
fi

# Verifier que le template a l'onglet Commandes
if grep -q "orders-tab" "$FILE3"; then
    echo "  [OK] Onglet Commandes trouve dans le template"
else
    echo "  [ERREUR] Onglet Commandes non trouve dans $FILE3"
    exit 1
fi

echo ""
echo "=============================================="
echo "DEPLOIEMENT VERS LA PRODUCTION"
echo "=============================================="
echo ""

# 1. Deployer order_service.py
echo "[1/3] Deploiement de order_service.py..."
scp "$FILE1" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$FILE1"
if [ $? -eq 0 ]; then
    echo "      [OK] order_service.py deploye"
else
    echo "      [ERREUR] Echec du deploiement de order_service.py"
    exit 1
fi

# 2. Deployer practitioners.py
echo "[2/3] Deploiement de practitioners.py..."
scp "$FILE2" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$FILE2"
if [ $? -eq 0 ]; then
    echo "      [OK] practitioners.py deploye"
else
    echo "      [ERREUR] Echec du deploiement de practitioners.py"
    exit 1
fi

# 3. Deployer le template
echo "[3/3] Deploiement de practitioner_detail_modern.html..."
scp "$FILE3" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$FILE3"
if [ $? -eq 0 ]; then
    echo "      [OK] Template deploye"
else
    echo "      [ERREUR] Echec du deploiement du template"
    exit 1
fi

echo ""
echo "=============================================="
echo "REDEMARRAGE DU SERVEUR"
echo "=============================================="
echo ""

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
ssh "$REMOTE_USER@$REMOTE_HOST" "pkill -f 'gunicorn.*config.wsgi' 2>/dev/null; sleep 2; cd $REMOTE_PATH && source $VENV_PATH/bin/activate && $VENV_PATH/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8888 --workers 3 --daemon"

if [ $? -eq 0 ]; then
    echo "  [OK] Gunicorn redemarre"
else
    echo "  [ATTENTION] Verifiez le redemarrage de Gunicorn manuellement"
fi

echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE"
echo "=============================================="
echo ""
echo "Fichiers deployes:"
echo "  - order_service.py (Service des commandes)"
echo "  - practitioners.py (Vue avec chargement orders_data)"
echo "  - practitioner_detail_modern.html (Template avec onglet Commandes)"
echo ""
echo "Nouvelles fonctionnalites:"
echo "  - Statistiques commandes (total depense, nombre, moyenne)"
echo "  - Commandes en cours avec statut"
echo "  - Historique des 5 dernieres commandes"
echo "  - Produit favori"
echo ""
echo "Testez sur: https://martialcomp.com/fr/competitions/club/practitioner/<ID>/"
echo ""
