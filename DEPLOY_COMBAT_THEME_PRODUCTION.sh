#!/bin/bash
# =============================================================================
# DEPLOIEMENT THEME SOMBRE - MODULE COMBAT ET DOCUMENTATION
# =============================================================================
# Date: 05 Decembre 2024
# Description: Deploie toutes les adaptations du theme sombre pour le module
#              combat, la documentation et la liste des competitions
# =============================================================================

set -e

# Configuration
REMOTE_USER="martialcomp"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/martialcomp"
LOCAL_PATH="."

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}=============================================================================${NC}"
echo -e "${CYAN}   DEPLOIEMENT THEME SOMBRE - MODULE COMBAT & DOCUMENTATION${NC}"
echo -e "${CYAN}=============================================================================${NC}"
echo ""

# =============================================================================
# LISTE DES FICHIERS A DEPLOYER
# =============================================================================

# Templates Combat (theme sombre complet)
COMBAT_TEMPLATES=(
    "apps/competitions/templates/competitions/combat/base.html"
    "apps/competitions/templates/competitions/combat/form_combat.html"
    "apps/competitions/templates/competitions/combat/liste_combats.html"
    "apps/competitions/templates/competitions/combat/liste_equipes.html"
    "apps/competitions/templates/competitions/combat/liste_equipes_par_categorie.html"
    "apps/competitions/templates/competitions/combat/select_competition_equipes.html"
    "apps/competitions/templates/competitions/combat/detail_equipe.html"
    "apps/competitions/templates/competitions/combat/form_equipe.html"
    "apps/competitions/templates/competitions/combat/form_membre_equipe.html"
    "apps/competitions/templates/competitions/combat/liste_poules.html"
    "apps/competitions/templates/competitions/combat/detail_poule.html"
    "apps/competitions/templates/competitions/combat/generer_poules.html"
)

# Templates Documentation (theme sombre)
DOC_TEMPLATES=(
    "apps/competitions/templates/competitions/dashboard/documentation/index.html"
    "apps/competitions/templates/competitions/dashboard/documentation/dashboard_doc.html"
    "apps/competitions/templates/competitions/dashboard/documentation/guide.html"
)

# Templates Competition (theme sombre)
COMPETITION_TEMPLATES=(
    "apps/competitions/templates/competitions/competition/list.html"
)

# Combiner tous les fichiers
ALL_FILES=(
    "${COMBAT_TEMPLATES[@]}"
    "${DOC_TEMPLATES[@]}"
    "${COMPETITION_TEMPLATES[@]}"
)

# =============================================================================
# AFFICHAGE DES FICHIERS
# =============================================================================

echo -e "${YELLOW}TEMPLATES COMBAT (${#COMBAT_TEMPLATES[@]} fichiers):${NC}"
for file in "${COMBAT_TEMPLATES[@]}"; do
    echo -e "  ${GREEN}+${NC} $file"
done
echo ""

echo -e "${YELLOW}TEMPLATES DOCUMENTATION (${#DOC_TEMPLATES[@]} fichiers):${NC}"
for file in "${DOC_TEMPLATES[@]}"; do
    echo -e "  ${GREEN}+${NC} $file"
done
echo ""

echo -e "${YELLOW}TEMPLATES COMPETITION (${#COMPETITION_TEMPLATES[@]} fichiers):${NC}"
for file in "${COMPETITION_TEMPLATES[@]}"; do
    echo -e "  ${GREEN}+${NC} $file"
done
echo ""

echo -e "${CYAN}Total: ${#ALL_FILES[@]} fichiers a deployer${NC}"
echo ""

# =============================================================================
# VERIFICATION DES FICHIERS LOCAUX
# =============================================================================

echo -e "${YELLOW}Verification des fichiers locaux...${NC}"
MISSING_FILES=()
for file in "${ALL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
        echo -e "  ${RED}MANQUANT:${NC} $file"
    else
        echo -e "  ${GREEN}OK:${NC} $file"
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo -e "${RED}ERREUR: ${#MISSING_FILES[@]} fichier(s) manquant(s)!${NC}"
    echo -e "${RED}Veuillez verifier les fichiers avant de continuer.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Tous les fichiers sont presents.${NC}"
echo ""

# =============================================================================
# COMMANDES DE DEPLOIEMENT
# =============================================================================

echo -e "${CYAN}=============================================================================${NC}"
echo -e "${CYAN}   COMMANDES DE DEPLOIEMENT${NC}"
echo -e "${CYAN}=============================================================================${NC}"
echo ""
echo -e "${YELLOW}Executez les commandes suivantes sur votre serveur:${NC}"
echo ""

# Commande 1: Backup
echo -e "${BLUE}# 1. BACKUP DES FICHIERS ACTUELS${NC}"
echo "ssh ${REMOTE_USER}@${REMOTE_HOST} << 'BACKUP_EOF'"
echo "cd ${REMOTE_PATH}"
echo "BACKUP_DIR=\"backups/theme_combat_\$(date +%Y%m%d_%H%M%S)\""
echo "mkdir -p \$BACKUP_DIR"
echo ""
echo "# Backup templates combat"
echo "mkdir -p \$BACKUP_DIR/combat"
echo "cp -r apps/competitions/templates/competitions/combat/*.html \$BACKUP_DIR/combat/ 2>/dev/null || true"
echo ""
echo "# Backup templates documentation"
echo "mkdir -p \$BACKUP_DIR/documentation"
echo "cp apps/competitions/templates/competitions/dashboard/documentation/*.html \$BACKUP_DIR/documentation/ 2>/dev/null || true"
echo ""
echo "# Backup template competition list"
echo "mkdir -p \$BACKUP_DIR/competition"
echo "cp apps/competitions/templates/competitions/competition/list.html \$BACKUP_DIR/competition/ 2>/dev/null || true"
echo ""
echo "echo \"Backup cree dans: \$BACKUP_DIR\""
echo "BACKUP_EOF"
echo ""

# Commande 2: Transfer SCP
echo -e "${BLUE}# 2. TRANSFERT DES FICHIERS (depuis le repertoire local)${NC}"
echo ""
echo "# Templates Combat"
for file in "${COMBAT_TEMPLATES[@]}"; do
    echo "scp \"$file\" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/$file"
done
echo ""
echo "# Templates Documentation"
for file in "${DOC_TEMPLATES[@]}"; do
    echo "scp \"$file\" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/$file"
done
echo ""
echo "# Templates Competition"
for file in "${COMPETITION_TEMPLATES[@]}"; do
    echo "scp \"$file\" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/$file"
done
echo ""

# Commande 3: Vider le cache
echo -e "${BLUE}# 3. VIDER LE CACHE DJANGO${NC}"
echo "ssh ${REMOTE_USER}@${REMOTE_HOST} << 'CACHE_EOF'"
echo "cd ${REMOTE_PATH}"
echo "source venv/bin/activate"
echo ""
echo "# Vider le cache Django"
echo "python manage.py clear_cache 2>/dev/null || echo 'Cache clear non disponible'"
echo ""
echo "# Supprimer fichiers .pyc"
echo "find . -name '*.pyc' -delete"
echo "find . -name '__pycache__' -type d -delete"
echo ""
echo "echo 'Cache vide'"
echo "CACHE_EOF"
echo ""

# Commande 4: Redemarrer le serveur
echo -e "${BLUE}# 4. REDEMARRER LE SERVEUR${NC}"
echo "ssh ${REMOTE_USER}@${REMOTE_HOST} << 'RESTART_EOF'"
echo "cd ${REMOTE_PATH}"
echo ""
echo "# Redemarrer Gunicorn"
echo "sudo systemctl restart gunicorn 2>/dev/null || sudo service gunicorn restart 2>/dev/null || echo 'Gunicorn non trouve'"
echo ""
echo "# Ou via supervisorctl"
echo "sudo supervisorctl restart martialcomp 2>/dev/null || echo 'Supervisor non utilise'"
echo ""
echo "# Verification du statut"
echo "sudo systemctl status gunicorn 2>/dev/null | head -5 || echo 'Statut non disponible'"
echo ""
echo "echo 'Serveur redemarre'"
echo "RESTART_EOF"
echo ""

# =============================================================================
# SCRIPT TOUT-EN-UN
# =============================================================================

echo -e "${CYAN}=============================================================================${NC}"
echo -e "${CYAN}   SCRIPT TOUT-EN-UN (copier-coller)${NC}"
echo -e "${CYAN}=============================================================================${NC}"
echo ""

cat << 'ALLINONE'
# ============================================
# DEPLOIEMENT COMPLET - COPIER CE BLOC
# ============================================

# Variables
REMOTE="martialcomp@martialcomp.com"
REMOTE_PATH="/var/www/martialcomp"

# 1. Backup sur le serveur
ssh $REMOTE "cd $REMOTE_PATH && mkdir -p backups/theme_$(date +%Y%m%d) && cp -r apps/competitions/templates/competitions/combat/*.html backups/theme_$(date +%Y%m%d)/ 2>/dev/null; cp -r apps/competitions/templates/competitions/dashboard/documentation/*.html backups/theme_$(date +%Y%m%d)/ 2>/dev/null; cp apps/competitions/templates/competitions/competition/list.html backups/theme_$(date +%Y%m%d)/ 2>/dev/null"

# 2. Transfert des fichiers combat
scp apps/competitions/templates/competitions/combat/base.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/form_combat.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/liste_combats.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/liste_equipes.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/liste_equipes_par_categorie.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/select_competition_equipes.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/detail_equipe.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/form_equipe.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/form_membre_equipe.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/liste_poules.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/detail_poule.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/
scp apps/competitions/templates/competitions/combat/generer_poules.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/

# 3. Transfert des fichiers documentation
scp apps/competitions/templates/competitions/dashboard/documentation/index.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/dashboard/documentation/
scp apps/competitions/templates/competitions/dashboard/documentation/dashboard_doc.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/dashboard/documentation/
scp apps/competitions/templates/competitions/dashboard/documentation/guide.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/dashboard/documentation/

# 4. Transfert du template competition list
scp apps/competitions/templates/competitions/competition/list.html $REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/competition/

# 5. Redemarrage du serveur
ssh $REMOTE "cd $REMOTE_PATH && source venv/bin/activate && find . -name '*.pyc' -delete && sudo systemctl restart gunicorn"

echo "Deploiement termine!"

ALLINONE

echo ""

# =============================================================================
# RESUME
# =============================================================================

echo -e "${CYAN}=============================================================================${NC}"
echo -e "${CYAN}   RESUME DES MODIFICATIONS${NC}"
echo -e "${CYAN}=============================================================================${NC}"
echo ""
echo -e "${GREEN}THEME SOMBRE APPLIQUE A:${NC}"
echo ""
echo -e "${YELLOW}  MODULE COMBAT:${NC}"
echo "    - base.html (template de base avec sidebar)"
echo "    - form_combat.html (formulaire creation/modification combat)"
echo "    - liste_combats.html (tableau de bord des combats)"
echo "    - liste_equipes.html (liste des equipes)"
echo "    - liste_equipes_par_categorie.html (equipes par categorie)"
echo "    - select_competition_equipes.html (selection competition)"
echo "    - detail_equipe.html (detail d'une equipe)"
echo "    - form_equipe.html (formulaire equipe)"
echo "    - form_membre_equipe.html (ajout membre)"
echo "    - liste_poules.html (liste des poules)"
echo "    - detail_poule.html (detail poule)"
echo "    - generer_poules.html (generation automatique)"
echo ""
echo -e "${YELLOW}  DOCUMENTATION:${NC}"
echo "    - index.html (page principale documentation)"
echo "    - dashboard_doc.html (documentation par dashboard)"
echo "    - guide.html (guides d'utilisation detailles)"
echo ""
echo -e "${YELLOW}  COMPETITIONS:${NC}"
echo "    - list.html (liste des competitions)"
echo ""
echo -e "${GREEN}VARIABLES CSS COHERENTES:${NC}"
echo "    --bg-primary: #0f172a"
echo "    --bg-secondary: #1e293b"
echo "    --bg-tertiary: #334155"
echo "    --text-primary: #f8fafc"
echo "    --text-secondary: #94a3b8"
echo "    --accent-gold: #c9a227"
echo "    --accent-primary: #3b82f6"
echo "    --accent-success: #10b981"
echo "    --accent-danger: #ef4444"
echo "    --accent-warning: #f59e0b"
echo "    --accent-info: #06b6d4"
echo "    --accent-purple: #8b5cf6"
echo ""
echo -e "${GREEN}COULEURS PAR TYPE DE DASHBOARD:${NC}"
echo "    Participant: Vert (#10b981)"
echo "    Club: Bleu (#3b82f6)"
echo "    Federation: Orange (#f59e0b)"
echo "    Arbitre: Rouge (#ef4444)"
echo "    Entraineur: Cyan (#06b6d4)"
echo "    Combat: Violet (#8b5cf6)"
echo ""
echo -e "${CYAN}=============================================================================${NC}"
echo -e "${CYAN}   URLS A TESTER APRES DEPLOIEMENT${NC}"
echo -e "${CYAN}=============================================================================${NC}"
echo ""
echo "  https://martialcomp.com/fr/competitions/combat/combats/competition/4/"
echo "  https://martialcomp.com/fr/competitions/combat/combats/creer/competition/4/"
echo "  https://martialcomp.com/fr/competitions/combat/equipes/"
echo "  https://martialcomp.com/fr/competitions/combat/poules/competition/4/"
echo "  https://martialcomp.com/fr/competitions/competitions/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/participant/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/club/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/federation/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/referee/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/coach_multidiscipline/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/combat/"
echo "  https://martialcomp.com/fr/competitions/dashboard/documentation/combat/guide/"
echo ""
echo -e "${GREEN}Fin du script de deploiement.${NC}"
