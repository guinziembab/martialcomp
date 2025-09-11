#!/bin/bash
# Script d'installation automatique pour les sites d'organisations
# Généré le 2025-06-13 22:27:08

echo "🚀 INSTALLATION DES SITES D'ORGANISATIONS EN PRODUCTION"
echo "========================================================"

# Variables
BACKUP_DIR="/opt/martialcomp/backups/organization_sites_20250613_222707"
APP_DIR="/opt/martialcomp/app"

# Créer le répertoire de sauvegarde
mkdir -p "$BACKUP_DIR"
echo "📁 Répertoire de sauvegarde: $BACKUP_DIR"

# Arrêter le service Django
echo "🔄 Arrêt du service Django..."
sudo systemctl stop martialcomp

echo "💾 SAUVEGARDE DES FICHIERS ORIGINAUX"
echo "===================================="

# Sauvegarder organizations/signals.py
if [ -f "/opt/martialcomp/app/organizations/signals.py" ]; then
    cp "/opt/martialcomp/app/organizations/signals.py" "$BACKUP_DIR/organizations_signals.py.backup"
    echo "✅ Sauvegardé: organizations/signals.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/organizations/signals.py")"
cp "organizations/signals.py" "/opt/martialcomp/app/organizations/signals.py"
echo "✅ Mis à jour: organizations/signals.py"

# Sauvegarder organizations/apps.py
if [ -f "/opt/martialcomp/app/organizations/apps.py" ]; then
    cp "/opt/martialcomp/app/organizations/apps.py" "$BACKUP_DIR/organizations_apps.py.backup"
    echo "✅ Sauvegardé: organizations/apps.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/organizations/apps.py")"
cp "organizations/apps.py" "/opt/martialcomp/app/organizations/apps.py"
echo "✅ Mis à jour: organizations/apps.py"

# Sauvegarder competitions/templates/organizations/sites/base_template.html
if [ -f "/opt/martialcomp/app/competitions/templates/organizations/sites/base_template.html" ]; then
    cp "/opt/martialcomp/app/competitions/templates/organizations/sites/base_template.html" "$BACKUP_DIR/competitions_templates_organizations_sites_base_template.html.backup"
    echo "✅ Sauvegardé: competitions/templates/organizations/sites/base_template.html"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/templates/organizations/sites/base_template.html")"
cp "competitions/templates/organizations/sites/base_template.html" "/opt/martialcomp/app/competitions/templates/organizations/sites/base_template.html"
echo "✅ Mis à jour: competitions/templates/organizations/sites/base_template.html"

# Sauvegarder competitions/templates/organizations/sites/club_template.html
if [ -f "/opt/martialcomp/app/competitions/templates/organizations/sites/club_template.html" ]; then
    cp "/opt/martialcomp/app/competitions/templates/organizations/sites/club_template.html" "$BACKUP_DIR/competitions_templates_organizations_sites_club_template.html.backup"
    echo "✅ Sauvegardé: competitions/templates/organizations/sites/club_template.html"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/templates/organizations/sites/club_template.html")"
cp "competitions/templates/organizations/sites/club_template.html" "/opt/martialcomp/app/competitions/templates/organizations/sites/club_template.html"
echo "✅ Mis à jour: competitions/templates/organizations/sites/club_template.html"

# Sauvegarder competitions/templates/organizations/sites/federation_template.html
if [ -f "/opt/martialcomp/app/competitions/templates/organizations/sites/federation_template.html" ]; then
    cp "/opt/martialcomp/app/competitions/templates/organizations/sites/federation_template.html" "$BACKUP_DIR/competitions_templates_organizations_sites_federation_template.html.backup"
    echo "✅ Sauvegardé: competitions/templates/organizations/sites/federation_template.html"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/templates/organizations/sites/federation_template.html")"
cp "competitions/templates/organizations/sites/federation_template.html" "/opt/martialcomp/app/competitions/templates/organizations/sites/federation_template.html"
echo "✅ Mis à jour: competitions/templates/organizations/sites/federation_template.html"

# Sauvegarder competitions/urls/organization_sites.py
if [ -f "/opt/martialcomp/app/competitions/urls/organization_sites.py" ]; then
    cp "/opt/martialcomp/app/competitions/urls/organization_sites.py" "$BACKUP_DIR/competitions_urls_organization_sites.py.backup"
    echo "✅ Sauvegardé: competitions/urls/organization_sites.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/urls/organization_sites.py")"
cp "competitions/urls/organization_sites.py" "/opt/martialcomp/app/competitions/urls/organization_sites.py"
echo "✅ Mis à jour: competitions/urls/organization_sites.py"

# Sauvegarder competitions/views/organization_sites.py
if [ -f "/opt/martialcomp/app/competitions/views/organization_sites.py" ]; then
    cp "/opt/martialcomp/app/competitions/views/organization_sites.py" "$BACKUP_DIR/competitions_views_organization_sites.py.backup"
    echo "✅ Sauvegardé: competitions/views/organization_sites.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/views/organization_sites.py")"
cp "competitions/views/organization_sites.py" "/opt/martialcomp/app/competitions/views/organization_sites.py"
echo "✅ Mis à jour: competitions/views/organization_sites.py"

# Sauvegarder config/urls.py
if [ -f "/opt/martialcomp/app/config/urls.py" ]; then
    cp "/opt/martialcomp/app/config/urls.py" "$BACKUP_DIR/config_urls.py.backup"
    echo "✅ Sauvegardé: config/urls.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/config/urls.py")"
cp "config/urls.py" "/opt/martialcomp/app/config/urls.py"
echo "✅ Mis à jour: config/urls.py"

# Sauvegarder competitions/utils/subdomain_generator.py
if [ -f "/opt/martialcomp/app/competitions/utils/subdomain_generator.py" ]; then
    cp "/opt/martialcomp/app/competitions/utils/subdomain_generator.py" "$BACKUP_DIR/competitions_utils_subdomain_generator.py.backup"
    echo "✅ Sauvegardé: competitions/utils/subdomain_generator.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/utils/subdomain_generator.py")"
cp "competitions/utils/subdomain_generator.py" "/opt/martialcomp/app/competitions/utils/subdomain_generator.py"
echo "✅ Mis à jour: competitions/utils/subdomain_generator.py"

# Sauvegarder competitions/utils/qr_generator_enhanced.py
if [ -f "/opt/martialcomp/app/competitions/utils/qr_generator_enhanced.py" ]; then
    cp "/opt/martialcomp/app/competitions/utils/qr_generator_enhanced.py" "$BACKUP_DIR/competitions_utils_qr_generator_enhanced.py.backup"
    echo "✅ Sauvegardé: competitions/utils/qr_generator_enhanced.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/utils/qr_generator_enhanced.py")"
cp "competitions/utils/qr_generator_enhanced.py" "/opt/martialcomp/app/competitions/utils/qr_generator_enhanced.py"
echo "✅ Mis à jour: competitions/utils/qr_generator_enhanced.py"

# Sauvegarder multitenant/models.py
if [ -f "/opt/martialcomp/app/multitenant/models.py" ]; then
    cp "/opt/martialcomp/app/multitenant/models.py" "$BACKUP_DIR/multitenant_models.py.backup"
    echo "✅ Sauvegardé: multitenant/models.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/multitenant/models.py")"
cp "multitenant/models.py" "/opt/martialcomp/app/multitenant/models.py"
echo "✅ Mis à jour: multitenant/models.py"

# Sauvegarder organizations/models.py
if [ -f "/opt/martialcomp/app/organizations/models.py" ]; then
    cp "/opt/martialcomp/app/organizations/models.py" "$BACKUP_DIR/organizations_models.py.backup"
    echo "✅ Sauvegardé: organizations/models.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/organizations/models.py")"
cp "organizations/models.py" "/opt/martialcomp/app/organizations/models.py"
echo "✅ Mis à jour: organizations/models.py"

# Sauvegarder config/settings.py
if [ -f "/opt/martialcomp/app/config/settings.py" ]; then
    cp "/opt/martialcomp/app/config/settings.py" "$BACKUP_DIR/config_settings.py.backup"
    echo "✅ Sauvegardé: config/settings.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/config/settings.py")"
cp "config/settings.py" "/opt/martialcomp/app/config/settings.py"
echo "✅ Mis à jour: config/settings.py"

# Sauvegarder competitions/signals.py
if [ -f "/opt/martialcomp/app/competitions/signals.py" ]; then
    cp "/opt/martialcomp/app/competitions/signals.py" "$BACKUP_DIR/competitions_signals.py.backup"
    echo "✅ Sauvegardé: competitions/signals.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/signals.py")"
cp "competitions/signals.py" "/opt/martialcomp/app/competitions/signals.py"
echo "✅ Mis à jour: competitions/signals.py"

# Sauvegarder competitions/models/practitioners.py
if [ -f "/opt/martialcomp/app/competitions/models/practitioners.py" ]; then
    cp "/opt/martialcomp/app/competitions/models/practitioners.py" "$BACKUP_DIR/competitions_models_practitioners.py.backup"
    echo "✅ Sauvegardé: competitions/models/practitioners.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/models/practitioners.py")"
cp "competitions/models/practitioners.py" "/opt/martialcomp/app/competitions/models/practitioners.py"
echo "✅ Mis à jour: competitions/models/practitioners.py"

# Sauvegarder competitions/migrations/0008_fix_family_fields_null.py
if [ -f "/opt/martialcomp/app/competitions/migrations/0008_fix_family_fields_null.py" ]; then
    cp "/opt/martialcomp/app/competitions/migrations/0008_fix_family_fields_null.py" "$BACKUP_DIR/competitions_migrations_0008_fix_family_fields_null.py.backup"
    echo "✅ Sauvegardé: competitions/migrations/0008_fix_family_fields_null.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/competitions/migrations/0008_fix_family_fields_null.py")"
cp "competitions/migrations/0008_fix_family_fields_null.py" "/opt/martialcomp/app/competitions/migrations/0008_fix_family_fields_null.py"
echo "✅ Mis à jour: competitions/migrations/0008_fix_family_fields_null.py"

# Sauvegarder test_organization_signals.py
if [ -f "/opt/martialcomp/app/test_organization_signals.py" ]; then
    cp "/opt/martialcomp/app/test_organization_signals.py" "$BACKUP_DIR/test_organization_signals.py.backup"
    echo "✅ Sauvegardé: test_organization_signals.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/test_organization_signals.py")"
cp "test_organization_signals.py" "/opt/martialcomp/app/test_organization_signals.py"
echo "✅ Mis à jour: test_organization_signals.py"

# Sauvegarder test_subdomain_routing.py
if [ -f "/opt/martialcomp/app/test_subdomain_routing.py" ]; then
    cp "/opt/martialcomp/app/test_subdomain_routing.py" "$BACKUP_DIR/test_subdomain_routing.py.backup"
    echo "✅ Sauvegardé: test_subdomain_routing.py"
fi

# Copier le nouveau fichier
mkdir -p "$(dirname "/opt/martialcomp/app/test_subdomain_routing.py")"
cp "test_subdomain_routing.py" "/opt/martialcomp/app/test_subdomain_routing.py"
echo "✅ Mis à jour: test_subdomain_routing.py"

echo ""
echo "📋 APPLICATION DES MIGRATIONS"
echo "============================"

# Aller dans le répertoire de l'application
cd "$APP_DIR"

# Activer l'environnement virtuel
source /var/www/vhosts/martialcomp.com/httpdocs/venv/bin/activate

# Appliquer les migrations
python manage.py migrate

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

echo ""
echo "🔄 REDÉMARRAGE DU SERVICE"
echo "========================"

# Redémarrer le service Django
sudo systemctl start martialcomp

# Attendre un peu que le service démarre
sleep 5

# Vérifier le statut
sudo systemctl status martialcomp

echo ""
echo "🧪 VALIDATION POST-DÉPLOIEMENT"
echo "=============================="

# Exécuter le script de validation
python validation_post_deployment.py

echo ""
echo "✅ INSTALLATION TERMINÉE!"
echo "========================"
echo ""
echo "📋 ÉTAPES SUIVANTES:"
echo "1. 🧪 Tester la création d'une organisation via l'admin"
echo "2. 🌐 Vérifier qu'un sous-domaine est généré automatiquement"
echo "3. 📱 Tester les QR codes (après correction de la librairie)"
echo "4. 🔍 Surveiller les logs: sudo journalctl -u martialcomp -f"
echo ""
echo "📁 Sauvegardes disponibles dans: $BACKUP_DIR"
echo ""
echo "🎉 Les sites d'organisations automatiques sont maintenant actifs!"
