#!/bin/bash

# Script amélioré pour créer un package de production avec validation de structure
# Version 2.0 - Avec vérification des chemins et structure

PACKAGE_NAME="martialcomp_production_$(date +%Y%m%d_%H%M%S).tar.gz"
TEMP_DIR="production_export_temp"
PROD_BASE_DIR="/var/www/vhosts/martialcomp.com/httpdocs"  # Chemin Plesk pour martialcomp.com

echo "📦 Création du package de production: $PACKAGE_NAME"
echo "🎯 Structure cible: $PROD_BASE_DIR"
echo ""

# Créer un dossier temporaire avec la structure attendue
mkdir -p $TEMP_DIR

echo "📋 Copie des fichiers essentiels avec structure de production..."

# 1. Fichiers racine essentiels
cp manage.py $TEMP_DIR/ 2>/dev/null
cp requirements.txt $TEMP_DIR/ 2>/dev/null

# 2. Configuration complète
echo "  → Configuration Django..."
cp -r config $TEMP_DIR/
# Nettoyer les __pycache__ dans config
find $TEMP_DIR/config -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 3. Applications (code source)
echo "  → Applications Django..."
mkdir -p $TEMP_DIR/apps
rsync -av --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='*.log' \
          --exclude='*.sqlite3' \
          --exclude='migrations/__pycache__' \
          apps/ $TEMP_DIR/apps/

# 4. Templates globaux
echo "  → Templates..."
if [ -d "templates" ]; then
    cp -r templates $TEMP_DIR/
fi

# 5. Fichiers statiques (pour production)
echo "  → Fichiers statiques..."
if [ -d "static" ]; then
    cp -r static $TEMP_DIR/
fi

# 6. Locales (traductions)
echo "  → Fichiers de traduction..."
if [ -d "locale" ]; then
    cp -r locale $TEMP_DIR/
fi

# 7. Créer les dossiers nécessaires (vides)
echo "  → Création des dossiers de production..."
mkdir -p $TEMP_DIR/staticfiles  # Pour collectstatic
mkdir -p $TEMP_DIR/media        # Pour les uploads
mkdir -p $TEMP_DIR/logs         # Pour les logs

# 7.5 Copier le fichier Passenger pour Plesk
echo "  → Configuration Passenger (Plesk)..."
cp passenger_wsgi.py.example $TEMP_DIR/passenger_wsgi.py 2>/dev/null

# 8. Créer un fichier d'information sur la structure
cat > $TEMP_DIR/STRUCTURE_INFO.txt << EOF
Structure du Package de Production MartialComp
=============================================

Ce package est conçu pour être extrait dans: $PROD_BASE_DIR

Structure après extraction:
$PROD_BASE_DIR/
├── manage.py
├── requirements.txt
├── config/
├── apps/
├── templates/
├── static/          (fichiers sources)
├── staticfiles/     (vide - pour collectstatic)
├── media/          (vide - pour uploads)
└── logs/           (vide - pour logs)

Instructions de déploiement:
1. Extraire dans le répertoire cible
2. Créer l'environnement virtuel
3. Installer les dépendances
4. Configurer les variables d'environnement
5. Exécuter les migrations
6. Collecter les fichiers statiques
7. Configurer le serveur web

Généré le: $(date)
EOF

# 9. Créer un script de déploiement
cat > $TEMP_DIR/deploy.sh << 'EOF'
#!/bin/bash
# Script de déploiement rapide

echo "🚀 Déploiement MartialComp..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Êtes-vous dans le bon répertoire?"
    exit 1
fi

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Collecter les fichiers statiques
echo "📁 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "🗄️ Application des migrations..."
python manage.py migrate

# Créer le superuser si nécessaire
echo "👤 Voulez-vous créer un superutilisateur? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo "✅ Déploiement terminé!"
echo "⚠️  N'oubliez pas de:"
echo "   - Configurer votre serveur web (Nginx/Apache)"
echo "   - Définir les variables d'environnement"
echo "   - Vérifier les permissions des dossiers"
EOF

chmod +x $TEMP_DIR/deploy.sh

# 10. Créer l'archive
echo ""
echo "🗜️  Création de l'archive..."
tar -czf $PACKAGE_NAME -C $TEMP_DIR .

# Nettoyer
rm -rf $TEMP_DIR

# Afficher les informations
SIZE=$(ls -lh $PACKAGE_NAME | awk '{print $5}')
echo ""
echo "✅ Package créé avec succès!"
echo "📊 Taille du package: $SIZE"
echo "📦 Fichier: $PACKAGE_NAME"
echo ""
echo "🚀 Instructions de déploiement:"
echo ""
echo "1. Sur le serveur de production:"
echo "   mkdir -p $PROD_BASE_DIR"
echo "   cd $PROD_BASE_DIR"
echo ""
echo "2. Transférer et extraire le package:"
echo "   scp $PACKAGE_NAME user@serveur:$PROD_BASE_DIR/"
echo "   tar -xzf $PACKAGE_NAME"
echo ""
echo "3. Exécuter le script de déploiement:"
echo "   ./deploy.sh"
echo ""
echo "📝 Note: Assurez-vous d'avoir configuré les variables d'environnement avant!"