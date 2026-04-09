#!/bin/bash
# =============================================================================
# DEPLOIEMENT - SOLUTION ALTERNATIVE AFFECTATION JUGES ET PRATIQUANTS
# =============================================================================
# Ce script déploie la solution d'affectation rapide :
# - Juges aux catégories (onglet Technical Judges)
# - Pratiquants aux catégories (onglet Registrations)
#
# Alternative au drag & drop qui peut ne pas fonctionner correctement.
#
# Fonctionnalités JUGES:
# 1. Bouton "Affecter des juges" sur chaque catégorie
# 2. Modal avec liste de juges et checkboxes
# 3. Recherche de juges dans la modal
# 4. Affectation multiple en un clic
#
# Fonctionnalités PRATIQUANTS:
# 1. Bouton "Affecter des pratiquants" sur chaque catégorie (icône verte)
# 2. Modal avec liste de pratiquants et checkboxes
# 3. Filtres par genre, statut, et recherche par nom
# 4. Affectation multiple en un clic
#
# Date: 2025-12-14
# =============================================================================

set -e

echo "=============================================="
echo "=== DEPLOIEMENT - Affectation Juges + Pratiquants ==="
echo "=============================================="
echo ""

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichier à déployer
FILE="apps/competitions/templates/competitions/club/competition_management_pro.html"

echo "=== ETAPE 1: Sauvegarde de l'ancien fichier ==="
ssh ${REMOTE_HOST} "cd ${REMOTE_PATH} && cp ${FILE} ${FILE}.backup_\$(date +%Y%m%d_%H%M%S)"
echo "  Sauvegarde creee"

echo ""
echo "=== ETAPE 2: Deploiement du nouveau fichier ==="
scp "${FILE}" "${REMOTE_HOST}:${REMOTE_PATH}/${FILE}"
echo "  Fichier deploye: ${FILE}"

echo ""
echo "=== ETAPE 3: Nettoyage des caches serveur ==="
ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Supprimer __pycache__
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "  Cache Python supprime"

# Vider le cache Django
source /var/www/vhosts/martialcomp.com/venv/bin/activate
python3 manage.py shell -c "from django.core.cache import cache; cache.clear(); print('  Cache Django vide')" 2>/dev/null || echo "  Cache Django: commande executee"
deactivate 2>/dev/null || true

# Redemarrer Apache/Gunicorn
touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py
sudo systemctl restart apache2 2>/dev/null || echo "  Redemarrage Apache via sudo non disponible"
echo "  Apache redemarre (wsgi.py touche)"
EOF

echo ""
echo "=== ETAPE 4: Verification du deploiement ==="
ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "  === JUGES ==="
echo "  Recherche 'judgeAssignmentModal':"
grep -c "judgeAssignmentModal" apps/competitions/templates/competitions/club/competition_management_pro.html && echo "    OK: Modal juges trouvee" || echo "    ERREUR"

echo "  Recherche 'openJudgeAssignmentModal':"
grep -c "openJudgeAssignmentModal" apps/competitions/templates/competitions/club/competition_management_pro.html && echo "    OK: Fonction JS juges trouvee" || echo "    ERREUR"

echo ""
echo "  === PRATIQUANTS ==="
echo "  Recherche 'practitionerAssignmentModal':"
grep -c "practitionerAssignmentModal" apps/competitions/templates/competitions/club/competition_management_pro.html && echo "    OK: Modal pratiquants trouvee" || echo "    ERREUR"

echo "  Recherche 'openPractitionerAssignmentModal':"
grep -c "openPractitionerAssignmentModal" apps/competitions/templates/competitions/club/competition_management_pro.html && echo "    OK: Fonction JS pratiquants trouvee" || echo "    ERREUR"

echo "  Recherche 'btn-assign-practitioners':"
grep -c "btn-assign-practitioners" apps/competitions/templates/competitions/club/competition_management_pro.html && echo "    OK: Boutons pratiquants trouves" || echo "    ERREUR"
EOF

echo ""
echo "=============================================="
echo "=== DEPLOIEMENT SERVEUR TERMINE ==="
echo "=============================================="
echo ""
echo "Testez sur: /competitions/club/competitions/4/manage/pro/"
echo ""
echo "=== ONGLET JUGES TECHNIQUES ==="
echo "  1. Chaque categorie a un bouton '+' (icone bleue)"
echo "  2. Le bouton ouvre une modal avec la liste des juges"
echo "  3. Cochez plusieurs juges et cliquez 'Affecter'"
echo ""
echo "=== ONGLET INSCRIPTIONS (Registrations) ==="
echo "  1. Chaque categorie a un bouton '+' (icone verte)"
echo "  2. Le bouton ouvre une modal avec la liste des pratiquants"
echo "  3. Filtrez par genre, statut, ou recherchez par nom"
echo "  4. Cochez plusieurs pratiquants et cliquez 'Affecter'"
echo ""
