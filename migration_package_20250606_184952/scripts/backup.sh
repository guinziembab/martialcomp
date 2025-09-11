#!/bin/bash
# Script de backup avant migration

echo "💾 BACKUP AVANT MIGRATION"
echo "========================="

# Variables
BACKUP_DIR="../backup_$(date +%Y%m%d_%H%M%S)"
PROJECT_DIR="."

echo "Création du backup dans: $BACKUP_DIR"

# Créer le dossier de backup
mkdir -p "$BACKUP_DIR"

# Backup des fichiers
cp -r "$PROJECT_DIR" "$BACKUP_DIR/project"

# Backup de la base de données (si SQLite)
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 "$BACKUP_DIR/"
    echo "✅ Base de données sauvegardée"
fi

# Backup des fichiers statiques
if [ -d "staticfiles" ]; then
    cp -r staticfiles "$BACKUP_DIR/"
    echo "✅ Fichiers statiques sauvegardés"
fi

# Backup des fichiers media
if [ -d "media" ]; then
    cp -r media "$BACKUP_DIR/"
    echo "✅ Fichiers media sauvegardés"
fi

echo "✅ Backup terminé: $BACKUP_DIR"
echo "🔄 Prêt pour la migration!"
