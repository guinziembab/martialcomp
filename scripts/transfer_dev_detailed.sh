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

