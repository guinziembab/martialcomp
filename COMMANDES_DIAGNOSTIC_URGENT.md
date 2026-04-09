# DIAGNOSTIC URGENT - Erreur 500 MartialComp

## Exécutez ces commandes sur le serveur de production:

### 1. Arrêter tous les processus Gunicorn existants
```bash
pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2
```

### 2. Nettoyer les caches Python
```bash
find /var/www/vhosts/martialcomp.com/httpdocs -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /var/www/vhosts/martialcomp.com/httpdocs -name "*.pyc" -delete 2>/dev/null || true
```

### 3. Vider le cache Redis (sessions corrompues)
```bash
redis-cli FLUSHALL
```

### 4. Tester l'import Django MANUELLEMENT
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python -c "
import django
django.setup()
print('Django OK')
from apps.competitions.models import Competition
print(f'Competitions: {Competition.objects.count()}')
"
```

### 5. Si l'étape 4 échoue, voir l'erreur exacte:
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python -c "
import traceback
try:
    import django
    django.setup()
except Exception as e:
    print('ERREUR:')
    traceback.print_exc()
"
```

### 6. Redémarrer Gunicorn proprement
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

/var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8888 \
    --workers 2 \
    --timeout 120 \
    --chdir /var/www/vhosts/martialcomp.com/httpdocs \
    --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log \
    --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log \
    --capture-output \
    --daemon

sleep 3
ps aux | grep gunicorn
```

### 7. Tester le site
```bash
curl -sL -w "\nHTTP: %{http_code}\n" \
    -H 'Host: martialcomp.com' \
    -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/' | head -20
```

### 8. Voir les erreurs récentes
```bash
tail -100 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log
```

---
## COPIER-COLLER RAPIDE (tout en un bloc):

```bash
# Arrêt + Nettoyage + Diagnostic + Redémarrage
pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2
find /var/www/vhosts/martialcomp.com/httpdocs -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find /var/www/vhosts/martialcomp.com/httpdocs -name "*.pyc" -delete 2>/dev/null || true
redis-cli FLUSHALL 2>/dev/null || true
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production
python -c "import django; django.setup(); print('Django OK')" && \
/var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8888 --workers 2 --timeout 120 \
    --chdir /var/www/vhosts/martialcomp.com/httpdocs \
    --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log \
    --capture-output --daemon && \
sleep 3 && curl -sL -w "\nHTTP: %{http_code}\n" \
    -H 'Host: martialcomp.com' -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/' | head -5
```
