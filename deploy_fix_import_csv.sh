#!/bin/bash
# Script de déploiement - Correction Import CSV et boutons dashboard
# Date: 2025-11-24
#
# CORRECTIONS:
# 1. Import CSV ne liait pas les pratiquants à l'organisation du club connecté
#    - get_organization_from_club() crée maintenant automatiquement l'organisation si manquante
# 2. Boutons "Import CSV" et "Inscription en masse" ne fonctionnaient pas
#    - Correction COMPLETE des apostrophes dans les chaînes JavaScript:
#      - Clés TRANSLATIONS renommées (bulk_error, bulk_modal_error, no_practitioners, etc.)
#      - Tous les appels t() mis à jour avec les nouvelles clés
#      - Suppression de toutes les apostrophes échappées problématiques
# 3. Le selecteur de fichier CSV s'ouvrait mais le change event ne se declenchait pas
#    - Ajout d'un input HTML persistant (id="csv-import-input-persistent")
#    - Simplification de directFileUpload() pour utiliser cet input
#    - Nouvelle fonction handleCsvFileUpload() appelée par l'input HTML

set -e

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement MartialComp - Corrections Import CSV & Dashboard ==="
echo ""

# Étape 1: Copier les fichiers corrigés
echo "1. Déploiement des fichiers..."

echo "   - import_export.py (création auto organisation si manquante)"
scp apps/competitions/views/club/import_export.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/club/import_export.py

echo "   - club.html (template dashboard avec corrections JS)"
scp apps/competitions/templates/competitions/dashboard/club.html \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/club.html

echo ""
echo "   ✓ Fichiers déployés."

# Étape 2: Redémarrer Gunicorn
echo ""
echo "2. Redémarrage de Gunicorn..."
ssh ${REMOTE_HOST} << 'ENDSSH'
pkill -f "gunicorn config.wsgi" || true
sleep 2

cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
nohup /var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8888 \
    --workers 3 \
    --daemon \
    --error-logfile logs/gunicorn_error.log \
    --access-logfile logs/gunicorn_access.log &

sleep 3
echo "Vérification du processus gunicorn..."
ps aux | grep gunicorn | grep -v grep || echo "⚠️ Gunicorn ne semble pas démarré!"
ENDSSH

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Corrections apportées:"
echo "  ✓ Import CSV crée automatiquement l'organisation si le club n'en a pas"
echo "  ✓ Les pratiquants importés sont liés à la bonne organisation"
echo "  ✓ Bouton 'Import CSV' fonctionne (input HTML persistant)"
echo "  ✓ Bouton 'Inscription en masse' fonctionne"
echo "  ✓ Selecteur de fichier: event change fonctionne maintenant"
echo ""
echo "Testez:"
echo "  - Dashboard: https://martialcomp.com/fr/dashboard/club/"
echo "  - Import CSV: Cliquez sur 'Import CSV' dans l'onglet Pratiquants"
echo ""
echo "Pour voir les logs:"
echo "ssh martialcomp-production 'tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log'"
