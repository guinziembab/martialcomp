#!/bin/bash

echo "=========================================="
echo "Déploiement Correction Types - Version Finale"
echo "=========================================="

# Transférer le template
echo "1. Transfert du template..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/club/competition_management_pro.html" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_pro.html

# Transférer la vue
echo "2. Transfert de la vue..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/club/event_organizer.py" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/event_organizer.py

# Transférer les URLs
echo "3. Transfert des URLs..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/urls/club.py" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/club.py

# Nettoyer et redémarrer
echo "4. Nettoyage et redémarrage..."
ssh martialcomp-production << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Supprimer tous les caches
echo "  - Suppression des caches Python..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete 2>/dev/null

# Vider le cache Django
echo "  - Vidage du cache Django..."
python3 manage.py shell -c "from django.core.cache import cache; cache.clear(); print('Cache vidé')" 2>&1 | grep -i "cache"

# Redémarrer les services
echo "  - Redémarrage de Gunicorn..."
sudo systemctl restart martialcomp

echo "  - Attente de 3 secondes..."
sleep 3

echo "  - Redémarrage d'Apache..."
sudo systemctl restart apache2

echo "  - Attente de 2 secondes..."
sleep 2

echo ""
echo "✅ Déploiement terminé !"
ENDSSH

echo ""
echo "=========================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=========================================="
echo ""
echo "Maintenant:"
echo "1. Allez sur: https://martialcomp.com/fr/competitions/club/competitions/4/manage/"
echo "2. Videz le cache: Ctrl + Shift + R"
echo "3. Ouvrez la Console (F12)"
echo "4. Vérifiez qu'il n'y a AUCUNE erreur JavaScript"
echo "5. Testez la création de type"
echo ""
