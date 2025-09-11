#!/bin/bash
# Script d'installation automatique pour la production
# Généré le 2025-06-13 19:26:22

echo "🚀 INSTALLATION DES CORRECTIONS EN PRODUCTION"
echo "=============================================="

# Arrêter le service Django
echo "🔄 Arrêt du service Django..."
sudo systemctl stop martialcomp

# Sauvegardes
BACKUP_DIR="/opt/martialcomp/backups/fix_20250613_192621"
mkdir -p "$BACKUP_DIR"

echo "💾 Création des sauvegardes..."

# Sauvegarder competitions/models/practitioners.py
if [ -f "/opt/martialcomp/app/competitions/models/practitioners.py" ]; then
    cp "/opt/martialcomp/app/competitions/models/practitioners.py" "$BACKUP_DIR/"
    echo "✅ Sauvegardé: competitions/models/practitioners.py"
fi

# Copier le nouveau fichier
cp "competitions/models/practitioners.py" "/opt/martialcomp/app/competitions/models/practitioners.py"
echo "✅ Mis à jour: competitions/models/practitioners.py"

# Sauvegarder competitions/migrations/0008_fix_family_fields_null.py
if [ -f "/opt/martialcomp/app/competitions/migrations/0008_fix_family_fields_null.py" ]; then
    cp "/opt/martialcomp/app/competitions/migrations/0008_fix_family_fields_null.py" "$BACKUP_DIR/"
    echo "✅ Sauvegardé: competitions/migrations/0008_fix_family_fields_null.py"
fi

# Copier le nouveau fichier
cp "competitions/migrations/0008_fix_family_fields_null.py" "/opt/martialcomp/app/competitions/migrations/0008_fix_family_fields_null.py"
echo "✅ Mis à jour: competitions/migrations/0008_fix_family_fields_null.py"

# Sauvegarder competitions/signals.py
if [ -f "/opt/martialcomp/app/competitions/signals.py" ]; then
    cp "/opt/martialcomp/app/competitions/signals.py" "$BACKUP_DIR/"
    echo "✅ Sauvegardé: competitions/signals.py"
fi

# Copier le nouveau fichier
cp "competitions/signals.py" "/opt/martialcomp/app/competitions/signals.py"
echo "✅ Mis à jour: competitions/signals.py"

# Sauvegarder grades/signals.py
if [ -f "/opt/martialcomp/app/grades/signals.py" ]; then
    cp "/opt/martialcomp/app/grades/signals.py" "$BACKUP_DIR/"
    echo "✅ Sauvegardé: grades/signals.py"
fi

# Copier le nouveau fichier
cp "grades/signals.py" "/opt/martialcomp/app/grades/signals.py"
echo "✅ Mis à jour: grades/signals.py"

# Appliquer les migrations
echo "🔄 Application des migrations..."
cd /opt/martialcomp/app
python3 manage.py migrate

# Redémarrer le service
echo "🔄 Redémarrage du service Django..."
sudo systemctl start martialcomp

# Vérifier le statut
echo "📊 Vérification du statut..."
sudo systemctl status martialcomp

echo "✅ Installation terminée!"
echo "📋 Testez maintenant l'ajout d'un pratiquant sur l'interface web"
echo "📁 Sauvegardes disponibles dans: $BACKUP_DIR"
