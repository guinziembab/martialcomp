#!/bin/bash
echo "⚡ SYNCHRONISATION RAPIDE PRODUCTION"
echo "==================================="

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SYNC_DIR="production_sync_$TIMESTAMP"
mkdir -p "$SYNC_DIR"

# Informations serveur
SERVER="root@212.227.78.104"
PASSWORD="68_02M@et@"
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "🔑 Serveur: $SERVER"
echo "📂 Chemin: $PROD_PATH"
echo "📁 Local: $SYNC_DIR"

# Fonctions SSH
ssh_exec() {
    sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER" "$1"
}

scp_get() {
    sshpass -p "$PASSWORD" scp -o StrictHostKeyChecking=no "$1" "$2"
}

scp_get_recursive() {
    sshpass -p "$PASSWORD" scp -r -o StrictHostKeyChecking=no "$1" "$2"
}

echo ""
echo "1️⃣ RÉCUPÉRATION CONFIGURATION ESSENTIELLE"
echo "=========================================="

# Configuration Django
echo "   ⚙️  Settings..."
scp_get "$SERVER:$PROD_PATH/config/settings.py" "$SYNC_DIR/settings_prod.py"

echo "   🔗 URLs..."
scp_get "$SERVER:$PROD_PATH/config/urls.py" "$SYNC_DIR/urls_prod.py"

echo "   📦 Requirements..."
scp_get "$SERVER:$PROD_PATH/requirements.txt" "$SYNC_DIR/requirements_prod.txt"

echo ""
echo "2️⃣ RÉCUPÉRATION DONNÉES PRODUCTION"
echo "=================================="

# Créer dump des données
echo "   📊 Création dump principal..."
ssh_exec "cd $PROD_PATH && python3 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > production_data_main.json"

echo "   📊 Création dump utilisateurs..."
ssh_exec "cd $PROD_PATH && python3 manage.py dumpdata auth.User > production_users.json"

echo "   📊 Création dump competitions..."
ssh_exec "cd $PROD_PATH && python3 manage.py dumpdata competitions > production_competitions.json"

echo "   📥 Récupération dumps..."
scp_get "$SERVER:$PROD_PATH/production_data_main.json" "$SYNC_DIR/"
scp_get "$SERVER:$PROD_PATH/production_users.json" "$SYNC_DIR/"
scp_get "$SERVER:$PROD_PATH/production_competitions.json" "$SYNC_DIR/"

echo ""
echo "3️⃣ RÉCUPÉRATION CODE ESSENTIEL"
echo "=============================="

# Apps principales
echo "   💻 App competitions..."
scp_get_recursive "$SERVER:$PROD_PATH/competitions/" "$SYNC_DIR/competitions/"

echo "   💻 App grades..."
scp_get_recursive "$SERVER:$PROD_PATH/grades/" "$SYNC_DIR/grades/" 2>/dev/null || echo "   ⚠️  grades non trouvée"

echo "   💻 App finances..."
scp_get_recursive "$SERVER:$PROD_PATH/finances/" "$SYNC_DIR/finances/" 2>/dev/null || echo "   ⚠️  finances non trouvée"

echo ""
echo "4️⃣ NETTOYAGE SERVEUR"
echo "===================="
ssh_exec "cd $PROD_PATH && rm -f production_data_main.json production_users.json production_competitions.json"

echo ""
echo "5️⃣ ANALYSE RÉCUPÉRÉE"
echo "===================="
TOTAL_SIZE=$(du -sh "$SYNC_DIR" | cut -f1)
TOTAL_FILES=$(find "$SYNC_DIR" -type f | wc -l)

echo "   📊 Taille: $TOTAL_SIZE"
echo "   📂 Fichiers: $TOTAL_FILES"

# Analyser les données
if [ -f "$SYNC_DIR/production_data_main.json" ]; then
    DATA_SIZE=$(du -h "$SYNC_DIR/production_data_main.json" | cut -f1)
    DATA_OBJECTS=$(grep -o '"model":' "$SYNC_DIR/production_data_main.json" | wc -l)
    echo "   🗄️  Données principales: $DATA_SIZE ($DATA_OBJECTS objets)"
fi

echo ""
echo "6️⃣ CRÉATION SCRIPT D'APPLICATION"
echo "==============================="

cat > "$SYNC_DIR/apply_production_sync.sh" << 'EOF'
#!/bin/bash
echo "🚀 APPLICATION SYNCHRONISATION PRODUCTION"
echo "========================================"

CURRENT_DIR=$(pwd)
BASE_DIR="$(dirname "$CURRENT_DIR")"

echo "📋 Vérification des fichiers..."
if [ ! -f "settings_prod.py" ] || [ ! -f "production_data_main.json" ]; then
    echo "❌ Fichiers essentiels manquants"
    exit 1
fi

echo "✅ Fichiers présents"

read -p "🤔 Appliquer la configuration production? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Application annulée"
    exit 1
fi

# Sauvegarde locale
echo "💾 Sauvegarde configuration locale..."
cp "$BASE_DIR/config/settings.py" "$BASE_DIR/config/settings_before_sync.py"
cp "$BASE_DIR/config/urls.py" "$BASE_DIR/config/urls_before_sync.py"

# Application configuration
echo "⚙️  Application configuration..."
cp settings_prod.py "$BASE_DIR/config/settings.py"
cp urls_prod.py "$BASE_DIR/config/urls.py"

# Adaptation locale
echo "🔧 Adaptation pour environnement local..."
cat >> "$BASE_DIR/config/settings.py" << 'LOCAL_SETTINGS'

# === ADAPTATIONS LOCALES ===
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

# Base de données locale
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

# Configuration locale
BASE_URL = 'http://127.0.0.1:8000'
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']
CSRF_COOKIE_SECURE = False
LOCAL_SETTINGS

# Application du code
echo "💻 Application du code..."
if [ -d "competitions" ]; then
    cp -r competitions/ "$BASE_DIR/"
    echo "   ✅ App competitions appliquée"
fi

if [ -d "grades" ]; then
    cp -r grades/ "$BASE_DIR/"
    echo "   ✅ App grades appliquée"
fi

if [ -d "finances" ]; then
    cp -r finances/ "$BASE_DIR/"
    echo "   ✅ App finances appliquée"
fi

# Requirements
echo "📦 Installation requirements..."
cp requirements_prod.txt "$BASE_DIR/requirements.txt"
cd "$BASE_DIR"
pip install -r requirements.txt

# Migration
echo "🗄️  Migration base de données..."
python3 manage.py makemigrations
python3 manage.py migrate

# Import données
echo "📥 Import données..."
cd "$CURRENT_DIR"
python3 "$BASE_DIR/manage.py" loaddata production_data_main.json

echo ""
echo "🎉 SYNCHRONISATION TERMINÉE"
echo "=========================="
echo "✅ Configuration production appliquée"
echo "✅ Code synchronisé"
echo "✅ Données importées"
echo ""
echo "🧪 DÉMARRER LE SERVEUR:"
echo "   cd $BASE_DIR"
echo "   python3 manage.py runserver"
echo ""
echo "🔙 RESTAURER SI PROBLÈME:"
echo "   ./restore_dev_backup.sh"
EOF

chmod +x "$SYNC_DIR/apply_production_sync.sh"

echo ""
echo "✅ SYNCHRONISATION RAPIDE TERMINÉE"
echo "=================================="
echo "📁 Données dans: $SYNC_DIR"
echo "📊 Taille: $TOTAL_SIZE"
echo "📂 Fichiers: $TOTAL_FILES"
echo ""
echo "🚀 APPLIQUER MAINTENANT:"
echo "   cd $SYNC_DIR"
echo "   ./apply_production_sync.sh"
echo ""
echo "🔙 RESTAURER SI PROBLÈME:"
echo "   ./restore_dev_backup.sh"