#!/bin/bash
# Script de deploiement - Systeme de gestion des roles multi-interfaces
# Date: 2026-01-08
# Description: Deploie le systeme complet de gestion des roles avec validation
#
# Fonctionnalites deployees:
# - Attribution de roles depuis fiche pratiquant
# - Workflow de validation (pending/approved/rejected)
# - Role switcher dans la sidebar
# - Notifications pour les attributions de roles
# - Dashboards Manager et Coach avec role switcher

set -e

REMOTE="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="c:/martial_hub_django/martialcomp"

echo "============================================================"
echo "DEPLOIEMENT SYSTEME DE GESTION DES ROLES - MartialComp"
echo "============================================================"
echo ""

# Liste des fichiers a deployer
FILES_TO_DEPLOY=(
    # Migration
    "apps/organizations/migrations/0012_add_membership_status_and_approval.py"

    # Formulaires
    "apps/competitions/forms/role_forms.py"

    # Vues
    "apps/competitions/views/roles.py"

    # Templates
    "apps/competitions/templates/competitions/club/assign_role_modal.html"
    "apps/competitions/templates/competitions/club/practitioner_detail.html"
    "apps/competitions/templates/competitions/roles/pending_approvals.html"
    "apps/competitions/templates/competitions/includes/role_switcher.html"
    "apps/competitions/templates/competitions/dashboard/base.html"
    "apps/competitions/templates/competitions/dashboard/manager.html"
    "apps/competitions/templates/competitions/dashboard/coach.html"

    # URLs
    "apps/competitions/urls/__init__.py"

    # Services
    "apps/competitions/services/notification_service.py"
)

echo "1. Creation des dossiers distants si necessaires..."
ssh $REMOTE "mkdir -p $REMOTE_PATH/apps/competitions/templates/competitions/roles"
ssh $REMOTE "mkdir -p $REMOTE_PATH/apps/competitions/templates/competitions/includes"
ssh $REMOTE "mkdir -p $REMOTE_PATH/apps/competitions/forms"

echo ""
echo "2. Deploiement des fichiers..."
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "   - $file"
    scp "$LOCAL_PATH/$file" "$REMOTE:$REMOTE_PATH/$file"
done

echo ""
echo "3. Execution de la migration..."
ssh $REMOTE << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

echo "   Verification des migrations..."
python manage.py showmigrations organizations | tail -5

echo "   Application de la migration..."
python manage.py migrate organizations --noinput

echo "   Verification post-migration..."
python manage.py showmigrations organizations | tail -5
ENDSSH

echo ""
echo "4. Redemarrage de Gunicorn..."
ssh $REMOTE << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Methode 1: Signal HUP
pkill -HUP gunicorn 2>/dev/null && echo "   Signal HUP envoye a Gunicorn" || true

# Methode 2: Restart systemd si disponible
if systemctl is-active --quiet gunicorn 2>/dev/null; then
    sudo systemctl restart gunicorn
    echo "   Gunicorn redémarre via systemd"
fi

sleep 2
echo "   Verification du processus Gunicorn..."
ps aux | grep gunicorn | grep -v grep | head -2
ENDSSH

echo ""
echo "============================================================"
echo "DEPLOIEMENT TERMINE"
echo "============================================================"
echo ""
echo "Fonctionnalites deployees:"
echo "  - Attribution de roles depuis fiche pratiquant"
echo "  - Interface de validation des roles pour admins"
echo "  - Role switcher dans tous les dashboards"
echo "  - Notifications pour les changements de roles"
echo ""
echo "URLs disponibles:"
echo "  - /competitions/practitioners/<id>/assign-role/"
echo "  - /competitions/roles/pending-approvals/"
echo "  - /competitions/roles/<id>/validate/"
echo "  - /competitions/api/user-roles/"
echo "  - /competitions/api/switch-role/"
echo ""
echo "Pour tester:"
echo "  1. Aller sur une fiche pratiquant"
echo "  2. Cliquer sur 'Attribuer un role'"
echo "  3. Verifier les notifications"
echo "  4. Tester le role switcher dans la sidebar"
