#!/bin/bash

# Script de déploiement pour corriger le problème d'affichage des tarifs (OK partout)
# Date: 2025-10-28

echo "=============================================="
echo "Déploiement de la correction du template welcome"
echo "=============================================="
echo ""

# Définir les chemins
LOCAL_TEMPLATE="/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/welcome.html"
REMOTE_TEMPLATE="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/welcome.html"

echo "1. Connexion au serveur de production..."
ssh martialcomp-production << 'ENDSSH'

# Aller dans le répertoire du projet
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "2. Sauvegarde du template actuel..."
cp apps/competitions/templates/competitions/welcome.html apps/competitions/templates/competitions/welcome.html.backup_$(date +%Y%m%d_%H%M%S)

echo "3. Template sauvegardé avec succès"
echo ""
echo "Maintenant, veuillez exécuter depuis votre machine locale:"
echo "scp $LOCAL_TEMPLATE martialcomp-production:$REMOTE_TEMPLATE"
echo ""
echo "Puis relancez ce script pour continuer..."

ENDSSH

echo ""
echo "=============================================="
echo "Instructions de déploiement manuel:"
echo "=============================================="
echo ""
echo "Étape 1: Transférer le fichier vers le serveur"
echo "scp '$LOCAL_TEMPLATE' martialcomp-production:'$REMOTE_TEMPLATE'"
echo ""
echo "Étape 2: Redémarrer les services (depuis le serveur)"
echo "ssh martialcomp-production"
echo "sudo systemctl restart apache2"
echo "sudo systemctl restart martialcomp"
echo ""
echo "Étape 3: Vider le cache (depuis le serveur)"
echo "cd /var/www/vhosts/martialcomp.com/httpdocs"
echo "source venv/bin/activate"
echo "python manage.py collectstatic --noinput"
echo ""
echo "=============================================="
