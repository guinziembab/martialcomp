#!/bin/bash
# Script de déploiement FORCÉ pour corriger le template liste_poules.html
# Ce script effectue un déploiement complet avec vérifications

set -e  # Arrêter en cas d'erreur

echo "=============================================="
echo "=== DÉPLOIEMENT FORCÉ liste_poules.html ==="
echo "=============================================="
echo "Date: $(date)"
echo ""

# Variables
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"

# Fichiers à déployer
TEMPLATE_LOCAL="apps/competitions/templates/competitions/combat/liste_poules.html"
TEMPLATE_REMOTE="${REMOTE_PATH}/apps/competitions/templates/competitions/combat/liste_poules.html"
VIEW_LOCAL="apps/competitions/views/combat.py"
VIEW_REMOTE="${REMOTE_PATH}/apps/competitions/views/combat.py"
URLS_LOCAL="apps/competitions/urls/combat.py"
URLS_REMOTE="${REMOTE_PATH}/apps/competitions/urls/combat.py"

echo "=== ÉTAPE 1: Diagnostic pré-déploiement ==="
echo ""

ssh ${REMOTE_HOST} << 'EOF'
echo "1.1 Recherche de tous les fichiers liste_poules.html sur le serveur..."
find /var/www/vhosts/martialcomp.com -name "liste_poules.html" -type f 2>/dev/null || echo "Aucun fichier trouvé"

echo ""
echo "1.2 Vérification du contenu actuel du template (recherche fa-magic)..."
grep -c "fa-magic" /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_poules.html 2>/dev/null || echo "fa-magic NON TROUVÉ (ancien template)"

echo ""
echo "1.3 Vérification du modal generatePoolsModal..."
grep -c "generatePoolsModal" /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/combat/liste_poules.html 2>/dev/null || echo "generatePoolsModal NON TROUVÉ (ancien template)"

echo ""
echo "1.4 Vérification de la configuration Django TEMPLATES..."
grep -A 20 "TEMPLATES = \[" /var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py 2>/dev/null | head -25 || echo "Fichier production.py non trouvé, vérification de base.py"
grep -A 20 "TEMPLATES = \[" /var/www/vhosts/martialcomp.com/httpdocs/config/settings/base.py 2>/dev/null | head -25

echo ""
echo "1.5 Vérification des loaders de template (cache?)..."
grep -i "cached.Loader\|filesystem.Loader" /var/www/vhosts/martialcomp.com/httpdocs/config/settings/*.py 2>/dev/null || echo "Pas de loader caché explicite"
EOF

echo ""
echo "=== ÉTAPE 2: Sauvegarde et déploiement des fichiers ==="
echo ""

# Sauvegarde sur le serveur distant
echo "2.1 Création de sauvegardes sur le serveur..."
ssh ${REMOTE_HOST} << EOF
# Créer un dossier de backup
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups/\$(date +%Y%m%d_%H%M%S)"
mkdir -p \${BACKUP_DIR}

# Sauvegarder les fichiers existants
cp -f ${TEMPLATE_REMOTE} \${BACKUP_DIR}/ 2>/dev/null || echo "Pas de template existant à sauvegarder"
cp -f ${VIEW_REMOTE} \${BACKUP_DIR}/ 2>/dev/null || echo "Pas de vue existante à sauvegarder"
cp -f ${URLS_REMOTE} \${BACKUP_DIR}/ 2>/dev/null || echo "Pas d'urls existant à sauvegarder"

echo "Sauvegardes créées dans: \${BACKUP_DIR}"
ls -la \${BACKUP_DIR}/
EOF

echo ""
echo "2.2 Copie des nouveaux fichiers..."

# Copier les fichiers
echo "  - Template liste_poules.html..."
scp ${TEMPLATE_LOCAL} ${REMOTE_HOST}:${TEMPLATE_REMOTE}

echo "  - Vue combat.py..."
scp ${VIEW_LOCAL} ${REMOTE_HOST}:${VIEW_REMOTE}

echo "  - URLs combat.py..."
scp ${URLS_LOCAL} ${REMOTE_HOST}:${URLS_REMOTE}

echo ""
echo "=== ÉTAPE 3: Nettoyage des caches ==="
echo ""

ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "3.1 Suppression COMPLÈTE de tous les fichiers __pycache__..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
echo "   Cache Python supprimé"

echo ""
echo "3.2 Vider le cache Django..."
source /var/www/vhosts/martialcomp.com/venv/bin/activate

python manage.py shell -c "
from django.core.cache import cache
from django.template.loader import engines
try:
    cache.clear()
    print('   Cache Django vidé')
except Exception as e:
    print(f'   Erreur cache: {e}')

# Réinitialiser les loaders de templates
for engine in engines.all():
    try:
        if hasattr(engine, 'engine'):
            eng = engine.engine
            if hasattr(eng, 'template_loaders'):
                for loader in eng.template_loaders:
                    if hasattr(loader, 'reset'):
                        loader.reset()
                        print('   Loader réinitialisé')
    except Exception as e:
        print(f'   Note loader: {e}')
" 2>/dev/null || echo "   Commande shell exécutée"

deactivate 2>/dev/null || true
EOF

echo ""
echo "=== ÉTAPE 4: Redémarrage des services ==="
echo ""

ssh ${REMOTE_HOST} << 'EOF'
echo "4.1 Touch du fichier wsgi.py (reload mod_wsgi)..."
touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py
touch /var/www/vhosts/martialcomp.com/httpdocs/martialcomp/wsgi.py 2>/dev/null || true

echo "4.2 Redémarrage d'Apache..."
sudo systemctl restart apache2 2>/dev/null || sudo service apache2 restart 2>/dev/null || echo "Impossible de redémarrer Apache (peut nécessiter des droits root)"

sleep 2

echo "4.3 Vérification du statut Apache..."
sudo systemctl status apache2 --no-pager 2>/dev/null | head -5 || service apache2 status 2>/dev/null | head -5 || echo "Statut Apache indisponible"
EOF

echo ""
echo "=== ÉTAPE 5: Vérification post-déploiement ==="
echo ""

ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "5.1 Vérification du contenu du template déployé..."
echo "   Recherche 'fa-magic':"
grep -n "fa-magic" apps/competitions/templates/competitions/combat/liste_poules.html | head -5

echo ""
echo "   Recherche 'generatePoolsModal':"
grep -n "generatePoolsModal" apps/competitions/templates/competitions/combat/liste_poules.html | head -5

echo ""
echo "   Recherche 'supprimer_poules_categorie':"
grep -n "supprimer_poules_categorie" apps/competitions/templates/competitions/combat/liste_poules.html | head -3

echo ""
echo "5.2 Vérification de la vue combat.py..."
echo "   Recherche 'def supprimer_poules_categorie':"
grep -n "def supprimer_poules_categorie" apps/competitions/views/combat.py | head -1

echo ""
echo "5.3 Vérification des URLs..."
echo "   Recherche 'supprimer_poules_categorie':"
grep -n "supprimer_poules_categorie" apps/competitions/urls/combat.py | head -2

echo ""
echo "5.4 Affichage des lignes clés du template (bouton Générer)..."
sed -n '555,560p' apps/competitions/templates/competitions/combat/liste_poules.html
EOF

echo ""
echo "=============================================="
echo "=== DÉPLOIEMENT TERMINÉ ==="
echo "=============================================="
echo ""
echo "ACTIONS À EFFECTUER MANUELLEMENT:"
echo "1. Ouvrir un navigateur en mode privé/incognito"
echo "2. Vider le cache du navigateur (Ctrl+Shift+Delete)"
echo "3. Aller sur la page des poules"
echo "4. Vérifier que:"
echo "   - Le bouton affiche l'icône baguette magique (fa-magic)"
echo "   - Un clic sur 'Générer automatiquement' ouvre un MODAL (pas un confirm)"
echo "   - Chaque catégorie a un bouton poubelle (rouge) pour la supprimer"
echo ""
echo "Si le problème persiste, vérifier:"
echo "   - Qu'il n'y a pas de reverse proxy ou CDN qui cache le HTML"
echo "   - Les logs Apache: /var/log/apache2/error.log"
echo ""
