"""
WSGI config for MartialComp project.
"""
import os
from django.core.wsgi import get_wsgi_application

# Charger les variables d'environnement depuis .env (optionnel)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv n'est pas installé, ce n'est pas critique
    pass

# Utiliser les settings de développement par défaut (sera surchargé par manage.py ou variable d'environnement)
# En production, définir DJANGO_SETTINGS_MODULE=config.settings.production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

application = get_wsgi_application()