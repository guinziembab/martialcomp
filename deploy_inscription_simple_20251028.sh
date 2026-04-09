#!/bin/bash

echo "=========================================="
echo "🚀 DÉPLOIEMENT - Formulaire d'Inscription Simplifié"
echo "=========================================="
echo ""

# Transférer le nouveau template
echo "1. Transfert du template d'inscription simplifié..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/club/competition_registration_simple.html" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_registration_simple.html

# Transférer le template de gestion mis à jour
echo "2. Transfert du template de gestion (avec lien mis à jour)..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/club/competition_management_simple.html" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_simple.html

# Transférer la vue registrations.py
echo "3. Transfert de registrations.py..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/club/registrations.py" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/registrations.py

# Transférer competitions.py avec l'API
echo "4. Transfert de competitions.py (avec API)..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/competitions.py" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/competitions.py

# Transférer les URLs
echo "5. Transfert des URLs competitions.py..."
scp "/mnt/c/martial_hub_django/martialcomp/apps/competitions/urls/competitions.py" \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/competitions.py

# Nettoyer et redémarrer
echo "6. Nettoyage et redémarrage..."
ssh martialcomp-production << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "  - Suppression des caches..."
find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find . -name '*.pyc' -delete 2>/dev/null

echo "  - Vidage du cache Django..."
python3 manage.py shell -c "from django.core.cache import cache; cache.clear(); print('✅ Cache vidé')" 2>&1 | grep '✅'

echo "  - Redémarrage de Gunicorn..."
sudo systemctl restart martialcomp

sleep 3

echo ""
echo "✅ Déploiement terminé !"
ENDSSH

echo ""
echo "=========================================="
echo "✅ FORMULAIRE D'INSCRIPTION SIMPLIFIÉ DÉPLOYÉ"
echo "=========================================="
echo ""
echo "📍 URL D'ACCÈS :"
echo "   https://martialcomp.com/fr/competitions/club/competition-registration/4/?simple=1"
echo ""
echo "🧪 À TESTER :"
echo "   1. Videz le cache (Ctrl + Shift + R)"
echo "   2. Sélectionnez un type de compétition"
echo "   3. Sélectionnez une catégorie (elle se charge automatiquement)"
echo "   4. Cochez des pratiquants"
echo "   5. Cliquez 'Inscrire'"
echo ""
echo "✨ Fonctionnalités :"
echo "   ✅ Sélection de type → Charge les catégories"
echo "   ✅ Sélection de catégorie"
echo "   ✅ Sélection multiple de pratiquants"
echo "   ✅ Résumé en temps réel"
echo "   ✅ Validation automatique"
echo "   ✅ Feedback visuel"
echo ""
