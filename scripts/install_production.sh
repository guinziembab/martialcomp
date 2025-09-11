#!/bin/bash

# Script d'installation complète pour la production MartialComp
# Automatise tout le processus d'installation

echo "=== INSTALLATION COMPLÈTE DE LA PRODUCTION MARTIALCOMP ==="
echo "Date: $(date)"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="$PROJECT_DIR/.venv"
PYTHON_VERSION="3.9"

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

# 1. Nettoyage des fichiers inutiles
step "1" "Nettoyage des fichiers inutiles..."
if [ -f "cleanup_production_files.sh" ]; then
    chmod +x cleanup_production_files.sh
    ./cleanup_production_files.sh
    check_error "Nettoyage terminé"
else
    echo -e "${YELLOW}⚠ Script de nettoyage non trouvé, continuation...${NC}"
fi

# 2. Vérification de la structure Django
step "2" "Vérification de la structure Django..."
if [ -f "verify_django_structure.sh" ]; then
    chmod +x verify_django_structure.sh
    ./verify_django_structure.sh
    check_error "Vérification de la structure"
else
    echo -e "${YELLOW}⚠ Script de vérification non trouvé, continuation...${NC}"
fi

# 3. Installation de Python et pip si nécessaire
step "3" "Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "Installation de Python 3..."
    apt update
    apt install -y python3 python3-pip python3-venv
    check_error "Installation de Python"
else
    echo -e "${GREEN}✓ Python 3 déjà installé${NC}"
fi

# 4. Création de l'environnement virtuel
step "4" "Création de l'environnement virtuel..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    check_error "Création de l'environnement virtuel"
else
    echo -e "${GREEN}✓ Environnement virtuel déjà existant${NC}"
fi

# 5. Activation de l'environnement virtuel
step "5" "Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"
check_error "Activation de l'environnement virtuel"

# 6. Mise à jour de pip
step "6" "Mise à jour de pip..."
pip install --upgrade pip
check_error "Mise à jour de pip"

# 7. Installation des dépendances
step "7" "Installation des dépendances Python..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    check_error "Installation des dépendances"
else
    echo -e "${RED}✗ Fichier requirements.txt manquant${NC}"
    exit 1
fi

# 8. Configuration de l'environnement de production
step "8" "Configuration de l'environnement de production..."
if [ -f "production.env" ]; then
    echo "Fichier production.env trouvé"
else
    echo -e "${YELLOW}⚠ Création d'un fichier production.env basique...${NC}"
    cat > production.env << EOF
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com
DATABASE_URL=sqlite:///db.sqlite3
STATIC_URL=/static/
MEDIA_URL=/media/
EOF
fi

# 9. Vérification de la configuration Django
step "9" "Vérification de la configuration Django..."
python manage.py check --deploy
check_error "Vérification de la configuration Django"

# 10. Création des migrations si nécessaire
step "10" "Création des migrations..."
python manage.py makemigrations --dry-run
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Aucune nouvelle migration nécessaire${NC}"
else
    echo "Création des nouvelles migrations..."
    python manage.py makemigrations
    check_error "Création des migrations"
fi

# 11. Application des migrations
step "11" "Application des migrations..."
python manage.py migrate
check_error "Application des migrations"

# 12. Collecte des fichiers statiques
step "12" "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
check_error "Collecte des fichiers statiques"

# 13. Création d'un superutilisateur si nécessaire
step "13" "Vérification du superutilisateur..."
echo "Vérification de l'existence d'un superutilisateur..."
if python manage.py shell -c "from django.contrib.auth.models import User; print('Superutilisateur existe' if User.objects.filter(is_superuser=True).exists() else 'Aucun superutilisateur')" 2>/dev/null | grep -q "Aucun superutilisateur"; then
    echo -e "${YELLOW}⚠ Aucun superutilisateur trouvé${NC}"
    echo "Pour créer un superutilisateur, exécutez:"
    echo "python manage.py createsuperuser"
else
    echo -e "${GREEN}✓ Superutilisateur existant${NC}"
fi

# 14. Test du serveur de développement
step "14" "Test du serveur de développement..."
echo "Test de démarrage du serveur (5 secondes)..."
timeout 5 python manage.py runserver 0.0.0.0:8000 &
SERVER_PID=$!
sleep 6
if kill -0 $SERVER_PID 2>/dev/null; then
    echo -e "${GREEN}✓ Serveur démarré avec succès${NC}"
    kill $SERVER_PID
else
    echo -e "${RED}✗ Problème de démarrage du serveur${NC}"
fi

# 15. Configuration des permissions
step "15" "Configuration des permissions..."
chmod -R 755 "$PROJECT_DIR"
chmod -R 777 "$PROJECT_DIR/media"
chmod -R 777 "$PROJECT_DIR/logs"
chmod 644 "$PROJECT_DIR/db.sqlite3"
check_error "Configuration des permissions"

# 16. Vérification finale
step "16" "Vérification finale..."
echo "=== RÉSUMÉ DE L'INSTALLATION ==="
echo "📁 Répertoire du projet: $PROJECT_DIR"
echo "🐍 Environnement virtuel: $VENV_DIR"
echo "📦 Dépendances installées: $(pip list | wc -l) packages"
echo "🗄️ Base de données: $(ls -lh db.sqlite3 2>/dev/null | awk '{print $5}' || echo 'Non trouvée')"
echo "📄 Fichiers statiques: $(find staticfiles -type f 2>/dev/null | wc -l) fichiers"

echo ""
echo "=== COMMANDES UTILES ==="
echo "🔧 Activer l'environnement: source $VENV_DIR/bin/activate"
echo "🚀 Démarrer le serveur: python manage.py runserver 0.0.0.0:8000"
echo "👤 Créer un superutilisateur: python manage.py createsuperuser"
echo "📊 Vérifier la configuration: python manage.py check --deploy"
echo "🔄 Appliquer les migrations: python manage.py migrate"
echo "📦 Collecter les statiques: python manage.py collectstatic"

echo ""
echo "=== CONFIGURATION APACHE/NGINX ==="
echo "Pour configurer Apache/Nginx, assurez-vous que:"
echo "1. Le DocumentRoot pointe vers: $PROJECT_DIR"
echo "2. Les fichiers statiques sont servis depuis: $PROJECT_DIR/staticfiles"
echo "3. Les fichiers média sont servis depuis: $PROJECT_DIR/media"
echo "4. Le WSGI pointe vers: $PROJECT_DIR/martialcomp/wsgi.py"

echo ""
echo -e "${GREEN}=== INSTALLATION TERMINÉE AVEC SUCCÈS ===${NC}"
echo "Date: $(date)" 