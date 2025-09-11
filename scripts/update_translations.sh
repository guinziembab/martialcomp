#!/bin/bash
# Script pour mettre à jour les traductions
# Exécutez ce script depuis le répertoire racine du projet

# Activer l'environnement virtuel si nécessaire
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "env" ]; then
    source env/bin/activate
fi

# Exécuter le script Python
python update_translations.py

# Désactiver l'environnement virtuel
deactivate 2>/dev/null || true