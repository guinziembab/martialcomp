#!/bin/bash
"""
Script complet pour rapatrier TOUTE la production en local
"""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROD_BACKUP_DIR="production_complete_$TIMESTAMP"

echo "🚀 MIGRATION PRODUCTION COMPLÈTE → LOCAL - $TIMESTAMP"
echo "=================================================="

# Créer répertoire pour les imports
mkdir -p "$PROD_BACKUP_DIR"

echo "📁 Répertoire d'import: $PROD_BACKUP_DIR"

# Demander les informations de connexion
echo ""
echo "🔑 CONFIGURATION CONNEXION SSH"
echo "=============================="
read -p "Adresse du serveur (ex: user@server.com): " PROD_SERVER
read -p "Chemin du projet sur le serveur (ex: /home/user/martialcomp): " PROD_PATH

echo ""
echo "🔍 Test de connexion au serveur de production..."

# Vérifier la connexion SSH
if ! ssh -o ConnectTimeout=10 "$PROD_SERVER" "echo 'Connexion SSH réussie'"; then
    echo "❌ Impossible de se connecter au serveur de production"
    echo "   Vérifiez votre configuration SSH et vos clés"
    exit 1
fi

echo "✅ Connexion SSH établie avec succès"

# Vérifier que le chemin du projet existe
if ! ssh "$PROD_SERVER" "[ -d '$PROD_PATH' ]"; then
    echo "❌ Le chemin $PROD_PATH n'existe pas sur le serveur"
    exit 1
fi

echo "✅ Projet trouvé sur le serveur"

# Vérifier que c'est bien un projet Django
if ! ssh "$PROD_SERVER" "[ -f '$PROD_PATH/manage.py' ]"; then
    echo "❌ Pas de fichier manage.py trouvé. Ce n'est pas un projet Django ?"
    exit 1
fi

echo "✅ Projet Django confirmé"

echo ""
echo "📦 RÉCUPÉRATION COMPLÈTE DE LA PRODUCTION"
echo "========================================="

# 1. Configuration Django
echo "⚙️  Configuration Django..."
scp "$PROD_SERVER:$PROD_PATH/config/settings.py" "$PROD_BACKUP_DIR/settings_prod.py"
scp "$PROD_SERVER:$PROD_PATH/config/urls.py" "$PROD_BACKUP_DIR/urls_prod.py"
scp "$PROD_SERVER:$PROD_PATH/config/wsgi.py" "$PROD_BACKUP_DIR/wsgi_prod.py" 2>/dev/null || true
echo "   ✅ Configuration récupérée"

# 2. Requirements et dépendances
echo "📦 Requirements et dépendances..."
scp "$PROD_SERVER:$PROD_PATH/requirements.txt" "$PROD_BACKUP_DIR/requirements_prod.txt"
scp "$PROD_SERVER:$PROD_PATH/requirements*.txt" "$PROD_BACKUP_DIR/" 2>/dev/null || true
echo "   ✅ Requirements récupérés"

# 3. Modèles Django COMPLETS
echo "📋 Modèles Django complets..."
mkdir -p "$PROD_BACKUP_DIR/models_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/models/" "$PROD_BACKUP_DIR/models_prod/competitions/"
scp -r "$PROD_SERVER:$PROD_PATH/grades/models/" "$PROD_BACKUP_DIR/models_prod/grades/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/finances/models/" "$PROD_BACKUP_DIR/models_prod/finances/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/organizations/models/" "$PROD_BACKUP_DIR/models_prod/organizations/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/shop/models/" "$PROD_BACKUP_DIR/models_prod/shop/" 2>/dev/null || true
echo "   ✅ Tous les modèles récupérés"

# 4. Vues Django COMPLÈTES
echo "👁️  Vues Django complètes..."
mkdir -p "$PROD_BACKUP_DIR/views_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/views/" "$PROD_BACKUP_DIR/views_prod/competitions/"
scp -r "$PROD_SERVER:$PROD_PATH/grades/views/" "$PROD_BACKUP_DIR/views_prod/grades/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/finances/views/" "$PROD_BACKUP_DIR/views_prod/finances/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/organizations/views/" "$PROD_BACKUP_DIR/views_prod/organizations/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/shop/views/" "$PROD_BACKUP_DIR/views_prod/shop/" 2>/dev/null || true
echo "   ✅ Toutes les vues récupérées"

# 5. Formulaires Django COMPLETS
echo "📝 Formulaires Django complets..."
mkdir -p "$PROD_BACKUP_DIR/forms_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/forms/" "$PROD_BACKUP_DIR/forms_prod/competitions/"
scp -r "$PROD_SERVER:$PROD_PATH/grades/forms/" "$PROD_BACKUP_DIR/forms_prod/grades/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/finances/forms/" "$PROD_BACKUP_DIR/forms_prod/finances/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/organizations/forms/" "$PROD_BACKUP_DIR/forms_prod/organizations/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/shop/forms/" "$PROD_BACKUP_DIR/forms_prod/shop/" 2>/dev/null || true
echo "   ✅ Tous les formulaires récupérés"

# 6. Templates COMPLETS
echo "🎨 Templates complets..."
mkdir -p "$PROD_BACKUP_DIR/templates_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/templates/" "$PROD_BACKUP_DIR/templates_prod/competitions/"
scp -r "$PROD_SERVER:$PROD_PATH/grades/templates/" "$PROD_BACKUP_DIR/templates_prod/grades/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/finances/templates/" "$PROD_BACKUP_DIR/templates_prod/finances/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/organizations/templates/" "$PROD_BACKUP_DIR/templates_prod/organizations/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/shop/templates/" "$PROD_BACKUP_DIR/templates_prod/shop/" 2>/dev/null || true
echo "   ✅ Tous les templates récupérés"

# 7. Migrations COMPLÈTES
echo "🔄 Migrations complètes..."
mkdir -p "$PROD_BACKUP_DIR/migrations_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/migrations/" "$PROD_BACKUP_DIR/migrations_prod/competitions/"
scp -r "$PROD_SERVER:$PROD_PATH/grades/migrations/" "$PROD_BACKUP_DIR/migrations_prod/grades/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/finances/migrations/" "$PROD_BACKUP_DIR/migrations_prod/finances/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/organizations/migrations/" "$PROD_BACKUP_DIR/migrations_prod/organizations/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/shop/migrations/" "$PROD_BACKUP_DIR/migrations_prod/shop/" 2>/dev/null || true
echo "   ✅ Toutes les migrations récupérées"

# 8. URLs COMPLÈTES
echo "🔗 URLs complètes..."
mkdir -p "$PROD_BACKUP_DIR/urls_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/urls/" "$PROD_BACKUP_DIR/urls_prod/competitions/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/grades/urls/" "$PROD_BACKUP_DIR/urls_prod/grades/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/finances/urls/" "$PROD_BACKUP_DIR/urls_prod/finances/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/organizations/urls/" "$PROD_BACKUP_DIR/urls_prod/organizations/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/shop/urls/" "$PROD_BACKUP_DIR/urls_prod/shop/" 2>/dev/null || true
echo "   ✅ Toutes les URLs récupérées"

# 9. Signaux et Apps COMPLETS
echo "📡 Signaux et Apps..."
scp "$PROD_SERVER:$PROD_PATH/competitions/signals.py" "$PROD_BACKUP_DIR/signals_competitions_prod.py" 2>/dev/null || true
scp "$PROD_SERVER:$PROD_PATH/grades/signals.py" "$PROD_BACKUP_DIR/signals_grades_prod.py" 2>/dev/null || true
scp "$PROD_SERVER:$PROD_PATH/organizations/signals.py" "$PROD_BACKUP_DIR/signals_organizations_prod.py" 2>/dev/null || true
scp "$PROD_SERVER:$PROD_PATH/competitions/apps.py" "$PROD_BACKUP_DIR/apps_competitions_prod.py" 2>/dev/null || true
scp "$PROD_SERVER:$PROD_PATH/grades/apps.py" "$PROD_BACKUP_DIR/apps_grades_prod.py" 2>/dev/null || true
echo "   ✅ Signaux et Apps récupérés"

# 10. Middleware et Utils
echo "🔧 Middleware et utilitaires..."
mkdir -p "$PROD_BACKUP_DIR/utils_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/middleware/" "$PROD_BACKUP_DIR/utils_prod/middleware/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/competitions/utils/" "$PROD_BACKUP_DIR/utils_prod/utils/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/competitions/templatetags/" "$PROD_BACKUP_DIR/utils_prod/templatetags/" 2>/dev/null || true
echo "   ✅ Utilitaires récupérés"

# 11. Fichiers statiques et media (échantillon)
echo "🎯 Fichiers statiques (échantillon)..."
mkdir -p "$PROD_BACKUP_DIR/static_media_sample"
ssh "$PROD_SERVER" "find $PROD_PATH -name 'static' -type d" > "$PROD_BACKUP_DIR/static_directories.txt" 2>/dev/null || true
ssh "$PROD_SERVER" "find $PROD_PATH -name 'media' -type d" > "$PROD_BACKUP_DIR/media_directories.txt" 2>/dev/null || true
echo "   ✅ Répertoires statiques listés"

# 12. SAUVEGARDE COMPLÈTE DES DONNÉES
echo "🗄️  Sauvegarde complète des données..."
echo "   📊 Création dump Django..."
ssh "$PROD_SERVER" "cd $PROD_PATH && python3 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > production_data_complete_$TIMESTAMP.json"

echo "   📊 Création dump avec auth..."
ssh "$PROD_SERVER" "cd $PROD_PATH && python3 manage.py dumpdata --natural-foreign --natural-primary > production_data_with_auth_$TIMESTAMP.json"

echo "   📊 Récupération dumps..."
scp "$PROD_SERVER:$PROD_PATH/production_data_complete_$TIMESTAMP.json" "$PROD_BACKUP_DIR/"
scp "$PROD_SERVER:$PROD_PATH/production_data_with_auth_$TIMESTAMP.json" "$PROD_BACKUP_DIR/"

echo "   📊 Apps spécifiques..."
ssh "$PROD_SERVER" "cd $PROD_PATH && python3 manage.py dumpdata competitions > production_competitions_$TIMESTAMP.json"
ssh "$PROD_SERVER" "cd $PROD_PATH && python3 manage.py dumpdata auth.User > production_users_$TIMESTAMP.json"
scp "$PROD_SERVER:$PROD_PATH/production_competitions_$TIMESTAMP.json" "$PROD_BACKUP_DIR/" 2>/dev/null || true
scp "$PROD_SERVER:$PROD_PATH/production_users_$TIMESTAMP.json" "$PROD_BACKUP_DIR/" 2>/dev/null || true

echo "   ✅ Toutes les données récupérées"

# 13. Informations système de production
echo "🔍 Informations système production..."
ssh "$PROD_SERVER" "cd $PROD_PATH && python3 --version" > "$PROD_BACKUP_DIR/python_version_prod.txt"
ssh "$PROD_SERVER" "cd $PROD_PATH && pip freeze" > "$PROD_BACKUP_DIR/pip_freeze_prod.txt"
ssh "$PROD_SERVER" "cd $PROD_PATH && python3 manage.py showmigrations" > "$PROD_BACKUP_DIR/migrations_status_prod.txt" 2>/dev/null || true
ssh "$PROD_SERVER" "uname -a" > "$PROD_BACKUP_DIR/system_info_prod.txt"
echo "   ✅ Informations système récupérées"

# 14. Nettoyer les fichiers temporaires sur le serveur
echo "🧹 Nettoyage serveur production..."
ssh "$PROD_SERVER" "cd $PROD_PATH && rm -f production_data_*_$TIMESTAMP.json production_competitions_$TIMESTAMP.json production_users_$TIMESTAMP.json"
echo "   ✅ Fichiers temporaires supprimés"

# 15. Créer un résumé complet
echo "📊 Création résumé complet..."
cat > "$PROD_BACKUP_DIR/MIGRATION_SUMMARY_$TIMESTAMP.md" << EOF
# Migration Production Complète - $TIMESTAMP

## 🎯 Source
- **Serveur**: $PROD_SERVER
- **Chemin**: $PROD_PATH
- **Date**: $(date)

## 📦 Contenu récupéré

### Configuration
- \`settings_prod.py\` - Configuration Django production
- \`urls_prod.py\` - URLs principales
- \`wsgi_prod.py\` - Configuration WSGI
- \`requirements_prod.txt\` - Dépendances Python

### Code Applicatif
- \`models_prod/\` - Tous les modèles Django
- \`views_prod/\` - Toutes les vues
- \`forms_prod/\` - Tous les formulaires
- \`templates_prod/\` - Tous les templates
- \`urls_prod/\` - Toutes les URLs
- \`utils_prod/\` - Middleware et utilitaires

### Base de données
- \`production_data_complete_$TIMESTAMP.json\` - Données complètes (sans auth system)
- \`production_data_with_auth_$TIMESTAMP.json\` - Données avec auth
- \`production_competitions_$TIMESTAMP.json\` - Données competitions
- \`production_users_$TIMESTAMP.json\` - Utilisateurs

### Système
- \`migrations_prod/\` - Toutes les migrations
- \`python_version_prod.txt\` - Version Python production
- \`pip_freeze_prod.txt\` - Packages installés
- \`migrations_status_prod.txt\` - État des migrations
- \`system_info_prod.txt\` - Info système

## 📊 Statistiques

- **Répertoires copiés**: $(find $PROD_BACKUP_DIR -type d | wc -l)
- **Fichiers copiés**: $(find $PROD_BACKUP_DIR -type f | wc -l)
- **Taille totale**: $(du -sh $PROD_BACKUP_DIR | cut -f1)

## 🚀 Application

Pour appliquer cette configuration :

\`\`\`bash
cd $PROD_BACKUP_DIR
chmod +x apply_complete_production.sh
./apply_complete_production.sh
\`\`\`

## 🔙 Restauration

En cas de problème :

\`\`\`bash
./restore_dev_backup.sh
\`\`\`
EOF

# 16. Créer script d'application automatique
cat > "$PROD_BACKUP_DIR/apply_complete_production.sh" << 'EOF'
#!/bin/bash
echo "🚀 APPLICATION CONFIGURATION PRODUCTION COMPLÈTE"
echo "================================================"

CURRENT_DIR=$(pwd)
BASE_DIR="$(dirname "$CURRENT_DIR")"

echo "📋 Vérification des fichiers..."

# Vérifier fichiers critiques
CRITICAL_FILES=(
    "settings_prod.py"
    "urls_prod.py"
    "requirements_prod.txt"
    "production_data_complete_*.json"
)

for file in "${CRITICAL_FILES[@]}"; do
    if ! ls $file 1> /dev/null 2>&1; then
        echo "❌ Fichier critique manquant: $file"
        exit 1
    fi
done

echo "✅ Fichiers critiques présents"

# Sauvegarde finale
echo "💾 Sauvegarde finale locale..."
cp "$BASE_DIR/config/settings.py" "$BASE_DIR/config/settings_pre_prod_migration.py"
cp "$BASE_DIR/config/urls.py" "$BASE_DIR/config/urls_pre_prod_migration.py"

# Application configuration
echo "⚙️  Application configuration..."
cp settings_prod.py "$BASE_DIR/config/settings.py"
cp urls_prod.py "$BASE_DIR/config/urls.py"

# Adaptation pour environnement local
echo "🔧 Adaptation configuration locale..."
cat >> "$BASE_DIR/config/settings.py" << 'SETTINGS_EOF'

# Adaptations pour environnement local
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

# Base de données locale
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',  # Adaptez selon votre config
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# URLs de base locale
BASE_URL = 'http://127.0.0.1:8000'

# CSRF pour développement
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']
SETTINGS_EOF

# Application du code
echo "💻 Application du code..."

if [ -d "models_prod" ]; then
    echo "   📋 Modèles..."
    cp -r models_prod/* "$BASE_DIR/"
fi

if [ -d "views_prod" ]; then
    echo "   👁️  Vues..."
    cp -r views_prod/* "$BASE_DIR/"
fi

if [ -d "forms_prod" ]; then
    echo "   📝 Formulaires..."
    cp -r forms_prod/* "$BASE_DIR/"
fi

if [ -d "templates_prod" ]; then
    echo "   🎨 Templates..."
    cp -r templates_prod/* "$BASE_DIR/"
fi

if [ -d "urls_prod" ]; then
    echo "   🔗 URLs..."
    cp -r urls_prod/* "$BASE_DIR/"
fi

if [ -d "migrations_prod" ]; then
    echo "   🔄 Migrations..."
    cp -r migrations_prod/* "$BASE_DIR/"
fi

if [ -d "utils_prod" ]; then
    echo "   🔧 Utilitaires..."
    cp -r utils_prod/* "$BASE_DIR/competitions/"
fi

# Signaux
for signal_file in signals_*_prod.py; do
    if [ -f "$signal_file" ]; then
        app_name=$(echo "$signal_file" | sed 's/signals_\(.*\)_prod.py/\1/')
        cp "$signal_file" "$BASE_DIR/$app_name/signals.py"
    fi
done

# Apps
for app_file in apps_*_prod.py; do
    if [ -f "$app_file" ]; then
        app_name=$(echo "$app_file" | sed 's/apps_\(.*\)_prod.py/\1/')
        cp "$app_file" "$BASE_DIR/$app_name/apps.py"
    fi
done

# Requirements
cp requirements_prod.txt "$BASE_DIR/requirements.txt"

echo "📦 Installation requirements..."
cd "$BASE_DIR"
pip install -r requirements.txt

echo "🗄️  Migration base de données..."
python3 manage.py makemigrations
python3 manage.py migrate

echo "📥 Import données production..."
cd "$CURRENT_DIR"
DATA_FILE=$(ls production_data_complete_*.json | head -1)
python3 "$BASE_DIR/manage.py" loaddata "$DATA_FILE"

echo ""
echo "🎉 MIGRATION PRODUCTION COMPLÈTE TERMINÉE"
echo "========================================"
echo "✅ Configuration appliquée"
echo "✅ Code synchronisé"
echo "✅ Base de données migrée"
echo "✅ Données importées"
echo ""
echo "🧪 TESTS:"
echo "   cd $BASE_DIR"
echo "   python3 manage.py runserver"
echo ""
echo "🔙 RESTAURATION SI PROBLÈME:"
echo "   ./restore_dev_backup.sh"
EOF

chmod +x "$PROD_BACKUP_DIR/apply_complete_production.sh"

echo ""
echo "🎉 MIGRATION PRODUCTION COMPLÈTE TERMINÉE"
echo "=================================================="
echo "📁 Données récupérées dans: $PROD_BACKUP_DIR"
echo "📊 Taille totale: $(du -sh $PROD_BACKUP_DIR | cut -f1)"
echo "📂 Fichiers récupérés: $(find $PROD_BACKUP_DIR -type f | wc -l)"
echo ""
echo "📋 PROCHAINE ÉTAPE:"
echo "   cd $PROD_BACKUP_DIR"
echo "   ./apply_complete_production.sh"
echo ""
echo "📖 RÉSUMÉ COMPLET:"
echo "   cat $PROD_BACKUP_DIR/MIGRATION_SUMMARY_$TIMESTAMP.md"
echo ""
echo "🔙 SI PROBLÈME:"
echo "   ./restore_dev_backup.sh"
echo ""
echo "⚠️  IMPORTANT: Vérifiez le résumé avant d'appliquer!"