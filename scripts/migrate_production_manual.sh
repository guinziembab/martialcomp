#!/bin/bash
"""
Script pour migration manuelle production → local
(Quand pas d'accès SSH direct)
"""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MANUAL_IMPORT_DIR="production_manual_$TIMESTAMP"

echo "📥 MIGRATION PRODUCTION MANUELLE - $TIMESTAMP"
echo "=============================================="

mkdir -p "$MANUAL_IMPORT_DIR"

cat > "$MANUAL_IMPORT_DIR/INSTRUCTIONS_MIGRATION.md" << 'EOF'
# Migration Production → Local - Instructions Manuelles

## 📋 Étapes à suivre sur le serveur de production

### 1. Connexion au serveur de production
```bash
ssh votre_user@votre_serveur.com
cd /chemin/vers/votre/projet/martialcomp
```

### 2. Sauvegarde des données production
```bash
# Sauvegarde Django
python3 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > production_data_$(date +%Y%m%d_%H%M%S).json

# Vérifier la taille du fichier
ls -lh production_data_*.json
```

### 3. Récupération des fichiers clés
Téléchargez ces fichiers depuis le serveur vers votre machine locale :

#### Configuration
- `config/settings.py` → `settings_prod.py`
- `config/urls.py` → `urls_prod.py`
- `requirements.txt` → `requirements_prod.txt`

#### Code applicatif
- `competitions/models/` (tout le dossier)
- `competitions/views/auth.py`
- `competitions/views/custom_login.py`
- `competitions/views/welcome.py`
- `competitions/signals.py`
- `competitions/templates/competitions/welcome.html`

#### Migrations
- `competitions/migrations/`
- `grades/migrations/`
- `finances/migrations/`

#### Données
- `production_data_YYYYMMDD_HHMMSS.json` (fichier créé à l'étape 2)

### 4. Téléchargement
Utilisez SCP, SFTP, ou votre interface de gestion de fichiers pour télécharger les fichiers listés ci-dessus dans le dossier :
`production_manual_TIMESTAMP/`

## 📥 Étapes sur votre machine locale

### 1. Placer les fichiers téléchargés
Copiez tous les fichiers téléchargés dans le dossier créé :
`production_manual_TIMESTAMP/`

### 2. Exécuter le script d'application
```bash
chmod +x production_manual_TIMESTAMP/apply_production_config.sh
./production_manual_TIMESTAMP/apply_production_config.sh
```

### 3. Vérification
Le script vous guidera pour :
- Comparer les configurations
- Appliquer les changements
- Importer les données
- Tester le système

## ⚠️  Points d'attention

1. **Sauvegarde obligatoire** : L'état local a déjà été sauvegardé
2. **Variables d'environnement** : Adaptez les variables de production pour le local
3. **Base de données** : Les données seront importées, vérifiez les conflits potentiels
4. **Dependencies** : Installez les nouveaux requirements si nécessaire

## 🆘 En cas de problème

Pour revenir à l'état précédent :
```bash
# Restaurer depuis la sauvegarde
./restore_dev_backup.sh
```
EOF

# Créer le script d'application
cat > "$MANUAL_IMPORT_DIR/apply_production_config.sh" << 'EOF'
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
EOF

chmod +x "$MANUAL_IMPORT_DIR/apply_production_config.sh"

# Créer un script de restauration
cat > "restore_dev_backup.sh" << 'EOF'
#!/bin/bash
echo "🔙 RESTAURATION SAUVEGARDE DÉVELOPPEMENT"
echo "========================================"

BACKUP_DIR="backup_dev_20250630_211015"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Sauvegarde non trouvée: $BACKUP_DIR"
    exit 1
fi

echo "🔄 Restauration depuis $BACKUP_DIR..."

# Restaurer configuration
cp "$BACKUP_DIR/settings_dev_"*.py config/settings.py
cp "$BACKUP_DIR/urls_dev_"*.py config/urls.py
cp "$BACKUP_DIR/requirements_dev_"*.txt requirements.txt

# Restaurer modèles
cp -r "$BACKUP_DIR/models/" competitions/

# Restaurer vues
cp -r "$BACKUP_DIR/views/" competitions/

# Restaurer formulaires
cp -r "$BACKUP_DIR/forms/" competitions/

# Restaurer templates
cp "$BACKUP_DIR/templates/welcome_dev_"*.html competitions/templates/competitions/welcome.html

# Restaurer signaux
cp "$BACKUP_DIR/signals_dev_"*.py competitions/signals.py

# Restaurer migrations
cp -r "$BACKUP_DIR/migrations/" ./

# Restaurer données
if [ -f "$BACKUP_DIR/django_data_backup.json" ]; then
    python3 manage.py loaddata "$BACKUP_DIR/django_data_backup.json"
fi

echo "✅ Restauration terminée"
echo "🔄 Redémarrez le serveur Django"
EOF

chmod +x restore_dev_backup.sh

echo "📁 Dossier créé: $MANUAL_IMPORT_DIR"
echo ""
echo "📋 DEUX OPTIONS DISPONIBLES:"
echo ""
echo "🔧 OPTION 1 - MIGRATION SSH AUTOMATIQUE:"
echo "   chmod +x migrate_production_to_local.sh"
echo "   ./migrate_production_to_local.sh"
echo ""
echo "📥 OPTION 2 - MIGRATION MANUELLE:"
echo "   1. Consultez: $MANUAL_IMPORT_DIR/INSTRUCTIONS_MIGRATION.md"
echo "   2. Téléchargez les fichiers manuellement depuis production"
echo "   3. Placez-les dans $MANUAL_IMPORT_DIR/"
echo "   4. Exécutez: $MANUAL_IMPORT_DIR/apply_production_config.sh"
echo ""
echo "🔙 RESTAURATION SI PROBLÈME:"
echo "   ./restore_dev_backup.sh"
echo ""
echo "⚠️  IMPORTANT: La sauvegarde dev a été créée dans backup_dev_20250630_211015/"