#!/bin/bash

echo "🔧 REDÉMARRAGE SÉCURISÉ DU SERVEUR DJANGO"
echo "=========================================="

# Variables
LOG_FILE="/tmp/django_restart_$(date +%Y%m%d_%H%M%S).log"
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

# Fonction de log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "🚀 Début du redémarrage sécurisé"

# 1. Vérifier le répertoire de travail
if [ ! -d "$PROJECT_DIR" ]; then
    log "❌ Répertoire projet non trouvé: $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"
log "📁 Répertoire de travail: $(pwd)"

# 2. Arrêter tous les processus gunicorn existants
log "1️⃣ Arrêt des processus gunicorn..."
pkill -f gunicorn 2>/dev/null || true
sleep 5

# Vérifier qu'ils sont bien arrêtés
REMAINING=$(ps aux | grep gunicorn | grep -v grep | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    log "⚠️ $REMAINING processus gunicorn encore actifs, arrêt forcé..."
    pkill -9 -f gunicorn 2>/dev/null || true
    sleep 3
fi

log "✅ Processus gunicorn arrêtés"

# 3. Vérifier l'environnement virtuel
if [ ! -f "venv/bin/activate" ]; then
    log "❌ Environnement virtuel non trouvé"
    exit 1
fi

source venv/bin/activate
log "✅ Environnement virtuel activé"

# 4. Vérifier que manage.py existe
if [ ! -f "manage.py" ]; then
    log "❌ manage.py non trouvé"
    exit 1
fi

# 5. Test Django
log "2️⃣ Test de l'application Django..."
python3 manage.py check 2>&1 | tee -a "$LOG_FILE"
CHECK_RESULT=${PIPESTATUS[0]}

if [ $CHECK_RESULT -ne 0 ]; then
    log "❌ Django check a échoué"
    exit 1
fi

log "✅ Django check réussi"

# 6. Créer les répertoires de logs
log "3️⃣ Préparation des logs..."
sudo mkdir -p /var/log/gunicorn 2>/dev/null || mkdir -p /var/log/gunicorn
sudo chown $(whoami):$(whoami) /var/log/gunicorn 2>/dev/null || true

# 7. Test de démarrage en mode non-daemon d'abord
log "4️⃣ Test de démarrage gunicorn..."
timeout 10s gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 1 2>&1 | tee -a "$LOG_FILE" &
GUNICORN_PID=$!

sleep 5

# Tester si gunicorn répond
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
log "Test HTTP local: $HTTP_CODE"

# Arrêter le test
kill $GUNICORN_PID 2>/dev/null || true
sleep 2

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "301" ] || [ "$HTTP_CODE" = "302" ]; then
    log "✅ Test gunicorn réussi"
else
    log "❌ Test gunicorn échoué (code: $HTTP_CODE)"
    exit 1
fi

# 8. Démarrage en mode daemon
log "5️⃣ Démarrage final en mode daemon..."
gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 2 \
    --timeout 120 \
    --daemon \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info

sleep 5

# 9. Vérification finale
if pgrep -f "gunicorn.*config.wsgi" > /dev/null; then
    log "✅ Gunicorn démarré en mode daemon"
    
    # Test final
    FINAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "000")
    log "Test final: HTTP $FINAL_CODE"
    
    if [ "$FINAL_CODE" = "200" ] || [ "$FINAL_CODE" = "301" ] || [ "$FINAL_CODE" = "302" ]; then
        log "✅ Serveur Django opérationnel"
    else
        log "⚠️ Serveur répond avec code: $FINAL_CODE"
    fi
else
    log "❌ Échec du démarrage en mode daemon"
    log "Logs d'erreur:"
    tail -n 10 /var/log/gunicorn/error.log 2>/dev/null || echo "Aucun log d'erreur"
    exit 1
fi

# 10. Redémarrer nginx
log "6️⃣ Redémarrage nginx..."
systemctl restart nginx 2>&1 | tee -a "$LOG_FILE"

if systemctl is-active nginx > /dev/null; then
    log "✅ Nginx redémarré"
else
    log "❌ Échec redémarrage nginx"
    exit 1
fi

# 11. Test final complet
log "7️⃣ Test final HTTPS..."
sleep 3
HTTPS_FINAL=$(curl -s -o /dev/null -w "%{http_code}" -k https://martialcomp.com/ 2>/dev/null || echo "000")
log "Test HTTPS final: $HTTPS_FINAL"

log "📄 Log complet: $LOG_FILE"

if [ "$HTTPS_FINAL" = "200" ] || [ "$HTTPS_FINAL" = "301" ] || [ "$HTTPS_FINAL" = "302" ]; then
    log "🎉 SUCCÈS: Serveur complètement opérationnel"
    echo ""
    echo "=========================================="
    echo "🎯 SUCCÈS COMPLET"
    echo "🌐 Site: https://martialcomp.com/"
    echo "🔧 Admin: https://martialcomp.com/fr/admin/"
    echo "📝 Onboarding: https://martialcomp.com/fr/onboarding/participant/"
    echo "📄 Log: $LOG_FILE"
    echo "=========================================="
else
    log "⚠️ Problème persistant avec HTTPS (code: $HTTPS_FINAL)"
    echo ""
    echo "=========================================="
    echo "⚠️ REDÉMARRAGE PARTIEL"
    echo "✅ Django: Opérationnel"
    echo "❌ HTTPS: Code $HTTPS_FINAL"
    echo "📄 Log: $LOG_FILE"
    echo "=========================================="
fi