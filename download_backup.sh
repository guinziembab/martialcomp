#!/bin/bash

# Script pour télécharger la dernière sauvegarde depuis le serveur

echo "=== TÉLÉCHARGEMENT DE LA SAUVEGARDE MARTIALCOMP ==="
echo ""

# Configuration
REMOTE_CONNECTION="martialcomp-production"
REMOTE_BACKUP_DIR="/root/backups"
LOCAL_BACKUP_DIR="/mnt/c/martial_hub_django/martialcomp/backups"

# Créer le répertoire local s'il n'existe pas
mkdir -p $LOCAL_BACKUP_DIR

echo "1. Connexion au serveur pour lister les sauvegardes..."
echo ""

# Lister les sauvegardes disponibles
echo "Sauvegardes disponibles sur le serveur:"
ssh ${REMOTE_CONNECTION} "ls -lh ${REMOTE_BACKUP_DIR}/martialcomp_backup_*_complete.tar.gz 2>/dev/null | tail -5"

echo ""

# Obtenir la dernière sauvegarde
LATEST_BACKUP=$(ssh ${REMOTE_CONNECTION} "ls -t ${REMOTE_BACKUP_DIR}/martialcomp_backup_*_complete.tar.gz 2>/dev/null | head -1")

if [ -z "$LATEST_BACKUP" ]; then
    echo "❌ Aucune sauvegarde trouvée sur le serveur"
    echo "Exécutez d'abord create_full_backup.sh sur le serveur"
    exit 1
fi

BACKUP_FILENAME=$(basename "$LATEST_BACKUP")

echo "2. Téléchargement de la dernière sauvegarde:"
echo "   📦 $BACKUP_FILENAME"
echo ""

# Télécharger avec indication de progression
scp -o ConnectTimeout=30 ${REMOTE_CONNECTION}:${LATEST_BACKUP} ${LOCAL_BACKUP_DIR}/

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sauvegarde téléchargée avec succès!"
    echo "📍 Emplacement local: ${LOCAL_BACKUP_DIR}/${BACKUP_FILENAME}"
    echo "📏 Taille: $(du -h ${LOCAL_BACKUP_DIR}/${BACKUP_FILENAME} | cut -f1)"
    
    # Créer un fichier README
    cat > ${LOCAL_BACKUP_DIR}/README.md << EOF
# Sauvegardes MartialComp

## Dernière sauvegarde: ${BACKUP_FILENAME}

### Contenu de la sauvegarde:
- Base de données PostgreSQL complète
- Tous les fichiers du projet (sans venv et cache)
- Configurations (.env.production, services, nginx)
- Scripts de maintenance

### Pour restaurer cette sauvegarde:
1. Copier le fichier sur le serveur
2. Exécuter le script de restauration correspondant

### Commandes de restauration:
\`\`\`bash
# Copier sur le serveur
scp ${BACKUP_FILENAME} martialcomp-production:/root/backups/

# Se connecter au serveur
ssh martialcomp-production

# Restaurer
cd /root/backups
./restore_${BACKUP_FILENAME%.tar.gz}.sh ${BACKUP_FILENAME}
\`\`\`

### ⚠️ ATTENTION
La restauration remplacera TOUTES les données actuelles!
Assurez-vous de vraiment vouloir restaurer avant de lancer la commande.

Date de téléchargement: $(date)
EOF

    echo ""
    echo "📄 README.md créé dans le dossier des sauvegardes"
    
else
    echo ""
    echo "❌ Erreur lors du téléchargement"
    echo "Vérifiez votre connexion SSH"
    exit 1
fi

echo ""
echo "============================================"
echo "TÉLÉCHARGEMENT TERMINÉ"
echo "============================================"
echo ""
echo "La sauvegarde est maintenant disponible localement:"
echo "📁 ${LOCAL_BACKUP_DIR}/"
echo ""
echo "Pour voir le contenu de l'archive:"
echo "tar -tzf ${LOCAL_BACKUP_DIR}/${BACKUP_FILENAME} | less"
echo ""
echo "============================================"