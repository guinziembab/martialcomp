#!/bin/bash

# Script de nettoyage pour préparer le transfert en production
# Ce script supprime les fichiers non essentiels pour réduire la taille du package

echo "🧹 Début du nettoyage pour production..."

# 1. Supprimer tous les fichiers __pycache__ et .pyc
echo "Suppression des fichiers Python compilés..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

# 2. Supprimer les archives et backups
echo "Suppression des archives et backups..."
rm -f *.tar.gz *.zip
rm -rf backup_* mobile_backup_* deployment_package_* production_package_* production_installer

# 3. Supprimer les fichiers de documentation temporaires
echo "Suppression des fichiers de documentation temporaires..."
rm -f BACKUP_*.md *_FIX_*.md STATUS_*.md DASHBOARD_*.md ERREURS_*.md FEDERATION_*.md
rm -f FINANCES_*.md IMPORT_*.md MOCK_*.md ORGANIZATION_*.md TECHNICAL_*.md VALIDATION_*.md
rm -f diagnostic_*.js test_*.js debug_*.js

# 4. Supprimer les environnements virtuels
echo "Suppression des environnements virtuels..."
rm -rf venv env .venv temp_venv

# 5. Supprimer les fichiers de base de données locales
echo "Suppression des fichiers de base de données locales..."
rm -f *.sqlite3 *.db *.sql

# 6. Supprimer les fichiers de logs
echo "Suppression des logs..."
find . -name "*.log" -delete

# 7. Nettoyer le dossier .git (optionnel - décommentez si nécessaire)
# echo "Nettoyage de l'historique Git..."
# git gc --aggressive --prune=now

# 8. Supprimer les fichiers Python de validation temporaires
echo "Suppression des fichiers de validation..."
rm -f validate_python_files.py

# 9. Supprimer les fichiers HTML d'erreur temporaires
echo "Suppression des templates d'erreur temporaires..."
rm -f templates/error.html

echo "✅ Nettoyage terminé!"
echo ""
echo "Taille estimée économisée:"
echo "- Environnements virtuels: ~585 MB"
echo "- Archives et backups: ~200 MB"  
echo "- Fichiers temporaires Python: ~50 MB"
echo "- Historique Git (si nettoyé): ~100 MB"
echo ""
echo "Total estimé: ~935 MB économisés"