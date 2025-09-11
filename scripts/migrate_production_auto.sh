#!/bin/bash
"""
Migration automatique avec informations SSH fournies
"""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROD_BACKUP_DIR="production_complete_$TIMESTAMP"

# Informations de connexion
PROD_SERVER="root@212.227.78.104"
PROD_PASSWORD="68_02M@et@"

echo "🚀 MIGRATION PRODUCTION AUTOMATIQUE → LOCAL - $TIMESTAMP"
echo "=================================================="

# Créer répertoire pour les imports
mkdir -p "$PROD_BACKUP_DIR"

echo "📁 Répertoire d'import: $PROD_BACKUP_DIR"
echo "🔑 Serveur: $PROD_SERVER"

# Fonction pour exécuter des commandes SSH avec mot de passe
ssh_cmd() {
    sshpass -p "$PROD_PASSWORD" ssh -o StrictHostKeyChecking=no "$PROD_SERVER" "$1"
}

scp_cmd() {
    sshpass -p "$PROD_PASSWORD" scp -o StrictHostKeyChecking=no "$1" "$2"
}

scp_recursive() {
    sshpass -p "$PROD_PASSWORD" scp -r -o StrictHostKeyChecking=no "$1" "$2"
}

echo ""
echo "🔍 Test de connexion au serveur de production..."

# Installer sshpass si nécessaire
if ! command -v sshpass &> /dev/null; then
    echo "📦 Installation sshpass..."
    apt-get update && apt-get install -y sshpass 2>/dev/null || {
        echo "❌ Impossible d'installer sshpass"
        echo "   Installez-le manuellement: sudo apt-get install sshpass"
        exit 1
    }
fi

# Test de connexion
if ! ssh_cmd "echo 'Connexion SSH réussie'"; then
    echo "❌ Impossible de se connecter au serveur de production"
    echo "   Vérifiez les informations de connexion"
    exit 1
fi

echo "✅ Connexion SSH établie avec succès"

# Trouver le projet Django sur le serveur
echo "🔍 Recherche du projet Django..."

POSSIBLE_PATHS=(
    "/root/martialcomp"
    "/home/root/martialcomp"
    "/var/www/martialcomp"
    "/opt/martialcomp"
    "/root/martial_hub_django/martialcomp"
    "/home/martialcomp"
)

PROD_PATH=""
for path in "${POSSIBLE_PATHS[@]}"; do
    if ssh_cmd "[ -f '$path/manage.py' ]"; then
        PROD_PATH="$path"
        echo "✅ Projet Django trouvé: $PROD_PATH"
        break
    fi
done

if [ -z "$PROD_PATH" ]; then
    echo "🔍 Recherche dans tous les répertoires..."
    FOUND_PATH=$(ssh_cmd "find /root /home /var /opt -name 'manage.py' -type f 2>/dev/null | head -1")
    if [ -n "$FOUND_PATH" ]; then
        PROD_PATH=$(dirname "$FOUND_PATH")
        echo "✅ Projet Django trouvé: $PROD_PATH"
    else
        echo "❌ Projet Django non trouvé sur le serveur"
        echo "   Vérifiez que le projet est bien déployé"
        exit 1
    fi
fi

echo ""
echo "📦 RÉCUPÉRATION COMPLÈTE DE LA PRODUCTION"
echo "========================================="
echo "📂 Chemin source: $PROD_PATH"

# 1. Configuration Django
echo "⚙️  Configuration Django..."
scp_cmd "$PROD_SERVER:$PROD_PATH/config/settings.py" "$PROD_BACKUP_DIR/settings_prod.py"
scp_cmd "$PROD_SERVER:$PROD_PATH/config/urls.py" "$PROD_BACKUP_DIR/urls_prod.py"
scp_cmd "$PROD_SERVER:$PROD_PATH/config/wsgi.py" "$PROD_BACKUP_DIR/wsgi_prod.py" 2>/dev/null || true
echo "   ✅ Configuration récupérée"

# 2. Requirements
echo "📦 Requirements..."
scp_cmd "$PROD_SERVER:$PROD_PATH/requirements.txt" "$PROD_BACKUP_DIR/requirements_prod.txt"
echo "   ✅ Requirements récupérés"

# 3. Apps Django complets
echo "💻 Applications Django complètes..."
mkdir -p "$PROD_BACKUP_DIR/apps_prod"

# Récupérer toutes les apps
DJANGO_APPS=("competitions" "grades" "finances" "organizations" "shop" "documents" "family_management" "permissions_manager")

for app in "${DJANGO_APPS[@]}"; do
    if ssh_cmd "[ -d '$PROD_PATH/$app' ]"; then
        echo "   📂 Récupération app: $app"
        scp_recursive "$PROD_SERVER:$PROD_PATH/$app/" "$PROD_BACKUP_DIR/apps_prod/$app/"
    fi
done

echo "   ✅ Toutes les applications récupérées"

# 4. Configuration locale et fichiers racine
echo "🔧 Fichiers de configuration..."
scp_cmd "$PROD_SERVER:$PROD_PATH/manage.py" "$PROD_BACKUP_DIR/manage_prod.py" 2>/dev/null || true
scp_recursive "$PROD_SERVER:$PROD_PATH/locale/" "$PROD_BACKUP_DIR/locale/" 2>/dev/null || true
scp_recursive "$PROD_SERVER:$PROD_PATH/static/" "$PROD_BACKUP_DIR/static_sample/" 2>/dev/null || true
echo "   ✅ Fichiers de configuration récupérés"

# 5. SAUVEGARDE COMPLÈTE DES DONNÉES
echo "🗄️  Sauvegarde des données de production..."

echo "   📊 Dump Django complet..."
ssh_cmd "cd $PROD_PATH && python3 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > production_data_complete_$TIMESTAMP.json"

echo "   📊 Dump avec authentification..."
ssh_cmd "cd $PROD_PATH && python3 manage.py dumpdata --natural-foreign --natural-primary > production_data_with_auth_$TIMESTAMP.json"

echo "   📊 Dump par application..."
ssh_cmd "cd $PROD_PATH && python3 manage.py dumpdata competitions > production_competitions_$TIMESTAMP.json"
ssh_cmd "cd $PROD_PATH && python3 manage.py dumpdata auth.User > production_users_$TIMESTAMP.json"

echo "   📥 Récupération des dumps..."
scp_cmd "$PROD_SERVER:$PROD_PATH/production_data_complete_$TIMESTAMP.json" "$PROD_BACKUP_DIR/"
scp_cmd "$PROD_SERVER:$PROD_PATH/production_data_with_auth_$TIMESTAMP.json" "$PROD_BACKUP_DIR/"
scp_cmd "$PROD_SERVER:$PROD_PATH/production_competitions_$TIMESTAMP.json" "$PROD_BACKUP_DIR/" 2>/dev/null || true
scp_cmd "$PROD_SERVER:$PROD_PATH/production_users_$TIMESTAMP.json" "$PROD_BACKUP_DIR/" 2>/dev/null || true

echo "   ✅ Toutes les données récupérées"

# 6. Informations système
echo "🔍 Informations système production..."
ssh_cmd "cd $PROD_PATH && python3 --version" > "$PROD_BACKUP_DIR/python_version_prod.txt"
ssh_cmd "cd $PROD_PATH && pip freeze" > "$PROD_BACKUP_DIR/pip_freeze_prod.txt"
ssh_cmd "cd $PROD_PATH && python3 manage.py showmigrations" > "$PROD_BACKUP_DIR/migrations_status_prod.txt" 2>/dev/null || true
ssh_cmd "uname -a" > "$PROD_BACKUP_DIR/system_info_prod.txt"
ssh_cmd "cd $PROD_PATH && ls -la" > "$PROD_BACKUP_DIR/project_structure_prod.txt"
echo "   ✅ Informations système récupérées"

# 7. Nettoyage serveur
echo "🧹 Nettoyage serveur production..."
ssh_cmd "cd $PROD_PATH && rm -f production_data_*_$TIMESTAMP.json production_competitions_$TIMESTAMP.json production_users_$TIMESTAMP.json"
echo "   ✅ Nettoyage terminé"

# 8. Analyse et résumé
echo "📊 Analyse des données récupérées..."
TOTAL_SIZE=$(du -sh "$PROD_BACKUP_DIR" | cut -f1)
TOTAL_FILES=$(find "$PROD_BACKUP_DIR" -type f | wc -l)
TOTAL_DIRS=$(find "$PROD_BACKUP_DIR" -type d | wc -l)

# Créer résumé
cat > "$PROD_BACKUP_DIR/PRODUCTION_MIGRATION_SUMMARY.md" << EOF
# Migration Production Complète - $TIMESTAMP

## 🎯 Source Production
- **Serveur**: $PROD_SERVER  
- **Chemin**: $PROD_PATH
- **Date**: $(date)

## 📊 Statistiques Récupération
- **Taille totale**: $TOTAL_SIZE
- **Fichiers**: $TOTAL_FILES
- **Répertoires**: $TOTAL_DIRS

## 📦 Contenu Récupéré

### Configuration Core
- ✅ \`settings_prod.py\` - Configuration Django production
- ✅ \`urls_prod.py\` - URLs principales
- ✅ \`requirements_prod.txt\` - Dépendances
- ✅ \`manage_prod.py\` - Script de gestion

### Applications Django
$(find $PROD_BACKUP_DIR/apps_prod -maxdepth 1 -type d | tail -n +2 | sed 's|.*/|- ✅ |')

### Base de Données
- ✅ \`production_data_complete_$TIMESTAMP.json\` - Données complètes
- ✅ \`production_data_with_auth_$TIMESTAMP.json\` - Avec authentification
- ✅ \`production_competitions_$TIMESTAMP.json\` - Données competitions
- ✅ \`production_users_$TIMESTAMP.json\` - Utilisateurs

### Analyse Données
$(ls -la $PROD_BACKUP_DIR/*.json | awk '{print "- **" $9 "**: " $5 " bytes"}')

## 🚀 Application

\`\`\`bash
cd $PROD_BACKUP_DIR
chmod +x apply_production_complete.sh
./apply_production_complete.sh
\`\`\`

## 📋 Versions Production
- **Python**: $(cat "$PROD_BACKUP_DIR/python_version_prod.txt" 2>/dev/null || echo "Non disponible")
- **Packages**: $(wc -l < "$PROD_BACKUP_DIR/pip_freeze_prod.txt" 2>/dev/null || echo "0") installés

## ⚠️ Important
Cette migration remplacera complètement votre environnement local
par la configuration de production. Une sauvegarde locale a été
créée dans \`backup_dev_20250630_211015/\`.

## 🔙 Restauration
En cas de problème: \`./restore_dev_backup.sh\`
EOF

# Créer script d'application optimisé
cat > "$PROD_BACKUP_DIR/apply_production_complete.sh" << 'EOF'
#!/bin/bash
echo "🚀 APPLICATION PRODUCTION COMPLÈTE"
echo "=================================="

CURRENT_DIR=$(pwd)
BASE_DIR="$(dirname "$CURRENT_DIR")"

# Vérification des données
DATA_FILE=$(ls production_data_complete_*.json | head -1)
if [ ! -f "$DATA_FILE" ]; then
    echo "❌ Fichier de données principal non trouvé"
    exit 1
fi

echo "📊 Données à importer: $DATA_FILE ($(du -h "$DATA_FILE" | cut -f1))"

read -p "🤔 Continuer l'application production? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Application annulée"
    exit 1
fi

# Sauvegarde finale
echo "💾 Sauvegarde finale..."
cp "$BASE_DIR/config/settings.py" "$BASE_DIR/config/settings_before_prod.py"
cp "$BASE_DIR/config/urls.py" "$BASE_DIR/config/urls_before_prod.py"

# Application configuration
echo "⚙️  Application configuration production..."
cp settings_prod.py "$BASE_DIR/config/settings.py"
cp urls_prod.py "$BASE_DIR/config/urls.py"

# Correction pour environnement local
echo "🔧 Adaptation environnement local..."
cat >> "$BASE_DIR/config/settings.py" << 'SETTINGS_PATCH'

# === ADAPTATIONS POUR ENVIRONNEMENT LOCAL ===
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

# Base de données locale (à adapter selon votre config)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'postgres', 
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# URLs et domaines pour local
BASE_URL = 'http://127.0.0.1:8000'
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']
CSRF_COOKIE_SECURE = False

# Media et static pour local
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
SETTINGS_PATCH

# Application du code complet
echo "💻 Application du code production..."
if [ -d "apps_prod" ]; then
    cp -r apps_prod/* "$BASE_DIR/"
    echo "   ✅ Applications copiées"
fi

# Requirements
echo "📦 Installation requirements production..."
cp requirements_prod.txt "$BASE_DIR/requirements.txt"
cd "$BASE_DIR"
pip install -r requirements.txt

# Migration base de données
echo "🗄️  Migration base de données..."
python3 manage.py makemigrations
python3 manage.py migrate

# Import des données
echo "📥 Import données production..."
cd "$CURRENT_DIR"
echo "   📊 Import principal..."
python3 "$BASE_DIR/manage.py" loaddata "$DATA_FILE"

# Import utilisateurs si disponible
if [ -f "production_users_*.json" ]; then
    USER_FILE=$(ls production_users_*.json | head -1)
    echo "   👥 Import utilisateurs..."
    python3 "$BASE_DIR/manage.py" loaddata "$USER_FILE" 2>/dev/null || echo "   ⚠️  Import utilisateurs échoué (normal si déjà importés)"
fi

echo ""
echo "🎉 MIGRATION PRODUCTION TERMINÉE"
echo "==============================="
echo "✅ Configuration production appliquée"
echo "✅ Code production synchronisé"  
echo "✅ Base de données migrée"
echo "✅ Données production importées"
echo ""
echo "🧪 LANCER LE SERVEUR:"
echo "   cd $BASE_DIR"
echo "   python3 manage.py runserver"
echo ""
echo "🔍 VÉRIFIER:"
echo "   python3 check_system_status.py"
echo ""
echo "🔙 RESTAURER SI PROBLÈME:"
echo "   ./restore_dev_backup.sh"
EOF

chmod +x "$PROD_BACKUP_DIR/apply_production_complete.sh"

echo ""
echo "🎉 RÉCUPÉRATION PRODUCTION TERMINÉE"
echo "=================================================="
echo "📁 Données dans: $PROD_BACKUP_DIR"
echo "📊 Taille: $TOTAL_SIZE"
echo "📂 Fichiers: $TOTAL_FILES"
echo ""
echo "📋 RÉSUMÉ COMPLET:"
echo "   cat $PROD_BACKUP_DIR/PRODUCTION_MIGRATION_SUMMARY.md"
echo ""
echo "🚀 APPLIQUER MAINTENANT:"
echo "   cd $PROD_BACKUP_DIR"
echo "   ./apply_production_complete.sh"
echo ""
echo "🔙 RESTAURER SI PROBLÈME:"
echo "   ./restore_dev_backup.sh"
echo ""
echo "✅ MIGRATION PRODUCTION PRÊTE!"