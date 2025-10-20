#!/bin/bash

# Script de sauvegarde complète du site MartialComp
# Date: $(date +"%Y-%m-%d %H:%M:%S")

echo "=== SAUVEGARDE COMPLÈTE DU SITE MARTIALCOMP ==="
echo ""

# Variables
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="martialcomp_backup_${BACKUP_DATE}"
BACKUP_DIR="/root/backups"
LOCAL_BACKUP_DIR="/mnt/c/martial_hub_django/martialcomp/backups"

# Créer les répertoires de sauvegarde
mkdir -p $BACKUP_DIR
mkdir -p $LOCAL_BACKUP_DIR

echo "📁 Répertoires de sauvegarde créés"
echo ""

# 1. Sauvegarde de la base de données
echo "1. SAUVEGARDE DE LA BASE DE DONNÉES"
echo "==================================="

cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Dump de la base de données PostgreSQL
echo "Exportation de la base de données..."
PGPASSWORD='AQWZSX123ok,' pg_dump -h localhost -U martialcomp_user -d martialcomp_db > $BACKUP_DIR/${BACKUP_NAME}_database.sql

if [ $? -eq 0 ]; then
    echo "✅ Base de données sauvegardée: ${BACKUP_NAME}_database.sql"
    echo "   Taille: $(du -h $BACKUP_DIR/${BACKUP_NAME}_database.sql | cut -f1)"
else
    echo "❌ Erreur lors de la sauvegarde de la base de données"
    exit 1
fi

echo ""

# 2. Sauvegarde des fichiers du projet
echo "2. SAUVEGARDE DES FICHIERS DU PROJET"
echo "===================================="

echo "Création de l'archive des fichiers..."
cd /var/www/vhosts/martialcomp.com

# Créer une archive tar avec compression
tar -czf $BACKUP_DIR/${BACKUP_NAME}_files.tar.gz \
    --exclude='httpdocs/venv' \
    --exclude='httpdocs/__pycache__' \
    --exclude='httpdocs/*/migrations/__pycache__' \
    --exclude='httpdocs/media/tmp/*' \
    --exclude='httpdocs/logs/*.log.*' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    httpdocs/

if [ $? -eq 0 ]; then
    echo "✅ Fichiers sauvegardés: ${BACKUP_NAME}_files.tar.gz"
    echo "   Taille: $(du -h $BACKUP_DIR/${BACKUP_NAME}_files.tar.gz | cut -f1)"
else
    echo "❌ Erreur lors de la sauvegarde des fichiers"
    exit 1
fi

echo ""

# 3. Sauvegarde des configurations importantes
echo "3. SAUVEGARDE DES CONFIGURATIONS"
echo "================================"

cd $BACKUP_DIR
mkdir -p ${BACKUP_NAME}_configs

# Copier les fichiers de configuration
cp /var/www/vhosts/martialcomp.com/httpdocs/.env.production ${BACKUP_NAME}_configs/
cp /etc/systemd/system/martialcomp.service ${BACKUP_NAME}_configs/
cp /var/www/vhosts/martialcomp.com/httpdocs/start_gunicorn.sh ${BACKUP_NAME}_configs/

# Sauvegarder la configuration nginx si elle existe
if [ -f "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf" ]; then
    cp /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf ${BACKUP_NAME}_configs/
fi

# Créer un fichier d'informations
cat > ${BACKUP_NAME}_configs/backup_info.txt << EOF
Sauvegarde MartialComp
Date: $(date)
Version Django: $(cd /var/www/vhosts/martialcomp.com/httpdocs && /var/www/vhosts/martialcomp.com/venv/bin/python -m django --version)
Python: $(python3 --version)
Serveur: $(hostname)
IP: $(hostname -I | awk '{print $1}')

Contenu de la sauvegarde:
- Base de données PostgreSQL: martialcomp_db
- Fichiers du projet (sans venv et cache)
- Configurations (.env.production, services, nginx)
- Scripts de maintenance

État du service au moment de la sauvegarde:
$(systemctl is-active martialcomp.service)
EOF

# Créer une archive des configs
tar -czf ${BACKUP_NAME}_configs.tar.gz ${BACKUP_NAME}_configs/
rm -rf ${BACKUP_NAME}_configs/

echo "✅ Configurations sauvegardées"
echo ""

# 4. Créer une archive complète
echo "4. CRÉATION DE L'ARCHIVE COMPLÈTE"
echo "================================="

echo "Création de l'archive finale..."
tar -czf ${BACKUP_NAME}_complete.tar.gz \
    ${BACKUP_NAME}_database.sql \
    ${BACKUP_NAME}_files.tar.gz \
    ${BACKUP_NAME}_configs.tar.gz

if [ $? -eq 0 ]; then
    echo "✅ Archive complète créée: ${BACKUP_NAME}_complete.tar.gz"
    echo "   Taille totale: $(du -h ${BACKUP_NAME}_complete.tar.gz | cut -f1)"
    
    # Nettoyer les fichiers individuels
    rm -f ${BACKUP_NAME}_database.sql
    rm -f ${BACKUP_NAME}_files.tar.gz
    rm -f ${BACKUP_NAME}_configs.tar.gz
else
    echo "❌ Erreur lors de la création de l'archive complète"
    exit 1
fi

echo ""

# 5. Copie locale (sera faite manuellement via SCP)
echo "5. INSTRUCTIONS POUR LA COPIE LOCALE"
echo "==================================="

echo "La sauvegarde est prête sur le serveur:"
echo "📍 Emplacement: $BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz"
echo ""
echo "Pour copier la sauvegarde en local, exécutez depuis votre machine locale:"
echo ""
echo "scp root@vigilant-swartz:$BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz $LOCAL_BACKUP_DIR/"
echo ""
echo "Ou utilisez la commande suivante si vous utilisez la connexion SSH martialcomp-production:"
echo ""
echo "scp martialcomp-production:$BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz $LOCAL_BACKUP_DIR/"
echo ""

# 6. Script de restauration
echo "6. CRÉATION DU SCRIPT DE RESTAURATION"
echo "====================================="

cat > $BACKUP_DIR/restore_${BACKUP_NAME}.sh << 'RESTORE_EOF'
#!/bin/bash

# Script de restauration pour la sauvegarde
BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <fichier_backup.tar.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Fichier de sauvegarde non trouvé: $BACKUP_FILE"
    exit 1
fi

echo "=== RESTAURATION DE MARTIALCOMP ==="
echo ""
echo "⚠️  ATTENTION: Cette opération va remplacer TOUTES les données actuelles!"
echo "Appuyez sur Ctrl+C pour annuler ou Entrée pour continuer..."
read

# Créer un répertoire temporaire
TEMP_DIR="/tmp/restore_$(date +%s)"
mkdir -p $TEMP_DIR

# Extraire l'archive
echo "Extraction de l'archive..."
tar -xzf $BACKUP_FILE -C $TEMP_DIR

# Arrêter le service
echo "Arrêt du service..."
systemctl stop martialcomp.service

# Restaurer la base de données
echo "Restauration de la base de données..."
DB_FILE=$(find $TEMP_DIR -name "*_database.sql" | head -1)
if [ -f "$DB_FILE" ]; then
    PGPASSWORD='AQWZSX123ok,' psql -h localhost -U martialcomp_user -d martialcomp_db < $DB_FILE
    echo "✅ Base de données restaurée"
else
    echo "❌ Fichier de base de données non trouvé"
fi

# Restaurer les fichiers
echo "Restauration des fichiers..."
FILES_ARCHIVE=$(find $TEMP_DIR -name "*_files.tar.gz" | head -1)
if [ -f "$FILES_ARCHIVE" ]; then
    cd /var/www/vhosts/martialcomp.com
    tar -xzf $FILES_ARCHIVE
    echo "✅ Fichiers restaurés"
else
    echo "❌ Archive des fichiers non trouvée"
fi

# Restaurer les configurations
echo "Restauration des configurations..."
CONFIGS_ARCHIVE=$(find $TEMP_DIR -name "*_configs.tar.gz" | head -1)
if [ -f "$CONFIGS_ARCHIVE" ]; then
    cd /tmp
    tar -xzf $CONFIGS_ARCHIVE
    # Restaurer les fichiers de config un par un avec confirmation
    echo "✅ Configurations extraites - vérifiez manuellement"
else
    echo "❌ Archive des configurations non trouvée"
fi

# Nettoyer
rm -rf $TEMP_DIR

# Redémarrer le service
echo "Redémarrage du service..."
systemctl start martialcomp.service

echo ""
echo "✅ Restauration terminée!"
echo "Vérifiez que tout fonctionne correctement."
RESTORE_EOF

chmod +x $BACKUP_DIR/restore_${BACKUP_NAME}.sh

echo "✅ Script de restauration créé: restore_${BACKUP_NAME}.sh"
echo ""

# 7. Résumé
echo "============================================"
echo "SAUVEGARDE COMPLÈTE TERMINÉE"
echo "============================================"
echo ""
echo "📦 Fichier de sauvegarde: ${BACKUP_NAME}_complete.tar.gz"
echo "📍 Emplacement: $BACKUP_DIR/"
echo "📏 Taille: $(du -h $BACKUP_DIR/${BACKUP_NAME}_complete.tar.gz | cut -f1)"
echo "🔧 Script de restauration: restore_${BACKUP_NAME}.sh"
echo ""
echo "La sauvegarde contient:"
echo "✅ Base de données complète"
echo "✅ Tous les fichiers du projet"
echo "✅ Configurations (.env, services, nginx)"
echo "✅ Scripts de maintenance"
echo ""
echo "N'oubliez pas de copier la sauvegarde en local!"
echo ""
echo "============================================"

# Nettoyer les anciennes sauvegardes (garder les 5 dernières)
echo ""
echo "Nettoyage des anciennes sauvegardes..."
cd $BACKUP_DIR
ls -t martialcomp_backup_*_complete.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
echo "✅ Anciennes sauvegardes nettoyées (5 dernières conservées)"