#!/bin/bash
# Script d'analyse des erreurs sur le serveur de production MartialComp
# À exécuter sur le serveur de production via SSH

echo "=== ANALYSE DES ERREURS DE PRODUCTION MARTIALCOMP ==="
echo "Date: $(date)"
echo ""

echo "1. DERNIÈRES ERREURS APACHE (50 dernières lignes)"
echo "=================================================="
sudo tail -50 /var/log/apache2/error.log | grep -E "(Error|ERROR|Traceback|Exception|500)" -A 5 -B 2
echo ""

echo "2. VÉRIFICATION DES LOGS DJANGO"
echo "================================"
if [ -d "/var/www/vhosts/martialcomp.com/httpdocs/logs/" ]; then
    echo "Répertoire logs trouvé:"
    ls -la /var/www/vhosts/martialcomp.com/httpdocs/logs/
    
    if [ -f "/var/www/vhosts/martialcomp.com/httpdocs/logs/django.log" ]; then
        echo ""
        echo "Contenu récent de django.log:"
        tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
    else
        echo "Fichier django.log non trouvé"
    fi
else
    echo "Répertoire logs non trouvé"
fi
echo ""

echo "3. INFORMATIONS PYTHON ET DJANGO"
echo "=================================="
echo "Version Python:"
python3 --version
echo ""

echo "Test import Django:"
cd /var/www/vhosts/martialcomp.com/httpdocs
python3 -c "import django; print('Django version:', django.get_version())" 2>&1
echo ""

echo "4. VÉRIFICATION DE L'ENVIRONNEMENT VIRTUEL"
echo "=========================================="
if [ -d "/var/www/vhosts/martialcomp.com/httpdocs/venv" ]; then
    echo "Environnement virtuel trouvé dans venv/"
    ls -la /var/www/vhosts/martialcomp.com/httpdocs/venv/bin/python*
elif [ -d "/var/www/vhosts/martialcomp.com/httpdocs/.venv" ]; then
    echo "Environnement virtuel trouvé dans .venv/"
    ls -la /var/www/vhosts/martialcomp.com/httpdocs/.venv/bin/python*
else
    echo "Aucun environnement virtuel standard trouvé"
fi
echo ""

echo "5. VÉRIFICATION DES PERMISSIONS"
echo "================================"
echo "Permissions du répertoire principal:"
ls -la /var/www/vhosts/martialcomp.com/httpdocs/ | head -10
echo ""

echo "6. STATUT DES SERVICES"
echo "======================="
echo "Apache2:"
sudo systemctl status apache2 | head -10
echo ""

echo "7. RECHERCHE D'ERREURS RÉCENTES DANS SYSLOG"
echo "============================================"
sudo journalctl -u apache2 --since "1 hour ago" | grep -E "(Error|ERROR|500|martialcomp)" | tail -20
echo ""

echo "8. VÉRIFICATION DE LA CONFIGURATION WSGI"
echo "========================================="
if [ -f "/var/www/vhosts/martialcomp.com/httpdocs/passenger_wsgi.py" ]; then
    echo "passenger_wsgi.py trouvé"
    echo "Premières lignes du fichier:"
    head -20 /var/www/vhosts/martialcomp.com/httpdocs/passenger_wsgi.py
else
    echo "passenger_wsgi.py NON TROUVÉ!"
fi

echo ""
echo "=== FIN DE L'ANALYSE ==="