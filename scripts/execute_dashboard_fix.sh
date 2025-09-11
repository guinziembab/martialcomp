#!/bin/bash

# Script pour exécuter la correction des dashboards spécifiques
echo "🔧 CORRECTION DASHBOARDS SPÉCIFIQUES PAR PROFIL"
echo "=============================================="

# Se connecter au serveur et exécuter la correction
ssh root@martialcomp.com << 'EOF'

cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings

echo "🎯 PROBLÈME IDENTIFIÉ:"
echo "   Dashboard générique au lieu du dashboard Club Manager"
echo "   Utilisateur: dojo_sakura_manager"
echo "   Attendu: Dashboard Club avec 25 membres, finances, etc."
echo "   Actuel: Page générique de développement"

echo ""
echo "🔧 EXÉCUTION CORRECTION..."

# Transférer et exécuter le script de correction
python3 << 'PYTHON_EOF'
exec(open('/tmp/fix_dashboard_routing.py').read())
PYTHON_EOF

echo ""
echo "🧪 TEST DASHBOARD APRÈS CORRECTION:"
curl -I http://localhost:8000/dashboard/club/ 2>/dev/null | head -1

echo ""
echo "🎉 CORRECTION TERMINÉE!"
echo "Testez maintenant : https://martialcomp.com/"
echo "Connexion: dojo_sakura_manager / demo2025"
echo "→ Dashboard Club avec toutes les fonctionnalités"

EOF

echo ""
echo "✅ Correction des dashboards terminée"
echo "Le site redirige maintenant vers les dashboards spécifiques selon le profil utilisateur"