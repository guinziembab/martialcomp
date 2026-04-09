#!/bin/bash
# Script de sauvegarde complète de la plateforme MartialComp
# Date: $(date +"%Y-%m-%d %H:%M:%S")

echo "=== SAUVEGARDE COMPLÈTE DE MARTIALCOMP PRODUCTION ==="
echo "Date de début: $(date +"%Y-%m-%d %H:%M:%S")"
echo ""

# Variables
BACKUP_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="martialcomp_backup_complete_${BACKUP_DATE}"
BACKUP_DIR="/root/backups/${BACKUP_NAME}"
PROD_DIR="/var/www/vhosts/martialcomp.com"

# Créer le répertoire de sauvegarde
echo "1. Création du répertoire de sauvegarde..."
mkdir -p ${BACKUP_DIR}

# Sauvegarde de la base de données PostgreSQL
echo ""
echo "2. Sauvegarde de la base de données PostgreSQL..."
DB_NAME="martialcomp_db"
DB_USER="django_user"
DB_BACKUP="${BACKUP_DIR}/database_${DB_NAME}_${BACKUP_DATE}.sql"

# Dump de la base de données
sudo -u postgres pg_dump ${DB_NAME} > ${DB_BACKUP}
if [ $? -eq 0 ]; then
    echo "   ✓ Base de données sauvegardée: $(du -h ${DB_BACKUP} | cut -f1)"
    gzip ${DB_BACKUP}
    echo "   ✓ Base de données compressée: $(du -h ${DB_BACKUP}.gz | cut -f1)"
else
    echo "   ✗ ERREUR lors de la sauvegarde de la base de données"
fi

# Sauvegarde du code source
echo ""
echo "3. Sauvegarde du code source..."
CODE_BACKUP="${BACKUP_DIR}/code_httpdocs_${BACKUP_DATE}.tar.gz"
cd ${PROD_DIR}
tar -czf ${CODE_BACKUP} \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='venv' \
    --exclude='logs/*.log' \
    --exclude='media/tmp/*' \
    httpdocs/
    
if [ $? -eq 0 ]; then
    echo "   ✓ Code source sauvegardé: $(du -h ${CODE_BACKUP} | cut -f1)"
else
    echo "   ✗ ERREUR lors de la sauvegarde du code source"
fi

# Sauvegarde des fichiers media
echo ""
echo "4. Sauvegarde des fichiers media..."
MEDIA_BACKUP="${BACKUP_DIR}/media_${BACKUP_DATE}.tar.gz"
if [ -d "${PROD_DIR}/httpdocs/media" ]; then
    tar -czf ${MEDIA_BACKUP} -C ${PROD_DIR}/httpdocs media/
    echo "   ✓ Fichiers media sauvegardés: $(du -h ${MEDIA_BACKUP} | cut -f1)"
else
    echo "   ! Pas de répertoire media trouvé"
fi

# Sauvegarde des fichiers static
echo ""
echo "5. Sauvegarde des fichiers static..."
STATIC_BACKUP="${BACKUP_DIR}/static_${BACKUP_DATE}.tar.gz"
if [ -d "${PROD_DIR}/httpdocs/static" ]; then
    tar -czf ${STATIC_BACKUP} -C ${PROD_DIR}/httpdocs static/
    echo "   ✓ Fichiers static sauvegardés: $(du -h ${STATIC_BACKUP} | cut -f1)"
else
    echo "   ! Pas de répertoire static trouvé"
fi

# Sauvegarde de la configuration
echo ""
echo "6. Sauvegarde de la configuration..."
CONFIG_BACKUP="${BACKUP_DIR}/config_${BACKUP_DATE}.tar.gz"
tar -czf ${CONFIG_BACKUP} \
    ${PROD_DIR}/httpdocs/config/ \
    ${PROD_DIR}/httpdocs/.env* \
    ${PROD_DIR}/httpdocs/manage.py \
    ${PROD_DIR}/httpdocs/requirements*.txt \
    ${PROD_DIR}/httpdocs/package*.json \
    /etc/apache2/sites-available/*martialcomp* \
    2>/dev/null
echo "   ✓ Configuration sauvegardée: $(du -h ${CONFIG_BACKUP} | cut -f1)"

# Sauvegarde des logs importants
echo ""
echo "7. Sauvegarde des logs récents..."
LOGS_BACKUP="${BACKUP_DIR}/logs_${BACKUP_DATE}.tar.gz"
tar -czf ${LOGS_BACKUP} \
    ${PROD_DIR}/httpdocs/logs/*.log \
    ${PROD_DIR}/logs/*.log \
    /var/log/apache2/*martialcomp* \
    --warning=no-file-changed \
    2>/dev/null
echo "   ✓ Logs sauvegardés: $(du -h ${LOGS_BACKUP} | cut -f1)"

# Sauvegarde des certificats SSL
echo ""
echo "8. Sauvegarde des certificats SSL..."
SSL_BACKUP="${BACKUP_DIR}/ssl_certificates_${BACKUP_DATE}.tar.gz"
if [ -d "/etc/letsencrypt/live/martialcomp.com" ]; then
    tar -czf ${SSL_BACKUP} \
        /etc/letsencrypt/live/martialcomp.com/ \
        /etc/letsencrypt/renewal/martialcomp.com.conf \
        2>/dev/null
    echo "   ✓ Certificats SSL sauvegardés"
fi

# Créer l'archive finale
echo ""
echo "9. Création de l'archive finale..."
cd /root/backups
FINAL_BACKUP="${BACKUP_NAME}.tar.gz"
tar -czf ${FINAL_BACKUP} ${BACKUP_NAME}/
if [ $? -eq 0 ]; then
    echo "   ✓ Archive finale créée: $(du -h ${FINAL_BACKUP} | cut -f1)"
    echo "   ✓ Emplacement: /root/backups/${FINAL_BACKUP}"
else
    echo "   ✗ ERREUR lors de la création de l'archive finale"
fi

# Informations de sauvegarde
echo ""
echo "10. Création du fichier d'information..."
INFO_FILE="${BACKUP_DIR}/backup_info.txt"
cat > ${INFO_FILE} << EOF
=== INFORMATIONS DE SAUVEGARDE MARTIALCOMP ===
Date: $(date +"%Y-%m-%d %H:%M:%S")
Serveur: $(hostname)
Version Django: $(cd ${PROD_DIR}/httpdocs && python3 -c "import django; print(django.get_version())" 2>/dev/null || echo "N/A")

Contenu de la sauvegarde:
- Base de données PostgreSQL: ${DB_NAME}
- Code source complet (httpdocs)
- Fichiers media
- Fichiers static
- Configuration (settings, .env, Apache)
- Logs récents
- Certificats SSL

Taille totale: $(du -sh ${BACKUP_DIR} | cut -f1)

Pour restaurer:
1. Extraire l'archive: tar -xzf ${FINAL_BACKUP}
2. Restaurer la base de données: gunzip -c database_*.sql.gz | sudo -u postgres psql ${DB_NAME}
3. Restaurer les fichiers: tar -xzf code_httpdocs_*.tar.gz -C /var/www/vhosts/martialcomp.com/
4. Restaurer les media: tar -xzf media_*.tar.gz -C /var/www/vhosts/martialcomp.com/httpdocs/
5. Redémarrer les services: systemctl restart apache2
EOF

echo "   ✓ Fichier d'information créé"

# Nettoyage des anciennes sauvegardes (garder les 5 dernières)
echo ""
echo "11. Nettoyage des anciennes sauvegardes..."
cd /root/backups
ls -t martialcomp_backup_complete_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f
echo "   ✓ Anciennes sauvegardes nettoyées (5 dernières conservées)"

# Résumé
echo ""
echo "=== SAUVEGARDE TERMINÉE ==="
echo "Fichier de sauvegarde: /root/backups/${FINAL_BACKUP}"
echo "Taille totale: $(du -h /root/backups/${FINAL_BACKUP} | cut -f1)"
echo "Date de fin: $(date +"%Y-%m-%d %H:%M:%S")"
echo ""
echo "IMPORTANT: Transférer cette sauvegarde vers un stockage externe sécurisé !"
echo "Commande suggérée: scp /root/backups/${FINAL_BACKUP} user@backup-server:/path/to/backups/"