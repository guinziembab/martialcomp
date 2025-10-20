#!/bin/bash

echo "=== VÉRIFICATION FINALE DU SITE ==="
echo ""

# 1. Vérifier que Gunicorn écoute
echo "1. Gunicorn:"
sudo ss -tlnp | grep :8000
echo ""

# 2. Tester localement avec différents paths
echo "2. Tests locaux:"
echo "- Racine:"
curl -s -I -H "Host: martialcomp.com" http://127.0.0.1:8000/
echo ""
echo "- Français:"
curl -s -I -H "Host: martialcomp.com" http://127.0.0.1:8000/fr/
echo ""
echo "- Admin:"
curl -s -I -H "Host: martialcomp.com" http://127.0.0.1:8000/admin/
echo ""

# 3. Vérifier la configuration Apache/Plesk
echo "3. Configuration Apache:"
if [ -d "/var/www/vhosts/system/martialcomp.com/conf" ]; then
    echo "Fichiers de configuration:"
    ls -la /var/www/vhosts/system/martialcomp.com/conf/
    echo ""
    echo "Vérification du proxy dans vhost_nginx.conf:"
    grep -i "proxy_pass\|location" /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf 2>/dev/null | head -10
fi

# 4. Afficher les ALLOWED_HOSTS
echo ""
echo "4. ALLOWED_HOSTS configurés:"
grep ALLOWED_HOSTS /var/www/vhosts/martialcomp.com/httpdocs/.env.production

# 5. Diagnostiquer le problème 400
echo ""
echo "5. Diagnostic du code 400:"
echo "Test avec curl verbeux:"
curl -v https://martialcomp.com 2>&1 | head -30

echo ""
echo "============================================"
echo "ACTIONS RECOMMANDÉES"
echo "============================================"
echo ""
echo "Si le site renvoie toujours 400:"
echo ""
echo "1. Vérifier que martialcomp.com est dans ALLOWED_HOSTS"
echo "2. Redémarrer Apache après les changements de config:"
echo "   systemctl restart apache2"
echo "3. Reconfigurer via Plesk:"
echo "   /usr/local/psa/admin/sbin/httpdmng --reconfigure-domain martialcomp.com"
echo ""
echo "Le site devrait être accessible sur:"
echo "- https://martialcomp.com"
echo "- https://martialcomp.com/fr/ (version française)"
echo "- https://martialcomp.com/admin/ (administration)"
echo ""
echo "============================================"