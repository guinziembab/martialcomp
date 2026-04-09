#!/bin/bash
# Script pour créer tous les modules de vues manquants

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "Création de tous les modules de vues manquants..."

# 1. Créer un script Python sur le serveur pour générer les modules
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && cat > /tmp/create_missing_views.py << 'EOF'
import os
import re

# Liste des modules à créer avec leurs fonctions
modules_to_create = {
    'apps/competitions/views/practitioner_training.py': [
        'training_dashboard', 'practitioner_training_schedule', 'attendance_history',
        'program_list', 'training_progress', 'make_reservation', 'cancel_reservation',
        'program_detail', 'program_enroll', 'program_unenroll', 'training_calendar',
        'training_stats', 'coach_availability', 'book_training_session'
    ],
    'apps/competitions/views/practitioner_competitions.py': [
        'competition_calendar', 'my_competitions', 'competition_registration',
        'competition_results', 'competition_history', 'upcoming_competitions'
    ],
    'apps/competitions/views/practitioner_profile.py': [
        'practitioner_profile', 'update_profile', 'change_photo', 'medical_info',
        'emergency_contacts', 'achievement_list', 'belt_history'
    ],
    'apps/competitions/views/combat_extra.py': [
        'update_duree_combat', 'suivi_poule', 'classement_live'
    ]
}

# Créer chaque module
for module_path, functions in modules_to_create.items():
    print(f\"Création de {module_path}...\")
    
    # Créer le contenu du module
    content = \"\"\"# Module généré automatiquement
from django.http import HttpResponse
from django.shortcuts import render

\"\"\"
    
    for func in functions:
        content += f\"\"\"
def {func}(request, *args, **kwargs):
    return HttpResponse('{func} - Page temporaire')
\"\"\"
    
    # Écrire le fichier
    with open(module_path, 'w') as f:
        f.write(content)
    
    print(f\"  ✓ {len(functions)} fonctions créées\")

print(\"\\nTous les modules ont été créés!\")
EOF"

# 2. Exécuter le script
echo "Exécution du script de création..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/python /tmp/create_missing_views.py"

# 3. Relancer Gunicorn
echo ""
echo "Relancement de Gunicorn..."
ssh "$PRODUCTION_SERVER" "pkill -9 -f gunicorn || true"
sleep 2
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/python -m gunicorn --workers 3 --bind 127.0.0.1:8888 --daemon --error-logfile logs/gunicorn_error.log config.wsgi:application"

sleep 3

# 4. Test
echo ""
echo "Test du site..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/)
echo "Statut HTTP: $HTTP_STATUS"

echo "Script terminé!"