#!/bin/bash

# Script de sauvegarde avant nettoyage complet
# À exécuter sur le serveur de production AVANT toute suppression

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups"
BACKUP_NAME="martialcomp_full_backup_$(date +%Y%m%d_%H%M%S)"

echo "💾 Sauvegarde Complète Production - MartialComp"
echo "📅 Date: $(date)"
echo "📍 Source: $PROD_DIR"
echo "📦 Destination: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
echo ""

# Vérifications
if [ ! -d "$PROD_DIR" ]; then
    echo "❌ Erreur: Le répertoire $PROD_DIR n'existe pas!"
    exit 1
fi

# Créer le répertoire de backup si nécessaire
mkdir -p $BACKUP_DIR

echo "⚠️  ATTENTION: Cette sauvegarde va inclure:"
echo "   - Tous les fichiers de code"
echo "   - Les uploads utilisateurs (media/)"
echo "   - Les fichiers de configuration"
echo "   - Les logs existants"
echo "   - La base de données (export séparé recommandé)"
echo ""
echo "Voulez-vous continuer? (yes/no)"
read -r response

if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "❌ Sauvegarde annulée."
    exit 0
fi

echo ""
echo "🔍 Analyse de l'espace nécessaire..."
SIZE_NEEDED=$(du -sb $PROD_DIR 2>/dev/null | cut -f1)
SIZE_AVAILABLE=$(df $BACKUP_DIR | tail -1 | awk '{print $4}')
SIZE_NEEDED_MB=$((SIZE_NEEDED / 1024 / 1024))
SIZE_AVAILABLE_MB=$((SIZE_AVAILABLE / 1024))

echo "   - Espace nécessaire: ~${SIZE_NEEDED_MB} MB"
echo "   - Espace disponible: ${SIZE_AVAILABLE_MB} MB"

if [ $SIZE_NEEDED -gt $((SIZE_AVAILABLE * 1024)) ]; then
    echo "❌ Erreur: Pas assez d'espace disque!"
    exit 1
fi

# 1. Export de la base de données (si PostgreSQL)
echo ""
echo "🗄️  Export de la base de données..."
if command -v pg_dump &> /dev/null; then
    echo "PostgreSQL détecté. Voulez-vous exporter la base? (yes/no)"
    read -r response
    if [[ "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
        echo "Nom de la base de données:"
        read -r DB_NAME
        echo "Utilisateur PostgreSQL:"
        read -r DB_USER
        
        pg_dump -U $DB_USER -d $DB_NAME -f "$BACKUP_DIR/${BACKUP_NAME}_database.sql"
        
        if [ $? -eq 0 ]; then
            echo "✅ Base de données exportée: ${BACKUP_NAME}_database.sql"
        else
            echo "⚠️  Erreur lors de l'export de la base de données"
        fi
    fi
else
    echo "PostgreSQL non détecté ou pg_dump non disponible."
fi

# 2. Créer l'archive de sauvegarde
echo ""
echo "📦 Création de l'archive de sauvegarde..."
echo "   Cela peut prendre plusieurs minutes..."

cd $(dirname $PROD_DIR)
tar -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    $(basename $PROD_DIR) 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Archive créée avec succès!"
else
    echo "❌ Erreur lors de la création de l'archive!"
    exit 1
fi

# 3. Sauvegarder les éléments critiques séparément
echo ""
echo "📋 Sauvegarde des éléments critiques..."

cd $PROD_DIR

# Media (uploads utilisateurs)
if [ -d "media" ] && [ "$(ls -A media 2>/dev/null)" ]; then
    echo "   → Sauvegarde du dossier media..."
    tar -czf "$BACKUP_DIR/${BACKUP_NAME}_media.tar.gz" media/
fi

# Configuration
if [ -f ".env" ] || [ -f ".env.production" ]; then
    echo "   → Sauvegarde des fichiers de configuration..."
    tar -czf "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" .env* 2>/dev/null
fi

# Liste des fichiers importants
echo ""
echo "📝 Génération de la liste des fichiers..."
find . -type f -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" | sort > "$BACKUP_DIR/${BACKUP_NAME}_filelist.txt"

# 4. Créer un fichier de métadonnées
cat > "$BACKUP_DIR/${BACKUP_NAME}_info.txt" << EOF
Sauvegarde MartialComp Production
==================================
Date: $(date)
Serveur: $(hostname)
Répertoire source: $PROD_DIR
Taille originale: $(du -sh $PROD_DIR | cut -f1)

Fichiers de sauvegarde créés:
- ${BACKUP_NAME}.tar.gz (archive complète)
$([ -f "$BACKUP_DIR/${BACKUP_NAME}_database.sql" ] && echo "- ${BACKUP_NAME}_database.sql (base de données)")
$([ -f "$BACKUP_DIR/${BACKUP_NAME}_media.tar.gz" ] && echo "- ${BACKUP_NAME}_media.tar.gz (uploads utilisateurs)")
$([ -f "$BACKUP_DIR/${BACKUP_NAME}_config.tar.gz" ] && echo "- ${BACKUP_NAME}_config.tar.gz (configuration)")
- ${BACKUP_NAME}_filelist.txt (liste des fichiers)
- ${BACKUP_NAME}_info.txt (ce fichier)

Instructions de restauration:
1. Extraire l'archive principale: tar -xzf ${BACKUP_NAME}.tar.gz
2. Restaurer la base de données: psql -U user -d dbname < ${BACKUP_NAME}_database.sql
3. Vérifier les permissions des fichiers
4. Redémarrer les services
EOF

# 5. Afficher le résumé
echo ""
echo "✅ Sauvegarde terminée avec succès!"
echo ""
echo "📊 Résumé des sauvegardes:"
echo "============================"
ls -lh $BACKUP_DIR/${BACKUP_NAME}* | awk '{print $9 ": " $5}'
echo ""
echo "📍 Emplacement: $BACKUP_DIR"
echo ""
echo "⚠️  IMPORTANT: Vérifiez que la sauvegarde est complète avant de procéder au nettoyage!"
echo ""
echo "💡 Prochaines étapes:"
echo "1. Vérifier l'intégrité de la sauvegarde"
echo "2. Copier la sauvegarde vers un emplacement sûr (hors serveur)"
echo "3. Procéder au nettoyage avec production_clean_all.sh"