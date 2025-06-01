#!/bin/bash
echo "Application des migrations pour les modèles de planification d'événements..."

# Activer l'environnement virtuel
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "env/bin/activate" ]; then
    source env/bin/activate
else
    echo "Environnement virtuel non trouvé. Veuillez activer manuellement l'environnement virtuel."
    exit 1
fi

# Exécuter le script Python
python apply_event_planning_migrations.py

# Désactiver l'environnement virtuel
deactivate

echo "Processus terminé."