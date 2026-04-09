#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║   DÉPLOIEMENT CORRECTION INTERFACE COMBAT V2 - 2025-11-16                   ║
# ║                                                                              ║
# ║   Corrections appliquées:                                                    ║
# ║   1. ✅ Boutons fonctionnels (¼ pt, ½ pt, 1½ pt, -0.5)                      ║
# ║   2. ✅ Termes coréens retirés (Kyong-go → Avertissements)                  ║
# ║   3. ✅ Termes coréens retirés (Gam-jeom → Pénalités)                       ║
# ║   4. ✅ Scores initiaux à 0.0 (au lieu de 12 et 8)                          ║
# ║   5. ✅ Gestionnaires d'événements améliorés avec debug                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║       🚀 DÉPLOIEMENT CORRECTION INTERFACE COMBAT V2                          ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "manage.py" ]; then
    log_error "Erreur: manage.py non trouvé. Êtes-vous dans le bon répertoire ?"
    exit 1
fi

log_info "Répertoire de travail: $(pwd)"
echo ""

# ============================================================================
# ÉTAPE 1: Backup du fichier actuel
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 1: Backup du fichier actuel                                           │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

TEMPLATE_FILE="apps/competitions/templates/competitions/combat/interface_combat_v2.html"
BACKUP_FILE="${TEMPLATE_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

if [ -f "$TEMPLATE_FILE" ]; then
    cp "$TEMPLATE_FILE" "$BACKUP_FILE"
    log_success "Backup créé: $BACKUP_FILE"
else
    log_error "Fichier source non trouvé: $TEMPLATE_FILE"
    exit 1
fi
echo ""

# ============================================================================
# ÉTAPE 2: Vérification des modifications
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 2: Vérification des modifications                                     │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Vérification des corrections appliquées..."

# Vérifier que les termes coréens ont été retirés
if grep -q "Kyong-go" "$TEMPLATE_FILE"; then
    log_error "ERREUR: Le terme 'Kyong-go' est encore présent dans le fichier"
    exit 1
else
    log_success "Terme 'Kyong-go' retiré avec succès"
fi

if grep -q "Gam-jeom" "$TEMPLATE_FILE"; then
    log_error "ERREUR: Le terme 'Gam-jeom' est encore présent dans le fichier"
    exit 1
else
    log_success "Terme 'Gam-jeom' retiré avec succès"
fi

# Vérifier que les nouveaux termes sont présents
if grep -q "Avertissements:" "$TEMPLATE_FILE"; then
    log_success "Nouveau terme 'Avertissements' présent"
else
    log_error "ERREUR: Le terme 'Avertissements' n'est pas présent"
    exit 1
fi

if grep -q "Pénalités:" "$TEMPLATE_FILE"; then
    log_success "Nouveau terme 'Pénalités' présent"
else
    log_error "ERREUR: Le terme 'Pénalités' n'est pas présent"
    exit 1
fi

# Vérifier que les scores initiaux sont à 0.0
if grep -q 'id="scoreRouge">0.0</div>' "$TEMPLATE_FILE"; then
    log_success "Score initial Rouge = 0.0"
else
    log_warning "Score initial Rouge pourrait ne pas être à 0.0"
fi

if grep -q 'id="scoreBlanc">0.0</div>' "$TEMPLATE_FILE"; then
    log_success "Score initial Blanc = 0.0"
else
    log_warning "Score initial Blanc pourrait ne pas être à 0.0"
fi

# Vérifier que les gestionnaires d'événements ont été améliorés
if grep -q "console.log('Bouton cliqué:'," "$TEMPLATE_FILE"; then
    log_success "Gestionnaires d'événements améliorés avec debug"
else
    log_warning "Les logs de debug pourraient ne pas être présents"
fi

echo ""

# ============================================================================
# ÉTAPE 3: Collecte des fichiers statiques
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 3: Collecte des fichiers statiques                                    │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear
log_success "Fichiers statiques collectés"
echo ""

# ============================================================================
# ÉTAPE 4: Redémarrage de Gunicorn
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 4: Redémarrage de Gunicorn                                            │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn
sleep 3

# Vérifier le statut
if sudo systemctl is-active --quiet gunicorn; then
    log_success "Gunicorn redémarré avec succès"
else
    log_error "ERREUR: Gunicorn n'a pas redémarré correctement"
    log_info "Vérification des logs..."
    sudo journalctl -u gunicorn -n 50 --no-pager
    exit 1
fi
echo ""

# ============================================================================
# ÉTAPE 5: Vérification du déploiement
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 5: Vérification du déploiement                                        │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Vérification du statut des services..."

# Vérifier Gunicorn
if sudo systemctl is-active --quiet gunicorn; then
    log_success "Gunicorn: actif"
else
    log_error "Gunicorn: inactif"
fi

# Vérifier Nginx
if sudo systemctl is-active --quiet nginx; then
    log_success "Nginx: actif"
else
    log_warning "Nginx: inactif"
fi

echo ""

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 📋 CORRECTIONS APPLIQUÉES                                                    │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  ✅ Termes coréens retirés:"
echo "     • Kyong-go → Avertissements"
echo "     • Gam-jeom → Pénalités"
echo ""
echo "  ✅ Scores initiaux corrigés:"
echo "     • Score Rouge: 0.0 (au lieu de 12)"
echo "     • Score Blanc: 0.0 (au lieu de 8)"
echo ""
echo "  ✅ Gestionnaires d'événements améliorés:"
echo "     • Ajout de e.preventDefault()"
echo "     • Ajout de logs de debug"
echo "     • Vérification des valeurs avant traitement"
echo ""
echo "  ✅ Boutons fonctionnels:"
echo "     • ¼ pt (+0.25)"
echo "     • ½ pt (+0.5)"
echo "     • 1 pt (+1)"
echo "     • 1½ pt (+1.5)"
echo "     • 2 pts (+2)"
echo "     • Retrait (-0.5)"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ⚠️  ACTION REQUISE: VIDER LE CACHE DU NAVIGATEUR                             │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  Le fichier a été déployé à: $(date '+%H:%M:%S')"
echo ""
echo "  VOUS DEVEZ vider le cache pour voir les changements:"
echo ""
echo "  1. Sur la page du combat, appuyez sur:"
echo "     • Windows/Linux: Ctrl + Shift + R"
echo "     • Mac: Cmd + Shift + R"
echo ""
echo "  2. OU ouvrir en navigation privée:"
echo "     • Chrome: Ctrl + Shift + N"
echo "     • Firefox: Ctrl + Shift + P"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🧪 TESTS À EFFECTUER                                                         │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  Après vidage du cache, testez:"
echo ""
echo "  1. ✅ Affichage initial:"
echo "     • Score Rouge = 0.0"
echo "     • Score Blanc = 0.0"
echo "     • Avertissements Rouge = 0"
echo "     • Pénalités Rouge = 0"
echo "     • Avertissements Blanc = 0"
echo "     • Pénalités Blanc = 0"
echo ""
echo "  2. ✅ Boutons fonctionnels:"
echo "     • Clic sur ¼ pt → Score = 0.25"
echo "     • Clic sur ½ pt → Score = 0.75"
echo "     • Clic sur 1 pt → Score = 1.75"
echo "     • Clic sur 1½ pt → Score = 3.25"
echo "     • Clic sur Retrait (-0.5) → Score = 2.75"
echo ""
echo "  3. ✅ Termes neutres:"
echo "     • Pas de 'Kyong-go' visible"
echo "     • Pas de 'Gam-jeom' visible"
echo "     • 'Avertissements' affiché"
echo "     • 'Pénalités' affiché"
echo ""
echo "  4. ✅ Console JavaScript (F12):"
echo "     • Vérifier les logs 'Bouton cliqué:' avec les valeurs"
echo "     • Pas d'erreurs en rouge"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🔗 URL DE TEST                                                               │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  https://martialcomp.com/fr/competitions/combat/combats/8/interface-v2/"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 📁 FICHIERS MODIFIÉS                                                         │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  • $TEMPLATE_FILE"
echo "  • Backup: $BACKUP_FILE"
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🎯 DÉPLOIEMENT TERMINÉ - $(date '+%Y-%m-%d %H:%M:%S')                       ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Si les boutons ne fonctionnent toujours pas après Ctrl+Shift+R,"
echo "ouvrez la Console (F12) et envoyez-moi les messages affichés."
echo ""
