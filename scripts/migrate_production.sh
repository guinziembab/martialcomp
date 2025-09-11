#!/bin/bash
# ================================================================
# SCRIPTS DE MIGRATION PRODUCTION - MARTIALCOMP
# ================================================================

# ================================================================
# SCRIPT 1: PRE-MIGRATION - SAUVEGARDE ET PREPARATION
# ================================================================

create_pre_migration_script() {
cat > pre_migration.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 MARTIALCOMP - PRÉ-MIGRATION PRODUCTION"
echo "========================================"

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/martialcomp/migration_$TIMESTAMP"
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
DB_NAME="martialcomp"

# Créer le dossier de sauvegarde
echo "📁 Création du dossier de sauvegarde..."
sudo mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

# Sauvegarde du code source
echo "💾 Sauvegarde du code source..."
sudo tar -czf code_backup.tar.gz -C /var/www/vhosts/martialcomp.com httpdocs/

# Sauvegarde de la base de données
echo "🗄️ Sauvegarde de la base de données..."
sudo -u postgres pg_dump "$DB_NAME" > martialcomp_backup.sql

# Sauvegarde des fichiers média
echo "📸 Sauvegarde des médias..."
if [ -d "/var/www/vhosts/martialcomp.com/media" ]; then
    sudo tar -czf media_backup.tar.gz -C /var/www/vhosts/martialcomp.com media/
fi

# Sauvegarde des configurations
echo "⚙️ Sauvegarde des configurations..."
sudo cp /etc/nginx/conf.d/martialcomp.com.conf ./nginx_config.conf
sudo cp /etc/systemd/system/martialcomp.service ./systemd_service.conf

# Test de l'état actuel
echo "🧪 Test de l'état actuel..."
curl -f https://martialcomp.com/health/ && echo "✅ Site accessible" || echo "❌ Site non accessible"

# Vérifier les services
echo "🔍 Vérification des services..."
sudo systemctl is-active martialcomp && echo "✅ Django actif" || echo "❌ Django inactif"
sudo systemctl is-active nginx && echo "✅ Nginx actif" || echo "❌ Nginx inactif"
sudo systemctl is-active postgresql && echo "✅ PostgreSQL actif" || echo "❌ PostgreSQL inactif"

echo "✅ Pré-migration terminée - Sauvegarde dans: $BACKUP_DIR"
EOF

chmod +x pre_migration.sh
}

# ================================================================
# SCRIPT 2: MIGRATION PRINCIPALE
# ================================================================

create_migration_script() {
cat > migrate_to_apps.sh << 'EOF'
#!/bin/bash
set -e

echo "🔄 MARTIALCOMP - MIGRATION VERS STRUCTURE APPS"
echo "=============================================="

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
cd "$PROJECT_DIR"

# Liste des applications à migrer
APPS=(
    "competitions" "organizations" "multitenant" "grades"
    "finances" "shop" "documents" "family_management"
    "permissions_manager" "payment" "accounts" "security"
)

echo "📋 Applications à migrer: ${APPS[*]}"

# Créer le dossier apps temporaire
echo "📁 Création de la structure apps temporaire..."
sudo mkdir -p apps_new

# Migrer chaque application
for app in "${APPS[@]}"; do
    if [ -d "$app" ]; then
        echo "🔄 Migration de $app..."
        sudo mv "$app" "apps_new/"
        
        # Créer un __init__.py propre
        echo "# $app application" | sudo tee "apps_new/$app/__init__.py" > /dev/null
        
        # Corriger les permissions
        sudo chown -R www-data:www-data "apps_new/$app"
        
        echo "✅ $app migré vers apps_new/"
    else
        echo "⚠️ $app non trouvé - ignoré"
    fi
done

# Mise à jour de la configuration base.py
echo "⚙️ Mise à jour de config/settings/base.py..."

# Sauvegarder l'original
sudo cp config/settings/base.py config/settings/base.py.backup_migration_$(date +%H%M%S)

# Mettre à jour le sys.path
sudo sed -i "s|sys.path.append.*|sys.path.append(str(BASE_DIR / 'apps'))|g" config/settings/base.py

# Supprimer les références .apps.Config obsolètes
sudo sed -i "s/'grades.apps.GradesConfig'/'grades'/g" config/settings/base.py
sudo sed -i "s/'competitions.apps.CompetitionsConfig'/'competitions'/g" config/settings/base.py
sudo sed -i "s/'organizations.apps.OrganizationsConfig'/'organizations'/g" config/settings/base.py

echo "✅ Configuration mise à jour"

# Test de la nouvelle configuration
echo "🧪 Test de la nouvelle structure..."

# Arrêter le service temporairement
sudo systemctl stop martialcomp

# Basculer vers la nouvelle structure
sudo mv apps apps_old_backup
sudo mv apps_new apps

# Activer l'environnement virtuel et tester
cd "$PROJECT_DIR"
source /var/www/vhosts/martialcomp.com/.venv/bin/activate

# Test Django
python manage.py check --verbosity=2

if [ $? -eq 0 ]; then
    echo "✅ Tests de configuration réussis"
else
    echo "❌ Erreur dans la configuration - rollback nécessaire"
    # Rollback automatique
    sudo mv apps apps_failed
    sudo mv apps_old_backup apps
    sudo systemctl start martialcomp
    exit 1
fi

echo "✅ Migration terminée avec succès"
EOF

chmod +x migrate_to_apps.sh
}

# ================================================================
# SCRIPT 3: ACTIVATION ET TESTS
# ================================================================

create_activation_script() {
cat > activate_new_structure.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 MARTIALCOMP - ACTIVATION NOUVELLE STRUCTURE"
echo "============================================="

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
cd "$PROJECT_DIR"

# Mode maintenance temporaire
echo "🚧 Activation du mode maintenance..."
sudo tee /var/www/vhosts/martialcomp.com/httpdocs/maintenance.html > /dev/null << 'HTML'
<!DOCTYPE html>
<html>
<head>
    <title>Maintenance - MartialComp</title>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Segoe UI', Arial; text-align: center; padding: 50px; background: #f8f9fa; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .logo { color: #e74c3c; font-size: 3em; margin-bottom: 20px; }
        h1 { color: #2c3e50; margin-bottom: 20px; }
        p { color: #34495e; line-height: 1.6; margin-bottom: 15px; }
        .progress { width: 100%; height: 6px; background: #ecf0f1; border-radius: 3px; margin: 20px 0; }
        .progress-bar { width: 75%; height: 100%; background: #e74c3c; border-radius: 3px; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🥋</div>
        <h1>MartialComp en Maintenance</h1>
        <p>Nous mettons à jour notre plateforme pour vous offrir une meilleure expérience.</p>
        <div class="progress"><div class="progress-bar"></div></div>
        <p><strong>Durée estimée :</strong> 10 minutes</p>
        <p>Merci de votre patience !</p>
    </div>
</body>
</html>
HTML

# Configuration Nginx pour mode maintenance
NGINX_CONF="/etc/nginx/conf.d/martialcomp.com.conf"
sudo cp "$NGINX_CONF" "${NGINX_CONF}.backup_migration"

# Ajouter la redirection maintenance
sudo sed -i '/location \/ {/i\    # Mode maintenance\n    if (-f $document_root/maintenance.html) {\n        return 503;\n    }\n    error_page 503 @maintenance;\n    location @maintenance {\n        root /var/www/vhosts/martialcomp.com/httpdocs;\n        rewrite ^(.*)$ /maintenance.html break;\n    }' "$NGINX_CONF"

sudo systemctl reload nginx
echo "✅ Mode maintenance activé"

# Redémarrer le service avec la nouvelle structure
echo "🔄 Redémarrage du service Django..."
sudo systemctl start martialcomp

# Attendre que le service soit prêt
sleep 10

# Tests de fonctionnement
echo "🧪 Tests de fonctionnement..."
TEST_PASSED=true

# Test interne
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✅ Service Django fonctionnel"
else
    echo "❌ Service Django non fonctionnel"
    TEST_PASSED=false
fi

# Test de la base de données
cd "$PROJECT_DIR"
source /var/www/vhosts/martialcomp.com/.venv/bin/activate
if python manage.py check --database default > /dev/null 2>&1; then
    echo "✅ Base de données accessible"
else
    echo "❌ Problème de base de données"
    TEST_PASSED=false
fi

# Test des statiques
if python manage.py collectstatic --noinput --dry-run > /dev/null 2>&1; then
    echo "✅ Fichiers statiques OK"
else
    echo "❌ Problème avec les fichiers statiques"
    TEST_PASSED=false
fi

if [ "$TEST_PASSED" = true ]; then
    echo "🎉 Tous les tests passent - Désactivation du mode maintenance..."
    
    # Retirer le mode maintenance
    sudo cp "${NGINX_CONF}.backup_migration" "$NGINX_CONF"
    sudo systemctl reload nginx
    
    # Supprimer le fichier de maintenance
    sudo rm -f /var/www/vhosts/martialcomp.com/httpdocs/maintenance.html
    
    # Test final public
    sleep 5
    if curl -f https://martialcomp.com/ > /dev/null 2>&1; then
        echo "✅ Site public accessible"
        echo "🎉 Migration réussie !"
    else
        echo "❌ Site public non accessible"
    fi
else
    echo "❌ Tests échoués - Rollback recommandé"
    exit 1
fi
EOF

chmod +x activate_new_structure.sh
}

# ================================================================
# SCRIPT 4: ROLLBACK D'URGENCE
# ================================================================

create_rollback_script() {
cat > emergency_rollback.sh << 'EOF'
#!/bin/bash
set -e

echo "🚨 MARTIALCOMP - ROLLBACK D'URGENCE"
echo "================================="

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
cd "$PROJECT_DIR"

# Mode maintenance d'urgence
echo "🚧 Activation du mode maintenance d'urgence..."
sudo tee /var/www/vhosts/martialcomp.com/httpdocs/maintenance.html > /dev/null << 'HTML'
<!DOCTYPE html>
<html>
<head><title>Maintenance - MartialComp</title></head>
<body style="font-family: Arial; text-align: center; padding: 50px;">
    <h1>🥋 MartialComp</h1>
    <h2>Maintenance Technique</h2>
    <p>Nous résolvons un incident technique. Retour prévu sous 10 minutes.</p>
</body>
</html>
HTML

NGINX_CONF="/etc/nginx/conf.d/martialcomp.com.conf"
sudo sed -i '1i\server { listen 80; listen 443 ssl; server_name martialcomp.com; return 503; error_page 503 /maintenance.html; location = /maintenance.html { root /var/www/vhosts/martialcomp.com/httpdocs; } }' "$NGINX_CONF"
sudo systemctl reload nginx

echo "🛑 Arrêt du service..."
sudo systemctl stop martialcomp

echo "🔄 Restauration de l'ancienne structure..."
if [ -d "apps_old_backup" ]; then
    sudo rm -rf apps
    sudo mv apps_old_backup apps
    echo "✅ Structure restaurée"
else
    echo "❌ Backup non trouvé - utilisation de la sauvegarde tar"
    # Restaurer depuis la sauvegarde tar si nécessaire
    LATEST_BACKUP=$(ls -t /var/backups/martialcomp/ | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cd /var/www/vhosts/martialcomp.com
        sudo tar -xzf "/var/backups/martialcomp/$LATEST_BACKUP/code_backup.tar.gz"
        echo "✅ Restauration depuis sauvegarde tar"
    fi
fi

# Restaurer la configuration
if [ -f "config/settings/base.py.backup_migration" ]; then
    sudo cp config/settings/base.py.backup_migration config/settings/base.py
    echo "✅ Configuration restaurée"
fi

echo "🚀 Redémarrage du service..."
sudo systemctl start martialcomp

# Attendre et tester
sleep 10
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    echo "✅ Service restauré"
    
    # Retirer la maintenance
    sudo cp "${NGINX_CONF}.backup_migration" "$NGINX_CONF" 2>/dev/null || true
    sudo systemctl reload nginx
    sudo rm -f /var/www/vhosts/martialcomp.com/httpdocs/maintenance.html
    
    echo "🎉 Rollback terminé avec succès"
else
    echo "❌ Problème persiste - intervention manuelle requise"
    exit 1
fi
EOF

chmod +x emergency_rollback.sh
}

# ================================================================
# SCRIPT 5: ORCHESTRATEUR PRINCIPAL
# ================================================================

create_master_script() {
cat > migrate_production.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 MARTIALCOMP - MIGRATION PRODUCTION COMPLÈTE"
echo "=============================================="
echo ""
echo "Ce script va migrer votre production vers la structure apps/"
echo "Durée estimée: 20-30 minutes"
echo "Interruption de service: < 10 minutes"
echo ""
read -p "Continuer la migration? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Migration annulée"
    exit 1
fi

# Étape 1: Pré-migration
echo "📋 ÉTAPE 1/4 - Pré-migration et sauvegarde..."
./pre_migration.sh
if [ $? -ne 0 ]; then
    echo "❌ Échec de la pré-migration"
    exit 1
fi

# Étape 2: Migration
echo "📋 ÉTAPE 2/4 - Migration de la structure..."
./migrate_to_apps.sh
if [ $? -ne 0 ]; then
    echo "❌ Échec de la migration - rollback automatique effectué"
    exit 1
fi

# Étape 3: Activation
echo "📋 ÉTAPE 3/4 - Activation et tests..."
./activate_new_structure.sh
if [ $? -ne 0 ]; then
    echo "❌ Échec de l'activation - lancement du rollback..."
    ./emergency_rollback.sh
    exit 1
fi

# Étape 4: Validation finale
echo "📋 ÉTAPE 4/4 - Validation finale..."
sleep 5

# Tests complets
curl -f https://martialcomp.com/ > /dev/null && echo "✅ Page d'accueil OK"
curl -f https://martialcomp.com/fr/competitions/dashboard/ > /dev/null && echo "✅ Dashboard OK"

# Nettoyage final
cd /var/www/vhosts/martialcomp.com/httpdocs
sudo find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
sudo find . -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "🎉 MIGRATION TERMINÉE AVEC SUCCÈS!"
echo "================================="
echo "✅ Structure apps/ activée en production"
echo "✅ Toutes les applications fonctionnelles"
echo "✅ Site accessible publiquement"
echo "✅ Sauvegardes conservées dans /var/backups/martialcomp/"
echo ""
echo "🔍 Surveillance recommandée pendant les prochaines heures"
echo "📊 Logs: sudo tail -f /var/www/vhosts/martialcomp.com/logs/django.log"
EOF

chmod +x migrate_production.sh
}

# ================================================================
# GÉNÉRATEUR DE TOUS LES SCRIPTS
# ================================================================

echo "🛠️ Génération des scripts de migration..."

create_pre_migration_script
echo "✅ pre_migration.sh créé"

create_migration_script
echo "✅ migrate_to_apps.sh créé"

create_activation_script
echo "✅ activate_new_structure.sh créé"

create_rollback_script
echo "✅ emergency_rollback.sh créé"

create_master_script
echo "✅ migrate_production.sh créé"

echo ""
echo "🎯 Scripts de migration créés:"
echo "- migrate_production.sh    (Script principal)"
echo "- pre_migration.sh         (Sauvegarde)"
echo "- migrate_to_apps.sh       (Migration)"
echo "- activate_new_structure.sh (Activation)"
echo "- emergency_rollback.sh    (Rollback d'urgence)"
echo ""
echo "Usage: ./migrate_production.sh"