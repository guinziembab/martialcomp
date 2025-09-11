#!/bin/bash
# Commandes exactes à exécuter sur le serveur de production

# 1. Se déplacer dans /tmp
cd /tmp

# 2. Extraire l'archive (utilisez le nom exact du fichier)
tar -xzf martialcomp_update_20250826_204045.tar.gz

# 3. Vérifier que l'extraction s'est bien passée
ls -la transfer_package/

# 4. Se déplacer dans le dossier transfer_package
cd transfer_package

# 5. Rendre le script exécutable
chmod +x deploy_on_server.sh

# 6. Exécuter le script de déploiement
./deploy_on_server.sh

# 7. Nettoyer après le déploiement
cd /
rm -rf /tmp/martialcomp_update_20250826_204045.tar.gz
rm -rf /tmp/transfer_package
rm -rf /tmp/patches

# 8. Vérifier que tout fonctionne
systemctl status gunicorn
curl http://localhost/api/health/