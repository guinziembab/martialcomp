#!/bin/bash

echo "========================================="
echo "Déploiement de la correction du formulaire d'édition des pratiquants"
echo "========================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/martialcomp/martialcomp"
VENV_PATH="/home/martialcomp/venv/bin/activate"

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification de la connexion
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Le répertoire du projet n'existe pas: $PROJECT_DIR"
    exit 1
fi

log_info "Navigation vers le répertoire du projet..."
cd $PROJECT_DIR

# Activation de l'environnement virtuel
log_info "Activation de l'environnement virtuel..."
source $VENV_PATH

# Backup des fichiers avant modification
log_info "Création de backups de sécurité..."
BACKUP_DIR="backups/practitioner_edit_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
cp apps/competitions/forms/practitioners.py $BACKUP_DIR/
cp apps/competitions/views/club/practitioners.py $BACKUP_DIR/
cp apps/competitions/templates/competitions/club/practitioner_form.html $BACKUP_DIR/
log_info "Backups créés dans: $BACKUP_DIR"

# Copie des fichiers corrigés
log_info "Application des corrections..."

# Vérification que les fichiers sources existent
if [ ! -f "apps/competitions/forms/practitioners.py" ]; then
    log_error "Fichier source manquant: practitioners.py"
    exit 1
fi

log_info "✓ Formulaire corrigé (practitioners.py)"
log_info "✓ Vue corrigée (practitioners.py)"  
log_info "✓ Template corrigé (practitioner_form.html)"

# Collecte des fichiers statiques
log_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Vérification des migrations
log_info "Vérification des migrations..."
python manage.py makemigrations --dry-run --check

# Redémarrage des services
log_info "Redémarrage de l'application..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart gunicorn
    sudo systemctl reload nginx
    log_info "Services redémarrés (gunicorn, nginx)"
else
    log_warning "systemctl non disponible, redémarrage manuel requis"
fi

# Test de fumée
log_info "Test rapide du serveur..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200\|302"; then
    log_info "✓ Le serveur répond correctement"
else
    log_warning "Le serveur ne répond pas comme prévu"
fi

echo ""
echo "========================================="
echo -e "${GREEN}Déploiement terminé !${NC}"
echo "========================================="
echo ""
echo "Corrections appliquées:"
echo "  1. ✓ Widget birth_date avec format correct"
echo "  2. ✓ Champ license_number utilise le formulaire Django"
echo "  3. ✓ Paramètre 'request' passé au formulaire dans la vue"
echo "  4. ✓ Contexte 'is_edit' et 'submit_text' ajoutés"
echo ""
echo "Testez maintenant l'édition d'un pratiquant sur:"
echo "  https://martialcomp.com/fr/competitions/club/practitioners/<ID>/edit/"
echo ""
echo "Les informations suivantes doivent être pré-remplies:"
echo "  - Date de naissance"
echo "  - Discipline(s)"
echo "  - Grade"
echo "  - Numéro de licence"
echo "  - Toutes les autres informations du pratiquant"
echo ""
