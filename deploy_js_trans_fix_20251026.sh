#!/bin/bash
# Script de déploiement - Correction des {% trans %} dans JavaScript
# Date: 26 Octobre 2025 - 21h15
# Correction: Remplacement de tous les {% trans %} problématiques dans club.html

set -e

echo "🚀 Déploiement de la correction JavaScript {% trans %}"
echo "=================================================="

# Configuration - À ADAPTER selon votre serveur
PROD_USER="root"  # ou votre utilisateur SSH
PROD_HOST="martialcomp.com"  # ou l'IP du serveur
PROD_PATH="/var/www/martialcomp"  # Chemin de l'application sur le serveur
TEMPLATE_FILE="apps/competitions/templates/competitions/dashboard/club.html"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${YELLOW}📋 Vérification du fichier local...${NC}"

# Vérifier que le fichier existe localement
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo -e "${RED}❌ Fichier non trouvé: $TEMPLATE_FILE${NC}"
    exit 1
fi

# Vérifier qu'il n'y a plus de {% trans %} avec guillemets simples
TRANS_COUNT=$(grep -c "'{% trans" "$TEMPLATE_FILE" || echo "0")
if [ "$TRANS_COUNT" -gt 0 ]; then
    echo -e "${RED}❌ ATTENTION: $TRANS_COUNT {% trans %} avec guillemets simples trouvés!${NC}"
    echo "Lignes concernées:"
    grep -n "'{% trans" "$TEMPLATE_FILE"
    exit 1
fi

echo -e "${GREEN}✅ Fichier local validé (0 {% trans %} problématique)${NC}"

echo ""
echo -e "${YELLOW}📤 Copie du fichier vers le serveur...${NC}"

# Créer une sauvegarde sur le serveur
BACKUP_NAME="club_html_backup_$(date +%Y%m%d_%H%M%S).html"
ssh "$PROD_USER@$PROD_HOST" "mkdir -p $PROD_PATH/backups && cp $PROD_PATH/$TEMPLATE_FILE $PROD_PATH/backups/$BACKUP_NAME" || {
    echo -e "${RED}❌ Échec de la sauvegarde${NC}"
    exit 1
}

echo -e "${GREEN}✅ Sauvegarde créée: $BACKUP_NAME${NC}"

# Copier le fichier corrigé
scp "$TEMPLATE_FILE" "$PROD_USER@$PROD_HOST:$PROD_PATH/$TEMPLATE_FILE" || {
    echo -e "${RED}❌ Échec de la copie${NC}"
    exit 1
}

echo -e "${GREEN}✅ Fichier copié sur le serveur${NC}"

echo ""
echo -e "${YELLOW}🔄 Redémarrage des services...${NC}"

# Collecter les fichiers statiques et redémarrer
ssh "$PROD_USER@$PROD_HOST" << 'ENDSSH'
cd /var/www/martialcomp

# Activer l'environnement virtuel
source venv/bin/activate

# Collecter les fichiers statiques
python3 manage.py collectstatic --noinput

# Redémarrer le service (adapter selon votre configuration)
if systemctl is-active --quiet gunicorn; then
    sudo systemctl restart gunicorn
    echo "✅ Gunicorn redémarré"
elif systemctl is-active --quiet uwsgi; then
    sudo systemctl restart uwsgi
    echo "✅ uWSGI redémarré"
else
    echo "⚠️  Service non détecté, redémarrage manuel nécessaire"
fi

# Redémarrer Nginx
sudo systemctl reload nginx
echo "✅ Nginx rechargé"

ENDSSH

echo ""
echo -e "${GREEN}=================================================="
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo "==================================================${NC}"
echo ""
echo "🧪 TESTS À EFFECTUER:"
echo "1. Ouvrez: https://martialcomp.com/fr/competitions/dashboard/club/"
echo "2. Appuyez sur Ctrl+Shift+F5 pour vider le cache"
echo "3. Ouvrez la console (F12)"
echo "4. Cliquez sur 'Pratiquants'"
echo "5. Vérifiez qu'il n'y a plus d'erreur JavaScript"
echo "6. Vérifiez que l'âge s'affiche correctement"
echo ""
echo -e "${YELLOW}📝 En cas de problème:${NC}"
echo "Restaurer la sauvegarde avec:"
echo "ssh $PROD_USER@$PROD_HOST 'cp $PROD_PATH/backups/$BACKUP_NAME $PROD_PATH/$TEMPLATE_FILE'"
echo ""
