#!/bin/bash

# Script de déploiement production MartialComp
# Serveur: 212.227.78.104
# Domaines: martialcomp.com + *.martialcomp.com
# Configuration multi-tenant avec QR codes

set -e  # Arrêt en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables de configuration
SERVER_IP="212.227.78.104"
DOMAIN="martialcomp.com"
APP_USER="martialcomp"
APP_DIR="/opt/martialcomp"
REPO_URL="https://github.com/VOTRE-USERNAME/martialcomp.git"  # À MODIFIER

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}   DÉPLOIEMENT PRODUCTION MARTIALCOMP    ${NC}"
echo -e "${BLUE}   Sites en Sous-domaine avec QR Codes   ${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Vérification des permissions
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Ce script ne doit pas être exécuté en root${NC}" 
   echo "Utilisez: sudo -u $APP_USER $0"
   exit 1
fi

# Fonction d'affichage des étapes
print_step() {
    echo -e "${GREEN}[ÉTAPE] $1${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[ATTENTION] $1${NC}"
}

print_error() {
    echo -e "${RED}[ERREUR] $1${NC}"
}

# ==========================================
# ÉTAPE 1: PRÉPARATION SYSTÈME
# ==========================================

print_step "1. Préparation du système et vérifications"

# Vérifier PostgreSQL
print_info "Vérification PostgreSQL..."
if ! sudo systemctl is-active --quiet postgresql; then
    print_error "PostgreSQL n'est pas démarré"
    exit 1
fi

# Vérifier Redis
print_info "Vérification Redis..."
if ! sudo systemctl is-active --quiet redis-server; then
    print_warning "Redis n'est pas démarré, tentative de démarrage..."
    sudo systemctl start redis-server
fi

# Vérifier Nginx
print_info "Vérification Nginx..."
if ! sudo systemctl is-active --quiet nginx; then
    print_error "Nginx n'est pas démarré"
    exit 1
fi

print_info "Système vérifié ✓"

# ==========================================
# ÉTAPE 2: CONFIGURATION BASE DE DONNÉES
# ==========================================

print_step "2. Configuration base de données PostgreSQL"

# Vérifier connexion à la base
print_info "Test connexion base de données..."
if ! PGPASSWORD="AQWZSX123ok," psql -h localhost -U martialcomp_user -d martialcomp_db -c "SELECT 1;" > /dev/null 2>&1; then
    print_error "Impossible de se connecter à la base de données"
    print_info "Vérifiez vos identifiants dans le fichier .env"
    exit 1
fi

print_info "Base de données accessible ✓"

# ==========================================
# ÉTAPE 3: DÉPLOIEMENT APPLICATION
# ==========================================

print_step "3. Déploiement de l'application Django"

# Créer les répertoires si nécessaire
print_info "Création des répertoires..."
sudo mkdir -p $APP_DIR/{logs,staticfiles,media/qr_codes,run}
sudo chown -R $APP_USER:www-data $APP_DIR
sudo chmod -R 755 $APP_DIR
sudo chmod -R 775 $APP_DIR/media
sudo chmod -R 775 $APP_DIR/logs

# Backup de l'application existante si elle existe
if [ -d "$APP_DIR/app" ]; then
    print_info "Sauvegarde de l'application existante..."
    sudo mv $APP_DIR/app $APP_DIR/app_backup_$(date +%Y%m%d_%H%M%S)
fi

# Clonage du repository
print_info "Clonage du repository..."
cd $APP_DIR
git clone $REPO_URL app
cd app

# Installation environnement virtuel
print_info "Configuration environnement Python..."
python3 -m venv venv
source venv/bin/activate

# Installation dépendances
print_info "Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary django-redis

# Configuration fichier .env
print_info "Configuration du fichier .env..."
cp env_production_template.txt .env
chmod 600 .env

print_warning "ATTENTION: Vérifiez et modifiez le fichier .env avec vos vraies clés:"
print_info "- Mot de passe email IONOS"
print_info "- Clés Stripe production"
print_info "- Autres configurations sensibles"

# ==========================================
# ÉTAPE 4: MIGRATIONS ET CONFIGURATION DJANGO
# ==========================================

print_step "4. Migrations Django et configuration"

# Charger les variables d'environnement
source .env

# Migrations
print_info "Exécution des migrations..."
python manage.py migrate --settings=config.settings_production_final

# Collecte fichiers statiques
print_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --settings=config.settings_production_final

# Création superutilisateur (si nécessaire)
print_info "Pour créer un superutilisateur, exécutez:"
print_info "python manage.py createsuperuser --settings=config.settings_production_final"

# ==========================================
# ÉTAPE 5: CONFIGURATION NGINX
# ==========================================

print_step "5. Configuration Nginx"

# Copier la configuration Nginx
print_info "Configuration Nginx..."
sudo cp nginx_production_config.conf /etc/nginx/sites-available/martialcomp

# Activer le site
sudo ln -sf /etc/nginx/sites-available/martialcomp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration Nginx
print_info "Test configuration Nginx..."
if ! sudo nginx -t; then
    print_error "Erreur dans la configuration Nginx"
    exit 1
fi

print_info "Configuration Nginx ✓"

# ==========================================
# ÉTAPE 6: CONFIGURATION GUNICORN
# ==========================================

print_step "6. Configuration Gunicorn"

# Copier configuration Gunicorn
print_info "Configuration Gunicorn..."
cp gunicorn_production_config.py $APP_DIR/

# Configuration service systemd
print_info "Configuration service systemd..."
sudo tee /etc/systemd/system/martialcomp.service > /dev/null <<EOF
[Unit]
Description=MartialComp Django Application
After=network.target postgresql.service redis.service
Requires=postgresql.service

[Service]
Type=forking
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR/app
Environment="PATH=$APP_DIR/app/venv/bin"
EnvironmentFile=$APP_DIR/app/.env
ExecStart=$APP_DIR/app/venv/bin/gunicorn \\
    --config $APP_DIR/gunicorn_production_config.py \\
    --daemon \\
    config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ==========================================
# ÉTAPE 7: DÉMARRAGE DES SERVICES
# ==========================================

print_step "7. Démarrage des services"

# Recharger systemd
sudo systemctl daemon-reload

# Arrêter les services existants
print_info "Arrêt des services existants..."
sudo systemctl stop martialcomp 2>/dev/null || true

# Démarrer les services
print_info "Démarrage service MartialComp..."
sudo systemctl start martialcomp
sudo systemctl enable martialcomp

# Redémarrer Nginx
print_info "Redémarrage Nginx..."
sudo systemctl reload nginx

# ==========================================
# ÉTAPE 8: VÉRIFICATIONS FINALES
# ==========================================

print_step "8. Vérifications finales"

# Vérifier statut des services
print_info "Vérification statut services..."

if sudo systemctl is-active --quiet martialcomp; then
    print_info "✓ Service MartialComp actif"
else
    print_error "✗ Service MartialComp inactif"
    sudo systemctl status martialcomp
fi

if sudo systemctl is-active --quiet nginx; then
    print_info "✓ Nginx actif"
else
    print_error "✗ Nginx inactif"
fi

if sudo systemctl is-active --quiet postgresql; then
    print_info "✓ PostgreSQL actif"
else
    print_error "✗ PostgreSQL inactif"
fi

# Test de connectivité
print_info "Test de connectivité..."
if curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN | grep -q "200\|301\|302"; then
    print_info "✓ Site accessible via HTTPS"
else
    print_warning "Site peut ne pas être accessible immédiatement"
fi

# ==========================================
# INFORMATIONS FINALES
# ==========================================

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}   DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !     ${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo -e "${BLUE}URLs d'accès:${NC}"
echo -e "  • Site principal: https://$DOMAIN"
echo -e "  • Administration: https://$DOMAIN/admin/"
echo -e "  • API: https://$DOMAIN/api/"
echo ""
echo -e "${BLUE}Commandes utiles:${NC}"
echo -e "  • Logs application: sudo journalctl -u martialcomp -f"
echo -e "  • Logs Nginx: sudo tail -f /var/log/nginx/martialcomp_*.log"
echo -e "  • Restart app: sudo systemctl restart martialcomp"
echo -e "  • Reload Nginx: sudo systemctl reload nginx"
echo ""
echo -e "${YELLOW}Actions à effectuer:${NC}"
echo -e "  1. Configurer le certificat SSL wildcard avec Let's Encrypt"
echo -e "  2. Modifier le fichier .env avec vos vraies clés"
echo -e "  3. Créer un superutilisateur Django"
echo -e "  4. Tester la création d'organisations et sous-domaines"
echo -e "  5. Vérifier la génération des QR codes"
echo ""
echo -e "${GREEN}Prêt pour la production ! 🚀${NC}"