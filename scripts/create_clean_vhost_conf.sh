#!/bin/bash
# Script pour générer un vhost.conf propre pour martialcomp.com (Passenger/Django/Plesk)
# À exécuter sur le serveur de production avec les droits root

VHOST_CONF_PATH="/var/www/vhosts/system/martialcomp.com/conf/vhost.conf"

cat > "$VHOST_CONF_PATH" <<'EOF'
ServerName martialcomp.com
ServerAlias www.martialcomp.com

DocumentRoot /var/www/vhosts/martialcomp.com/httpdocs

<Directory /var/www/vhosts/martialcomp.com/httpdocs>
    Require all granted
    Options -MultiViews
    AllowOverride All
</Directory>

<IfModule mod_passenger.c>
    PassengerEnabled on
    PassengerAppRoot /var/www/vhosts/martialcomp.com/httpdocs
    PassengerAppType wsgi
    PassengerStartupFile passenger_wsgi.py
    PassengerPython /var/www/vhosts/martialcomp.com/httpdocs/.venv/bin/python
    PassengerMinInstances 1
    PassengerLogLevel 7
</IfModule>

ErrorLog /var/www/vhosts/martialcomp.com/logs/error.log
CustomLog /var/www/vhosts/martialcomp.com/logs/access.log combined
EOF

echo "Fichier $VHOST_CONF_PATH généré avec succès."
echo "Redémarrage d'Apache..."
systemctl restart apache2
echo "Terminé. Vérifiez l'accès au site et les logs si besoin." 
# Script pour générer un vhost.conf propre pour martialcomp.com (Passenger/Django/Plesk)
# À exécuter sur le serveur de production avec les droits root

VHOST_CONF_PATH="/var/www/vhosts/system/martialcomp.com/conf/vhost.conf"

cat > "$VHOST_CONF_PATH" <<'EOF'
ServerName martialcomp.com
ServerAlias www.martialcomp.com

DocumentRoot /var/www/vhosts/martialcomp.com/httpdocs

<Directory /var/www/vhosts/martialcomp.com/httpdocs>
    Require all granted
    Options -MultiViews
    AllowOverride All
</Directory>

<IfModule mod_passenger.c>
    PassengerEnabled on
    PassengerAppRoot /var/www/vhosts/martialcomp.com/httpdocs
    PassengerAppType wsgi
    PassengerStartupFile passenger_wsgi.py
    PassengerPython /var/www/vhosts/martialcomp.com/httpdocs/.venv/bin/python
    PassengerMinInstances 1
    PassengerLogLevel 7
</IfModule>

ErrorLog /var/www/vhosts/martialcomp.com/logs/error.log
CustomLog /var/www/vhosts/martialcomp.com/logs/access.log combined
EOF

echo "Fichier $VHOST_CONF_PATH généré avec succès."
echo "Redémarrage d'Apache..."
systemctl restart apache2
echo "Terminé. Vérifiez l'accès au site et les logs si besoin." 