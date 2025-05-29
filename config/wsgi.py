"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Utiliser settings_postgres.py pour avoir PostgreSQL tout en évitant les problèmes d'importation
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')

application = get_wsgi_application()
