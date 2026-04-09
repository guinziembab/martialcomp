#!/bin/bash

echo "=== REDÉMARRAGE FORCÉ DE DJANGO ==="
echo "Date: $(date)"

SSH_HOST="martialcomp-production"

echo "1. Arrêt des processus gunicorn..."
ssh $SSH_HOST "sudo pkill -9 -f 'gunicorn.*config.wsgi:application' 2>/dev/null || true"

echo "2. Attente..."
sleep 2

echo "3. Vérification que les processus sont arrêtés..."
ssh $SSH_HOST "ps aux | grep gunicorn | grep -v grep || echo 'Tous les processus gunicorn sont arrêtés'"

echo "4. Redémarrage via systemd ou supervisor..."
# Essayer plusieurs méthodes
ssh $SSH_HOST "sudo systemctl restart gunicorn 2>/dev/null || sudo supervisorctl restart all 2>/dev/null || true"

echo "5. Si rien ne marche, démarrage manuel..."
ssh $SSH_HOST "cd /var/www/vhosts/martialcomp.com/httpdocs && nohup /var/www/vhosts/martialcomp.com/venv/bin/gunicorn --workers 3 --worker-class sync --worker-connections 1000 --max-requests 1000 --max-requests-jitter 100 --preload --bind 127.0.0.1:8000 --timeout 300 --keep-alive 2 --log-level info --log-file /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn.log --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log config.wsgi:application > /dev/null 2>&1 & echo 'Gunicorn démarré manuellement'"

echo "6. Redémarrage nginx..."
ssh $SSH_HOST "sudo systemctl reload nginx"

echo ""
echo "✅ REDÉMARRAGE TERMINÉ !"
echo ""
echo "Attendez 10 secondes puis testez :"
echo "1. https://martialcomp.com/fr/competitions/competitions/4/"
echo "2. https://martialcomp.com/favicon.ico (devrait retourner 200)"
echo ""
echo "Si l'erreur persiste, vérifiez les logs :"
echo "ssh $SSH_HOST 'tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log'"