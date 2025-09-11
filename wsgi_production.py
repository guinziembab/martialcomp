import os
import sys
from django.core.wsgi import get_wsgi_application

# Ajouter le chemin du projet au PYTHONPATH
project_path = '/var/www/vhosts/martialcomp.com/httpdocs'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Configuration pour IONOS/Plesk
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'martialcomp.settings')

# Application WSGI
application = get_wsgi_application()

# Pour compatibilite avec certains serveurs
app = application
