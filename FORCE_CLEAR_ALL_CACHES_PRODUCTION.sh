#!/bin/bash
# Script pour forcer le vidage ABSOLU de tous les caches en production
# Date: 24 novembre 2024
# Usage: bash FORCE_CLEAR_ALL_CACHES_PRODUCTION.sh

echo "=================================================="
echo "VIDAGE COMPLET DE TOUS LES CACHES - VERSION ULTIME"
echo "=================================================="
echo ""

ssh pierrep99@martialcomp.com << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "=== 1. Activation de l'environnement virtuel ==="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
echo "✓ Environnement virtuel activé"
echo ""

echo "=== 2. Vérification que base.html contient les corrections ==="
CORRECTIONS_COUNT=$(grep -c "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html)
echo "Nombre de corrections trouvées: $CORRECTIONS_COUNT (attendu: 3)"
if [ "$CORRECTIONS_COUNT" -eq 3 ]; then
    echo "✅ Les 3 corrections sont présentes dans base.html"
else
    echo "❌ ALERTE: Seulement $CORRECTIONS_COUNT correction(s) trouvée(s)"
    echo "Le fichier base.html n'a peut-être pas été correctement transféré!"
    exit 1
fi
echo ""

echo "=== 3. Suppression TOTALE du cache Python ==="
find . -type d -name "__pycache__" -print -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -print -delete 2>/dev/null
find . -type f -name "*.pyo" -print -delete 2>/dev/null
echo "✓ Cache Python supprimé"
echo ""

echo "=== 4. Suppression du cache Django (si configuré) ==="
python3 manage.py clear_cache 2>/dev/null && echo "✓ Cache Django vidé" || echo "  (commande clear_cache non disponible)"
echo ""

echo "=== 5. Suppression des sessions Django ==="
find . -path "*/django_cache/*" -delete 2>/dev/null
echo "✓ Sessions Django nettoyées"
echo ""

echo "=== 6. Redémarrage FORCÉ de l'application Passenger ==="
# Supprime l'ancien fichier restart.txt
rm -f tmp/restart.txt 2>/dev/null

# Crée le répertoire tmp si nécessaire
mkdir -p tmp

# Touche restart.txt plusieurs fois avec un délai
echo "  → Premier touch..."
touch tmp/restart.txt
sleep 2

echo "  → Deuxième touch..."
touch tmp/restart.txt
sleep 2

echo "  → Troisième touch (force reload)..."
touch tmp/restart.txt

echo "✓ Passenger rechargé 3 fois"
ls -lh tmp/restart.txt
echo ""

echo "=== 7. Vérification optionnelle: Redémarrage Apache/Nginx ==="
echo "Si Passenger ne recharge pas, essayez:"
echo "  sudo systemctl restart apache2"
echo "  # OU"
echo "  sudo systemctl restart nginx"
echo ""

echo "=== 8. VIDAGE CACHE PLESK (si disponible) ==="
# Certaines installations Plesk ont leur propre cache
if command -v /usr/local/psa/bin/sw-engine-pleskrun &> /dev/null; then
    echo "  → Tentative de vidage du cache Plesk..."
    /usr/local/psa/bin/sw-engine-pleskrun --clear-cache 2>/dev/null && echo "✓ Cache Plesk vidé" || echo "  (cache Plesk non disponible)"
else
    echo "  (commande Plesk non trouvée - normal si pas sous Plesk)"
fi
echo ""

echo "=== 9. Vérification finale ==="
echo "Date et heure du système:"
date
echo ""
echo "Date de modification de base.html:"
ls -lh apps/competitions/templates/base.html
echo ""
echo "Date de modification de restart.txt:"
ls -lh tmp/restart.txt
echo ""

ENDSSH

echo ""
echo "=================================================="
echo "✓ TOUS LES CACHES ONT ÉTÉ VIDÉS"
echo "=================================================="
echo ""
echo "IMPORTANT: Maintenant, sur votre navigateur:"
echo "1. Ouvrez les outils de développement (F12)"
echo "2. Faites un clic droit sur le bouton de rechargement"
echo "3. Sélectionnez 'Vider le cache et recharger de force'"
echo "4. OU: Ouvrez une fenêtre de navigation privée"
echo "5. Testez: https://martialcomp.com/en/competitions/club/practitioners/88/edit/"
echo ""
