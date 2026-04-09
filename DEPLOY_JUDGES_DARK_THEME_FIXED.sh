#!/bin/bash
# Script de déploiement du template judges.html corrigé (dark/gold theme)
# Exécuter depuis un environnement avec accès SSH au serveur

REMOTE_HOST="root@87.106.162.45"  # IP réelle du serveur
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement du template Judges Dark/Gold Theme (CORRIGÉ) ==="
echo ""

# 1. Backup du template existant
echo "[1/3] Backup du template existant..."
ssh $REMOTE_HOST "
    cd $REMOTE_PATH/apps/competitions/templates/competitions/management/
    cp judges.html judges.html.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'judges.html non existant'
"

# 2. Copie du template corrigé
echo "[2/3] Copie de judges.html corrigé..."
scp apps/competitions/templates/competitions/management/judges.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/management/judges.html

# 3. Redémarrage du service
echo "[3/3] Redémarrage de Gunicorn..."
ssh $REMOTE_HOST "systemctl restart martialcomp || supervisorctl restart martialcomp || pkill -HUP gunicorn"

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Template déployé:"
echo "  - judges.html (Gestion des juges et arbitres)"
echo ""
echo "URL à tester:"
echo "  - https://martialcomp.com/fr/competitions/management/4/judges/"
echo ""
echo "Corrections appliquées:"
echo "  - URL 'schedule_overview' -> 'schedule'"
echo "  - URL 'scoring' -> 'scoring_dashboard'"
echo "  - Ajout vérifications null pour assignment.registration"
echo "  - Ajout vérifications null pour judge.practitioner"
echo "  - Ajout vérifications null pour judge.user"
