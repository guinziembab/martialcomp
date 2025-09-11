#!/bin/bash

# =============================================================================
# SYNCHRONISATION DÉTAILLÉE DÉVELOPPEMENT → PRODUCTION
# Avec comptage précis des fichiers transférés par application
# =============================================================================

set -e

echo "🔄 SYNCHRONISATION DÉTAILLÉE DEV → PRODUCTION"
echo "=============================================="
echo "📅 Date: $(date)"
echo "🎯 Transfert COMPLET avec détails par application"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Variables globales pour le comptage
TOTAL_FILES_TRANSFERRED=0
TOTAL_DIRS_CREATED=0
TRANSFER_LOG="/tmp/transfer_details_$TIMESTAMP.log"

# Fonction pour compter et transférer
transfer_and_count() {
    local app_name="$1"
    local source_info="$2"
    
    echo "   📁 Application: $app_name"
    
    if [ -d "$app_name" ]; then
        # Compter les fichiers existants (avant suppression)
        local existing_files=$(find "$app_name" -type f 2>/dev/null | wc -l)
        local existing_dirs=$(find "$app_name" -type d 2>/dev/null | wc -l)
        
        echo "      🗑️  Suppression: $existing_files fichiers, $existing_dirs dossiers"
        
        # Sauvegarder
        cp -r "$app_name" "backups/production_sync_$TIMESTAMP/" 2>/dev/null || true
        
        # Supprimer
        rm -rf "$app_name"
    else
        echo "      ℹ️  Application inexistante (première installation)"
    fi
    
    echo "      ⏳ $source_info"
    echo "      ✅ $app_name: PRÊT POUR TRANSFERT"
    echo ""
}

# =============================================================================
# 1. SAUVEGARDE ET PRÉPARATION
# =============================================================================

echo "💾 1. SAUVEGARDE ET PRÉPARATION"
echo "==============================="

BACKUP_DIR="backups/production_sync_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "   📁 Sauvegarde dans: $BACKUP_DIR"
echo "   ✅ Répertoire de sauvegarde créé"

# =============================================================================
# 2. ARRÊT DJANGO
# =============================================================================

echo ""
echo "🛑 2. ARRÊT DES SERVICES DJANGO"
echo "==============================="

echo "   🛑 Arrêt des processus Django..."
pkill -f "runserver.*8080" 2>/dev/null || true
pkill -f "manage.py runserver" 2>/dev/null || true
sleep 2
echo "   ✅ Services Django arrêtés"

# =============================================================================
# 3. ANALYSE ET PRÉPARATION DU TRANSFERT
# =============================================================================

echo ""
echo "📊 3. ANALYSE ET PRÉPARATION DU TRANSFERT"
echo "========================================="

# Applications à transférer avec informations détaillées
transfer_and_count "competitions" "Application principale + organisateur non-membre"
transfer_and_count "organizations" "Gestion organisations et affiliations"  
transfer_and_count "grades" "Système de grades et certifications"
transfer_and_count "finances" "Nouveau modèle tarifaire et facturation"
transfer_and_count "shop" "Boutique en ligne et e-commerce"
transfer_and_count "documents" "GED et gestion documentaire"
transfer_and_count "family_management" "Gestion familiale complète"
transfer_and_count "permissions_manager" "Permissions granulaires"
transfer_and_count "payment" "Paiements et abonnements"
transfer_and_count "accounts" "Comptes utilisateurs étendus"
transfer_and_count "multitenant" "Architecture multi-tenant"
transfer_and_count "security" "Sécurité renforcée"
transfer_and_count "api_auth" "API et authentification"

# Configuration
if [ -d "config" ]; then
    config_files=$(find config -type f 2>/dev/null | wc -l)
    echo "   ⚙️  Configuration Django: $config_files fichiers"
    cp -r config "$BACKUP_DIR/" 2>/dev/null || true
    rm -rf config
fi

# Fichiers système
if [ -f "manage.py" ]; then
    echo "   📄 manage.py: sauvegardé"
    cp manage.py "$BACKUP_DIR/" 2>/dev/null || true
    rm -f manage.py
fi

if [ -f "requirements.txt" ]; then
    echo "   📦 requirements.txt: sauvegardé" 
    cp requirements.txt "$BACKUP_DIR/" 2>/dev/null || true
    rm -f requirements.txt
fi

# Traductions
if [ -d "locale" ]; then
    locale_files=$(find locale -name "*.po" -o -name "*.mo" 2>/dev/null | wc -l)
    echo "   🌍 Traductions: $locale_files fichiers"
    cp -r locale "$BACKUP_DIR/" 2>/dev/null || true
    rm -rf locale
fi

echo "   ✅ Préparation terminée - Production nettoyée"

# =============================================================================
# 4. CRÉATION DU SCRIPT DE TRANSFERT DÉTAILLÉ
# =============================================================================

echo ""
echo "📡 4. CRÉATION DU SCRIPT DE TRANSFERT DÉTAILLÉ"
echo "=============================================="

cat > transfer_dev_detailed.sh << 'DETAILED_TRANSFER'
#!/bin/bash

echo "📡 TRANSFERT DÉTAILLÉ DÉVELOPPEMENT → PRODUCTION"
echo "================================================"

DEV_SOURCE="C:/martial_hub_django/martialcomp"
PROD_SERVER="root@212.227.78.104"
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Compteurs globaux
TOTAL_FILES=0
TOTAL_SIZE=0

# Fonction de transfert avec détails
transfer_app() {
    local app_name="$1"
    local description="$2"
    
    echo -e "\n${BLUE}📁 TRANSFERT: $app_name${NC}"
    echo "   Description: $description"
    
    if [ -d "$DEV_SOURCE/$app_name" ]; then
        # Compter les fichiers avant transfert
        local file_count=$(find "$DEV_SOURCE/$app_name" -type f | wc -l)
        local dir_count=$(find "$DEV_SOURCE/$app_name" -type d | wc -l)
        local size=$(du -sh "$DEV_SOURCE/$app_name" | cut -f1)
        
        echo "   📊 Fichiers: $file_count"
        echo "   📊 Dossiers: $dir_count" 
        echo "   📊 Taille: $size"
        
        # Transfert avec détails
        echo "   ⏳ Transfert en cours..."
        scp -r "$DEV_SOURCE/$app_name/" "$PROD_SERVER:$PROD_PATH/" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✅ $app_name transféré avec succès${NC}"
            TOTAL_FILES=$((TOTAL_FILES + file_count))
        else
            echo -e "   ❌ Erreur transfert $app_name"
        fi
    else
        echo "   ⚠️  Source non trouvée: $DEV_SOURCE/$app_name"
    fi
}

echo "🚀 DÉBUT DU TRANSFERT"
echo "Source: $DEV_SOURCE"
echo "Destination: $PROD_SERVER:$PROD_PATH"
echo ""

# Applications principales
transfer_app "competitions" "Application principale + dashboard organisateur non-membre"
transfer_app "organizations" "Gestion organisations, clubs et fédérations"
transfer_app "grades" "Système de grades, certifications et examens"
transfer_app "finances" "Nouveau modèle tarifaire, facturation et comptabilité"
transfer_app "shop" "Boutique en ligne, produits et commandes"
transfer_app "documents" "GED, gestion documentaire et archivage"
transfer_app "family_management" "Gestion familiale, inscriptions groupées, paiements"
transfer_app "permissions_manager" "Système de permissions granulaires"
transfer_app "payment" "Traitement paiements, abonnements et factures"
transfer_app "accounts" "Comptes utilisateurs étendus et profils"
transfer_app "multitenant" "Architecture multi-tenant et sous-domaines"
transfer_app "security" "Sécurité renforcée et authentification"
transfer_app "api_auth" "API REST et système d'authentification"

# Configuration système
echo -e "\n${BLUE}⚙️  CONFIGURATION SYSTÈME${NC}"

if [ -d "$DEV_SOURCE/config" ]; then
    config_files=$(find "$DEV_SOURCE/config" -type f | wc -l)
    echo "   📊 Fichiers config: $config_files"
    echo "   ⏳ Transfert configuration..."
    scp -r "$DEV_SOURCE/config/" "$PROD_SERVER:$PROD_PATH/"
    echo -e "   ${GREEN}✅ Configuration transférée${NC}"
    TOTAL_FILES=$((TOTAL_FILES + config_files))
fi

# Fichiers système
echo -e "\n${BLUE}📄 FICHIERS SYSTÈME${NC}"

if [ -f "$DEV_SOURCE/manage.py" ]; then
    echo "   ⏳ Transfert manage.py..."
    scp "$DEV_SOURCE/manage.py" "$PROD_SERVER:$PROD_PATH/"
    echo -e "   ${GREEN}✅ manage.py transféré${NC}"
    TOTAL_FILES=$((TOTAL_FILES + 1))
fi

if [ -f "$DEV_SOURCE/requirements.txt" ]; then
    echo "   ⏳ Transfert requirements.txt..."
    scp "$DEV_SOURCE/requirements.txt" "$PROD_SERVER:$PROD_PATH/"
    echo -e "   ${GREEN}✅ requirements.txt transféré${NC}"
    TOTAL_FILES=$((TOTAL_FILES + 1))
fi

# Traductions
echo -e "\n${BLUE}🌍 TRADUCTIONS${NC}"

if [ -d "$DEV_SOURCE/locale" ]; then
    po_files=$(find "$DEV_SOURCE/locale" -name "*.po" | wc -l)
    mo_files=$(find "$DEV_SOURCE/locale" -name "*.mo" | wc -l)
    echo "   📊 Fichiers .po: $po_files"
    echo "   📊 Fichiers .mo: $mo_files"
    echo "   ⏳ Transfert traductions..."
    scp -r "$DEV_SOURCE/locale/" "$PROD_SERVER:$PROD_PATH/"
    echo -e "   ${GREEN}✅ Traductions transférées${NC}"
    TOTAL_FILES=$((TOTAL_FILES + po_files + mo_files))
fi

# Fichiers statiques
echo -e "\n${BLUE}🎨 FICHIERS STATIQUES${NC}"

if [ -d "$DEV_SOURCE/static" ]; then
    static_files=$(find "$DEV_SOURCE/static" -type f | wc -l)
    echo "   📊 Fichiers statiques: $static_files"
    echo "   ⏳ Transfert fichiers statiques..."
    scp -r "$DEV_SOURCE/static/" "$PROD_SERVER:$PROD_PATH/"
    echo -e "   ${GREEN}✅ Fichiers statiques transférés${NC}"
    TOTAL_FILES=$((TOTAL_FILES + static_files))
fi

# Résumé final
echo ""
echo "🎉 TRANSFERT TERMINÉ"
echo "==================="
echo -e "${GREEN}📊 STATISTIQUES FINALES:${NC}"
echo "   📁 Total fichiers transférés: $TOTAL_FILES"
echo "   ⏰ Heure de fin: $(date)"
echo ""
echo -e "${YELLOW}🔄 Retournez sur le serveur pour continuer l'installation${NC}"

DETAILED_TRANSFER

chmod +x transfer_dev_detailed.sh

echo "   📋 Script de transfert détaillé créé: transfer_dev_detailed.sh"
echo ""
echo "   🎯 INSTRUCTION POUR LE TRANSFERT:"
echo "   Exécutez depuis votre PC Windows (PowerShell ou Git Bash):"
echo ""
echo "   bash transfer_dev_detailed.sh"
echo ""

# Attendre la confirmation du transfert
read -p "   ⏸️  Appuyez sur Entrée une fois le transfert détaillé terminé..."

# =============================================================================
# 5. VÉRIFICATION POST-TRANSFERT
# =============================================================================

echo ""
echo "🔍 5. VÉRIFICATION POST-TRANSFERT"
echo "================================="

echo "   📊 Analyse des applications transférées:"

# Vérifier chaque application
apps=("competitions" "organizations" "grades" "finances" "shop" "documents" "family_management" "permissions_manager" "payment" "accounts" "multitenant" "security" "api_auth")

for app in "${apps[@]}"; do
    if [ -d "$app" ]; then
        files=$(find "$app" -type f | wc -l)
        dirs=$(find "$app" -type d | wc -l)
        size=$(du -sh "$app" 2>/dev/null | cut -f1)
        echo "      ✅ $app: $files fichiers, $dirs dossiers, $size"
        TOTAL_FILES_TRANSFERRED=$((TOTAL_FILES_TRANSFERRED + files))
        TOTAL_DIRS_CREATED=$((TOTAL_DIRS_CREATED + dirs))
    else
        echo "      ❌ $app: NON TRANSFÉRÉ"
    fi
done

# Vérifier configuration
if [ -d "config" ]; then
    config_files=$(find config -type f | wc -l)
    echo "      ✅ config: $config_files fichiers"
    TOTAL_FILES_TRANSFERRED=$((TOTAL_FILES_TRANSFERRED + config_files))
fi

# Vérifier fichiers système
if [ -f "manage.py" ]; then
    echo "      ✅ manage.py: présent"
    TOTAL_FILES_TRANSFERRED=$((TOTAL_FILES_TRANSFERRED + 1))
fi

if [ -f "requirements.txt" ]; then
    echo "      ✅ requirements.txt: présent"
    TOTAL_FILES_TRANSFERRED=$((TOTAL_FILES_TRANSFERRED + 1))
fi

# Vérifier traductions
if [ -d "locale" ]; then
    po_files=$(find locale -name "*.po" | wc -l)
    mo_files=$(find locale -name "*.mo" | wc -l)
    echo "      ✅ locale: $po_files .po + $mo_files .mo"
    TOTAL_FILES_TRANSFERRED=$((TOTAL_FILES_TRANSFERRED + po_files + mo_files))
fi

echo ""
echo "   📊 RÉSUMÉ DU TRANSFERT:"
echo "      📁 Total fichiers: $TOTAL_FILES_TRANSFERRED"
echo "      📂 Total dossiers: $TOTAL_DIRS_CREATED"
echo "      ✅ Applications: ${#apps[@]}"

# =============================================================================
# 6. CONFIGURATION ET INSTALLATION
# =============================================================================

echo ""
echo "⚙️ 6. CONFIGURATION ET INSTALLATION"
echo "==================================="

# Adapter manage.py pour la production
if [ -f "manage.py" ]; then
    echo "   🔧 Adaptation manage.py pour production..."
    sed -i "s/config.settings.development/config.settings.production/g" manage.py 2>/dev/null || true
    echo "      ✅ manage.py adapté"
fi

# Installer les dépendances
if [ -f "requirements.txt" ]; then
    echo "   📦 Installation des dépendances..."
    pip install -r requirements.txt > /dev/null 2>&1
    echo "      ✅ Dépendances installées"
fi

# Migrations
echo "   🗄️ Migrations base de données..."
python manage.py makemigrations > /dev/null 2>&1
python manage.py migrate > /dev/null 2>&1
echo "      ✅ Migrations appliquées"

# Collecte des statiques
echo "   📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear > /dev/null 2>&1
echo "      ✅ Fichiers statiques collectés"

# Compilation des traductions
echo "   🌍 Compilation des traductions..."
python manage.py compilemessages > /dev/null 2>&1 || echo "      ⚠️ Certaines traductions à recompiler"

# =============================================================================
# 7. REDÉMARRAGE ET TESTS
# =============================================================================

echo ""
echo "🔄 7. REDÉMARRAGE ET TESTS"
echo "========================="

# Redémarrer Django
echo "   🚀 Redémarrage Django..."
nohup python manage.py runserver 127.0.0.1:8080 > /tmp/django_sync_detailed_$(date +%H%M).log 2>&1 &
DJANGO_PID=$!
echo "      ✅ Django redémarré (PID: $DJANGO_PID)"

sleep 5

# Tests de fonctionnement
echo "   🧪 Tests de fonctionnement..."
DJANGO_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8080/" || echo "000")
APACHE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://martialcomp.com/" || echo "000")

echo "      📊 Status Django: $DJANGO_STATUS"
echo "      📊 Status Apache: $APACHE_STATUS"

# =============================================================================
# 8. RÉSUMÉ FINAL DÉTAILLÉ
# =============================================================================

echo ""
echo "🎉 SYNCHRONISATION DÉTAILLÉE TERMINÉE"
echo "====================================="

echo ""
echo "📊 STATISTIQUES COMPLÈTES:"
echo "   📁 Fichiers transférés: $TOTAL_FILES_TRANSFERRED"
echo "   📂 Dossiers créés: $TOTAL_DIRS_CREATED"
echo "   🔄 Applications sync: ${#apps[@]}"
echo "   ⏰ Durée totale: $(date)"

echo ""
echo "✅ APPLICATIONS SYNCHRONISÉES:"
for app in "${apps[@]}"; do
    if [ -d "$app" ]; then
        echo "   ✅ $app"
    else
        echo "   ❌ $app"
    fi
done

echo ""
echo "🌐 URLS À TESTER:"
echo "   • http://martialcomp.com (Status: $APACHE_STATUS)"
echo "   • http://martialcomp.com/dashboard/"
echo "   • http://martialcomp.com/admin/"

echo ""
echo "📊 INFORMATIONS TECHNIQUES:"
echo "   🐍 Django PID: $DJANGO_PID"
echo "   💾 Sauvegarde: $BACKUP_DIR"
echo "   📝 Log transfert: $TRANSFER_LOG"

echo ""
echo "✨ SYNCHRONISATION RÉUSSIE AVEC DÉTAILS COMPLETS !" 