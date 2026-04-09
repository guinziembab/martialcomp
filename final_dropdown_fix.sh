#\!/bin/bash
echo "=== FIX FINAL DROPDOWN ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Redémarrer gunicorn pour appliquer tous les changements
sudo pkill -HUP -f gunicorn
sleep 2

echo "✓ Redémarrage effectué"
echo ""
echo "Le dropdown devrait maintenant fonctionner avec le fix simple appliqué."
echo "Il utilise onclick() au lieu de Bootstrap pour contourner l'erreur JS."

SSHEOF
