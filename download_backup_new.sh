#!/bin/bash
# Script pour télécharger la sauvegarde de production

BACKUP_FILE="martialcomp_backup_complete_20251115_125258.tar.gz"
LOCAL_DIR="./backups_production"
REMOTE_FILE="martialcomp-production:/root/backups/${BACKUP_FILE}"

echo "=== TÉLÉCHARGEMENT DE LA SAUVEGARDE ==="
echo ""

# Créer le répertoire local
mkdir -p ${LOCAL_DIR}

echo "1. Téléchargement de la sauvegarde (1.2G)..."
echo "   Depuis: ${REMOTE_FILE}"
echo "   Vers: ${LOCAL_DIR}/${BACKUP_FILE}"
echo ""
echo "   Cela peut prendre plusieurs minutes..."

# Télécharger avec affichage de la progression
scp -o "Compression=yes" ${REMOTE_FILE} ${LOCAL_DIR}/

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Téléchargement réussi !"
    echo "✓ Fichier sauvé dans: ${LOCAL_DIR}/${BACKUP_FILE}"
    echo "✓ Taille: $(ls -lh ${LOCAL_DIR}/${BACKUP_FILE} | awk '{print $5}')"
    
    # Créer un fichier de vérification
    echo ""
    echo "2. Création du fichier de vérification..."
    cd ${LOCAL_DIR}
    sha256sum ${BACKUP_FILE} > ${BACKUP_FILE}.sha256
    echo "✓ Checksum créé: ${BACKUP_FILE}.sha256"
    
    echo ""
    echo "=== SAUVEGARDE LOCALE TERMINÉE ==="
    echo "Pour extraire et explorer la sauvegarde:"
    echo "  cd ${LOCAL_DIR}"
    echo "  tar -xzf ${BACKUP_FILE}"
else
    echo ""
    echo "✗ ERREUR lors du téléchargement !"
fi