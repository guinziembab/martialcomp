#!/bin/bash

echo "=== RÉPARATION D'URGENCE APACHE ==="
echo ""

# 1. Créer les fichiers manquants
echo "1. Création des fichiers de configuration manquants..."
mkdir -p /var/www/vhosts/system/martialcomp.com/conf/

# Créer vhost_ssl.conf vide ou avec configuration minimale
touch /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf

# 2. Démarrer Apache avec configuration minimale
echo ""
echo "2. Tentative de démarrage d'Apache..."
systemctl start apache2

if [ $? -ne 0 ]; then
    echo "Apache ne démarre toujours pas. Reconfiguration complète..."
    
    # 3. Reconfigurer le domaine via Plesk
    echo ""
    echo "3. Reconfiguration complète du domaine via Plesk..."
    /usr/local/psa/admin/sbin/httpdmng --reconfigure-domain martialcomp.com
    
    # 4. Démarrer Apache à nouveau
    echo ""
    echo "4. Nouveau démarrage d'Apache..."
    systemctl start apache2
fi

# 5. Vérifier le statut
echo ""
echo "5. Statut d'Apache :"
systemctl status apache2 --no-pager | head -15

# 6. Si Apache fonctionne, ajouter la configuration WSGI
if systemctl is-active apache2 >/dev/null; then
    echo ""
    echo "6. Apache fonctionne ! Ajout de la configuration WSGI..."
    
    # Configuration pour vhost.conf (HTTP)
    cat > /var/www/vhosts/system/martialcomp.com/conf/vhost.conf << 'EOF'
WSGIScriptAlias / /var/www/vhosts/martialcomp.com/httpdocs/wsgi.py
WSGIDaemonProcess martialcomp python-home=/var/www/vhosts/martialcomp.com/venv python-path=/var/www/vhosts/martialcomp.com/httpdocs
WSGIProcessGroup martialcomp

<Directory /var/www/vhosts/martialcomp.com/httpdocs>
    <Files wsgi.py>
        Require all granted
    </Files>
</Directory>

Alias /static/ /var/www/vhosts/martialcomp.com/httpdocs/staticfiles/
Alias /media/ /var/www/vhosts/martialcomp.com/httpdocs/media/

<Directory /var/www/vhosts/martialcomp.com/httpdocs/staticfiles>
    Require all granted
</Directory>

<Directory /var/www/vhosts/martialcomp.com/httpdocs/media>
    Require all granted
</Directory>
EOF

    # Même configuration pour vhost_ssl.conf (HTTPS)
    cp /var/www/vhosts/system/martialcomp.com/conf/vhost.conf /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf
    
    # 7. Reconfigurer avec les nouvelles directives
    echo ""
    echo "7. Application de la configuration WSGI..."
    /usr/local/psa/admin/sbin/httpdmng --reconfigure-domain martialcomp.com
    
    # 8. Recharger Apache
    echo ""
    echo "8. Rechargement d'Apache..."
    systemctl reload apache2
    
    # 9. Test final
    echo ""
    echo "9. Test du site..."
    sleep 2
    curl -I https://martialcomp.com
else
    echo ""
    echo "❌ Apache ne fonctionne pas. Vérification des logs..."
    journalctl -u apache2 -n 50 | grep -i error | tail -20
fi

echo ""
echo "=== FIN DE LA RÉPARATION ==="