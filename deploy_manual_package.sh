#!/bin/bash

# Script pour créer un package de déploiement manuel
echo "📦 CRÉATION DU PACKAGE DE DÉPLOIEMENT MANUEL"
echo "============================================="

# Créer un dossier de déploiement avec timestamp
DEPLOY_DIR="deployment_package_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEPLOY_DIR"

echo "📁 Création du dossier: $DEPLOY_DIR"

# Copier les fichiers corrigés
echo "📄 Copie des fichiers corrigés..."

# Vue federations corrigée
mkdir -p "$DEPLOY_DIR/apps/competitions/views"
cp "apps/competitions/views/federations.py" "$DEPLOY_DIR/apps/competitions/views/"
echo "   ✅ federations.py"

# Template examens corrigé
mkdir -p "$DEPLOY_DIR/apps/competitions/templates/competitions/federations/examens"
cp "apps/competitions/templates/competitions/federations/examens/list.html" "$DEPLOY_DIR/apps/competitions/templates/competitions/federations/examens/"
echo "   ✅ list.html"

# URLs dashboard corrigées
mkdir -p "$DEPLOY_DIR/apps/competitions/urls"
cp "apps/competitions/urls/dashboard.py" "$DEPLOY_DIR/apps/competitions/urls/"
echo "   ✅ dashboard.py"

# Scripts de correction
cp "fix_all_issues_production.py" "$DEPLOY_DIR/"
cp "fix_migration_production.py" "$DEPLOY_DIR/" 2>/dev/null || echo "   ⚠️ fix_migration_production.py non trouvé"
echo "   ✅ Scripts de correction"

# Créer un script de déploiement sur serveur
cat > "$DEPLOY_DIR/deploy_on_server.sh" << 'EOF'
#!/bin/bash
# Script à exécuter sur le serveur martialcomp.com

echo "🚀 DÉPLOIEMENT SUR SERVEUR - MartialComp"
echo "========================================"

# Vérifier qu'on est dans le bon répertoire
if [[ ! -f "manage.py" ]]; then
    echo "❌ Erreur: manage.py non trouvé. Exécuter depuis /var/www/martialcomp"
    exit 1
fi

# Sauvegarde
echo "💾 Création de sauvegarde..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r apps/competitions/views/federations.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r apps/competitions/templates/competitions/federations/examens/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r apps/competitions/urls/dashboard.py "$BACKUP_DIR/" 2>/dev/null || true
echo "   ✅ Sauvegarde créée dans $BACKUP_DIR"

# Appliquer les corrections
echo "🔧 Application des corrections..."
cp apps/competitions/views/federations.py apps/competitions/views/federations.py.backup
cp apps/competitions/urls/dashboard.py apps/competitions/urls/dashboard.py.backup
cp apps/competitions/templates/competitions/federations/examens/list.html apps/competitions/templates/competitions/federations/examens/list.html.backup

echo "   ✅ Fichiers copiés"

# Correction des migrations
echo "🗄️ Correction des migrations..."
python3 manage.py migrate --fake competitions 0007 || echo "   ⚠️ Migration fake échouée, on continue..."
rm -f apps/competitions/migrations/0008_remove_* 2>/dev/null || true
rm -f apps/competitions/migrations/0009_alter_* 2>/dev/null || true
python3 manage.py makemigrations
python3 manage.py migrate

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python3 manage.py collectstatic --noinput

# Vérification Django
echo "🔍 Vérification Django..."
python3 manage.py check

# Redémarrage des services
echo "🔄 Redémarrage des services..."
sudo systemctl restart nginx
sudo systemctl restart gunicorn || sudo systemctl restart martialcomp || echo "   ⚠️ Service Django non redémarré"

# Test final
echo "🧪 Test final..."
sleep 3
curl -I https://martialcomp.com/fr/competitions/federations/3/examens/ || echo "   ⚠️ Test de connexion échoué"

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "📋 Vérifier manuellement:"
echo "   - https://martialcomp.com/fr/competitions/federations/3/examens/"
echo "   - https://martialcomp.com/fr/competitions/dashboard/documentation/"
EOF

chmod +x "$DEPLOY_DIR/deploy_on_server.sh"

# Créer les instructions de déploiement
cat > "$DEPLOY_DIR/INSTRUCTIONS.md" << 'EOF'
# INSTRUCTIONS DE DÉPLOIEMENT MANUEL

## 🎯 Objectif
Corriger l'erreur 500 sur https://martialcomp.com/fr/competitions/federations/3/examens/

## 📦 Contenu du Package
- `apps/competitions/views/federations.py` - Vue corrigée avec gestion d'erreurs
- `apps/competitions/templates/competitions/federations/examens/list.html` - Template corrigé
- `apps/competitions/urls/dashboard.py` - URLs corrigées
- `deploy_on_server.sh` - Script de déploiement automatique

## 🚀 Étapes de Déploiement

### 1. Transférer le package sur le serveur
```bash
# Depuis votre machine locale
scp -r deployment_package_* root@martialcomp.com:/tmp/

# Ou utiliser votre méthode de transfert préférée
```

### 2. Se connecter au serveur et appliquer
```bash
# Connexion au serveur
ssh root@martialcomp.com

# Aller dans le répertoire de l'application
cd /var/www/martialcomp

# Copier les fichiers du package
cp -r /tmp/deployment_package_*/apps/* apps/
cp /tmp/deployment_package_*/fix_all_issues_production.py .

# Exécuter le script de déploiement
chmod +x /tmp/deployment_package_*/deploy_on_server.sh
/tmp/deployment_package_*/deploy_on_server.sh
```

### 3. Vérification
- Tester: https://martialcomp.com/fr/competitions/federations/3/examens/
- Code attendu: 200 (OK) ou 302 (redirection si non connecté)

## 🔍 En Cas de Problème
```bash
# Voir les logs
tail -f /var/log/django/martialcomp.log
tail -f /var/log/nginx/error.log

# Restaurer la sauvegarde si nécessaire
cd /var/www/martialcomp
cp backup_*/federations.py apps/competitions/views/
systemctl restart gunicorn
```

## ✅ Fichiers Corrigés
- **federations.py**: Gestion d'erreurs améliorée pour les examens
- **list.html**: Template corrigé avec bonne extension et blocks
- **dashboard.py**: URL pattern manquant ajouté
EOF

# Créer une archive pour transfer facile
tar -czf "${DEPLOY_DIR}.tar.gz" "$DEPLOY_DIR"

echo ""
echo "✅ PACKAGE DE DÉPLOIEMENT CRÉÉ"
echo "==============================="
echo "📁 Dossier: $DEPLOY_DIR"
echo "📦 Archive: ${DEPLOY_DIR}.tar.gz"
echo ""
echo "🚀 ÉTAPES SUIVANTES:"
echo "1. Transférer ${DEPLOY_DIR}.tar.gz sur le serveur"
echo "2. Extraire: tar -xzf ${DEPLOY_DIR}.tar.gz"
echo "3. Suivre les instructions dans ${DEPLOY_DIR}/INSTRUCTIONS.md"
echo ""
echo "🎯 OBJECTIF: Corriger https://martialcomp.com/fr/competitions/federations/3/examens/"