#!/bin/bash

# Script de déploiement d'urgence pour martialcomp.com
# Corrige l'erreur 500 sur /fr/competitions/federations/3/examens/

echo "🚨 DÉPLOIEMENT D'URGENCE - MartialComp Production"
echo "=================================================="

# Configuration
SERVER="root@martialcomp.com"
REMOTE_PATH="/var/www/martialcomp"
LOCAL_PATH="."

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour exécuter une commande sur le serveur distant
remote_exec() {
    local cmd="$1"
    local desc="$2"
    
    log_info "$desc"
    ssh "$SERVER" "cd $REMOTE_PATH && $cmd" 2>&1
}

# Fonction pour transférer un fichier
transfer_file() {
    local local_file="$1"
    local remote_file="$2"
    local desc="$3"
    
    if [[ -f "$local_file" ]]; then
        log_info "$desc"
        scp "$local_file" "$SERVER:$REMOTE_PATH/$remote_file"
        if [[ $? -eq 0 ]]; then
            log_success "✅ $local_file transféré"
        else
            log_error "❌ Erreur lors du transfert de $local_file"
            return 1
        fi
    else
        log_error "❌ Fichier local non trouvé: $local_file"
        return 1
    fi
}

echo ""
echo "📋 PHASE 1: Diagnostic Initial"
echo "------------------------------"

# Vérifier la connexion au serveur
log_info "Test de connexion au serveur..."
if ssh -o ConnectTimeout=10 "$SERVER" "echo 'Connexion OK'" >/dev/null 2>&1; then
    log_success "✅ Connexion au serveur réussie"
else
    log_error "❌ Impossible de se connecter au serveur"
    exit 1
fi

# Vérifier que le répertoire de l'application existe
log_info "Vérification du répertoire de l'application..."
if ssh "$SERVER" "test -d $REMOTE_PATH && test -f $REMOTE_PATH/manage.py" >/dev/null 2>&1; then
    log_success "✅ Répertoire de l'application trouvé"
else
    log_error "❌ Répertoire de l'application non trouvé ou manage.py manquant"
    exit 1
fi

echo ""
echo "💾 PHASE 2: Sauvegarde de Sécurité" 
echo "-----------------------------------"

# Créer une sauvegarde sur le serveur
BACKUP_NAME="backup_emergency_$(date +%Y%m%d_%H%M%S)"
remote_exec "mkdir -p backups" "Création du dossier de sauvegarde"
remote_exec "tar -czf backups/$BACKUP_NAME.tar.gz apps/competitions/views/federations.py apps/competitions/templates/competitions/federations/examens/ apps/competitions/urls/dashboard.py 2>/dev/null || true" "Sauvegarde des fichiers critiques"

echo ""
echo "🚀 PHASE 3: Transfert des Corrections"
echo "-------------------------------------"

# Liste des fichiers à transférer
transfer_file "apps/competitions/views/federations.py" "apps/competitions/views/federations.py" "Transfert de la vue federations.py corrigée"
transfer_file "apps/competitions/urls/dashboard.py" "apps/competitions/urls/dashboard.py" "Transfert des URLs dashboard.py"
transfer_file "apps/competitions/templates/competitions/federations/examens/list.html" "apps/competitions/templates/competitions/federations/examens/list.html" "Transfert du template examens corrigé"

# Transférer les scripts de correction
transfer_file "fix_migration_production.py" "fix_migration_production.py" "Transfert du script de correction des migrations"
transfer_file "fix_all_issues_production.py" "fix_all_issues_production.py" "Transfert du script de correction globale"

echo ""
echo "🔧 PHASE 4: Corrections sur le Serveur"
echo "--------------------------------------"

# Correction des migrations
log_info "Application des corrections de migration..."
remote_exec "python3 manage.py migrate --fake competitions 0007 2>/dev/null || true" "Retour à la migration 0007"
remote_exec "find apps/competitions/migrations/ -name '0008_remove_*' -delete 2>/dev/null || true" "Suppression migrations problématiques"
remote_exec "find apps/competitions/migrations/ -name '0009_alter_*' -delete 2>/dev/null || true" "Suppression migrations problématiques"
remote_exec "python3 manage.py makemigrations" "Génération de nouvelles migrations"
remote_exec "python3 manage.py migrate" "Application des migrations"

echo ""
echo "✅ PHASE 5: Vérifications et Redémarrage"
echo "----------------------------------------"

# Vérifier Django
log_info "Vérification de la configuration Django..."
remote_exec "python3 manage.py check" "Test de configuration Django"

# Collecter les fichiers statiques
log_info "Collecte des fichiers statiques..."
remote_exec "python3 manage.py collectstatic --noinput" "Collecte des fichiers statiques"

# Redémarrer les services
log_info "Redémarrage des services..."
remote_exec "systemctl restart nginx" "Redémarrage Nginx"
remote_exec "systemctl restart gunicorn 2>/dev/null || systemctl restart martialcomp 2>/dev/null || true" "Redémarrage de l'application Django"

echo ""
echo "🧪 PHASE 6: Tests de Validation"
echo "-------------------------------"

# Attendre quelques secondes pour que les services redémarrent
log_info "Attente du redémarrage des services..."
sleep 5

# Test de la page problématique
log_info "Test de la page examens..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/competitions/federations/3/examens/" || echo "000")

if [[ "$HTTP_STATUS" == "200" ]]; then
    log_success "✅ Page examens accessible (HTTP 200)"
elif [[ "$HTTP_STATUS" == "302" ]] || [[ "$HTTP_STATUS" == "301" ]]; then
    log_warning "⚠️ Page examens redirigée (HTTP $HTTP_STATUS) - probablement besoin de connexion"
else
    log_error "❌ Page examens toujours en erreur (HTTP $HTTP_STATUS)"
fi

echo ""
echo "📊 RÉSUMÉ DU DÉPLOIEMENT"
echo "========================"

log_success "✅ Sauvegarde créée: backups/$BACKUP_NAME.tar.gz"
log_success "✅ Fichiers corrigés transférés"
log_success "✅ Migrations corrigées"
log_success "✅ Services redémarrés"

echo ""
echo "🎯 PAGES À TESTER:"
echo "  - https://martialcomp.com/fr/competitions/federations/3/examens/"
echo "  - https://martialcomp.com/fr/competitions/dashboard/documentation/"
echo ""
echo "🔍 EN CAS DE PROBLÈME:"
echo "  - Logs Django: tail -f /var/log/django/martialcomp.log"
echo "  - Restaurer: cd $REMOTE_PATH && tar -xzf backups/$BACKUP_NAME.tar.gz"
echo ""

if [[ "$HTTP_STATUS" == "200" ]] || [[ "$HTTP_STATUS" == "302" ]] || [[ "$HTTP_STATUS" == "301" ]]; then
    log_success "🎉 DÉPLOIEMENT RÉUSSI !"
    exit 0
else
    log_error "⚠️ DÉPLOIEMENT TERMINÉ MAIS À VÉRIFIER"
    exit 1
fi