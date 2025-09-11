import sys
import os

# Ajouter le chemin du projet au path Python
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

# Définir explicitement le module de settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Importer l'application WSGI Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 
import os

# Ajouter le chemin du projet au path Python
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

# Définir explicitement le module de settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Importer l'application WSGI Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application() 