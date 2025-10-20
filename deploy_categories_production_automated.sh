#!/bin/bash
# Script automatisé de déploiement des corrections de catégories en production
# Ce script applique toutes les corrections nécessaires automatiquement

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement automatisé des corrections de catégories"
echo "======================================================="
echo "Date: $(date)"
echo ""

# Vérifier qu'on est bien en production
if [[ "$HOSTNAME" != "vigilant-swartz" ]] && [[ ! -d "/var/www/vhosts/martialcomp.com" ]]; then
    echo "❌ ERREUR: Ce script doit être exécuté sur le serveur de production!"
    echo "Hostname actuel: $HOSTNAME"
    exit 1
fi

echo "✅ Environnement de production confirmé"

# Variables
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"
BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"

# Naviguer vers le projet
cd $PROJECT_DIR

# Créer le dossier de backup
echo ""
echo "📦 Création des backups dans $BACKUP_DIR..."
mkdir -p $BACKUP_DIR

# Sauvegarder les fichiers
cp apps/competitions/views/categories.py $BACKUP_DIR/categories.py.backup
cp apps/competitions/urls/competitions.py $BACKUP_DIR/competitions_urls.py.backup
cp apps/competitions/templates/competitions/club/competition_management_detail.html $BACKUP_DIR/competition_management_detail.html.backup
echo "✅ Backups créés"

# Activer l'environnement virtuel
echo ""
echo "🐍 Activation de l'environnement virtuel..."
source $VENV_PATH/bin/activate

# 1. Corriger categories.py
echo ""
echo "📝 Mise à jour de categories.py..."

# Vérifier si l'import Grade existe déjà
if ! grep -q "from apps.grades.models import Grade" apps/competitions/views/categories.py; then
    # Ajouter l'import après la ligne des imports de models
    sed -i '/from ..models import Competition, CompetitionCategory, CompetitionType/a from apps.grades.models import Grade' apps/competitions/views/categories.py
    echo "✅ Import Grade ajouté"
else
    echo "✅ Import Grade déjà présent"
fi

# Vérifier si la fonction get_discipline_grades existe
if ! grep -q "def get_discipline_grades" apps/competitions/views/categories.py; then
    echo "➕ Ajout de la fonction get_discipline_grades..."
    cat >> apps/competitions/views/categories.py << 'EOF'


@login_required
def get_discipline_grades(request, competition_id):
    """Récupérer les grades disponibles pour la discipline d'une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        # Récupérer les grades pour la discipline
        grades = Grade.objects.filter(discipline=competition.discipline).order_by('order_field')
        
        # Formatter les grades pour le JSON
        grades_data = []
        for grade in grades:
            grades_data.append({
                'id': grade.id,
                'name': grade.name,
                'color': grade.color if hasattr(grade, 'color') else None,
                'order': grade.order_field
            })
        
        return JsonResponse({
            'success': True,
            'grades': grades_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })
EOF
    echo "✅ Fonction get_discipline_grades ajoutée"
else
    echo "✅ Fonction get_discipline_grades déjà présente"
fi

# 2. Corriger les URLs
echo ""
echo "📝 Mise à jour des URLs..."

# Mettre à jour l'import
sed -i 's/from apps.competitions.views.categories import (/from apps.competitions.views.categories import (\n    competition_categories, add_category, delete_category, get_discipline_grades/' apps/competitions/urls/competitions.py 2>/dev/null || \
sed -i 's/competition_categories, add_category, delete_category/competition_categories, add_category, delete_category, get_discipline_grades/' apps/competitions/urls/competitions.py

# Ajouter la route si elle n'existe pas
if ! grep -q "get_discipline_grades" apps/competitions/urls/competitions.py; then
    sed -i "/path('<int:competition_id>\/categories\/delete\/', delete_category, name='delete_category_detailed'),/a\    path('<int:competition_id>/api/grades/', get_discipline_grades, name='get_discipline_grades')," apps/competitions/urls/competitions.py
    echo "✅ Route API grades ajoutée"
else
    echo "✅ Route API grades déjà présente"
fi

# 3. Vérifier la syntaxe Python
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
    echo "❌ Erreur de syntaxe dans competitions.py!"
    exit 1
fi

# 4. Collecter les fichiers statiques
echo ""
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --settings=config.settings.production

# 5. Redémarrer le service
echo ""
echo "🔄 Redémarrage du service martialcomp..."
sudo systemctl restart martialcomp.service

# 6. Attendre et vérifier
sleep 3
echo ""
echo "📊 Vérification du statut du service..."
if sudo systemctl is-active --quiet martialcomp.service; then
    echo "✅ Service martialcomp actif et fonctionnel"
    sudo systemctl status martialcomp.service --no-pager | head -n 10
else
    echo "❌ ERREUR: Le service martialcomp ne démarre pas!"
    echo "Consultez les logs avec: sudo journalctl -u martialcomp.service -n 100"
    exit 1
fi

echo ""
echo "======================================================="
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo ""
echo "⚠️  IMPORTANT: Le template HTML doit être modifié manuellement"
echo "    car il contient du code JavaScript complexe."
echo ""
echo "📝 Modifications à faire dans le template:"
echo "1. Remplacer les inputs text des grades par des selects"
echo "2. Ajouter le JavaScript de gestion AJAX"
echo ""
echo "📄 Instructions complètes dans:"
echo "   DEPLOIEMENT_PRODUCTION_CATEGORIES_COMPLET.md"
echo ""
echo "🧪 Pour tester:"
echo "1. https://martialcomp.com/fr/competitions/club/competitions/[ID]/manage/"
echo "2. Cliquer sur 'Ajouter une catégorie'"
echo "3. Vérifier que les grades se chargent"
echo ""
echo "📊 Logs en temps réel:"
echo "   sudo journalctl -u martialcomp.service -f"
echo ""
echo "🔙 En cas de problème, les backups sont dans:"
echo "   $BACKUP_DIR"