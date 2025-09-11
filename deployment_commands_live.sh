#!/bin/bash
# Commandes à exécuter sur le serveur de production

# 1. Vérifier si le fichier a été transféré
echo "1. Vérification des fichiers transférés..."
ls -la /tmp/martialcomp_update_*.tar.gz

# 2. Si le fichier existe, extraire
echo "2. Extraction de l'archive..."
cd /tmp
tar -xzf martialcomp_update_*.tar.gz

# 3. Vérifier l'extraction
echo "3. Contenu extrait :"
ls -la /tmp/transfer_package/
ls -la /tmp/patches/

# 4. Aller dans transfer_package
cd /tmp/transfer_package

# 5. Rendre le script exécutable
echo "4. Préparation du script de déploiement..."
chmod +x deploy_on_server.sh

# 6. Vérifier le contenu du script
echo "5. Aperçu du script de déploiement :"
head -20 deploy_on_server.sh

# 7. Exécuter le déploiement
echo "6. Exécution du déploiement..."
./deploy_on_server.sh