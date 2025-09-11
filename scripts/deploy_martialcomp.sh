#!/bin/bash

echo "=== DÉPLOIEMENT MARTIALCOMP ==="
echo "Date: $(date)"
echo ""

# Variables
PROJECT_DIR="/var/www/vhosts/martialcomp.com"
VENV_DIR="$PROJECT_DIR/venv"
HTTPDOCS_DIR="$PROJECT_DIR/httpdocs"

echo "1. ACTIVATION DE L'ENVIRONNEMENT VIRTUEL..."
source $VENV_DIR/bin/activate

echo "2. NAVIGATION VERS LE PROJET..."
cd $HTTPDOCS_DIR

echo "3. VÉRIFICATION DES DÉPENDANCES..."
pip list | grep Django

echo "4. DIAGNOSTIC POSTGRESQL..."
# Exécuter le script de diagnostic
bash $HTTPDOCS_DIR/scripts/diagnostic_postgresql.sh

echo "5. CORRECTION POSTGRESQL SI NÉCESSAIRE..."
# Exécuter le script de correction
bash $HTTPDOCS_DIR/scripts/fix_postgresql.sh

echo "6. TEST DE CONNEXION BASE DE DONNÉES..."
if PGPASSWORD='martialcomp123' psql -h localhost -U martialcomp_user -d martialcomp_db -c 'SELECT 1;' >/dev/null 2>&1; then
    echo "✅ PostgreSQL fonctionne - Utilisation de la configuration PostgreSQL"
    SETTINGS_FILE="config.settings_production"
else
    echo "⚠️ PostgreSQL non disponible - Utilisation de SQLite temporaire"
    SETTINGS_FILE="config.settings_sqlite"
fi

echo "7. MIGRATIONS..."
python manage.py migrate --settings=$SETTINGS_FILE

echo "8. COLLECTE DES FICHIERS STATIQUES..."
python manage.py collectstatic --noinput --settings=$SETTINGS_FILE

echo "9. VÉRIFICATION DU PROJET..."
python manage.py check --settings=$SETTINGS_FILE

echo "10. DÉMARRAGE DU SERVEUR DE TEST..."
echo "Le serveur sera accessible sur http://martialcomp.com:8000"
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

python manage.py runserver 0.0.0.0:8000 --settings=$SETTINGS_FILE

echo ""
echo "=== FIN DU DÉPLOIEMENT ===" 