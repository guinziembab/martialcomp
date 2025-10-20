#!/bin/bash
# Script de déploiement des corrections pour les catégories de compétition
# Corrige: 
# 1. L'affichage JSON brut lors de la création de catégorie
# 2. La sélection des grades (remplace les inputs text par des dropdowns)

echo "🚀 Déploiement des corrections pour les catégories de compétition..."
echo "Date: $(date)"
echo "================================================"

# Vérifier si on est en production
if [[ "$HOSTNAME" == "vigilant-swartz" ]] || [[ -d "/var/www/vhosts/martialcomp.com" ]]; then
    echo "✅ Environnement de production détecté"
    PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
    VENV_PATH="/var/www/vhosts/martialcomp.com/venv"
    IS_PROD=true
else
    echo "🔧 Environnement de développement détecté"
    PROJECT_DIR="$(pwd)"
    VENV_PATH="venv_regen"
    IS_PROD=false
fi

cd $PROJECT_DIR

# 1. Backup des fichiers
echo ""
echo "📦 Création des backups..."
mkdir -p backups
cp apps/competitions/views/categories.py backups/categories.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null
cp apps/competitions/urls/competitions.py backups/competitions_urls.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null
cp apps/competitions/templates/competitions/club/competition_management_detail.html backups/competition_management_detail.html.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null

# 2. Activer l'environnement virtuel
echo ""
echo "🐍 Activation de l'environnement virtuel..."
source $VENV_PATH/bin/activate

# 3. Vérifier la syntaxe Python des fichiers modifiés
echo ""
echo "🔍 Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/categories.py
if [ $? -eq 0 ]; then
    echo "✅ categories.py - Syntaxe valide"
else
    echo "❌ Erreur de syntaxe dans categories.py!"
    exit 1
fi

python -m py_compile apps/competitions/urls/competitions.py
if [ $? -eq 0 ]; then
    echo "✅ competitions.py (urls) - Syntaxe valide"
else
    echo "❌ Erreur de syntaxe dans competitions.py (urls)!"
    exit 1
fi

# 4. En production, collecter les statiques et redémarrer
if [ "$IS_PROD" = true ]; then
    echo ""
    echo "📁 Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput --settings=config.settings.production
    
    echo ""
    echo "🔄 Redémarrage du service..."
    sudo systemctl restart martialcomp.service
    
    echo ""
    echo "📊 Vérification du service..."
    sleep 3
    sudo systemctl status martialcomp.service --no-pager | head -n 10
fi

echo ""
echo "================================================"
echo "✅ Déploiement terminé!"
echo ""
echo "📝 Corrections appliquées:"
echo "1. ✅ JavaScript AJAX pour gérer la soumission du formulaire de catégorie"
echo "2. ✅ Affichage de messages de succès/erreur dans l'interface (plus de JSON brut)"
echo "3. ✅ Endpoint API pour récupérer les grades de la discipline"
echo "4. ✅ Dropdowns de sélection de grades (remplace les inputs text)"
echo "5. ✅ Chargement dynamique des grades à l'ouverture du modal"
echo ""
echo "🧪 Pour tester:"
echo "1. Accédez à la page de gestion d'une compétition"
echo "2. Cliquez sur 'Ajouter une catégorie'"
echo "3. Vérifiez que les grades se chargent dans les dropdowns"
echo "4. Créez une catégorie et vérifiez l'affichage du message de succès"
echo ""
if [ "$IS_PROD" = true ]; then
    echo "📊 Logs de production:"
    echo "   sudo journalctl -u martialcomp.service -f"
else
    echo "📊 Logs de développement:"
    echo "   Vérifier la console du serveur de développement"
fi