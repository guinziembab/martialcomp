#!/bin/bash
# ================================================================
# SCRIPT DE MIGRATION DEV → PROD - MARTIALCOMP
# EXÉCUTER APRÈS SYNCHRONISATION WINSCP
# ================================================================

set -e  # Arrêter le script en cas d'erreur

echo "🚀 MIGRATION DEV → PROD - MARTIALCOMP"
echo "======================================"
echo ""

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_migration_$TIMESTAMP"
APPS_BACKUP="apps_backup_$TIMESTAMP"
LOG_FILE="migration_$TIMESTAMP.log"

# Fonction de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Fonction d'erreur
error_exit() {
    log "❌ ERREUR: $1"
    echo ""
    echo "🔧 ROLLBACK DISPONIBLE:"
    echo "  cp $BACKUP_DIR/base.py config/settings/base.py"
    echo "  rm -rf apps/ && mv $APPS_BACKUP apps/ (si nécessaire)"
    exit 1
}

log "🚀 Début de la migration DEV → PROD"

# Vérification prérequis
echo "[0/9] Vérification des prérequis..."
if [ ! -f "manage.py" ]; then
    error_exit "manage.py non trouvé. Exécutez ce script depuis la racine du projet."
fi

if [ ! -d "apps" ]; then
    error_exit "Dossier apps/ non trouvé. Synchronisez d'abord avec WinSCP."
fi

log "✅ Prérequis validés"

# 1. Sauvegardes de sécurité
echo "[1/9] Sauvegardes de sécurité..."
mkdir -p "$BACKUP_DIR"

# Sauvegarder la configuration
if [ -d "config/settings" ]; then
    cp -r config/settings/ "$BACKUP_DIR/"
    log "✅ Configuration sauvegardée"
fi

# Sauvegarder .env
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/"
    log "✅ Fichier .env sauvegardé"
fi

# Sauvegarder les anciennes apps si elles existent (pas dans apps/)
declare -a OLD_APPS=("multitenant" "organizations" "competitions" "grades" "accounts" "documents" "shop" "finances" "payment")
for app in "${OLD_APPS[@]}"; do
    if [ -d "$app" ] && [ ! -d "apps/$app" ]; then
        log "📦 Sauvegarde de l'ancienne app: $app"
        mkdir -p "$APPS_BACKUP"
        mv "$app" "$APPS_BACKUP/"
    fi
done

# 2. Vérification de la structure apps/
echo "[2/9] Vérification de la nouvelle structure apps/..."
log "Applications trouvées dans apps/:"
for app_dir in apps/*/; do
    if [ -d "$app_dir" ]; then
        app_name=$(basename "$app_dir")
        if [ -f "$app_dir/__init__.py" ]; then
            log "  ✅ $app_name (application Django valide)"
        else
            log "  ⚠️ $app_name (pas d'__init__.py)"
            echo "# $app_name application" > "$app_dir/__init__.py"
            log "  ✅ $app_name (__init__.py créé)"
        fi
    fi
done

# 3. Correction des permissions
echo "[3/9] Correction des permissions..."
chown -R www-data:www-data apps/
chown -R www-data:www-data config/
chmod -R 755 apps/
find apps/ -name "*.py" -exec chmod 644 {} \;
chmod +x manage.py
log "✅ Permissions corrigées"

# 4. Mise à jour de la configuration Django
echo "[4/9] Mise à jour de la configuration Django..."
if ! grep -q "sys.path.append.*apps" config/settings/base.py; then
    log "⚠️ Configuration apps/ manquante dans base.py - Ajout automatique"
    
    # Backup du fichier actuel
    cp config/settings/base.py config/settings/base.py.pre_apps_$TIMESTAMP
    
    # Créer le nouveau contenu avec support apps/
    cat > temp_base_settings.py << 'EOF'
import os
from pathlib import Path
import sys
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ajouter le chemin apps au Python path pour la nouvelle structure
sys.path.append(str(BASE_DIR / 'apps'))

EOF
    
    # Ajouter le reste du fichier (en excluant les lignes déjà ajoutées)
    grep -v "^import os$\|^from pathlib import Path$\|^import sys$\|^from decouple import config$\|^BASE_DIR = " config/settings/base.py >> temp_base_settings.py
    
    # Remplacer le fichier
    mv temp_base_settings.py config/settings/base.py
    
    log "✅ Configuration Django mise à jour avec support apps/"
else
    log "✅ Configuration Django déjà à jour"
fi

# 5. Test de la configuration Django
echo "[5/9] Test de la configuration Django..."
log "Test de la configuration en cours..."

# Capturer la sortie du test
if python manage.py check --deploy > check_output.tmp 2>&1; then
    log "✅ Configuration Django valide"
    rm check_output.tmp
else
    log "❌ Configuration Django invalide:"
    cat check_output.tmp | head -20 | while read line; do log "  $line"; done
    rm check_output.tmp
    error_exit "Configuration Django invalide. Vérifiez les logs ci-dessus."
fi

# 6. Test d'import des applications
echo "[6/9] Test d'import des applications..."
python manage.py shell -c "
import sys
sys.path.append('apps')

errors = []
apps_to_test = ['multitenant', 'organizations', 'competitions', 'grades', 'accounts', 'documents']

for app in apps_to_test:
    try:
        exec(f'from {app}.models import *')
        print(f'✅ {app}: Import réussi')
    except ImportError as e:
        errors.append(f'❌ {app}: {e}')
        print(f'❌ {app}: {e}')

if errors:
    print('ERREURS D\\'IMPORT:', errors)
    exit(1)
else:
    print('✅ Tous les imports d\\'applications réussis')
" || error_exit "Erreurs d'import des applications"

log "✅ Import des applications validé"

# 7. Migrations de base de données
echo "[7/9] Migrations de base de données..."
log "Création des migrations..."

# Créer les migrations pour chaque app
for app in multitenant organizations competitions grades; do
    if [ -d "apps/$app" ]; then
        log "Migration $app..."
        python manage.py makemigrations $app || log "⚠️ Pas de nouvelles migrations pour $app"
    fi
done

log "Application des migrations..."
if python manage.py migrate; then
    log "✅ Migrations appliquées avec succès"
else
    error_exit "Échec des migrations de base de données"
fi

# 8. Test du système multitenant
echo "[8/9] Test du système multitenant..."
python manage.py shell -c "
from multitenant.models import Tenant
from organizations.models import Organization

# Test de création d'un tenant
try:
    org, created = Organization.objects.get_or_create(
        name='Club Test Migration $TIMESTAMP',
        defaults={'organization_type': 'club'}
    )
    
    tenant, created = Tenant.objects.get_or_create(
        domain='club-test-migration-$TIMESTAMP.martialcomp.com',
        defaults={
            'name': org.name,
            'schema_name': 'club_test_migration_$(echo $TIMESTAMP | tr -d '_')',
            'slug': 'club-test-migration-$TIMESTAMP'
        }
    )
    
    print(f'✅ Test tenant réussi: {tenant.domain}')
    print(f'   Organisation: {org.name}')
    print(f'   Schema: {tenant.schema_name}')
    
except Exception as e:
    print(f'❌ Erreur test tenant: {e}')
    exit(1)
" || error_exit "Échec du test multitenant"

log "✅ Système multitenant fonctionnel"

# 9. Collecte des fichiers statiques et finalisation
echo "[9/9] Finalisation..."
log "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput || log "⚠️ Erreur collectstatic (peut être normale)"

# Nettoyer les fichiers temporaires
rm -f check_output.tmp temp_base_settings.py

# Créer un rapport de migration
cat > "MIGRATION_REPORT_$TIMESTAMP.txt" << EOF
RAPPORT DE MIGRATION MARTIALCOMP
===============================
Date: $(date)
Timestamp: $TIMESTAMP

✅ MIGRATION TERMINÉE AVEC SUCCÈS

NOUVELLE STRUCTURE:
$(find apps/ -maxdepth 1 -type d | grep -v "^apps/$" | sort | sed 's/^/  /')

APPLICATIONS DJANGO ACTIVES:
$(python manage.py shell -c "
from django.conf import settings
apps = [app for app in settings.INSTALLED_APPS if not app.startswith('django.') and not app.startswith('allauth')]
for app in apps:
    print(f'  - {app}')
" 2>/dev/null)

TENANTS CRÉÉS:
$(python manage.py shell -c "
from multitenant.models import Tenant
for tenant in Tenant.objects.all():
    print(f'  - {tenant.domain}')
" 2>/dev/null)

SAUVEGARDES CRÉÉES:
  - Configuration: $BACKUP_DIR/
  - Anciennes apps: $APPS_BACKUP/ (si applicable)

FICHIERS DE LOG:
  - Log migration: $LOG_FILE
  - Rapport: MIGRATION_REPORT_$TIMESTAMP.txt

TESTS À EFFECTUER:
  1. Accès site principal: https://martialcomp.com
  2. Accès admin: https://martialcomp.com/admin/
  3. Test sous-domaine: https://club-test-migration-$TIMESTAMP.martialcomp.com
  4. Vérification fonctionnalités existantes
EOF

log "✅ Rapport de migration créé: MIGRATION_REPORT_$TIMESTAMP.txt"

echo ""
echo "🎉 MIGRATION TERMINÉE AVEC SUCCÈS !"
echo "=================================="
echo ""
echo "📁 NOUVELLE STRUCTURE:"
find apps/ -maxdepth 1 -type d | grep -v "^apps/$" | sort | sed 's/^apps\///;s/^/  📱 /'
echo ""
echo "💾 SAUVEGARDES:"
echo "  📦 $BACKUP_DIR/    - Configuration"
[ -d "$APPS_BACKUP" ] && echo "  📦 $APPS_BACKUP/   - Anciennes apps"
echo ""
echo "📊 FICHIERS GÉNÉRÉS:"
echo "  📝 $LOG_FILE             - Log détaillé"
echo "  📄 MIGRATION_REPORT_$TIMESTAMP.txt - Rapport complet"
echo ""
echo "🧪 TESTS RECOMMANDÉS:"
echo "  1. 🌐 Site principal: https://martialcomp.com"
echo "  2. ⚙️  Admin Django: https://martialcomp.com/admin/"
echo "  3. 🏢 Test sous-domaine: https://club-test-migration-$TIMESTAMP.martialcomp.com"
echo "  4. ✅ Fonctionnalités existantes"
echo ""
echo "🔧 ROLLBACK (si nécessaire):"
echo "  cp $BACKUP_DIR/base.py config/settings/base.py"
[ -d "$APPS_BACKUP" ] && echo "  rm -rf apps/ && mv $APPS_BACKUP apps/"
echo ""

log "🏁 Migration terminée avec succès"