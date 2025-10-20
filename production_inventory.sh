#!/bin/bash

# Script d'inventaire pour analyser l'état actuel de la production
# À exécuter sur le serveur de production

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
REPORT_FILE="inventory_production_$(date +%Y%m%d_%H%M%S).txt"

echo "📊 Inventaire de Production - MartialComp"
echo "📅 Date: $(date)"
echo "📍 Répertoire: $PROD_DIR"
echo ""

# Vérifier si on est dans le bon environnement
if [ ! -d "$PROD_DIR" ]; then
    echo "❌ Erreur: Le répertoire $PROD_DIR n'existe pas!"
    echo "Êtes-vous sur le serveur de production?"
    exit 1
fi

# Commencer le rapport
cat > $REPORT_FILE << EOF
===============================================
INVENTAIRE PRODUCTION MARTIALCOMP
===============================================
Date: $(date)
Répertoire: $PROD_DIR
===============================================

EOF

cd $PROD_DIR

echo "1️⃣ Analyse de l'espace disque..."
echo "1. ESPACE DISQUE" >> $REPORT_FILE
echo "=================" >> $REPORT_FILE
du -sh . >> $REPORT_FILE 2>/dev/null
echo "" >> $REPORT_FILE

echo "2️⃣ Taille des principaux dossiers..."
echo "2. TAILLE DES DOSSIERS PRINCIPAUX" >> $REPORT_FILE
echo "===================================" >> $REPORT_FILE
du -sh */ 2>/dev/null | sort -hr >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "3️⃣ Recherche des gros fichiers (>10MB)..."
echo "3. FICHIERS VOLUMINEUX (>10MB)" >> $REPORT_FILE
echo "================================" >> $REPORT_FILE
find . -type f -size +10M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "4️⃣ Inventaire des archives et backups..."
echo "4. ARCHIVES ET BACKUPS" >> $REPORT_FILE
echo "=======================" >> $REPORT_FILE
find . -type f \( -name "*.tar.gz" -o -name "*.zip" -o -name "*.tar" -o -name "*.gz" -o -name "*.sql" -o -name "*.bak" \) -exec ls -lh {} \; 2>/dev/null >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "5️⃣ Fichiers temporaires Python..."
echo "5. FICHIERS TEMPORAIRES PYTHON" >> $REPORT_FILE
echo "================================" >> $REPORT_FILE
echo "Nombre de fichiers .pyc: $(find . -name "*.pyc" 2>/dev/null | wc -l)" >> $REPORT_FILE
echo "Nombre de dossiers __pycache__: $(find . -name "__pycache__" -type d 2>/dev/null | wc -l)" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "6️⃣ Environnements virtuels Python..."
echo "6. ENVIRONNEMENTS VIRTUELS" >> $REPORT_FILE
echo "===========================" >> $REPORT_FILE
find . -maxdepth 3 -type d \( -name "venv" -o -name "env" -o -name ".venv" -o -name "virtualenv" \) -exec ls -ld {} \; 2>/dev/null >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "7️⃣ Fichiers de logs..."
echo "7. FICHIERS DE LOGS" >> $REPORT_FILE
echo "====================" >> $REPORT_FILE
find . -name "*.log" -type f -exec ls -lh {} \; 2>/dev/null | head -20 >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "8️⃣ Bases de données locales..."
echo "8. BASES DE DONNÉES LOCALES" >> $REPORT_FILE
echo "=============================" >> $REPORT_FILE
find . -type f \( -name "*.sqlite3" -o -name "*.db" \) -exec ls -lh {} \; 2>/dev/null >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "9️⃣ Structure des dossiers (niveau 1)..."
echo "9. STRUCTURE ACTUELLE" >> $REPORT_FILE
echo "======================" >> $REPORT_FILE
ls -la | grep "^d" >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "🔟 Fichiers de configuration sensibles..."
echo "10. FICHIERS DE CONFIGURATION" >> $REPORT_FILE
echo "==============================" >> $REPORT_FILE
find . -maxdepth 3 -type f \( -name ".env*" -o -name "*.key" -o -name "*secret*" \) -exec ls -la {} \; 2>/dev/null >> $REPORT_FILE
echo "" >> $REPORT_FILE

echo "1️⃣1️⃣ Contenu du dossier media..."
echo "11. CONTENU MEDIA" >> $REPORT_FILE
echo "==================" >> $REPORT_FILE
if [ -d "media" ]; then
    echo "Taille totale: $(du -sh media 2>/dev/null | cut -f1)" >> $REPORT_FILE
    echo "Nombre de fichiers: $(find media -type f 2>/dev/null | wc -l)" >> $REPORT_FILE
    echo "Types de fichiers:" >> $REPORT_FILE
    find media -type f -exec file {} \; 2>/dev/null | cut -d: -f2 | sort | uniq -c | sort -nr | head -10 >> $REPORT_FILE
fi
echo "" >> $REPORT_FILE

echo "1️⃣2️⃣ État Git (si présent)..."
echo "12. ÉTAT GIT" >> $REPORT_FILE
echo "=============" >> $REPORT_FILE
if [ -d ".git" ]; then
    echo "Taille .git: $(du -sh .git 2>/dev/null | cut -f1)" >> $REPORT_FILE
    echo "Branch actuelle: $(git branch --show-current 2>/dev/null)" >> $REPORT_FILE
    echo "Dernier commit: $(git log -1 --oneline 2>/dev/null)" >> $REPORT_FILE
fi
echo "" >> $REPORT_FILE

echo ""
echo "✅ Inventaire terminé!"
echo "📄 Rapport sauvé dans: $REPORT_FILE"
echo ""
echo "📊 Résumé rapide:"
echo "=================="
echo "- Espace total utilisé: $(du -sh . 2>/dev/null | cut -f1)"
echo "- Fichiers .pyc: $(find . -name "*.pyc" 2>/dev/null | wc -l)"
echo "- Archives trouvées: $(find . -type f \( -name "*.tar.gz" -o -name "*.zip" \) 2>/dev/null | wc -l)"
echo "- Fichiers logs: $(find . -name "*.log" -type f 2>/dev/null | wc -l)"
echo ""
echo "💡 Prochaines étapes:"
echo "1. Examiner le rapport: cat $REPORT_FILE"
echo "2. Identifier ce qui doit être préservé"
echo "3. Exécuter le script de sauvegarde"
echo "4. Procéder au nettoyage"