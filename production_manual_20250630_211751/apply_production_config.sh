#!/bin/bash
echo "🔧 APPLICATION CONFIGURATION PRODUCTION"
echo "========================================"

CURRENT_DIR=$(pwd)

# Vérifier la présence des fichiers de production
echo "🔍 Vérification des fichiers..."

REQUIRED_FILES=(
    "settings_prod.py"
    "urls_prod.py" 
    "requirements_prod.txt"
    "production_data_*.json"
)

MISSING_FILES=()
for file in "${REQUIRED_FILES[@]}"; do
    if ! ls $file 1> /dev/null 2>&1; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo "❌ Fichiers manquants:"
    printf '   - %s\n' "${MISSING_FILES[@]}"
    echo ""
    echo "📋 Suivez d'abord les instructions dans INSTRUCTIONS_MIGRATION.md"
    exit 1
fi

echo "✅ Tous les fichiers nécessaires sont présents"

# Analyser les différences
echo ""
echo "📊 Analyse des différences..."

if [ -f "settings_prod.py" ]; then
    echo "⚙️  Settings:"
    echo "   📊 Prod: $(wc -l < settings_prod.py) lignes"
    echo "   📊 Local: $(wc -l < ../config/settings.py) lignes"
fi

if [ -f "requirements_prod.txt" ]; then
    echo "📦 Requirements:"
    echo "   📊 Prod: $(wc -l < requirements_prod.txt) packages"
    echo "   📊 Local: $(wc -l < ../requirements.txt) packages"
fi

DATA_FILE=$(ls production_data_*.json | head -1)
if [ -f "$DATA_FILE" ]; then
    echo "🗄️  Données:"
    echo "   📊 Fichier: $DATA_FILE"
    echo "   📊 Taille: $(du -h "$DATA_FILE" | cut -f1)"
    echo "   📊 Objets: $(grep -o '"model":' "$DATA_FILE" | wc -l)"
fi

echo ""
read -p "🤔 Voulez-vous continuer l'application? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Application annulée"
    exit 1
fi

# Backup final avant application
echo "💾 Sauvegarde finale avant changements..."
cp ../config/settings.py ../config/settings_pre_migration.py
cp ../config/urls.py ../config/urls_pre_migration.py

# Application des configurations
echo ""
echo "🔄 Application des configurations..."

echo "   ⚙️  Settings..."
cp settings_prod.py ../config/settings.py

echo "   🔗 URLs..."
cp urls_prod.py ../config/urls.py

echo "   📦 Requirements..."
cp requirements_prod.txt ../requirements.txt

# Application des modèles si présents
if [ -d "models_prod" ]; then
    echo "   📋 Modèles..."
    cp -r models_prod/* ../competitions/models/
fi

# Application des migrations si présentes
if [ -d "migrations_prod" ]; then
    echo "   🔄 Migrations..."
    cp -r migrations_prod/* ../
fi

# Application des vues si présentes
if [ -d "views_prod" ]; then
    echo "   👁️  Vues..."
    cp -r views_prod/* ../competitions/views/
fi

# Application des templates si présents
if [ -f "templates_prod/welcome_prod.html" ]; then
    echo "   🎨 Templates..."
    cp templates_prod/welcome_prod.html ../competitions/templates/competitions/welcome.html
fi

# Application des signaux si présents
if [ -f "signals_prod.py" ]; then
    echo "   📡 Signaux..."
    cp signals_prod.py ../competitions/signals.py
fi

echo "✅ Configuration appliquée"

# Installation des requirements
echo ""
echo "📦 Installation des nouveaux requirements..."
cd ..
pip install -r requirements.txt

# Migration de la base de données
echo ""
echo "🗄️  Migration base de données..."
python3 manage.py makemigrations
python3 manage.py migrate

# Import des données
echo ""
echo "📥 Import des données production..."
cd "$CURRENT_DIR"
python3 ../manage.py loaddata "$DATA_FILE"

echo ""
echo "🎉 MIGRATION TERMINÉE"
echo "===================="
echo "✅ Configuration production appliquée"
echo "✅ Données importées"
echo ""
echo "🧪 TESTS RECOMMANDÉS:"
echo "   python3 manage.py runserver"
echo "   # Tester connexion admin"
echo "   # Tester inscription nouveaux utilisateurs"
echo "   # Tester processus onboarding"
echo ""
echo "🔙 POUR REVENIR EN ARRIÈRE:"
echo "   cp config/settings_pre_migration.py config/settings.py"
echo "   cp config/urls_pre_migration.py config/urls.py"
