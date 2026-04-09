#!/bin/bash
# =============================================================================
# DEPLOIEMENT CORRECTION CREATION EQUIPE - FILTRAGE PRATIQUANTS
# Date: 2024-12-02
# Description: Correction du filtrage pour afficher uniquement les pratiquants
#              du club inscrits à la compétition, regroupés par catégorie.
#
# Problème résolu:
#   - L'ancien filtre utilisait `practitioner__organization=club_organization`
#   - Mais certains pratiquants n'ont pas leur organization correctement définie
#   - Solution: Filtrer par la liste des IDs des pratiquants du club
# =============================================================================

SSH_HOST="martialcomp-production"
REMOTE_BASE="/var/www/vhosts/martialcomp.com/httpdocs"

echo "========================================"
echo "DEPLOIEMENT CORRECTION CREATION EQUIPE"
echo "========================================"
echo ""

# =============================================================================
# 1. VUE API
# =============================================================================
echo "1. Transfert de la vue registration_api.py..."
scp apps/competitions/views/club/registration_api.py ${SSH_HOST}:${REMOTE_BASE}/apps/competitions/views/club/registration_api.py
echo "   -> Vue transférée"
echo ""

# =============================================================================
# 2. TEMPLATE
# =============================================================================
echo "2. Transfert du template competition_registration_simple.html..."
scp apps/competitions/templates/competitions/club/competition_registration_simple.html ${SSH_HOST}:${REMOTE_BASE}/apps/competitions/templates/competitions/club/competition_registration_simple.html
echo "   -> Template transféré"
echo ""

# =============================================================================
# 3. VERIFICATION SYNTAXE
# =============================================================================
echo "3. Vérification de la syntaxe Python sur le serveur..."
ssh ${SSH_HOST} "cd ${REMOTE_BASE} && source ../venv/bin/activate && python3 -m py_compile apps/competitions/views/club/registration_api.py"
echo "   -> Syntaxe OK"
echo ""

# =============================================================================
# 4. REDEMARRAGE
# =============================================================================
echo "4. Redémarrage du serveur..."
ssh ${SSH_HOST} "sudo systemctl restart apache2"
echo "   -> Apache redémarré"
echo ""

echo "========================================"
echo "DEPLOIEMENT TERMINE"
echo "========================================"
echo ""
echo "Corrections déployées:"
echo "  - Filtrage des pratiquants corrigé (utilise liste IDs au lieu d'organization)"
echo "  - Modal de création d'équipe amélioré"
echo "  - Seuls les pratiquants INSCRITS à la compétition sont affichés"
echo "  - Pratiquants regroupés par catégorie"
echo "  - Compteurs de sélection en temps réel"
echo "  - Design amélioré (2 colonnes: titulaires / remplaçants)"
echo ""
echo "Testez sur: https://martialcomp.com/en/competitions/club/competition-registration/4/"
echo ""
