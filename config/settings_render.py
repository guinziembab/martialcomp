# config/settings_render.py
from .settings import *

# Override settings specifically for Render
DEBUG = False

# Ensure ALLOWED_HOSTS contains the Render domain
ALLOWED_HOSTS = ['*.onrender.com', 'martialcomp-minimal-1.onrender.com', 'localhost']

# Configure database if needed
# import dj_database_url
# DATABASE_URL = os.environ.get('DATABASE_URL')
# if DATABASE_URL:
#     DATABASES = {
#         'default': dj_database_url.config(default=DATABASE_URL, conn_max_age=600)
#     }

# Configure static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True