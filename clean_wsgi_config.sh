#!/bin/bash

echo "=== NETTOYAGE ET CONFIGURATION WSGI PROPRE ==="
echo ""

# 1. Chercher toutes les configurations WSGI existantes
echo "1. Recherche des configurations WSGI existantes..."
grep -r "WSGIDaemonProcess\|WSGIScriptAlias" /etc/apache2/ 2>/dev/null | grep -i martialcomp | head -10
echo ""
grep -r "WSGIDaemonProcess\|WSGIScriptAlias" /var/www/vhosts/system/martialcomp.com/ 2>/dev/null | head -10

# 2. Supprimer temporairement les configurations personnalisées
echo ""
echo "2. Suppression temporaire des configurations personnalisées..."
mv /var/www/vhosts/system/martialcomp.com/conf/vhost.conf /var/www/vhosts/system/martialcomp.com/conf/vhost.conf.bak 2>/dev/null
mv /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf.bak 2>/dev/null

# 3. Reconfigurer pour nettoyer
echo ""
echo "3. Reconfiguration propre via Plesk..."
/usr/local/psa/admin/sbin/httpdmng --reconfigure-domain martialcomp.com

# 4. Vérifier qu'Apache fonctionne toujours
echo ""
echo "4. Vérification qu'Apache fonctionne..."
systemctl reload apache2
if ! systemctl is-active apache2 >/dev/null; then
    echo "Erreur : Apache ne fonctionne plus !"
    systemctl start apache2
fi

# 5. Option 1 : Utiliser un simple script CGI Python au lieu de WSGI
echo ""
echo "5. Configuration alternative avec script Python simple..."
cat > /var/www/vhosts/system/martialcomp.com/conf/vhost.conf << 'EOF'
# Redirection vers l'application Django via proxy
ProxyPass /static/ !
ProxyPass /media/ !
ProxyPass / http://localhost:8000/
ProxyPassReverse / http://localhost:8000/

# Fichiers statiques
Alias /static/ /var/www/vhosts/martialcomp.com/httpdocs/staticfiles/
Alias /media/ /var/www/vhosts/martialcomp.com/httpdocs/media/

<Directory /var/www/vhosts/martialcomp.com/httpdocs/staticfiles>
    Require all granted
</Directory>

<Directory /var/www/vhosts/martialcomp.com/httpdocs/media>
    Require all granted
</Directory>
EOF

# Copier pour HTTPS
cp /var/www/vhosts/system/martialcomp.com/conf/vhost.conf /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf

# 6. Créer un script de démarrage Gunicorn
echo ""
echo "6. Création du script de démarrage Gunicorn..."
cat > start_gunicorn.sh << 'EOF'
#!/bin/bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Charger l'environnement
export $(grep -v '^#' .env.production | xargs)

# Démarrer Gunicorn
exec gunicorn config.wsgi:application \
    --bind localhost:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile logs/gunicorn-access.log \
    --error-logfile logs/gunicorn-error.log
EOF
chmod +x start_gunicorn.sh

# 7. Installer et démarrer Gunicorn
echo ""
echo "7. Installation de Gunicorn..."
/var/www/vhosts/martialcomp.com/venv/bin/pip install gunicorn

# 8. Créer un service systemd pour Gunicorn
echo ""
echo "8. Création du service Gunicorn..."
cat > /etc/systemd/system/martialcomp-gunicorn.service << 'EOF'
[Unit]
Description=Gunicorn daemon for MartialComp
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
ExecStart=/var/www/vhosts/martialcomp.com/httpdocs/start_gunicorn.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 9. Démarrer Gunicorn
echo ""
echo "9. Démarrage de Gunicorn..."
systemctl daemon-reload
systemctl stop martialcomp-gunicorn 2>/dev/null
systemctl start martialcomp-gunicorn
systemctl enable martialcomp-gunicorn

# 10. Activer les modules proxy d'Apache
echo ""
echo "10. Activation des modules proxy..."
a2enmod proxy proxy_http

# 11. Reconfigurer Apache
echo ""
echo "11. Application de la configuration..."
/usr/local/psa/admin/sbin/httpdmng --reconfigure-domain martialcomp.com
systemctl reload apache2

# 12. Test final
echo ""
echo "12. Test du site..."
sleep 3
echo "Statut Gunicorn :"
systemctl status martialcomp-gunicorn --no-pager | head -10
echo ""
echo "Test HTTP :"
curl -I https://martialcomp.com

echo ""
echo "=== CONFIGURATION TERMINÉE ==="
echo ""
echo "Le site utilise maintenant Gunicorn avec un proxy Apache."
echo "Logs Gunicorn : tail -f logs/gunicorn-*.log"
echo "Service : systemctl status martialcomp-gunicorn"