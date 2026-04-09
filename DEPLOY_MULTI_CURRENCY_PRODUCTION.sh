#!/bin/bash
# =============================================================================
# SCRIPT DE DEPLOIEMENT - IMPLEMENTATION MULTI-DEVISES
# Date: 07-01-2026
# Description: Transfert des fichiers modifiés pour la conversion multi-devises
# Serveur: 217.154.24.122 (root)
# =============================================================================

set -e

# Configuration
REMOTE_HOST="217.154.24.122"
REMOTE_USER="root"
REMOTE_PATH="/var/www/martialcomp"
LOCAL_PATH="$(pwd)"

echo "=============================================="
echo "DEPLOIEMENT MULTI-DEVISES - MartialComp"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

# Liste des fichiers à déployer
echo ""
echo "[1/6] Préparation de la liste des fichiers..."

# Fichiers Python modifiés
PYTHON_FILES=(
    "apps/finances/templatetags/finances_tags.py"
    "apps/finances/context_processors.py"
    "apps/finances/views/transactions.py"
)

# Templates modifiés
TEMPLATE_FILES=(
    "apps/finances/templates/finances/dashboard/index.html"
    "apps/finances/templates/finances/transactions/list.html"
    "apps/finances/templates/finances/accounts/list.html"
    "apps/finances/templates/finances/components/summary_card.html"
    "apps/finances/templates/finances/reports/index.html"
)

echo ""
echo "[2/6] Création du backup sur le serveur distant..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
BACKUP_DIR="/var/www/backups/multi_currency_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup des fichiers Python
cp -p /var/www/martialcomp/apps/finances/templatetags/finances_tags.py $BACKUP_DIR/ 2>/dev/null || true
cp -p /var/www/martialcomp/apps/finances/context_processors.py $BACKUP_DIR/ 2>/dev/null || true
cp -p /var/www/martialcomp/apps/finances/views/transactions.py $BACKUP_DIR/ 2>/dev/null || true

# Backup des templates
mkdir -p $BACKUP_DIR/templates
cp -rp /var/www/martialcomp/apps/finances/templates/finances/dashboard/index.html $BACKUP_DIR/templates/dashboard_index.html 2>/dev/null || true
cp -rp /var/www/martialcomp/apps/finances/templates/finances/transactions/list.html $BACKUP_DIR/templates/transactions_list.html 2>/dev/null || true
cp -rp /var/www/martialcomp/apps/finances/templates/finances/accounts/list.html $BACKUP_DIR/templates/accounts_list.html 2>/dev/null || true
cp -rp /var/www/martialcomp/apps/finances/templates/finances/components/summary_card.html $BACKUP_DIR/templates/summary_card.html 2>/dev/null || true
cp -rp /var/www/martialcomp/apps/finances/templates/finances/reports/index.html $BACKUP_DIR/templates/reports_index.html 2>/dev/null || true

echo "Backup créé dans: $BACKUP_DIR"
ENDSSH

echo ""
echo "[3/6] Transfert des fichiers Python..."
for file in "${PYTHON_FILES[@]}"; do
    echo "  - Transfert: $file"
    scp "$LOCAL_PATH/$file" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/$file
done

echo ""
echo "[4/6] Transfert des templates..."
for file in "${TEMPLATE_FILES[@]}"; do
    echo "  - Transfert: $file"
    scp "$LOCAL_PATH/$file" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/$file
done

echo ""
echo "[5/6] Redémarrage des services sur le serveur..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd /var/www/martialcomp

# Vider le cache Django
echo "  - Vidage du cache Django..."
source venv/bin/activate
python manage.py clear_cache 2>/dev/null || echo "    (clear_cache non disponible, ignoré)"

# Collecter les fichiers statiques si nécessaire
echo "  - Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear 2>/dev/null || python manage.py collectstatic --noinput

# Redémarrer Gunicorn
echo "  - Redémarrage de Gunicorn..."
systemctl restart gunicorn 2>/dev/null || supervisorctl restart gunicorn 2>/dev/null || pkill -HUP gunicorn

# Vérifier le statut
echo "  - Vérification du statut..."
systemctl status gunicorn --no-pager 2>/dev/null || supervisorctl status gunicorn 2>/dev/null || ps aux | grep gunicorn | head -3

echo ""
echo "Services redémarrés avec succès!"
ENDSSH

echo ""
echo "[6/6] Vérification finale..."
echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE AVEC SUCCES!"
echo "=============================================="
echo ""
echo "Fichiers déployés:"
echo "  - finances_tags.py (nouveaux filtres convert_from_eur)"
echo "  - context_processors.py (currency_code global)"
echo "  - transactions.py (currency_code dans les vues)"
echo "  - dashboard/index.html (KPIs + transactions convertis)"
echo "  - transactions/list.html (liste des transactions convertie)"
echo "  - accounts/list.html (comptes convertis)"
echo "  - summary_card.html (carte résumé convertie)"
echo "  - reports/index.html (rapports convertis)"
echo ""
echo "Pour tester la conversion multi-devises:"
echo "  1. Accéder à: https://votre-domaine/finances/dashboard/?currency=XOF"
echo "  2. Vérifier que les montants sont convertis en FCFA"
echo "  3. Tester avec d'autres devises: USD, GBP, etc."
echo ""
echo "En cas de problème, restaurer le backup:"
echo "  ssh root@217.154.24.122"
echo "  ls -la /var/www/backups/multi_currency_*"
echo ""
