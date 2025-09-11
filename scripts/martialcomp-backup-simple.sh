#!/bin/bash
# Script de sauvegarde simple MartialComp - IONOS Production

set -e

# Configuration
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/martialcomp_backup_$BACKUP_DATE"
DOMAIN="martialcomp.com"
HTTPDOCS="/var/www/vhosts/$DOMAIN/httpdocs"
VHOST_CONF="/var/www/vhosts/system/$DOMAIN/conf"

# Affichage
echo "=============================================="
echo "   SAUVEGARDE MARTIALCOMP PRODUCTION"
echo "=============================================="
echo "Date: $(date)"
echo "Serveur: $(hostname)"
echo ""

# Vérifier les permissions root
if [ "$EUID" -ne 0 ]; then
    echo "ERREUR: Ce script doit être exécuté en tant que root"
    exit 1
fi

# Vérifier l'espace disque
echo "[INFO] Vérification de l'espace disque..."
df -h /

# Créer les répertoires de sauvegarde
echo "[INFO] Création des répertoires de sauvegarde..."
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/logs"
mkdir -p "$BACKUP_DIR/configs"
mkdir -p "$BACKUP_DIR/database"
mkdir -p "$BACKUP_DIR/files"
echo "[SUCCESS] Répertoires créés: $BACKUP_DIR"

# Sauvegarde de la configuration Plesk
echo "[INFO] Sauvegarde de la configuration Plesk..."
if command -v plesk >/dev/null 2>&1; then
    plesk bin server_pref --export -file "$BACKUP_DIR/configs/plesk_server_config.xml" 2>/dev/null || echo "[WARNING] Impossible d'exporter la config serveur Plesk"
    plesk bin site --export "$DOMAIN" -file "$BACKUP_DIR/configs/plesk_${DOMAIN}_config.xml" 2>/dev/null || echo "[WARNING] Impossible d'exporter la config domaine"
    echo "[SUCCESS] Configuration Plesk sauvegardée"
else
    echo "[WARNING] Plesk CLI non trouvé"
fi

# Sauvegarde des configurations web
echo "[INFO] Sauvegarde des configurations web..."
if [ -d "$VHOST_CONF" ]; then
    cp -r "$VHOST_CONF" "$BACKUP_DIR/configs/vhost_conf/"
    echo "[SUCCESS] Configuration vhost sauvegardée"
else
    echo "[WARNING] Répertoire vhost non trouvé"
fi
if [ -d "/etc/nginx" ]; then
    cp -r "/etc/nginx" "$BACKUP_DIR/configs/nginx/"
    echo "[SUCCESS] Configuration Nginx sauvegardée"
fi

# Sauvegarde de la configuration Gunicorn
echo "[INFO] Sauvegarde de la configuration Gunicorn..."
if [ -f "/etc/systemd/system/gunicorn.service" ]; then
    cp "/etc/systemd/system/gunicorn.service" "$BACKUP_DIR/configs/"
    echo "[SUCCESS] Service gunicorn.service sauvegardé"
fi
if [ -f "/etc/systemd/system/martialcomp.service" ]; then
    cp "/etc/systemd/system/martialcomp.service" "$BACKUP_DIR/configs/"
    echo "[SUCCESS] Service martialcomp.service sauvegardé"
fi
if [ -f "$HTTPDOCS/gunicorn.conf.py" ]; then
    cp "$HTTPDOCS/gunicorn.conf.py" "$BACKUP_DIR/configs/"
    echo "[SUCCESS] Configuration Gunicorn du projet sauvegardée"
fi
ps aux | grep gunicorn > "$BACKUP_DIR/configs/gunicorn_processes.txt"
if [ -d "/var/log/gunicorn" ]; then
    cp -r "/var/log/gunicorn" "$BACKUP_DIR/logs/"
    echo "[SUCCESS] Logs Gunicorn sauvegardés"
fi

# Sauvegarde de la configuration Django
echo "[INFO] Sauvegarde de la configuration Django..."
if [ -d "$HTTPDOCS/config/settings" ]; then
    cp -r "$HTTPDOCS/config/settings" "$BACKUP_DIR/configs/django_settings/"
    echo "[SUCCESS] Settings Django sauvegardés"
fi
for config_file in "$HTTPDOCS/config/wsgi.py" "$HTTPDOCS/config/asgi.py" "$HTTPDOCS/config/urls.py" "$HTTPDOCS/config/celery.py" "$HTTPDOCS/manage.py"; do
    if [ -f "$config_file" ]; then
        cp "$config_file" "$BACKUP_DIR/configs/"
        echo "[SUCCESS] $(basename $config_file) sauvegardé"
    fi
done
if [ -f "$HTTPDOCS/.env" ]; then
    cp "$HTTPDOCS/.env" "$BACKUP_DIR/configs/"
    echo "[SUCCESS] Fichier .env sauvegardé"
fi
if [ -f "$HTTPDOCS/requirements.txt" ]; then
    cp "$HTTPDOCS/requirements.txt" "$BACKUP_DIR/configs/"
    echo "[SUCCESS] Requirements sauvegardés"
fi

# Sauvegarde de la base de données
echo "[INFO] Sauvegarde de la base de données..."
db_backup_file="$BACKUP_DIR/database/martialcomp_db_$BACKUP_DATE.sql"
if command -v psql >/dev/null 2>&1 && systemctl is-active --quiet postgresql; then
    echo "[INFO] Sauvegarde PostgreSQL..."
    if sudo -u postgres pg_dump martialcomp > "$db_backup_file" 2>/dev/null; then
        echo "[SUCCESS] Base de données PostgreSQL sauvegardée"
    elif pg_dump -U postgres martialcomp > "$db_backup_file" 2>/dev/null; then
        echo "[SUCCESS] Base de données PostgreSQL sauvegardée"
    else
        echo "[ERROR] Échec de la sauvegarde PostgreSQL"
        sudo -u postgres psql -l > "$BACKUP_DIR/database/postgres_databases.txt" 2>/dev/null
    fi
elif command -v mysql >/dev/null 2>&1 && systemctl is-active --quiet mysql; then
    echo "[INFO] Sauvegarde MySQL..."
    if mysqldump -u root martialcomp > "$db_backup_file" 2>/dev/null; then
        echo "[SUCCESS] Base de données MySQL sauvegardée"
    else
        echo "[ERROR] Échec de la sauvegarde MySQL"
        mysql -u root -e "SHOW DATABASES;" > "$BACKUP_DIR/database/mysql_databases.txt" 2>/dev/null
    fi
else
    echo "[WARNING] Aucune base de données PostgreSQL ou MySQL active trouvée"
fi

# Sauvegarde des fichiers média
echo "[INFO] Sauvegarde des fichiers média..."
if [ -d "$HTTPDOCS/media" ]; then
    cp -r "$HTTPDOCS/media" "$BACKUP_DIR/files/"
    echo "[SUCCESS] Fichiers média sauvegardés"
else
    echo "[WARNING] Répertoire média non trouvé"
fi

# Sauvegarde des fichiers statiques
echo "[INFO] Sauvegarde des fichiers statiques..."
if [ -d "$HTTPDOCS/staticfiles" ]; then
    cp -r "$HTTPDOCS/staticfiles" "$BACKUP_DIR/files/"
    echo "[SUCCESS] Fichiers statiques sauvegardés"
else
    echo "[WARNING] Répertoire staticfiles non trouvé"
fi
if [ -d "$HTTPDOCS/static" ]; then
    cp -r "$HTTPDOCS/static" "$BACKUP_DIR/files/"
    echo "[SUCCESS] Répertoire static sauvegardé"
fi

# Sauvegarde des logs
echo "[INFO] Sauvegarde des logs..."
if [ -d "$HTTPDOCS/logs" ]; then
    cp -r "$HTTPDOCS/logs" "$BACKUP_DIR/logs/project_logs/"
    echo "[SUCCESS] Logs du projet sauvegardés"
fi
for log_file in "/var/log/nginx/access.log" "/var/log/nginx/error.log" "/var/www/vhosts/system/$DOMAIN/logs/access_log" "/var/www/vhosts/system/$DOMAIN/logs/error_log" "/var/www/vhosts/system/$DOMAIN/logs/access_ssl_log"; do
    if [ -f "$log_file" ]; then
        cp "$log_file" "$BACKUP_DIR/logs/"
        echo "[SUCCESS] $(basename $log_file) sauvegardé"
    fi
done

# Sauvegarde des informations système
echo "[INFO] Sauvegarde des informations système..."
{
    echo "=== INFORMATIONS SYSTÈME ==="
    echo "Date de sauvegarde: $(date)"
    echo "Serveur: $(hostname)"
    echo "OS: $(cat /etc/os-release | head -1)"
    echo "Noyau: $(uname -r)"
    echo "Uptime: $(uptime)"
    echo ""
    echo "=== SERVICES ACTIFS ==="
    systemctl list-units --type=service --state=active | grep -E "(nginx|apache|gunicorn|martialcomp|postgresql|mysql)"
    echo ""
    echo "=== PROCESSUS GUNICORN ==="
    ps aux | grep gunicorn | grep -v grep
    echo ""
    echo "=== PORTS ÉCOUTÉS ==="
    netstat -tlpn | grep -E ":(80|443|8001|5432|3306)"
    echo ""
    echo "=== ESPACE DISQUE ==="
    df -h
    echo ""
    echo "=== MÉMOIRE ==="
    free -h
} > "$BACKUP_DIR/system_info.txt"

crontab -l > "$BACKUP_DIR/current_crontab.txt" 2>/dev/null || echo "Aucun crontab configuré" > "$BACKUP_DIR/current_crontab.txt"
echo "[SUCCESS] Informations système sauvegardées"

# Sauvegarde du code source
echo "[INFO] Sauvegarde du code source..."
cd "$HTTPDOCS"
tar -czf "$BACKUP_DIR/source_code.tar.gz" \
    --exclude="venv" \
    --exclude="node_modules" \
    --exclude="*.pyc" \
    --exclude="__pycache__" \
    --exclude="media" \
    --exclude="staticfiles" \
    --exclude="logs" \
    --exclude=".git" \
    . 2>/dev/null
echo "[SUCCESS] Code source sauvegardé"

# Compression finale
echo "[INFO] Compression de la sauvegarde..."
cd "$(dirname "$BACKUP_DIR")"
compressed_file="martialcomp_backup_$BACKUP_DATE.tar.gz"
tar -czf "$compressed_file" "$(basename "$BACKUP_DIR")"
size=$(du -h "$compressed_file" | cut -f1)
echo "[SUCCESS] Sauvegarde compressée: $compressed_file ($size)"
rm -rf "$BACKUP_DIR"
echo ""
echo "=============================================="
echo "   SAUVEGARDE TERMINÉE"
echo "=============================================="
echo "Fichier: $(pwd)/$compressed_file"
echo "Taille: $size"
echo "Date: $(date)"
echo ""
echo "Pour restaurer:"
echo "  tar -xzf $compressed_file"
echo "  cd $(basename \"$BACKUP_DIR\")"
echo ""
echo "Pour récupérer depuis Windows:"
echo "  scp root@martialcomp.com:$(pwd)/$compressed_file ."
echo ""
echo "🎉 Sauvegarde complète terminée!"