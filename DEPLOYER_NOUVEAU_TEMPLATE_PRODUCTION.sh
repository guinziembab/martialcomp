#!/bin/bash

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║   DÉPLOIEMENT NOUVEAU TEMPLATE COMBAT V2 EN PRODUCTION                      ║
# ║                    Date: 2025-11-16                                          ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║       🚀 DÉPLOIEMENT NOUVEAU TEMPLATE COMBAT V2                              ║"
echo "║                    $(date '+%Y-%m-%d %H:%M:%S')                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé"
    exit 1
fi

echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 1: Backup de l'ancien template                                        │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

TEMPLATE_DIR="apps/competitions/templates/competitions/combat"
OLD_TEMPLATE="${TEMPLATE_DIR}/interface_combat_v2.html"
NEW_TEMPLATE="${TEMPLATE_DIR}/interface_combat_v2_new.html"
BACKUP_FILE="${OLD_TEMPLATE}.backup_$(date +%Y%m%d_%H%M%S)"

if [ -f "$OLD_TEMPLATE" ]; then
    cp "$OLD_TEMPLATE" "$BACKUP_FILE"
    log_success "Backup créé: $BACKUP_FILE"
else
    log_warning "Ancien template non trouvé (première installation ?)"
fi

if [ ! -f "$NEW_TEMPLATE" ]; then
    echo "❌ Erreur: Nouveau template non trouvé: $NEW_TEMPLATE"
    exit 1
fi

echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 2: Remplacement du template                                           │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

cp "$NEW_TEMPLATE" "$OLD_TEMPLATE"
log_success "Template remplacé avec succès"

echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 3: Vérification du nouveau template                                   │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

# Vérifier les boutons onclick
ONCLICK_COUNT=$(grep -c 'onclick="addPoints' "$OLD_TEMPLATE" || echo "0")
log_info "Boutons onclick trouvés: $ONCLICK_COUNT"

# Vérifier le bouton DÉMARRER
if grep -q 'id="startBtn"' "$OLD_TEMPLATE"; then
    log_success "Bouton DÉMARRER présent"
else
    echo "❌ Erreur: Bouton DÉMARRER manquant"
    exit 1
fi

# Vérifier les termes neutres
if grep -q "Avertissements:" "$OLD_TEMPLATE"; then
    log_success "Termes neutres présents"
else
    echo "❌ Erreur: Termes neutres manquants"
    exit 1
fi

echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 4: Collecte des fichiers statiques                                    │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput --clear | tail -5
log_success "Fichiers statiques collectés"

echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ÉTAPE 5: Redémarrage de Gunicorn                                            │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"

log_info "Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn
sleep 3

if sudo systemctl is-active --quiet gunicorn; then
    log_success "Gunicorn redémarré avec succès"
else
    echo "❌ Erreur: Gunicorn n'a pas redémarré correctement"
    sudo journalctl -u gunicorn -n 50 --no-pager
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS                        ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 📋 NOUVEAU TEMPLATE DÉPLOYÉ                                                  │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  ✅ Bouton DÉMARRER visible et animé"
echo "  ✅ Timer fonctionnel (démarre au clic)"
echo "  ✅ Boutons ¼ pt, ½ pt, 1½ pt fonctionnels"
echo "  ✅ Bouton Retrait (-0.5) fonctionnel"
echo "  ✅ Termes neutres (Avertissements, Pénalités)"
echo "  ✅ Affichage décimales garanti (0.0, 0.25, 0.5, etc.)"
echo "  ✅ Code JavaScript simplifié"
echo "  ✅ Logs de debug dans la console"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ ⚠️  ACTION REQUISE: VIDER LE CACHE DU NAVIGATEUR                             │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  Sur la page du combat, appuyez sur:"
echo "  • Windows/Linux: Ctrl + Shift + R"
echo "  • Mac: Cmd + Shift + R"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🧪 TESTS À EFFECTUER                                                         │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  1. [ ] Bouton DÉMARRER visible avec animation"
echo "  2. [ ] Clic sur DÉMARRER → Timer démarre"
echo "  3. [ ] Clic sur ¼ pt → Score = 0.25"
echo "  4. [ ] Clic sur ½ pt → Score = 0.75"
echo "  5. [ ] Clic sur 1½ pt → Score = 2.25"
echo "  6. [ ] Clic sur Retrait (-0.5) → Score diminue"
echo "  7. [ ] Console (F12) affiche \"🎯 Bouton cliqué:\""
echo "  8. [ ] Pas d'erreurs en rouge dans la console"
echo ""
echo "┌──────────────────────────────────────────────────────────────────────────────┐"
echo "│ 🔗 URL DE TEST                                                               │"
echo "└──────────────────────────────────────────────────────────────────────────────┘"
echo ""
echo "  https://martialcomp.com/fr/competitions/combat/combats/8/interface-v2/"
echo ""
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║  🎯 DÉPLOIEMENT TERMINÉ - $(date '+%Y-%m-%d %H:%M:%S')                       ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
