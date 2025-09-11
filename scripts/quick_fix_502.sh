#!/bin/bash
# Script de correction rapide pour l'erreur 502

echo "🔧 CORRECTION RAPIDE 502 BAD GATEWAY"
echo "===================================="

# Aller dans le répertoire du projet
cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Arrêter tous les processus gunicorn
echo "1️⃣ Arrêt des processus gunicorn..."
pkill -f gunicorn
sleep 3

# 2. Vérifier l'application Django
echo "2️⃣ Test Django..."
if [ ! -f "manage.py" ]; then
    echo "❌ manage.py non trouvé!"
    exit 1
fi

# 3. Activer l'environnement virtuel
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
else
    echo "⚠️ Création environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    pip install django gunicorn
fi

# 4. Test rapide Django
echo "3️⃣ Test rapide Django..."
python3 manage.py check --deploy || python3 manage.py check

# 5. Redémarrer gunicorn
echo "4️⃣ Redémarrage gunicorn..."
mkdir -p /var/log/gunicorn

gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 2 \
    --daemon \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log

sleep 5

# 6. Vérifier que gunicorn fonctionne
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn démarré"
    
    # Test local
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ || echo "000")
    echo "Test local: HTTP $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
        echo "✅ Django répond"
    else
        echo "⚠️ Django répond avec: $HTTP_CODE"
        echo "Logs gunicorn:"
        tail -n 5 /var/log/gunicorn/error.log
    fi
else
    echo "❌ Gunicorn n'a pas démarré"
    echo "Logs gunicorn:"
    tail -n 10 /var/log/gunicorn/error.log
    exit 1
fi

# 7. Redémarrer nginx
echo "5️⃣ Redémarrage nginx..."
systemctl restart nginx

# 8. Test final
sleep 3
echo "6️⃣ Test final..."
FINAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k https://martialcomp.com/ || echo "000")
echo "Test HTTPS: HTTP $FINAL_CODE"

if [ "$FINAL_CODE" = "200" ] || [ "$FINAL_CODE" = "301" ] || [ "$FINAL_CODE" = "302" ]; then
    echo "🎉 SUCCÈS: Site accessible!"
    echo "🌐 Testez: https://martialcomp.com/fr/competitions/practitioner/notifications/"
else
    echo "⚠️ Erreur persistante: $FINAL_CODE"
    echo "Logs nginx:"
    tail -n 5 /var/log/nginx/martialcomp_error.log
fi

echo "===================================="