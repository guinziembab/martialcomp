#!/bin/bash

echo "=== Déploiement de la correction du JavaScript parasite ==="

# Copier le script
echo "Copie du script de correction..."
scp remove_js_text.py root@martialcomp.com:/tmp/

# Exécuter sur le serveur
echo "Exécution de la correction..."
ssh root@martialcomp.com "cd /var/www/vhosts/martialcomp.com/httpdocs && python3 /tmp/remove_js_text.py && rm -f /tmp/remove_js_text.py"

echo "Correction déployée!"