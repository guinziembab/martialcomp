#!/bin/bash

# Script de nettoyage complet pour la production MartialComp
# Supprime tous les fichiers inutiles et temporaires

echo "=== NETTOYAGE COMPLET DE LA PRODUCTION MARTIALCOMP ==="
echo "Date: $(date)"
echo ""

# Fonction pour afficher le nombre de fichiers supprimés
count_and_delete() {
    local pattern="$1"
    local description="$2"
    local count=$(find . -type f -name "$pattern" | wc -l)
    if [ $count -gt 0 ]; then
        echo "Suppression de $count fichiers $description..."
        find . -type f -name "$pattern" -delete
        echo "✓ Supprimé $count fichiers $description"
    else
        echo "✓ Aucun fichier $description trouvé"
    fi
}

# Fonction pour supprimer les dossiers vides
remove_empty_dirs() {
    local dir_pattern="$1"
    local description="$2"
    local count=$(find . -type d -name "$dir_pattern" -empty | wc -l)
    if [ $count -gt 0 ]; then
        echo "Suppression de $count dossiers vides $description..."
        find . -type d -name "$dir_pattern" -empty -delete
        echo "✓ Supprimé $count dossiers vides $description"
    else
        echo "✓ Aucun dossier vide $description trouvé"
    fi
}

echo "1. Suppression des fichiers de sauvegarde et temporaires..."
count_and_delete "*.backup_*" "de sauvegarde"
count_and_delete "*.bak" "de sauvegarde (.bak)"
count_and_delete "*.tmp" "temporaires"
count_and_delete "*.temp" "temporaires"
count_and_delete "*~" "de sauvegarde (~)"
count_and_delete ".#*" "de verrouillage"

echo ""
echo "2. Suppression des archives compressées..."
count_and_delete "*.zip" "ZIP"
count_and_delete "*.gz" "GZ"
count_and_delete "*.tar" "TAR"
count_and_delete "*.tar.gz" "TAR.GZ"
count_and_delete "*.rar" "RAR"
count_and_delete "*.7z" "7Z"

echo ""
echo "3. Suppression des fichiers de cache Python..."
count_and_delete "*.pyc" "Python compilés (.pyc)"
count_and_delete "*.pyo" "Python optimisés (.pyo)"
count_and_delete "__pycache__" "dossiers __pycache__"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "4. Suppression des fichiers de développement..."
count_and_delete "*.log" "de logs"
count_and_delete "*.sqlite3" "SQLite (sauf db.sqlite3 principal)"
count_and_delete "*.db" "de base de données"
count_and_delete "*.sql" "SQL (sauf ceux nécessaires)"

echo ""
echo "5. Suppression des fichiers de configuration temporaires..."
count_and_delete "*.env.local" "d'environnement local"
count_and_delete "*.env.backup" "d'environnement de sauvegarde"
count_and_delete "*.conf.backup" "de configuration de sauvegarde"

echo ""
echo "6. Suppression des fichiers de test et de debug..."
count_and_delete "*test*.py" "de test Python"
count_and_delete "*debug*.py" "de debug Python"
count_and_delete "*_test.py" "de test Python"
count_and_delete "test_*.py" "de test Python"

echo ""
echo "7. Suppression des fichiers de clés SSH et certificats..."
count_and_delete "*.pem" "de certificats"
count_and_delete "*.key" "de clés privées"
count_and_delete "*.pub" "de clés publiques (sauf nécessaires)"

echo ""
echo "8. Suppression des fichiers de documentation temporaires..."
count_and_delete "*.md.backup" "de documentation de sauvegarde"
count_and_delete "*.txt.backup" "de texte de sauvegarde"

echo ""
echo "9. Suppression des dossiers vides..."
remove_empty_dirs "temp_*" "temporaires"
remove_empty_dirs "*_backup" "de sauvegarde"
remove_empty_dirs "*_old" "anciens"

echo ""
echo "10. Nettoyage des fichiers spécifiques à MartialComp..."
# Supprimer les fichiers de base de données temporaires
if [ -f "db_temp.sqlite3" ]; then
    rm -f db_temp.sqlite3
    echo "✓ Supprimé db_temp.sqlite3"
fi

if [ -f "db_translation_only.sqlite3" ]; then
    rm -f db_translation_only.sqlite3
    echo "✓ Supprimé db_translation_only.sqlite3"
fi

# Supprimer les fichiers de debug spécifiques
count_and_delete "debug_*.py" "de debug spécifiques"
count_and_delete "diagnostic_*.sh" "de diagnostic"
count_and_delete "fix_*.py" "de correction"
count_and_delete "fix_*.sh" "de correction"

echo ""
echo "11. Vérification de l'espace disque..."
echo "Espace disque avant nettoyage:"
df -h .

echo ""
echo "12. Nettoyage des fichiers avec des noms étranges..."
# Supprimer les fichiers avec des noms suspects
find . -type f -name "=*" -delete 2>/dev/null || true
find . -type f -name "*Cache*" -delete 2>/dev/null || true
find . -type f -size 0 -name ".*" -delete 2>/dev/null || true

echo ""
echo "13. Protection des fichiers essentiels..."
echo "Fichiers essentiels conservés:"
echo "- manage.py"
echo "- requirements.txt"
echo "- settings.py"
echo "- urls.py"
echo "- wsgi.py"
echo "- db.sqlite3 (base de données principale)"

echo ""
echo "14. Vérification finale de l'espace disque..."
echo "Espace disque après nettoyage:"
df -h .

echo ""
echo "=== NETTOYAGE TERMINÉ ==="
echo "Date: $(date)"
echo ""
echo "Fichiers et dossiers conservés:"
echo "- Structure Django complète"
echo "- Templates et fichiers statiques"
echo "- Base de données principale"
echo "- Configuration de production"
echo "- Scripts de déploiement essentiels"

echo ""
echo "Pour vérifier la structure Django:"
echo "python manage.py check --deploy"
echo ""
echo "Pour tester le serveur:"
echo "python manage.py runserver 0.0.0.0:8000" 