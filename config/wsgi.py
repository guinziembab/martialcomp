"""
WSGI config forcé pour traductions
"""
import os
from django.core.wsgi import get_wsgi_application

# FORCER le settings simple
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_fixed')

application = get_wsgi_application()
