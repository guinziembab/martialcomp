# Guide manuel pour mettre à jour la sécurité en production

## 1. Nouvelle clé secrète générée

```
DzhqL8hNwhFBNwCxLlpCUlNvAKfqQw1uXN6Y-TE8JIp_GYcOJQy6b57-Cz8ef-csJCg
```

## 2. Mettre à jour le fichier .env en production

Connectez-vous en SSH et éditez le fichier .env :

```bash
ssh psaserv@martialcomp.com
cd /var/www/vhosts/martialcomp.com/httpdocs
nano .env
```

Remplacez le contenu par :

```env
DEBUG=False
SECRET_KEY=DzhqL8hNwhFBNwCxLlpCUlNvAKfqQw1uXN6Y-TE8JIp_GYcOJQy6b57-Cz8ef-csJCg

# Configuration base de données PostgreSQL
POSTGRES_DB=martialcomp_db
POSTGRES_USER=martialcomp_user
POSTGRES_PASSWORD=martialcomp_password_2024
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Configuration email
EMAIL_HOST_USER=your_email@martialcomp.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@martialcomp.com

# Configuration statiques
STATIC_URL=/static/
MEDIA_URL=/media/
```

## 3. Mettre à jour le fichier production.py

Éditez le fichier production.py :

```bash
nano config/settings/production.py
```

Remplacez le contenu par :

```python
# config/settings/production.py
import os
from pathlib import Path
from decouple import config
from .base import *

print('DEBUG DECOUPLE:', config('POSTGRES_USER', default='AUCUNE'), config('POSTGRES_PASSWORD', default='AUCUN'))
print('POSTGRES_USER:', config('POSTGRES_USER', default='AUCUNE'))
print('POSTGRES_PASSWORD:', config('POSTGRES_PASSWORD', default='AUCUN'))
print('POSTGRES_DB:', config('POSTGRES_DB', default='AUCUNE'))

# BASE_DIR déjà défini dans base.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = False

ALLOWED_HOSTS = [
    '.martialcomp.com',
    'martialcomp.com',
    'www.martialcomp.com',
    '212.227.78.104',
    '127.0.0.1',
    'localhost',
]

# Base de données PostgreSQL pour production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST', default='localhost'),
        'PORT': config('POSTGRES_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Sécurité renforcée (activation des paramètres de sécurité)
SECURE_SSL_REDIRECT = True  # Changé de False à True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True  # Changé de False à True
CSRF_COOKIE_SECURE = True  # Changé de False à True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600  # Activé (1 heure pour commencer)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Activé
SECURE_HSTS_PRELOAD = True  # Activé

CSRF_TRUSTED_ORIGINS = [
    'https://martialcomp.com',
    'https://www.martialcomp.com',
    'https://*.martialcomp.com',
    'http://212.227.78.104:8080',
    'http://127.0.0.1:8080',
    'http://localhost:8080',
]
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_AGE = None

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@martialcomp.com')

BASE_URL = 'https://martialcomp.com'

LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/competitions/onboarding/role/'
LOGOUT_REDIRECT_URL = '/fr/'

ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_USERNAME_REQUIRED = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django_errors.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'competitions': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

LOGIN_URL = '/accounts/login/'
```

## 4. Installer python-decouple si nécessaire

```bash
pip install python-decouple
```

## 5. Vérifier et redémarrer les services

```bash
# Vérifier la configuration
python manage.py check --deploy

# Collecter les fichiers statiques
python manage.py collectstatic --noinput

# Appliquer les migrations
python manage.py migrate

# Redémarrer Gunicorn (trouver le PID d'abord)
ps aux | grep gunicorn
kill -HUP [PID_GUNICORN]
```

## 6. Vérifications finales

1. Tester l'accès au site : https://martialcomp.com
2. Vérifier que le mode DEBUG est désactivé
3. Tester la connexion HTTPS
4. Vérifier les logs : `/tmp/django_errors.log`

## 7. Créer le dossier de logs si nécessaire

```bash
sudo mkdir -p /var/log/martialcomp
sudo chown psaserv:psaserv /var/log/martialcomp
```

## Résultats attendus

Après ces modifications, la commande `python manage.py check --deploy` ne devrait plus afficher d'erreurs de sécurité et le site devrait être accessible en HTTPS avec tous les paramètres de sécurité activés.

## Changements principaux apportés

1. **DEBUG = False** - Mode debug désactivé
2. **SECURE_SSL_REDIRECT = True** - Redirection HTTPS forcée
3. **SESSION_COOKIE_SECURE = True** - Cookies de session sécurisés
4. **CSRF_COOKIE_SECURE = True** - Cookies CSRF sécurisés
5. **SECURE_HSTS_SECONDS = 3600** - HSTS activé (1 heure)
6. **SECURE_HSTS_INCLUDE_SUBDOMAINS = True** - HSTS pour sous-domaines
7. **SECURE_HSTS_PRELOAD = True** - HSTS preload activé
