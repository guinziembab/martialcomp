#!/bin/bash
"""
Script pour rapatrier la configuration et données de production vers local
"""

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROD_BACKUP_DIR="production_import_$TIMESTAMP"

echo "🚀 MIGRATION PRODUCTION → LOCAL - $TIMESTAMP"
echo "=============================================="

# Créer répertoire pour les imports
mkdir -p "$PROD_BACKUP_DIR"

echo "📁 Répertoire d'import: $PROD_BACKUP_DIR"

# Configuration SSH pour se connecter au serveur de production
read -p "🔑 Adresse du serveur de production (ex: user@server.com): " PROD_SERVER
read -p "📂 Chemin du projet sur le serveur (ex: /home/user/martialcomp): " PROD_PATH

echo ""
echo "🔍 Connexion au serveur de production..."

# Vérifier la connexion SSH
if ! ssh -o ConnectTimeout=10 "$PROD_SERVER" "echo 'Connexion réussie'"; then
    echo "❌ Impossible de se connecter au serveur de production"
    echo "   Vérifiez votre configuration SSH"
    exit 1
fi

echo "✅ Connexion SSH établie"

# 1. Récupérer la configuration Django de production
echo ""
echo "⚙️  Récupération configuration Django..."
scp "$PROD_SERVER:$PROD_PATH/config/settings.py" "$PROD_BACKUP_DIR/settings_prod.py"
scp "$PROD_SERVER:$PROD_PATH/config/urls.py" "$PROD_BACKUP_DIR/urls_prod.py"
echo "   ✅ Configuration récupérée"

# 2. Récupérer les requirements de production
echo "📦 Récupération requirements..."
scp "$PROD_SERVER:$PROD_PATH/requirements.txt" "$PROD_BACKUP_DIR/requirements_prod.txt"
echo "   ✅ Requirements récupérés"

# 3. Récupérer les modèles de production
echo "📋 Récupération modèles..."
mkdir -p "$PROD_BACKUP_DIR/models_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/models/" "$PROD_BACKUP_DIR/models_prod/"
echo "   ✅ Modèles récupérés"

# 4. Récupérer les migrations de production
echo "🔄 Récupération migrations..."
mkdir -p "$PROD_BACKUP_DIR/migrations_prod"
scp -r "$PROD_SERVER:$PROD_PATH/competitions/migrations/" "$PROD_BACKUP_DIR/migrations_prod/competitions/"
scp -r "$PROD_SERVER:$PROD_PATH/grades/migrations/" "$PROD_BACKUP_DIR/migrations_prod/grades/" 2>/dev/null || true
scp -r "$PROD_SERVER:$PROD_PATH/finances/migrations/" "$PROD_BACKUP_DIR/migrations_prod/finances/" 2>/dev/null || true
echo "   ✅ Migrations récupérées"

# 5. Récupérer les données Django de production
echo "🗄️  Sauvegarde données production..."
ssh "$PROD_SERVER" "cd $PROD_PATH && python3 manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > production_data_$TIMESTAMP.json"
scp "$PROD_SERVER:$PROD_PATH/production_data_$TIMESTAMP.json" "$PROD_BACKUP_DIR/"
echo "   ✅ Données récupérées"

# 6. Récupérer les templates de production
echo "🎨 Récupération templates..."
mkdir -p "$PROD_BACKUP_DIR/templates_prod"
scp "$PROD_SERVER:$PROD_PATH/competitions/templates/competitions/welcome.html" "$PROD_BACKUP_DIR/templates_prod/welcome_prod.html" 2>/dev/null || true
echo "   ✅ Templates récupérés"

# 7. Récupérer les vues importantes
echo "👁️  Récupération vues critiques..."
mkdir -p "$PROD_BACKUP_DIR/views_prod"
scp "$PROD_SERVER:$PROD_PATH/competitions/views/custom_login.py" "$PROD_BACKUP_DIR/views_prod/" 2>/dev/null || true
scp "$PROD_SERVER:$PROD_PATH/competitions/views/auth.py" "$PROD_BACKUP_DIR/views_prod/" 2>/dev/null || true
scp "$PROD_SERVER:$PROD_PATH/competitions/views/welcome.py" "$PROD_BACKUP_DIR/views_prod/" 2>/dev/null || true
echo "   ✅ Vues récupérées"

# 8. Récupérer les signaux de production
echo "📡 Récupération signaux..."
scp "$PROD_SERVER:$PROD_PATH/competitions/signals.py" "$PROD_BACKUP_DIR/signals_prod.py" 2>/dev/null || true
echo "   ✅ Signaux récupérés"

# 9. Nettoyer le fichier temporaire sur le serveur
ssh "$PROD_SERVER" "rm -f $PROD_PATH/production_data_$TIMESTAMP.json"

echo ""
echo "📊 Analyse des différences..."

# Créer un script d'analyse des différences
cat > "$PROD_BACKUP_DIR/analyze_differences.sh" << 'EOF'
#!/bin/bash
echo "🔍 ANALYSE DES DIFFÉRENCES PRODUCTION ↔ LOCAL"
echo "=============================================="

echo "⚙️  Configuration Django:"
if [ -f "settings_prod.py" ] && [ -f "../config/settings.py" ]; then
    echo "   📊 Lignes prod: $(wc -l < settings_prod.py)"
    echo "   📊 Lignes local: $(wc -l < ../config/settings.py)"
    echo "   📈 Différences majeures:"
    diff --brief settings_prod.py ../config/settings.py || echo "   ⚠️  Fichiers différents"
else
    echo "   ❌ Impossible de comparer"
fi

echo ""
echo "📦 Requirements:"
if [ -f "requirements_prod.txt" ] && [ -f "../requirements.txt" ]; then
    echo "   📊 Packages prod: $(wc -l < requirements_prod.txt)"
    echo "   📊 Packages local: $(wc -l < ../requirements.txt)"
    echo "   📈 Différences:"
    diff requirements_prod.txt ../requirements.txt | head -10 || echo "   ✅ Identiques"
else
    echo "   ❌ Impossible de comparer"
fi

echo ""
echo "🗄️  Données:"
if [ -f "production_data_*.json" ]; then
    DATA_FILE=$(ls production_data_*.json | head -1)
    echo "   📊 Taille données prod: $(du -h "$DATA_FILE" | cut -f1)"
    echo "   📊 Objets dans fichier: $(grep -o '"model":' "$DATA_FILE" | wc -l)"
else
    echo "   ❌ Pas de données récupérées"
fi
EOF

chmod +x "$PROD_BACKUP_DIR/analyze_differences.sh"

echo ""
echo "🎉 RÉCUPÉRATION PRODUCTION TERMINÉE"
echo "=============================================="
echo "📁 Données dans: $PROD_BACKUP_DIR"
echo "📊 Analyse: ./$PROD_BACKUP_DIR/analyze_differences.sh"
echo ""
echo "📋 PROCHAINES ÉTAPES:"
echo "   1. Analyser les différences"
echo "   2. Sauvegarder l'état local actuel (✅ Fait)"
echo "   3. Appliquer la configuration production"
echo "   4. Importer les données production"
echo "   5. Tester le système"
echo ""
echo "💡 COMMANDES SUGGÉRÉES:"
echo "   # Analyser les différences"
echo "   cd $PROD_BACKUP_DIR && ./analyze_differences.sh"
echo ""
echo "   # Appliquer config production (APRÈS VÉRIFICATION)"
echo "   # cp $PROD_BACKUP_DIR/settings_prod.py config/settings.py"
echo "   # cp $PROD_BACKUP_DIR/urls_prod.py config/urls.py"
echo ""
echo "   # Importer données production"
echo "   # python3 manage.py loaddata $PROD_BACKUP_DIR/production_data_*.json"
echo ""
echo "⚠️  ATTENTION: Vérifiez et adaptez avant d'appliquer!"