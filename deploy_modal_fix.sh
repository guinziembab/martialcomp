#!/bin/bash
# Script de déploiement pour corriger le modal de génération des poules
# Ce script doit être exécuté depuis le serveur local

echo "=== Déploiement du correctif Modal Génération Poules ==="
echo "Date: $(date)"
echo ""

# Variables
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"

# Étape 1: Copier les fichiers modifiés
echo "=== Étape 1: Copie des fichiers ==="

# Template liste_poules.html
echo "Copie de liste_poules.html..."
scp apps/competitions/templates/competitions/combat/liste_poules.html \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/combat/

# Vue combat.py
echo "Copie de combat.py..."
scp apps/competitions/views/combat.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/

echo ""
echo "=== Étape 2: Vider tous les caches sur le serveur ==="

ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Suppression du cache Python (__pycache__)..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "2. Vérification du fichier déployé..."
grep -c "generatePoolsModal" apps/competitions/templates/competitions/combat/liste_poules.html
grep "fa-magic" apps/competitions/templates/competitions/combat/liste_poules.html | head -3

echo "3. Suppression du cache Django (si configuré)..."
# Vider le cache Django via management command si disponible
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Essayer de vider le cache Django
python manage.py shell -c "
from django.core.cache import cache
try:
    cache.clear()
    print('Cache Django vidé avec succès')
except Exception as e:
    print(f'Erreur cache Django: {e}')
" 2>/dev/null || echo "Pas de cache Django ou commande non disponible"

echo "4. Touch du fichier wsgi.py pour forcer le rechargement..."
touch config/wsgi.py
touch martialcomp/wsgi.py 2>/dev/null || true

echo "5. Vérification de la configuration Apache..."
# Vérifier si mod_wsgi est utilisé
apache2ctl -M 2>/dev/null | grep wsgi || echo "mod_wsgi peut ne pas être listé"

EOF

echo ""
echo "=== Étape 3: Redémarrage d'Apache ==="
ssh ${REMOTE_HOST} "sudo systemctl restart apache2 && echo 'Apache redémarré avec succès' || sudo service apache2 restart"

echo ""
echo "=== Étape 4: Vérification finale ==="
ssh ${REMOTE_HOST} << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "Contenu des premières lignes contenant 'generatePoolsModal':"
grep -n "generatePoolsModal" apps/competitions/templates/competitions/combat/liste_poules.html | head -5

echo ""
echo "Contenu autour du bouton (lignes 530-535):"
sed -n '530,535p' apps/competitions/templates/competitions/combat/liste_poules.html

echo ""
echo "Status Apache:"
sudo systemctl status apache2 --no-pager | head -10
EOF

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "IMPORTANT: Testez maintenant dans un navigateur en navigation privée:"
echo "1. Videz le cache du navigateur (Ctrl+Shift+Delete)"
echo "2. Ouvrez en mode navigation privée"
echo "3. Allez sur la page des poules"
echo "4. Vérifiez que le bouton affiche 'fa-magic' (baguette magique) et non 'fa-pencil'"
echo "5. Cliquez sur 'Générer automatiquement' - le modal doit s'ouvrir"
