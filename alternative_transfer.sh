#!/bin/bash
# Script alternatif pour transfert avec rsync

PRODUCTION_HOST="root@martialcomp.com"
PRODUCTION_DIR="/var/www/martialcomp"

echo "======================================"
echo "TRANSFERT ALTERNATIF AVEC RSYNC"
echo "======================================"
echo ""
echo "Ce script utilise rsync pour un transfert plus fiable."
echo "Vous devrez entrer le mot de passe SSH une seule fois."
echo ""
echo "Appuyez sur ENTER pour continuer..."
read

# Créer une archive complète
echo "Création de l'archive de transfert..."
tar -czf martialcomp_update_$(date +%Y%m%d_%H%M%S).tar.gz \
    transfer_package/ \
    patches/ \
    api/urls.py \
    api_auth/views.py \
    api_auth/models.py \
    api_auth/serializers.py \
    api_auth/urls.py \
    apps/

echo ""
echo "Archive créée. Transfert vers le serveur..."
echo ""

# Utiliser rsync pour le transfert
rsync -avzP --stats \
    martialcomp_update_*.tar.gz \
    $PRODUCTION_HOST:/tmp/

echo ""
echo "======================================"
echo "INSTRUCTIONS POUR FINALISER"
echo "======================================"
echo ""
echo "Connectez-vous au serveur avec:"
echo "  ssh $PRODUCTION_HOST"
echo ""
echo "Puis exécutez:"
echo "  cd /tmp"
echo "  tar -xzf martialcomp_update_*.tar.gz"
echo "  cd transfer_package"
echo "  chmod +x deploy_on_server.sh"
echo "  ./deploy_on_server.sh"
echo ""