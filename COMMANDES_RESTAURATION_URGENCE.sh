#!/bin/bash
# 🚨 COMMANDES DE RESTAURATION D'URGENCE
# Date : 14 Novembre 2025
# Objectif : Remettre martialcomp.com en ligne

echo "=========================================="
echo "🚨 RESTAURATION D'URGENCE - MARTIALCOMP"
echo "=========================================="
echo ""

# Connexion SSH
echo "📡 Connexion au serveur..."
ssh martialcomp-production << 'ENDSSH'

# Variables
HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"
VENV="/var/www/vhosts/martialcomp.com/venv"

cd $HTTPDOCS

echo ""
echo "=========================================="
echo "ÉTAPE 1 : SAUVEGARDE DE SÉCURITÉ"
echo "=========================================="

# Créer un backup horodaté
BACKUP_DIR="backup_urgence_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

echo "📦 Sauvegarde des fichiers actuels..."
cp config/urls.py $BACKUP_DIR/
cp apps/competitions/views/competitions.py $BACKUP_DIR/
cp apps/competitions/templates/competitions/competition/detail_enhanced.html $BACKUP_DIR/ 2>/dev/null || echo "detail_enhanced.html n'existe pas"

echo "✅ Sauvegarde créée dans : $BACKUP_DIR"

echo ""
echo "=========================================="
echo "ÉTAPE 2 : RESTAURATION DES FICHIERS"
echo "=========================================="

# Option A : Restaurer depuis les sauvegardes originales
echo "🔄 Restauration depuis les sauvegardes..."

# Restaurer URLs
if [ -f "config/urls.py.original" ]; then
    cp config/urls.py.original config/urls.py
    echo "✅ urls.py restauré depuis urls.py.original"
else
    echo "❌ urls.py.original introuvable"
fi

# Restaurer la vue
if [ -f "apps/competitions/views/competitions.py.backup_20251026_081137" ]; then
    cp apps/competitions/views/competitions.py.backup_20251026_081137 apps/competitions/views/competitions.py
    echo "✅ competitions.py restauré depuis backup du 26/10"
else
    echo "❌ Sauvegarde competitions.py introuvable"
fi

# Supprimer le template problématique
if [ -f "apps/competitions/templates/competitions/competition/detail_enhanced.html" ]; then
    rm -f apps/competitions/templates/competitions/competition/detail_enhanced.html
    echo "✅ detail_enhanced.html supprimé"
else
    echo "⚠️  detail_enhanced.html déjà absent"
fi

echo ""
echo "=========================================="
echo "ÉTAPE 3 : NETTOYAGE DU CACHE"
echo "=========================================="

echo "🧹 Nettoyage du cache Python..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -type f -name '*.pyc' -delete 2>/dev/null
echo "✅ Cache Python nettoyé"

echo ""
echo "=========================================="
echo "ÉTAPE 4 : REDÉMARRAGE DE GUNICORN"
echo "=========================================="

echo "🔄 Arrêt de Gunicorn..."
pkill -9 -f gunicorn
sleep 3

echo "🚀 Démarrage de Gunicorn..."
$VENV/bin/gunicorn \
  --workers 3 \
  --bind 127.0.0.1:8000 \
  --access-logfile logs/gunicorn_access.log \
  --error-logfile logs/gunicorn_error.log \
  --log-level info \
  config.wsgi:application \
  --daemon

sleep 5

# Vérifier le nombre de processus
GUNICORN_COUNT=$(pgrep -f "gunicorn.*config" | wc -l)
echo "📊 Processus Gunicorn actifs : $GUNICORN_COUNT"

if [ $GUNICORN_COUNT -ge 4 ]; then
    echo "✅ Gunicorn démarré correctement"
else
    echo "⚠️  Gunicorn n'a pas démarré correctement (attendu: 4-5, actuel: $GUNICORN_COUNT)"
fi

echo ""
echo "=========================================="
echo "ÉTAPE 5 : TESTS"
echo "=========================================="

echo "🧪 Test en local..."
RESPONSE=$(curl -s -H "X-Forwarded-Proto: https" -H "Host: martialcomp.com" http://127.0.0.1:8000/competition/4/ | head -50)

if echo "$RESPONSE" | grep -q "<title>"; then
    TITLE=$(echo "$RESPONSE" | grep -o "<title>.*</title>" | head -1)
    echo "✅ Site répond : $TITLE"
else
    echo "❌ Site ne répond pas correctement"
    echo "Réponse : $RESPONSE"
fi

echo ""
echo "=========================================="
echo "ÉTAPE 6 : VÉRIFICATION DES LOGS"
echo "=========================================="

echo "📋 Dernières erreurs Gunicorn :"
tail -20 logs/gunicorn_error.log | grep -i error || echo "Aucune erreur récente"

echo ""
echo "📋 Dernières erreurs Django :"
tail -20 logs/django.log | grep -i error || echo "Aucune erreur récente"

echo ""
echo "=========================================="
echo "RÉSUMÉ"
echo "=========================================="
echo ""
echo "Fichiers restaurés :"
echo "  - config/urls.py (depuis urls.py.original)"
echo "  - apps/competitions/views/competitions.py (depuis backup 26/10)"
echo "  - detail_enhanced.html (supprimé)"
echo ""
echo "Processus Gunicorn : $GUNICORN_COUNT"
echo ""
echo "🔗 Testez maintenant :"
echo "   https://martialcomp.com/competition/4/"
echo ""
echo "⚠️  Note : L'URL a changé de /competitions/4/ à /competition/4/"
echo ""

ENDSSH

echo ""
echo "=========================================="
echo "TEST DEPUIS L'EXTÉRIEUR"
echo "=========================================="

echo "🌐 Test du site public..."
sleep 5

HTTP_STATUS=$(curl -I https://martialcomp.com/competition/4/ 2>&1 | grep "HTTP/" | head -1)
echo "Status : $HTTP_STATUS"

if echo "$HTTP_STATUS" | grep -q "200"; then
    echo "✅ SITE EN LIGNE !"
elif echo "$HTTP_STATUS" | grep -q "502\|503"; then
    echo "❌ Site toujours hors ligne ($HTTP_STATUS)"
    echo ""
    echo "Actions supplémentaires nécessaires :"
    echo "1. Vérifier les logs Apache : tail -100 /var/log/apache2/error.log"
    echo "2. Redémarrer Apache : systemctl restart apache2"
    echo "3. Tester Gunicorn en mode debug (sans --daemon)"
else
    echo "⚠️  Status inattendu : $HTTP_STATUS"
fi

echo ""
echo "=========================================="
echo "FIN DE LA RESTAURATION"
echo "=========================================="
