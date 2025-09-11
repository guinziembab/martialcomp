#!/bin/bash

# Script de synchronisation pré-configuré pour Windows
# Chemins et paramètres adaptés à l'environnement MartialComp

echo "=== SYNCHRONISATION COMPLÈTE DEV → PROD (Windows) ==="
echo "Date: $(date)"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration pré-définie pour Windows
BACKUP_LOCAL="/c/martial_hub_django/martialcomp/backups"
SERVER_HOST="martialcomp.com"
SERVER_USER="root"
SERVER_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Configuration des bases de données
DEV_HOST="localhost"
DEV_USER="martialcomp_user"
DEV_DB="martialcomp_db"
DEV_PORT="5432"

PROD_HOST="localhost"
PROD_USER="martialcomp_user"
PROD_DB="martialcomp_db"
PROD_PASSWORD="MartialComp2025Production!"
PROD_PORT="5432"

# Fonction pour afficher les étapes
step() {
    echo -e "${BLUE}[ÉTAPE $1]${NC} $2"
}

# Fonction pour vérifier les erreurs
check_error() {
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ ERREUR: $1${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ $1${NC}"
    fi
}

# Vérification de l'environnement
echo "🔍 Vérification de l'environnement..."
echo "OS: Windows (PowerShell/Git Bash)"
echo "Backup local: $BACKUP_LOCAL"
echo "Serveur: $SERVER_HOST"

# Vérifier l'existence du dossier backup
if [ ! -d "$BACKUP_LOCAL" ]; then
    echo -e "${RED}✗ Dossier backup non trouvé: $BACKUP_LOCAL${NC}"
    echo "Veuillez vérifier que le dossier existe ou spécifier le bon chemin."
    exit 1
fi

echo -e "${GREEN}✓ Dossier backup trouvé${NC}"

# A. Export de la base de développement
step "A" "Export de la base de développement..."
echo "Export de la base $DEV_DB depuis $DEV_HOST..."

# Détecter pg_dump sur Windows
PG_DUMP_CMD=""
PG_PATHS=(
    "/c/Program Files/PostgreSQL/*/bin/pg_dump.exe"
    "C:/Program Files/PostgreSQL/*/bin/pg_dump.exe"
    "/usr/bin/pg_dump"
    "pg_dump"
)

for path in "${PG_PATHS[@]}"; do
    if ls $path 2>/dev/null | head -1 > /dev/null; then
        PG_DUMP_CMD=$(ls $path 2>/dev/null | head -1)
        break
    fi
done

if [ -z "$PG_DUMP_CMD" ]; then
    echo -e "${RED}✗ pg_dump non trouvé${NC}"
    echo "Veuillez installer PostgreSQL ou spécifier le chemin manuellement."
    exit 1
fi

echo "Utilisation de: $PG_DUMP_CMD"

# Export avec gestion d'erreur
$PG_DUMP_CMD -U "$DEV_USER" -h "$DEV_HOST" -p "$DEV_PORT" "$DEV_DB" > dev_dump.sql 2>/tmp/pg_dump_error.log

if [ $? -eq 0 ]; then
    DUMP_SIZE=$(du -h dev_dump.sql 2>/dev/null | cut -f1 || echo "N/A")
    echo -e "${GREEN}✓ Export réussi: dev_dump.sql ($DUMP_SIZE)${NC}"
else
    echo -e "${RED}✗ Erreur lors de l'export:${NC}"
    cat /tmp/pg_dump_error.log 2>/dev/null || echo "Erreur inconnue"
    rm -f /tmp/pg_dump_error.log
    exit 1
fi

rm -f /tmp/pg_dump_error.log

# B. Transfert du dump vers la production
step "B" "Transfert du dump vers la production..."
echo "Transfert de dev_dump.sql vers $SERVER_HOST..."

scp dev_dump.sql "$SERVER_USER@$SERVER_HOST:/root/"
check_error "Transfert du dump vers la production"

# C. Sauvegarde de la base de production
step "C" "Sauvegarde de la base de production..."
echo "Création d'une sauvegarde de sécurité..."

BACKUP_FILE="prod_backup_$(date +%Y%m%d_%H%M%S).sql"
ssh "$SERVER_USER@$SERVER_HOST" "PGPASSWORD='$PROD_PASSWORD' pg_dump -U $PROD_USER -h $PROD_HOST -p $PROD_PORT $PROD_DB > /root/$BACKUP_FILE"
check_error "Sauvegarde de la base de production"

# D. Import du dump de développement sur la production
step "D" "Import du dump de développement sur la production..."
echo "⚠ ATTENTION: Cette opération va écraser les données de production !"
echo "Sauvegarde créée: $BACKUP_FILE"
echo ""

# Demander confirmation
read -p "Continuer avec l'import ? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠ Import annulé par l'utilisateur${NC}"
    exit 0
fi

echo "Import en cours..."
ssh "$SERVER_USER@$SERVER_HOST" "PGPASSWORD='$PROD_PASSWORD' psql -U $PROD_USER -h $PROD_HOST -p $PROD_PORT -d $PROD_DB < /root/dev_dump.sql"
check_error "Import du dump de développement"

# E. Transfert des configurations système
step "E" "Transfert des configurations système..."
echo "Transfert des fichiers de configuration depuis le backup local..."

# Fonction pour transférer un fichier
transfer_file() {
    local source="$1"
    local dest="$2"
    local description="$3"
    
    if [ -f "$source" ]; then
        scp "$source" "$SERVER_USER@$SERVER_HOST:$dest"
        echo "✓ $description transféré"
    else
        echo "⚠ $description non trouvé: $source"
    fi
}

echo "Transfert des configurations système..."

# Apache
transfer_file "$BACKUP_LOCAL/vhost.conf" "/etc/apache2/sites-available/" "Configuration Apache vhost"
transfer_file "$BACKUP_LOCAL/martialcomp.conf" "/etc/apache2/sites-available/" "Configuration Apache martialcomp"

# Nginx
transfer_file "$BACKUP_LOCAL/nginx_martialcomp.conf" "/etc/nginx/sites-available/" "Configuration Nginx"
transfer_file "$BACKUP_LOCAL/nginx.conf" "/etc/nginx/" "Configuration Nginx principale"

# Gunicorn
transfer_file "$BACKUP_LOCAL/gunicorn.service" "/etc/systemd/system/" "Service Gunicorn"
transfer_file "$BACKUP_LOCAL/gunicorn.conf.py" "/etc/gunicorn/" "Configuration Gunicorn"

# Plesk (si applicable)
transfer_file "$BACKUP_LOCAL/plesk_config.conf" "/etc/psa/" "Configuration Plesk"

# Fichiers d'environnement
transfer_file "$BACKUP_LOCAL/production.env" "/var/www/vhosts/martialcomp.com/httpdocs/" "Fichier d'environnement production"

echo "Transfert des configurations terminé"

# F. Redémarrage des services
step "F" "Redémarrage des services..."
echo "Redémarrage des services web..."

ssh "$SERVER_USER@$SERVER_HOST" << 'EOF'
systemctl restart apache2
systemctl restart nginx
systemctl daemon-reload
systemctl restart gunicorn
systemctl status apache2 nginx gunicorn --no-pager
EOF
check_error "Redémarrage des services"

# G. Script d'installation Django
step "G" "Installation Django finale..."
echo "Lancement du script d'installation Django..."

ssh "$SERVER_USER@$SERVER_HOST" "cd $SERVER_PATH && ./install_production.sh"
check_error "Installation Django"

# Vérification finale
step "VÉRIFICATION" "Vérification finale..."
echo "Test de la connexion à l'application..."

# Test de connectivité
if curl -s -o /dev/null -w "%{http_code}" "http://$SERVER_HOST" | grep -q "200\|302"; then
    echo -e "${GREEN}✓ Application accessible${NC}"
else
    echo -e "${YELLOW}⚠ Application non accessible (vérifiez les logs)${NC}"
fi

echo ""
echo "=== SYNCHRONISATION TERMINÉE ==="
echo "Date: $(date)"
echo ""
echo "📊 Résumé:"
echo "- Export base dev: ✓"
echo "- Transfert dump: ✓"
echo "- Sauvegarde prod: $BACKUP_FILE"
echo "- Import base dev: ✓"
echo "- Config système: ✓"
echo "- Services redémarrés: ✓"
echo "- Django installé: ✓"
echo ""
echo "🔗 URL: http://$SERVER_HOST"
echo "📁 Dossier: $SERVER_PATH"
echo "🗄️ Base: $PROD_DB"
echo ""
echo "Pour vérifier les logs:"
echo "ssh $SERVER_USER@$SERVER_HOST 'tail -f $SERVER_PATH/logs/*.log'" 