#!/bin/bash
# Script de redémarrage d'urgence

echo "=== REDÉMARRAGE D'URGENCE DU SERVEUR ==="

ssh martialcomp-production << 'EOF'
echo "1. Arrêt complet de Gunicorn..."
sudo pkill -9 -f gunicorn
sleep 2

echo "2. Nettoyage des processus zombies..."
sudo pkill -9 -f "python.*manage.py"
sudo pkill -9 -f "python.*wsgi"

echo "3. Vérification des logs récents..."
echo "Dernières erreurs Gunicorn:"
tail -n 10 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log 2>/dev/null || echo "Pas de log d'erreur"

echo "4. Nettoyage des fichiers Python compilés..."
cd /var/www/vhosts/martialcomp.com/httpdocs
sudo find . -name "*.pyc" -delete
sudo find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "5. Redémarrage de PostgreSQL (au cas où)..."
sudo systemctl restart postgresql

echo "6. Démarrage de Gunicorn..."
cd /var/www/vhosts/martialcomp.com
sudo -u www-data /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8888 \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log \
    --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log \
    --log-level info \
    --chdir /var/www/vhosts/martialcomp.com/httpdocs \
    --daemon \
    config.wsgi:application

echo "7. Attente du démarrage..."
sleep 5

echo "8. Vérification du statut..."
if pgrep -f "gunicorn.*config.wsgi" > /dev/null; then
    echo "✓ Gunicorn démarré avec succès"
    ps aux | grep gunicorn | grep -v grep | head -5
else
    echo "✗ Gunicorn n'a pas démarré"
    echo "Tentative de démarrage en mode debug..."
    cd /var/www/vhosts/martialcomp.com/httpdocs
    sudo -u www-data /var/www/vhosts/martialcomp.com/venv/bin/python manage.py check
fi

echo "9. Redémarrage d'Apache..."
sudo systemctl restart apache2

echo "10. Test de connectivité..."
sleep 2
response=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8888/ 2>/dev/null || echo "000")
if [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
    echo "✓ Serveur accessible (HTTP $response)"
else
    echo "✗ Serveur inaccessible (HTTP $response)"
    echo "Logs d'erreur récents:"
    tail -5 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log 2>/dev/null
fi

echo ""
echo "✓ Processus de redémarrage terminé"
EOF

echo ""
echo "=== REDÉMARRAGE TERMINÉ ==="