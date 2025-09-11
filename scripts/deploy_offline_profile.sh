#!/bin/bash
# Script de déploiement pour la fonctionnalité de profil hors-ligne
# À exécuter dans l'environnement de production

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages d'étape
function step() {
    echo -e "\n${YELLOW}==== $1 ====${NC}\n"
}

# Fonction pour afficher les messages de succès
function success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Fonction pour afficher les messages d'erreur
function error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    error "Ce script doit être exécuté depuis le répertoire racine du projet Django"
fi

# Étape 1: Sauvegarde de la base de données
step "1. Sauvegarde de la base de données"
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    success "Répertoire de sauvegarde créé"
fi

# Détecter le type de base de données
if [ -f "db.sqlite3" ]; then
    # SQLite
    cp db.sqlite3 "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
    success "Base de données SQLite sauvegardée dans $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
else
    # PostgreSQL ou autre - utiliser la commande Django dumpdata
    python manage.py dumpdata > "$BACKUP_DIR/data_backup_$TIMESTAMP.json"
    if [ $? -eq 0 ]; then
        success "Base de données sauvegardée dans $BACKUP_DIR/data_backup_$TIMESTAMP.json"
    else
        error "Échec de la sauvegarde de la base de données"
    fi
fi

# Étape 2: Exécuter la migration
step "2. Exécution de la migration pour le profil hors-ligne"
python manage.py migrate competitions 0023_add_offline_profile_support
if [ $? -eq 0 ]; then
    success "Migration appliquée avec succès"
else
    error "Échec de la migration"
fi

# Étape 3: Compiler les traductions
step "3. Compilation des fichiers de traduction"
python manage.py compilemessages
if [ $? -eq 0 ]; then
    success "Traductions compilées avec succès"
else
    echo -e "${YELLOW}⚠️  Avertissement : Impossible de compiler les traductions. Vérifiez que gettext est installé.${NC}"
    echo "  Vous devrez peut-être d'abord extraire les messages avec : python manage.py makemessages -a"
fi

# Étape 4: Collecter les fichiers statiques
step "4. Déploiement des fichiers statiques"
python manage.py collectstatic --noinput
if [ $? -eq 0 ]; then
    success "Fichiers statiques collectés avec succès"
else
    error "Échec de la collecte des fichiers statiques"
fi

# Étape 5: Redémarrer le serveur si nécessaire
step "5. Redémarrage des services"
echo "Selon votre configuration, vous devrez peut-être redémarrer le serveur WSGI."
echo "Commandes typiques :"
echo "  - Gunicorn : sudo systemctl restart gunicorn"
echo "  - uWSGI : sudo systemctl restart uwsgi"
echo "  - Apache : sudo systemctl restart apache2"
echo "  - Nginx (frontend uniquement) : sudo systemctl restart nginx"

# Étape 6: Vérification finale
step "6. Vérification du déploiement"
echo "Vérifiez que le serveur a bien redémarré et que la fonctionnalité est disponible."
echo "URLs à tester :"
echo "  - /scan/practitioners/ID/offline-profile/ (génération du profil hors-ligne)"
echo "  - /scan/profile/offline/ (consultation d'un profil hors-ligne)"

success "Déploiement terminé !"