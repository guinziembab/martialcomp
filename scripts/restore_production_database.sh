#!/bin/bash

# Script de restauration de la base de données de production MartialComp
# Date: $(date)

echo "=== RESTAURATION BASE DE DONNEES PRODUCTION MARTIALCOMP ==="

# Variables
BACKUP_FILE="/mnt/c/martial_hub_django/martialcomp_backup_local/martialcomp_light_backup_20250716_235217/martialcomp_db_backup.sql"
REMOTE_USER="root"
REMOTE_HOST="martialcomp.com"
REMOTE_BACKUP_PATH="/tmp/martialcomp_db_backup.sql"
DB_NAME="martialcomp_db"
DB_USER="martialcomp_user"

echo "1. Vérification de l'existence du fichier de sauvegarde..."
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERREUR: Fichier de sauvegarde introuvable: $BACKUP_FILE"
    exit 1
fi

echo "   ✓ Fichier trouvé ($(du -h "$BACKUP_FILE" | cut -f1))"

echo "2. Transfert du fichier de sauvegarde vers le serveur..."
scp "$BACKUP_FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_BACKUP_PATH"

if [ $? -eq 0 ]; then
    echo "   ✓ Transfert réussi"
else
    echo "   ✗ Erreur lors du transfert"
    exit 1
fi

echo "3. Commandes à exécuter sur le serveur de production:"
echo "   Connectez-vous au serveur: ssh root@martialcomp.com"
echo ""
echo "   Puis exécutez les commandes suivantes:"
echo ""
echo "   # Arrêter Gunicorn temporairement"
echo "   sudo systemctl stop gunicorn"
echo ""
echo "   # Sauvegarder l'état actuel (optionnel)"
echo "   pg_dump -U martialcomp_user -h localhost martialcomp_db > /tmp/current_state_backup.sql"
echo ""
echo "   # Restaurer la base de données"
echo "   psql -U martialcomp_user -h localhost -d martialcomp_db < $REMOTE_BACKUP_PATH"
echo ""
echo "   # Redémarrer Gunicorn"
echo "   sudo systemctl start gunicorn"
echo ""
echo "   # Vérifier le statut"
echo "   sudo systemctl status gunicorn"
echo ""

echo "4. Après la restauration, testez:"
echo "   - Site principal: https://martialcomp.com"
echo "   - Interface admin: https://martialcomp.com/admin/"
echo ""

echo "=== Script de transfert terminé ==="
echo "Suivez maintenant les instructions ci-dessus sur le serveur."