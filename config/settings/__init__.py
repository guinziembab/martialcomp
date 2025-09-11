# config/settings/__init__.py
# Ce fichier assure que la configuration correcte est chargée
# et force DEBUG=True pour le développement local

import os

# Forcer DEBUG à True pour le développement local
os.environ['DJANGO_DEBUG'] = 'True'

# Définir ALLOWED_HOSTS par défaut
if 'ALLOWED_HOSTS' not in os.environ:
    os.environ['ALLOWED_HOSTS'] = 'localhost,127.0.0.1,0.0.0.0,*'

# Déterminer l'environnement (development, staging, production)
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

# Importer la configuration correspondante
if DJANGO_ENV == 'production':
    from .production import *
elif DJANGO_ENV == 'staging':
    from .staging import *
else:
    from .development import *

# S'assurer que DEBUG est True en développement local
if DJANGO_ENV == 'development':
    DEBUG = True
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']