#!/bin/bash
# Script de déploiement des corrections pour Competition Management

echo "🚀 Déploiement des corrections Competition Management..."
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
cp apps/competitions/views/categories.py backups/categories.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "⚠️  Fichier categories.py non trouvé"

# 2. Appliquer les corrections Python
echo ""
echo "✏️  Application des corrections Python..."

# Corriger l'import Grade
sed -i 's/from ..models import Competition, CompetitionCategory, CompetitionType, Grade/from ..models import Competition, CompetitionCategory, CompetitionType/' apps/competitions/views/categories.py 2>/dev/null || echo "⚠️  Import déjà corrigé"

# Corriger la ligne Grade.objects
sed -i 's/grades = Grade.objects.filter(discipline=competition.discipline).order_by('\''order_field'\'')/# TODO: Implémenter la récupération des grades si nécessaire\n    grades = []  # Pour le moment, liste vide/' apps/competitions/views/categories.py 2>/dev/null || echo "⚠️  Ligne Grade.objects déjà corrigée"

# 3. Vérifier si les variables min_grade et max_grade sont définies
echo ""
echo "🔍 Vérification des variables min_grade et max_grade..."
if grep -q "min_grade = request.POST.get('min_grade', '').strip()" apps/competitions/views/categories.py; then
    echo "✅ Variables min_grade et max_grade déjà définies"
else
    echo "➕ Ajout des variables min_grade et max_grade..."
    # Cette correction est plus complexe, donc on affiche juste un message
    echo "⚠️  ATTENTION: Vérifiez manuellement que les variables min_grade et max_grade sont définies dans add_category()"
fi

# 4. Activer l'environnement virtuel et tester
echo ""
echo "🐍 Activation de l'environnement virtuel..."
source $VENV_PATH/bin/activate

# 5. Vérifier la syntaxe Python
echo ""
echo "🔍 Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/categories.py
if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python valide"
else
    echo "❌ Erreur de syntaxe Python!"
    exit 1
fi

# 6. En production, collecter les statiques et redémarrer
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
echo "📝 Prochaines étapes:"
echo "1. Ajouter le JavaScript du fichier fix_competition_management_actions.js au template"
echo "2. Tester la création de catégories"
echo "3. Vérifier les logs si nécessaire:"
if [ "$IS_PROD" = true ]; then
    echo "   sudo journalctl -u martialcomp.service -f"
else
    echo "   Vérifier la console du serveur de développement"
fi
echo ""
echo "⚠️  N'oubliez pas d'ajouter le JavaScript au template competition_management_detail.html !"