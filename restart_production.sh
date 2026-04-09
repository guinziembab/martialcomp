#!/bin/bash
# Script de redémarrage complet de la production

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "Redémarrage complet de la production..."

# 1. Arrêter les processus existants
echo "1. Arrêt de Gunicorn..."
ssh "$PRODUCTION_SERVER" "pkill -f gunicorn || true"
sleep 2

# 2. Nettoyer les fichiers de cache Python
echo "2. Nettoyage du cache Python..."
ssh "$PRODUCTION_SERVER" "find $PRODUCTION_PATH -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true"

# 3. Vérifier la configuration Django
echo "3. Test de la configuration Django..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py check 2>&1 | tail -5 || echo 'Erreur de configuration'"

# 4. Démarrer Gunicorn sur le port 8888
echo "4. Démarrage de Gunicorn sur le port 8888..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && \
    /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --bind 127.0.0.1:8888 \
    --timeout 300 \
    --daemon \
    --pid /tmp/gunicorn.pid \
    --log-level info \
    --log-file $PRODUCTION_PATH/logs/gunicorn.log \
    --access-logfile $PRODUCTION_PATH/logs/gunicorn_access.log \
    --error-logfile $PRODUCTION_PATH/logs/gunicorn_error.log \
    config.wsgi:application"

sleep 3

# 5. Vérifier que Gunicorn est démarré
echo "5. Vérification de Gunicorn..."
ssh "$PRODUCTION_SERVER" "ps aux | grep gunicorn | grep -v grep | wc -l" | while read count; do
    if [ "$count" -gt 0 ]; then
        echo "✓ Gunicorn démarré avec $count processus"
    else
        echo "✗ Gunicorn n'est pas démarré!"
    fi
done

# 6. Redémarrer Apache
echo "6. Redémarrage d'Apache..."
ssh "$PRODUCTION_SERVER" "sudo systemctl restart apache2"

# 7. Test final
echo "7. Test du site..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ || echo "000")
echo "Statut HTTP: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo "✓ Site accessible!"
else
    echo "✗ Site toujours inaccessible"
    # Afficher les dernières erreurs
    echo "Logs Gunicorn:"
    ssh "$PRODUCTION_SERVER" "tail -10 $PRODUCTION_PATH/logs/gunicorn_error.log 2>/dev/null || echo 'Pas de log d erreur'"
fi

echo "Redémarrage terminé!"