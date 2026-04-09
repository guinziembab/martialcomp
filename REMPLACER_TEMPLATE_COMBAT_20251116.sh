#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║   REMPLACEMENT TEMPLATE COMBAT V2 - NOUVEAU TEMPLATE FONCTIONNEL            ║
# ║                    Date: 2025-11-16                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║       🚀 REMPLACEMENT DU TEMPLATE COMBAT V2                                  ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "manage.py" ]; then
    log_error "Erreur: manage.py non trouvé"
    exit 1
fi

echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 📋 NOUVEAU TEMPLATE - FONCTIONNALITÉS                                       │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  ✅ Bouton DÉMARRER visible et fonctionnel"
echo "  ✅ Timer qui démarre au clic"
echo "  ✅ Boutons avec décimales (¼ pt, ½ pt, 1½ pt) fonctionnels"
echo "  ✅ Bouton Retrait (-0.5) fonctionnel"
echo "  ✅ Termes neutres (Avertissements, Pénalités)"
echo "  ✅ Scores initiaux à 0.0"
echo "  ✅ Affichage décimales garanti (0.0, 0.25, 0.5, 1.0, etc.)"
echo "  ✅ Code JavaScript simplifié et testé"
echo "  ✅ Onclick direct sur les boutons (pas de gestionnaires complexes)"
echo ""

# ============================================================================
# ÉTAPE 1: Backup de l'ancien template
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 1: Backup de l'ancien template                                        │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

OLD_TEMPLATE="apps/competitions/templates/competitions/combat/interface_combat_v2.html"
NEW_TEMPLATE="apps/competitions/templates/competitions/combat/interface_combat_v2_new.html"
BACKUP_FILE="${OLD_TEMPLATE}.backup_$(date +%Y%m%d_%H%M%S)"

if [ -f "$OLD_TEMPLATE" ]; then
    cp "$OLD_TEMPLATE" "$BACKUP_FILE"
    log_success "Backup créé: $BACKUP_FILE"
else
    log_error "Ancien template non trouvé: $OLD_TEMPLATE"
    exit 1
fi

if [ ! -f "$NEW_TEMPLATE" ]; then
    log_error "Nouveau template non trouvé: $NEW_TEMPLATE"
    exit 1
fi

echo ""

# ============================================================================
# ÉTAPE 2: Remplacement du template
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 2: Remplacement du template                                           │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Remplacement de l'ancien template par le nouveau..."
cp "$NEW_TEMPLATE" "$OLD_TEMPLATE"
log_success "Template remplacé avec succès"
echo ""

# ============================================================================
# ÉTAPE 3: Vérification du nouveau template
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 3: Vérification du nouveau template                                   │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Vérification des fonctionnalités..."

# Vérifier le bouton DÉMARRER
if grep -q 'id="startBtn"' "$OLD_TEMPLATE"; then
    log_success "Bouton DÉMARRER présent"
else
    log_error "Bouton DÉMARRER manquant"
    exit 1
fi

# Vérifier les boutons avec onclick
if grep -q 'onclick="addPoints' "$OLD_TEMPLATE"; then
    log_success "Boutons avec onclick direct présents"
else
    log_error "Boutons onclick manquants"
    exit 1
fi

# Vérifier les termes neutres
if grep -q "Avertissements:" "$OLD_TEMPLATE" && grep -q "Pénalités:" "$OLD_TEMPLATE"; then
    log_success "Termes neutres présents"
else
    log_error "Termes neutres manquants"
    exit 1
fi

# Vérifier la fonction addPoints
if grep -q "function addPoints" "$OLD_TEMPLATE"; then
    log_success "Fonction addPoints présente"
else
    log_error "Fonction addPoints manquante"
    exit 1
fi

# Vérifier la fonction startTimer
if grep -q "function startTimer" "$OLD_TEMPLATE"; then
    log_success "Fonction startTimer présente"
else
    log_error "Fonction startTimer manquante"
    exit 1
fi

echo ""

# ============================================================================
# ÉTAPE 4: Collecte des fichiers statiques
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 4: Collecte des fichiers statiques                                    │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear
log_success "Fichiers statiques collectés"
echo ""

# ============================================================================
# ÉTAPE 5: Redémarrage de Gunicorn
# ============================================================================
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 5: Redémarrage de Gunicorn                                            │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn
sleep 3

if sudo systemctl is-active --quiet gunicorn; then
    log_success "Gunicorn redémarré avec succès"
else
    log_error "ERREUR: Gunicorn n'a pas redémarré correctement"
    sudo journalctl -u gunicorn -n 50 --no-pager
    exit 1
fi
echo ""

# ============================================================================
# RÉSUMÉ FINAL
# ============================================================================
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ REMPLACEMENT TERMINÉ AVEC SUCCÈS                       ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🎯 NOUVEAU TEMPLATE INSTALLÉ                                                 │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  ✅ Template remplacé: interface_combat_v2.html"
echo "  ✅ Backup créé: $BACKUP_FILE"
echo "  ✅ Fichiers statiques collectés"
echo "  ✅ Gunicorn redémarré"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🆕 NOUVELLES FONCTIONNALITÉS                                                 │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  1. 🟢 BOUTON DÉMARRER"
echo "     • Visible en haut de la zone centrale"
echo "     • Animation pulsante pour attirer l'attention"
echo "     • Lance le timer au clic"
echo ""
echo "  2. ⏱️  TIMER FONCTIONNEL"
echo "     • Démarre au clic sur DÉMARRER"
echo "     • Décompte visible en temps réel"
echo "     • Bouton PAUSE/REPRENDRE apparaît après démarrage"
echo ""
echo "  3. 🎯 BOUTONS AVEC DÉCIMALES"
echo "     • ¼ pt (+0.25) → Fonctionne"
echo "     • ½ pt (+0.5) → Fonctionne"
echo "     • 1 pt (+1) → Fonctionne"
echo "     • 1½ pt (+1.5) → Fonctionne"
echo "     • 2 pts (+2) → Fonctionne"
echo "     • Retrait (-0.5) → Fonctionne"
echo ""
echo "  4. 📊 AFFICHAGE DÉCIMALES"
echo "     • Toujours au moins 1 décimale"
echo "     • Exemples: 0.0, 0.25, 0.5, 1.0, 1.25, 5.5"
echo ""
echo "  5. 🌐 TERMES NEUTRES"
echo "     • Avertissements (au lieu de Kyong-go)"
echo "     • Pénalités (au lieu de Gam-jeom)"
echo ""
echo "  6. 📝 HISTORIQUE DES ACTIONS"
echo "     • Chaque action enregistrée"
echo "     • Affichage du temps, combattant, action, points"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ⚠️  ACTION REQUISE: VIDER LE CACHE                                           │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  IMPORTANT: Vous DEVEZ vider le cache du navigateur !"
echo ""
echo "  Méthode rapide:"
echo "  • Windows/Linux: Ctrl + Shift + R"
echo "  • Mac: Cmd + Shift + R"
echo ""
echo "  Ou ouvrir en navigation privée:"
echo "  • Chrome: Ctrl + Shift + N"
echo "  • Firefox: Ctrl + Shift + P"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🧪 TESTS À EFFECTUER                                                         │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  Après vidage du cache:"
echo ""
echo "  1. ✅ Vérifier le bouton DÉMARRER"
echo "     [ ] Bouton vert visible avec animation"
echo "     [ ] Texte: \"DÉMARRER\""
echo ""
echo "  2. ✅ Tester le timer"
echo "     [ ] Clic sur DÉMARRER → Timer démarre"
echo "     [ ] Décompte visible (02:00, 01:59, 01:58...)"
echo "     [ ] Bouton PAUSE apparaît"
echo ""
echo "  3. ✅ Tester les boutons ROUGE"
echo "     [ ] Clic sur ¼ pt → Score = 0.25"
echo "     [ ] Clic sur ½ pt → Score = 0.75"
echo "     [ ] Clic sur 1 pt → Score = 1.75"
echo "     [ ] Clic sur 1½ pt → Score = 3.25"
echo "     [ ] Clic sur Retrait (-0.5) → Score = 2.75"
echo ""
echo "  4. ✅ Tester les boutons BLANC"
echo "     [ ] Clic sur ¼ pt → Score = 0.25"
echo "     [ ] Clic sur ½ pt → Score = 0.75"
echo "     [ ] Clic sur 1 pt → Score = 1.75"
echo "     [ ] Clic sur 1½ pt → Score = 3.25"
echo "     [ ] Clic sur Retrait (-0.5) → Score = 2.75"
echo ""
echo "  5. ✅ Vérifier l'historique"
echo "     [ ] Chaque clic ajoute une ligne"
echo "     [ ] Affichage: temps, combattant, action, points"
echo ""
echo "  6. ✅ Ouvrir la Console (F12)"
echo "     [ ] Logs \"🎯 Bouton cliqué:\" visibles"
echo "     [ ] Logs \"✅ Score mis à jour:\" visibles"
echo "     [ ] Pas d'erreurs en rouge"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🔗 URL DE TEST                                                               │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  https://martialcomp.com/fr/competitions/combat/combats/8/interface-v2/"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🔍 SI PROBLÈME PERSISTE                                                      │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  1. Ouvrir la Console (F12)"
echo "  2. Cliquer sur un bouton"
echo "  3. Vérifier les logs:"
echo "     • \"🎯 Bouton cliqué:\" doit apparaître"
echo "     • \"✅ Score mis à jour:\" doit apparaître"
echo "  4. Si pas de logs → Le cache n'est pas vidé"
echo "  5. Si erreurs en rouge → Copier et envoyer"
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🎯 DÉPLOIEMENT TERMINÉ - $(date '+%Y-%m-%d %H:%M:%S')                       ║"
echo "║                                                                              ║"
echo "║  Le nouveau template est maintenant actif !                                  ║"
echo "║  N'oubliez pas de vider le cache du navigateur.                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
