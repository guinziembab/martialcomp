#!/bin/bash
# Script pour forcer le redémarrage complet de la production

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=========================================="
echo "Redémarrage forcé de la production"
echo "Date: $(date)"
echo "=========================================="

# 1. Tuer tous les processus Gunicorn
echo "1. Arrêt forcé de tous les processus Gunicorn..."
ssh "$PRODUCTION_SERVER" "pkill -9 -f gunicorn || true"
sleep 2

# 2. Nettoyer les PID files
echo "2. Nettoyage des fichiers PID..."
ssh "$PRODUCTION_SERVER" "rm -f /tmp/gunicorn.pid /var/run/gunicorn.pid || true"

# 3. Créer un script de démarrage sur le serveur
echo "3. Création du script de démarrage..."
ssh "$PRODUCTION_SERVER" "cat > /tmp/start_gunicorn.sh << 'EOF'
#!/bin/bash
cd /var/www/vhosts/martialcomp.com/httpdocs
export PYTHONPATH=/var/www/vhosts/martialcomp.com/httpdocs
/var/www/vhosts/martialcomp.com/venv/bin/python -m gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8888 \
    --daemon \
    --pid /tmp/gunicorn.pid \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    --timeout 300 \
    config.wsgi:application
EOF
chmod +x /tmp/start_gunicorn.sh"

# 4. Exécuter le script
echo "4. Démarrage de Gunicorn..."
ssh "$PRODUCTION_SERVER" "/tmp/start_gunicorn.sh"
sleep 3

# 5. Vérifier que Gunicorn est démarré
echo "5. Vérification des processus Gunicorn..."
ssh "$PRODUCTION_SERVER" "ps aux | grep 'gunicorn.*8888' | grep -v grep | wc -l" | while read count; do
    if [ "$count" -gt 0 ]; then
        echo "✓ Gunicorn démarré avec $count processus sur le port 8888"
    else
        echo "✗ Gunicorn n'est pas démarré!"
        echo "Dernières erreurs:"
        ssh "$PRODUCTION_SERVER" "tail -10 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log"
    fi
done

# 6. Redémarrer Apache
echo "6. Redémarrage d'Apache..."
ssh "$PRODUCTION_SERVER" "sudo systemctl restart apache2"
sleep 3

# 7. Test final
echo "7. Tests finaux..."
echo -n "  - Test local sur le serveur: "
ssh "$PRODUCTION_SERVER" "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8888/" || echo "Erreur"

echo -n "  - Test public HTTPS: "
curl -s -o /dev/null -w "%{http_code}\n" https://martialcomp.com/ || echo "Erreur"

# 8. Afficher l'état final
echo ""
echo "=========================================="
echo "État final:"
ssh "$PRODUCTION_SERVER" "ps aux | grep 'gunicorn.*8888' | grep -v grep" || echo "Aucun processus Gunicorn trouvé"
echo "=========================================="

echo "Redémarrage terminé!"