#!/bin/bash
# =============================================================================
# DEPLOIEMENT API MOBILE PRACTITIONER - MartialComp
# =============================================================================
# Date: 2026-01-18
# Description: Deploy role-specific mobile API endpoints for practitioners
# =============================================================================

set -e

echo "=============================================="
echo "DEPLOIEMENT API MOBILE PRACTITIONER"
echo "=============================================="

# Configuration
REMOTE_HOST="vps.martialcomp.net"
REMOTE_USER="martialcomp"
REMOTE_PATH="/var/www/martialcomp"
SSH_KEY="~/.ssh/id_rsa"

# Files to deploy
FILES_TO_DEPLOY=(
    "api/views.py"
    "api/urls.py"
)

echo ""
echo "1. Verification des fichiers locaux..."
for file in "${FILES_TO_DEPLOY[@]}"; do
    if [ -f "$file" ]; then
        echo "   [OK] $file"
    else
        echo "   [ERREUR] $file manquant!"
        exit 1
    fi
done

echo ""
echo "2. Transfert des fichiers vers le serveur..."
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "   Transfert: $file"
    scp -i $SSH_KEY "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$file"
done

echo ""
echo "3. Execution des commandes sur le serveur..."
ssh -i $SSH_KEY "$REMOTE_USER@$REMOTE_HOST" << 'ENDSSH'
cd /var/www/martialcomp

# Activer l'environnement virtuel
source venv/bin/activate

# Verifier la syntaxe Python
echo "   Checking Python syntax..."
python -m py_compile api/views.py
python -m py_compile api/urls.py

# Verifier Django
echo "   Running Django check..."
python manage.py check --settings=config.settings.production

# Redemarrer Gunicorn
echo "   Restarting Gunicorn..."
sudo systemctl restart gunicorn

# Verifier le statut
echo "   Checking Gunicorn status..."
sudo systemctl status gunicorn --no-pager | head -5

echo "   Deployment complete!"
ENDSSH

echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE AVEC SUCCES"
echo "=============================================="
echo ""
echo "Nouveaux endpoints disponibles:"
echo "  - /api/v1/mobile/dashboard/              (generic)"
echo "  - /api/v1/mobile/dashboard/admin/        (admin role)"
echo "  - /api/v1/mobile/dashboard/practitioner/ (practitioner role)"
echo "  - /api/v1/mobile/dashboard/participant/  (participant role)"
echo ""
echo "Le PractitionerDashboardView retourne:"
echo "  - dashboard_type: 'participant'"
echo "  - practitioner: info de base"
echo "  - upcoming_competitions: competitions ouvertes"
echo "  - my_registrations: inscriptions actuelles"
echo "  - combat_stats: statistiques combats"
echo "  - grade_progress: progression de grade"
echo "  - calendar_events: evenements a venir"
echo "  - notifications_count: notifications non lues"
echo ""
