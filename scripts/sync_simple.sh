#!/bin/bash

# Script de synchronisation simplifié
# Utilise le dump déjà généré

echo "=== SYNCHRONISATION SIMPLIFIÉE DEV → PROD ==="
echo "Date: $(date)"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_HOST="martialcomp.com"
SERVER_USER="root"
SERVER_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
DUMP_FILE="C:/martial_hub_django/martialcomp/backups/dev_dump.sql"

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

# Vérification du dump
step "1" "Vérification du dump de développement..."
if [ -f "$DUMP_FILE" ]; then
    DUMP_SIZE=$(Get-Item "$DUMP_FILE" | Select-Object -ExpandProperty Length)
    echo -e "${GREEN}✓ Dump trouvé: $DUMP_FILE ($DUMP_SIZE octets)${NC}"
else
    echo -e "${RED}✗ Dump non trouvé: $DUMP_FILE${NC}"
    exit 1
fi

# Transfert du dump vers la production
step "2" "Transfert du dump vers la production..."
echo "Transfert de dev_dump.sql vers $SERVER_HOST..."

scp "$DUMP_FILE" "$SERVER_USER@$SERVER_HOST:/root/dev_dump.sql"
check_error "Transfert du dump vers la production"

# Sauvegarde de la base de production
step "3" "Sauvegarde de la base de production..."
echo "Création d'une sauvegarde de sécurité..."

BACKUP_FILE="prod_backup_$(date +%Y%m%d_%H%M%S).sql"
ssh "$SERVER_USER@$SERVER_HOST" "PGPASSWORD='$PROD_PASSWORD' pg_dump -U $PROD_USER -h $PROD_HOST -p $PROD_PORT $PROD_DB > /root/$BACKUP_FILE"
check_error "Sauvegarde de la base de production"

# Import du dump de développement sur la production
step "4" "Import du dump de développement sur la production..."
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

# Redémarrage des services
step "5" "Redémarrage des services..."
echo "Redémarrage des services web..."

ssh "$SERVER_USER@$SERVER_HOST" << 'EOF'
systemctl restart apache2
systemctl restart nginx
systemctl daemon-reload
systemctl restart gunicorn
systemctl status apache2 nginx gunicorn --no-pager
EOF
check_error "Redémarrage des services"

# Installation Django finale
step "6" "Installation Django finale..."
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
echo "- Dump vérifié: ✓"
echo "- Transfert dump: ✓"
echo "- Sauvegarde prod: $BACKUP_FILE"
echo "- Import base dev: ✓"
echo "- Services redémarrés: ✓"
echo "- Django installé: ✓"
echo ""
echo "🔗 URL: http://$SERVER_HOST"
echo "📁 Dossier: $SERVER_PATH"
echo "🗄️ Base: $PROD_DB"
echo ""
echo "Pour vérifier les logs:"
echo "ssh $SERVER_USER@$SERVER_HOST 'tail -f $SERVER_PATH/logs/*.log'" 