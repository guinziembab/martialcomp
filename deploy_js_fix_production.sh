#!/bin/bash
# Script de déploiement pour la correction JavaScript sur la production
# À exécuter sur le serveur de production

echo "🚀 Déploiement de la correction JavaScript sur la production..."

# Variables de configuration (à adapter selon votre environnement de production)
PROD_TEMPLATE_PATH="/path/to/production/apps/competitions/templates/competitions/dashboard/club.html"
BACKUP_DIR="/path/to/backups"
CORRECTED_TEMPLATE="/path/to/corrected/club.html"

# Créer le répertoire de sauvegarde
mkdir -p "$BACKUP_DIR"

# Sauvegarder le template actuel
if [ -f "$PROD_TEMPLATE_PATH" ]; then
    cp "$PROD_TEMPLATE_PATH" "$BACKUP_DIR/club_template_backup_$(date +%Y%m%d_%H%M%S).html"
    echo "✅ Sauvegarde créée"
else
    echo "⚠️  Template de production non trouvé: $PROD_TEMPLATE_PATH"
fi

# Copier le template corrigé
if [ -f "$CORRECTED_TEMPLATE" ]; then
    cp "$CORRECTED_TEMPLATE" "$PROD_TEMPLATE_PATH"
    echo "✅ Template corrigé déployé"
else
    echo "❌ Template corrigé non trouvé: $CORRECTED_TEMPLATE"
    exit 1
fi

# Vérifier la correction
if grep -q "function calculateAges()" "$PROD_TEMPLATE_PATH"; then
    echo "✅ Correction JavaScript vérifiée"
else
    echo "❌ Correction JavaScript non trouvée"
    exit 1
fi

# Vérifier que le JavaScript n'est pas échappé
if grep -q "&lt;script&gt;" "$PROD_TEMPLATE_PATH"; then
    echo "❌ JavaScript échappé détecté - correction nécessaire"
    exit 1
else
    echo "✅ Aucun JavaScript échappé détecté"
fi

# Redémarrer le serveur web si nécessaire
# systemctl restart nginx
# systemctl restart gunicorn

echo "✅ Déploiement terminé"
echo "🌐 Vérifiez le site sur https://martialcomp.com/fr/competitions/dashboard/club/"