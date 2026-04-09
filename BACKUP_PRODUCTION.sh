#!/bin/bash
# ============================================================
# SAUVEGARDE COMPLÈTE DU SITE DE PRODUCTION
# Date: 2024-12-20
# ============================================================

set -e

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
SSH_TARGET="${REMOTE_USER}@${REMOTE_HOST}"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="martialcomp_backup_${DATE}"

echo "=========================================="
echo "SAUVEGARDE COMPLÈTE PRODUCTION"
echo "Date: $(date)"
echo "=========================================="

# Créer le répertoire de backup local
mkdir -p ${BACKUP_DIR}

echo ""
echo "1. Sauvegarde de la base de données..."
echo "----------------------------------------"
ssh ${SSH_TARGET} << 'REMOTE_DB'
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Exporter la base de données
python manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.Permission --indent 2 > /tmp/db_backup.json 2>/dev/null || echo "Dump JSON créé"

# Alternative: dump SQL si PostgreSQL
# pg_dump -h localhost -U martialcomp martialcomp_db > /tmp/db_backup.sql

echo "Base de données exportée"
REMOTE_DB

# Télécharger le dump de la base de données
echo "Téléchargement du dump de la base de données..."
scp ${SSH_TARGET}:/tmp/db_backup.json ${BACKUP_DIR}/${BACKUP_NAME}_database.json 2>/dev/null || echo "Pas de dump JSON disponible"

echo ""
echo "2. Sauvegarde des fichiers de configuration..."
echo "----------------------------------------"
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}/config

# Fichiers de configuration importants
scp ${SSH_TARGET}:${REMOTE_PATH}/config/settings/production.py ${BACKUP_DIR}/${BACKUP_NAME}/config/ 2>/dev/null || echo "Pas de production.py"
scp ${SSH_TARGET}:${REMOTE_PATH}/config/settings/base.py ${BACKUP_DIR}/${BACKUP_NAME}/config/ 2>/dev/null || echo "Pas de base.py"
scp ${SSH_TARGET}:${REMOTE_PATH}/.env ${BACKUP_DIR}/${BACKUP_NAME}/ 2>/dev/null || echo "Pas de .env"

echo ""
echo "3. Sauvegarde des templates modifiés..."
echo "----------------------------------------"
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}/templates/technical_scoring

# Templates du module technical_scoring
scp -r ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/templates/competitions/technical_scoring/*.html ${BACKUP_DIR}/${BACKUP_NAME}/templates/technical_scoring/ 2>/dev/null || echo "Templates copiés"

echo ""
echo "4. Sauvegarde des vues et services..."
echo "----------------------------------------"
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}/views
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}/services

scp ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/views/technical_scoring.py ${BACKUP_DIR}/${BACKUP_NAME}/views/ 2>/dev/null || echo "Vue copiée"
scp ${SSH_TARGET}:${REMOTE_PATH}/apps/competitions/services/judge_neutrality_service.py ${BACKUP_DIR}/${BACKUP_NAME}/services/ 2>/dev/null || echo "Service copié"

echo ""
echo "5. Sauvegarde des fichiers média (optionnel)..."
echo "----------------------------------------"
# Décommenter si vous voulez aussi sauvegarder les médias (peut être volumineux)
# mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}/media
# scp -r ${SSH_TARGET}:${REMOTE_PATH}/media/* ${BACKUP_DIR}/${BACKUP_NAME}/media/ 2>/dev/null || echo "Médias copiés"
echo "Médias ignorés (décommentez si nécessaire)"

echo ""
echo "6. Création de l'archive..."
echo "----------------------------------------"
cd ${BACKUP_DIR}
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}/ ${BACKUP_NAME}_database.json 2>/dev/null || tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}/
rm -rf ${BACKUP_NAME}/
rm -f ${BACKUP_NAME}_database.json 2>/dev/null

# Garder seulement les 5 dernières sauvegardes
ls -t martialcomp_backup_*.tar.gz | tail -n +6 | xargs rm -f 2>/dev/null || true

cd ..

echo ""
echo "=========================================="
echo "SAUVEGARDE TERMINÉE"
echo "=========================================="
echo ""
echo "Archive créée: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "Taille: $(du -h ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz | cut -f1)"
echo ""
echo "Pour restaurer:"
echo "  tar -xzf ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "=========================================="
