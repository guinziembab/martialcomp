#!/bin/bash

echo "🚀 Application du patch onboarding Federation"
echo "==========================================="

# Vérifier qu'on est dans le bon dossier
if [ ! -d "apps/competitions/templates" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Sauvegarder l'ancien fichier
BACKUP_FILE="apps/competitions/templates/competitions/onboarding/final_setup.html.backup_$(date +%Y%m%d_%H%M%S)"
cp apps/competitions/templates/competitions/onboarding/final_setup.html "$BACKUP_FILE"
echo "✅ Sauvegarde créée: $BACKUP_FILE"

# Copier le nouveau fichier
cp final_setup.html apps/competitions/templates/competitions/onboarding/final_setup.html
echo "✅ Template corrigé déployé"

echo ""
echo "✅ Patch appliqué avec succès!"
echo ""
echo "Le problème suivant a été corrigé:"
echo "- URLs 'competitions:federations:' remplacées par 'competitions:dashboard:'"
echo ""
echo "↩️  Pour restaurer:"
echo "   cp $BACKUP_FILE apps/competitions/templates/competitions/onboarding/final_setup.html"
