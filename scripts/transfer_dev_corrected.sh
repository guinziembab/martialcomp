#!/bin/bash

echo "📡 TRANSFERT CORRIGÉ DÉVELOPPEMENT → PRODUCTION"
echo "==============================================="

DEV_SOURCE="."  # Répertoire actuel (C:\martial_hub_django\martialcomp)
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
        local size=$(du -sh "$DEV_SOURCE/$app_name" 2>/dev/null | cut -f1 || echo "?")

        echo "   📊 Fichiers: $file_count"
        echo "   📊 Dossiers: $dir_count"
        echo "   📊 Taille: $size"

        # Transfert avec détails
        echo "   ⏳ Transfert en cours..."
        scp -r -o StrictHostKeyChecking=no "$DEV_SOURCE/$app_name/" "$PROD_SERVER:$PROD_PATH/" 2>/dev/null

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

# Fonction de transfert de fichier
transfer_file() {
    local file_name="$1"
    local description="$2"

    if [ -f "$DEV_SOURCE/$file_name" ]; then
        echo "   ⏳ Transfert $file_name..."
        scp -o StrictHostKeyChecking=no "$DEV_SOURCE/$file_name" "$PROD_SERVER:$PROD_PATH/"
        if [ $? -eq 0 ]; then
            echo -e "   ${GREEN}✅ $file_name transféré${NC}"
            TOTAL_FILES=$((TOTAL_FILES + 1))
        else
            echo -e "   ❌ Erreur transfert $file_name"
        fi
    else
        echo "   ⚠️  Fichier non trouvé: $file_name"
    fi
}

echo "🚀 DÉBUT DU TRANSFERT CORRIGÉ"
echo "Source: $(pwd)"
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
transfer_app "config" "Configuration système"

# Fichiers système principaux
echo -e "\n${BLUE}📄 FICHIERS SYSTÈME${NC}"
transfer_file "manage.py" "Fichier de gestion Django"
transfer_file "requirements.txt" "Dépendances Python"

# Templates
echo -e "\n${BLUE}🎨 TEMPLATES${NC}"
transfer_app "templates" "Templates HTML"

# Traductions
echo -e "\n${BLUE}🌍 TRADUCTIONS${NC}"
transfer_app "locale" "Fichiers de traduction"

# Fichiers statiques
echo -e "\n${BLUE}🎨 FICHIERS STATIQUES${NC}"
transfer_app "static" "Fichiers CSS, JS, images"

# Résumé final
echo ""
echo "🎉 TRANSFERT TERMINÉ"
echo "==================="
echo -e "${GREEN}📊 STATISTIQUES FINALES:${NC}"
echo "   📁 Total fichiers transférés: $TOTAL_FILES"
echo "   ⏰ Heure de fin: $(date)"
echo ""
echo -e "${YELLOW}🔄 Transfert terminé avec succès${NC}" 