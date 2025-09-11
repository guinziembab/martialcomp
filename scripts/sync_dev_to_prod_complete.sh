#!/bin/bash

# Script de synchronisation complète : Développement → Production
# Suit le schéma visuel étape par étape

echo "=== SYNCHRONISATION COMPLÈTE DEV → PROD ==="
echo "Date: $(date)"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuration
DEV_HOST="localhost"  # À adapter selon votre environnement de dev
DEV_USER="martialcomp_user"
DEV_DB="martialcomp_db"
DEV_PORT="5432"

PROD_HOST="localhost"
PROD_USER="martialcomp_user"
PROD_DB="martialcomp_db"
PROD_PASSWORD="MartialComp2025Production!"
PROD_PORT="5432"

SERVER_HOST="martialcomp.com"
SERVER_USER="root"
SERVER_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

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

# A. Export de la base de développement
step "A" "Export de la base de développement..."
echo "Export de la base $DEV_DB depuis $DEV_HOST..."

# Vérifier si pg_dump est disponible
if ! command -v pg_dump &> /dev/null; then
    echo -e "${YELLOW}⚠ pg_dump non trouvé, tentative avec chemin complet...${NC}"
    # Essayer les chemins courants pour PostgreSQL
    PG_PATHS=(
        "/usr/bin/pg_dump"
        "/usr/local/bin/pg_dump"
        "/opt/homebrew/bin/pg_dump"
        "C:/Program Files/PostgreSQL/*/bin/pg_dump.exe"
    )
    
    PG_DUMP_CMD=""
    for path in "${PG_PATHS[@]}"; do
        if [ -f "$path" ] || ls $path 2>/dev/null; then
            PG_DUMP_CMD="$path"
            break
        fi
    done
    
    if [ -z "$PG_DUMP_CMD" ]; then
        echo -e "${RED}✗ pg_dump non trouvé. Installez PostgreSQL ou spécifiez le chemin manuellement.${NC}"
        exit 1
    fi
else
    PG_DUMP_CMD="pg_dump"
fi

# Export avec gestion d'erreur
$PG_DUMP_CMD -U "$DEV_USER" -h "$DEV_HOST" -p "$DEV_PORT" "$DEV_DB" > dev_dump.sql 2>/tmp/pg_dump_error.log

if [ $? -eq 0 ]; then
    DUMP_SIZE=$(du -h dev_dump.sql | cut -f1)
    echo -e "${GREEN}✓ Export réussi: dev_dump.sql ($DUMP_SIZE)${NC}"
else
    echo -e "${RED}✗ Erreur lors de l'export:${NC}"
    cat /tmp/pg_dump_error.log
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

# Créer un script de transfert des configs
cat > transfer_configs.sh << 'EOF'
#!/bin/bash
# Script pour transférer les configurations système

BACKUP_LOCAL="C:/martial_hub_django/martialcomp_backup_local"
SERVER_HOST="martialcomp.com"
SERVER_USER="root"

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
EOF

chmod +x transfer_configs.sh
./transfer_configs.sh
check_error "Transfert des configurations système"

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