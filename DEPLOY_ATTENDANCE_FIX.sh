#!/bin/bash
# Script de déploiement des corrections du système de présences/absences
# Exécuter depuis WSL avec: bash DEPLOY_ATTENDANCE_FIX.sh

set -e

REMOTE_HOST="root@88.198.196.192"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"

echo "=== Déploiement des corrections Attendance ==="
echo ""

# 1. Déployer l'API backend
echo "1. Déploiement de l'API attendance_api.py..."
scp "$LOCAL_PATH/api/attendance_api.py" "$REMOTE_HOST:$REMOTE_PATH/api/"
echo "   ✓ attendance_api.py déployé"

# 2. Recharger Gunicorn
echo ""
echo "2. Rechargement de Gunicorn..."
ssh "$REMOTE_HOST" "kill -HUP \$(cat $REMOTE_PATH/gunicorn.pid 2>/dev/null) || systemctl reload gunicorn || echo 'Redémarrage manuel requis'"
echo "   ✓ Gunicorn rechargé"

echo ""
echo "=== Déploiement terminé avec succès ==="
echo ""
echo "Modifications déployées:"
echo "  - DeclareAbsenceScreen: récupération automatique du practitionerId"
echo "  - Sélecteur de date fonctionnel avec DateTimePicker"
echo "  - Écrans de gestion pour administrateurs:"
echo "    * AttendanceManagementScreen (dashboard)"
echo "    * PendingDeclarationsScreen (validation des absences)"
echo "    * RollCallScreen (feuille d'appel)"
echo ""
echo "Note: Les modifications mobile seront disponibles après rebuild de l'app Expo."
