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
