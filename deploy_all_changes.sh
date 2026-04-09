#!/bin/bash
# Script de déploiement complet pour toutes les modifications de la session
# Déploie tous les fichiers modifiés vers la production

echo "=== Déploiement complet de toutes les modifications ==="
echo ""

# Configuration
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_BASE_PATH="/mnt/c/martial_hub_django/martialcomp"

# Liste des fichiers à déployer (relatifs à la racine du projet)
FILES=(
    # Competition Management Pro
    "apps/competitions/templates/competitions/club/competition_management_pro.html"
    "apps/competitions/views/competition_management_pro.py"
    "apps/competitions/urls/club.py"
    
    # Category Management
    "apps/competitions/views/category_management.py"
    "apps/competitions/templates/base.html"
    
    # Schedule Management
    "apps/competitions/forms/schedule.py"
    "apps/competitions/templates/competitions/management/edit_competition_schedule.html"
    "apps/competitions/templates/competitions/management/schedule_conflicts.html"
    "apps/competitions/templates/competitions/management/schedule_visualizer.html"
    "apps/competitions/templates/competitions/management/schedule_export.html"
    "apps/competitions/templates/competitions/management/includes/schedule_actions.html"
    "apps/competitions/templates/competitions/management/includes/tatami_schedule.html"
    "apps/competitions/templates/competitions/management/includes/category_schedule_card.html"
    "apps/competitions/templates/competitions/management/edit_match_time_slot.html"
    "apps/competitions/templates/competitions/management/add_match_time_slot.html"
    "apps/competitions/templates/competitions/management/includes/match_time_slot_card.html"
    "apps/competitions/views/management/schedule.py"
    "apps/competitions/urls/management.py"
    "apps/competitions/templates/competitions/management/add_category_schedule.html"
    
    # Results Management
    "apps/competitions/views/management/results.py"
    
    # Participants Management
    "apps/competitions/forms/registrations.py"
    "apps/competitions/templates/competitions/management/bulk_approval.html"
    
    # Judges Management
    "apps/competitions/forms/judges.py"
    "apps/competitions/templates/competitions/management/add_judge_assignment.html"
    
    # Standalone Scoring Dashboard (déjà déployé mais on le vérifie)
    "apps/competitions/templates/competitions/standalone_scoring/admin/dashboard.html"
)

# Compteurs
TOTAL_FILES=${#FILES[@]}
SUCCESS_COUNT=0
FAILED_COUNT=0
FAILED_FILES=()

echo "Nombre de fichiers à déployer : $TOTAL_FILES"
echo ""

# Fonction pour déployer un fichier
deploy_file() {
    local file=$1
    local remote_file="$REMOTE_PATH/$file"
    local local_file="$LOCAL_BASE_PATH/$file"
    
    # Vérifier que le fichier local existe
    if [ ! -f "$local_file" ]; then
        echo "⚠️  Fichier local non trouvé : $file"
        return 1
    fi
    
    # Créer le répertoire distant si nécessaire
    local remote_dir=$(dirname "$remote_file")
    ssh "$REMOTE_HOST" "mkdir -p \"$remote_dir\""
    
    # Créer un backup
    local backup_file="${remote_file}.backup_$(date +%Y%m%d_%H%M%S)"
    ssh "$REMOTE_HOST" "if [ -f \"$remote_file\" ]; then cp \"$remote_file\" \"$backup_file\" && echo \"  ✓ Backup créé\"; fi" 2>/dev/null
    
    # Copier le fichier
    scp "$local_file" "$REMOTE_HOST:$remote_file" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ Déployé : $file"
        return 0
    else
        echo "  ✗ Échec : $file"
        return 1
    fi
}

# Déployer tous les fichiers
echo "Déploiement des fichiers..."
echo ""

for file in "${FILES[@]}"; do
    echo "[$((SUCCESS_COUNT + FAILED_COUNT + 1))/$TOTAL_FILES] $file"
    if deploy_file "$file"; then
        ((SUCCESS_COUNT++))
    else
        ((FAILED_COUNT++))
        FAILED_FILES+=("$file")
    fi
    echo ""
done

# Résumé
echo "=== Résumé du déploiement ==="
echo ""
echo "✅ Fichiers déployés avec succès : $SUCCESS_COUNT/$TOTAL_FILES"
if [ $FAILED_COUNT -gt 0 ]; then
    echo "❌ Fichiers en échec : $FAILED_COUNT"
    echo ""
    echo "Fichiers en échec :"
    for failed_file in "${FAILED_FILES[@]}"; do
        echo "  - $failed_file"
    done
    echo ""
fi

# Redémarrer le service Django
echo "Redémarrage du service Django..."
ssh "$REMOTE_HOST" "cd $REMOTE_PATH && bash start_gunicorn.sh >/dev/null 2>&1 && sleep 2 && ps aux | grep -i 'gunicorn.*config.wsgi' | grep -v grep | wc -l | xargs echo 'processus Gunicorn actifs :'"

if [ $? -eq 0 ]; then
    echo "✓ Service redémarré avec succès"
else
    echo "⚠️  Attention : Vérifiez manuellement le redémarrage du service"
fi

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "🌐 Vérifiez les pages suivantes :"
echo "  - https://martialcomp.com/fr/competitions/club/competitions/[ID]/manage/pro/"
echo "  - https://martialcomp.com/fr/competitions/competitions/3/manage-categories/"
echo "  - https://martialcomp.com/fr/competitions/management/schedule/3/edit/"
echo "  - https://martialcomp.com/fr/competitions/management/3/results/club/"
echo "  - https://martialcomp.com/fr/competitions/management/3/participants/bulk-approval/"
echo "  - https://martialcomp.com/fr/competitions/management/3/judges/add/"
echo "  - https://martialcomp.com/fr/competitions/standalone-scoring/admin/dashboard/"
