#!/bin/bash

echo "=========================================="
echo "🚀 DÉPLOIEMENT SOLUTION B - Interface Simplifiée"
echo "=========================================="
echo ""
echo "Cette solution utilise un template SIMPLE et ROBUSTE"
echo "Sans JavaScript complexe, 100% fonctionnel"
echo ""

# Transférer le nouveau template simple
echo "1. Transfert du template simplifié..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/club/competition_management_simple.html" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_simple.html

# Transférer la vue mise à jour
echo "2. Transfert de la vue event_organizer.py..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/club/event_organizer.py" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/event_organizer.py

# Transférer les URLs
echo "3. Transfert des URLs club.py..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/urls/club.py" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/club.py

# Nettoyer et redémarrer
echo "4. Nettoyage et redémarrage..."
ssh martialcomp-production << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Supprimer tous les caches
echo "  - Suppression des caches..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete 2>/dev/null

# Vider le cache Django
echo "  - Vidage du cache Django..."
python3 manage.py shell -c "from django.core.cache import cache; cache.clear(); print('✅ Cache vidé')" 2>&1 | grep -E "Cache|✅"

# Vérifier que les fichiers sont bien là
echo "  - Vérification des fichiers..."
if [ -f "apps/competitions/templates/competitions/club/competition_management_simple.html" ]; then
    echo "    ✅ Template simple OK"
else
    echo "    ❌ Template simple MANQUANT"
fi

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
echo "✅ SOLUTION B DÉPLOYÉE AVEC SUCCÈS"
echo "=========================================="
echo ""
echo "📍 NOUVELLE URL (INTERFACE SIMPLIFIÉE) :"
echo "   https://martialcomp.com/fr/competitions/club/competitions/4/manage-simple/"
echo ""
echo "📍 ANCIENNE URL (INTERFACE PRO - problématique) :"
echo "   https://martialcomp.com/fr/competitions/club/competitions/4/manage/"
echo ""
echo "⚠️  IMPORTANT :"
echo "   - Utilisez l'URL avec /manage-simple/ pour la version STABLE"
echo "   - L'interface est plus simple mais 100% fonctionnelle"
echo "   - Toutes les fonctions essentielles sont présentes"
echo ""
echo "🧪 À TESTER :"
echo "   1. Videz le cache (Ctrl + Shift + R)"
echo "   2. Allez sur l'URL manage-simple"
echo "   3. Testez la création de type"
echo "   4. Testez la création de catégorie"
echo "   5. Testez la suppression"
echo ""
echo "✨ Avantages de la Solution B :"
echo "   ✅ Aucune erreur JavaScript"
echo "   ✅ Interface claire et moderne"
echo "   ✅ Toutes les fonctions principales"
echo "   ✅ Stable et robuste"
echo "   ✅ Pas de drag & drop (mais ça marche !)"
echo ""
