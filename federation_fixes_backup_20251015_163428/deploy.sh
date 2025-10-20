#!/bin/bash
# Script de déploiement automatique

echo "🚀 Déploiement des corrections Federation..."

# Sauvegarder les fichiers actuels
for file in apps/competitions/views/onboarding/federations.py apps/competitions/views/onboarding/__init__.py apps/competitions/views/dashboard/federations.py; do
    if [ -f "$file" ]; then
        cp "$file" "${file}.backup_$(date +%Y%m%d_%H%M%S)"
        echo "Sauvegarde: $file"
    fi
done

# Copier les nouveaux fichiers
cp federations.py apps/competitions/views/onboarding/federations.py
cp __init__.py apps/competitions/views/onboarding/__init__.py
cp federations.py apps/competitions/views/dashboard/federations.py

echo "✅ Fichiers déployés"
echo "⚠️  N'oubliez pas de redémarrer le serveur!"
