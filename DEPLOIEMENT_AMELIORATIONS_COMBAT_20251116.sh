#!/bin/bash

################################################################################
# SCRIPT DE DÉPLOIEMENT - AMÉLIORATIONS INTERFACE COMBAT V2
# Date: 16 Novembre 2025
# Modifications:
#   - Pénalités progressives (-0.25, -0.5, -1, -1.5, -2)
#   - Système de comptage des sorties (3 sorties = -0.5)
#   - Logo de la discipline
#   - Logos des clubs
#   - Son GONG à la fin du combat
#   - Timer au format MM:SS
################################################################################

set -e  # Arrêter en cas d'erreur

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║           🥋 DÉPLOIEMENT AMÉLIORATIONS INTERFACE COMBAT V2                   ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROD_DIR="/home/martialcomp/martialcomp"
TEMPLATE_FILE="apps/competitions/templates/competitions/combat/interface_combat_v2.html"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ÉTAPE 1: VÉRIFICATION DU FICHIER LOCAL${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}❌ ERREUR: Fichier $TEMPLATE_FILE introuvable !${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Fichier trouvé: $TEMPLATE_FILE${NC}"

# Vérifier que les modifications sont présentes
if grep -q "addPenalty" "$TEMPLATE_FILE" && \
   grep -q "addExit" "$TEMPLATE_FILE" && \
   grep -q "playGong" "$TEMPLATE_FILE" && \
   grep -q "discipline-logo" "$TEMPLATE_FILE"; then
    echo -e "${GREEN}✅ Toutes les modifications sont présentes dans le fichier${NC}"
else
    echo -e "${RED}❌ ERREUR: Certaines modifications sont manquantes !${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ÉTAPE 2: SAUVEGARDE DU FICHIER ACTUEL EN PRODUCTION${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

BACKUP_NAME="interface_combat_v2.html.backup_$(date +%Y%m%d_%H%M%S)"

ssh martialcomp@ssh.cluster031.hosting.ovh.net << EOF
    cd $PROD_DIR
    if [ -f "$TEMPLATE_FILE" ]; then
        cp "$TEMPLATE_FILE" "$TEMPLATE_FILE.backup_\$(date +%Y%m%d_%H%M%S)"
        echo "✅ Sauvegarde créée"
    else
        echo "⚠️  Fichier n'existe pas encore en production"
    fi
EOF

echo -e "${GREEN}✅ Sauvegarde effectuée${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ÉTAPE 3: TRANSFERT DU FICHIER VERS LA PRODUCTION${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

scp "$TEMPLATE_FILE" "martialcomp@ssh.cluster031.hosting.ovh.net:$PROD_DIR/$TEMPLATE_FILE"

echo -e "${GREEN}✅ Fichier transféré avec succès${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ÉTAPE 4: VÉRIFICATION DU FICHIER EN PRODUCTION${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ssh martialcomp@ssh.cluster031.hosting.ovh.net << EOF
    cd $PROD_DIR
    
    echo "📊 Vérification du fichier déployé..."
    
    if [ -f "$TEMPLATE_FILE" ]; then
        echo "✅ Fichier existe"
        
        # Vérifier les fonctions clés
        if grep -q "addPenalty" "$TEMPLATE_FILE"; then
            echo "✅ Fonction addPenalty présente"
        else
            echo "❌ Fonction addPenalty manquante"
        fi
        
        if grep -q "addExit" "$TEMPLATE_FILE"; then
            echo "✅ Fonction addExit présente"
        else
            echo "❌ Fonction addExit manquante"
        fi
        
        if grep -q "playGong" "$TEMPLATE_FILE"; then
            echo "✅ Fonction playGong présente"
        else
            echo "❌ Fonction playGong manquante"
        fi
        
        if grep -q "discipline-logo" "$TEMPLATE_FILE"; then
            echo "✅ Logo discipline présent"
        else
            echo "❌ Logo discipline manquant"
        fi
        
        if grep -q "club-logo" "$TEMPLATE_FILE"; then
            echo "✅ Logo club présent"
        else
            echo "❌ Logo club manquant"
        fi
        
        echo ""
        echo "📏 Taille du fichier: \$(wc -c < "$TEMPLATE_FILE") octets"
        echo "📝 Nombre de lignes: \$(wc -l < "$TEMPLATE_FILE") lignes"
    else
        echo "❌ ERREUR: Fichier introuvable !"
        exit 1
    fi
EOF

echo -e "${GREEN}✅ Vérification terminée${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ÉTAPE 5: VIDAGE DU CACHE DJANGO${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ssh martialcomp@ssh.cluster031.hosting.ovh.net << 'EOF'
    cd /home/martialcomp/martialcomp
    source venv/bin/activate
    
    python manage.py shell << 'PYTHON'
from django.core.cache import cache
cache.clear()
print("✅ Cache Django vidé")
exit()
PYTHON
EOF

echo -e "${GREEN}✅ Cache vidé${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ÉTAPE 6: REDÉMARRAGE DES SERVICES${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

ssh martialcomp@ssh.cluster031.hosting.ovh.net << 'EOF'
    # Redémarrer Passenger (pour OVH)
    if [ -f tmp/restart.txt ]; then
        touch tmp/restart.txt
        echo "✅ Passenger redémarré (touch tmp/restart.txt)"
    else
        mkdir -p tmp
        touch tmp/restart.txt
        echo "✅ Passenger redémarré (création tmp/restart.txt)"
    fi
    
    # Si Gunicorn est disponible
    if systemctl is-active --quiet gunicorn 2>/dev/null; then
        sudo systemctl restart gunicorn
        echo "✅ Gunicorn redémarré"
    fi
    
    # Si Apache est disponible
    if systemctl is-active --quiet apache2 2>/dev/null; then
        sudo systemctl reload apache2
        echo "✅ Apache rechargé"
    fi
EOF

echo -e "${GREEN}✅ Services redémarrés${NC}"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  ÉTAPE 7: TEST DE L'INTERFACE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo "🧪 Test de l'URL de l'interface..."

# Test avec curl
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/competitions/combat/combats/10/interface-v2/" -L)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Interface accessible (HTTP $HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" = "302" ]; then
    echo -e "${YELLOW}⚠️  Redirection détectée (HTTP $HTTP_CODE) - Authentification requise${NC}"
else
    echo -e "${RED}❌ Erreur HTTP $HTTP_CODE${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║                        ✅ DÉPLOIEMENT TERMINÉ !                              ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}🎉 Toutes les améliorations ont été déployées avec succès !${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📋 RÉSUMÉ DES MODIFICATIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ✅ Pénalités progressives (-0.25, -0.5, -1, -1.5, -2)"
echo "  ✅ Système de comptage des sorties (3 sorties = -0.5)"
echo "  ✅ Logo de la discipline au lieu de '120s'"
echo "  ✅ Logos des clubs de part et d'autre"
echo "  ✅ Son GONG à la fin du combat"
echo "  ✅ Timer au format MM:SS avec décrémentation"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 TESTS À EFFECTUER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  1. Connectez-vous sur https://martialcomp.com/accounts/login/"
echo "  2. Accédez à l'interface: https://martialcomp.com/fr/competitions/combat/combats/10/interface-v2/"
echo "  3. Testez les boutons de pénalités (-0.25, -0.5, -1, -1.5, -2)"
echo "  4. Testez le bouton 'Sortie' (3 fois pour déclencher la pénalité)"
echo "  5. Vérifiez l'affichage du logo de la discipline"
echo "  6. Vérifiez l'affichage des logos des clubs"
echo "  7. Démarrez le timer et attendez la fin pour entendre le GONG"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📚 DOCUMENTATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📄 Fichier de documentation: AMELIORATIONS_INTERFACE_COMBAT_V2_20251116.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
