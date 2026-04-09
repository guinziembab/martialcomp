"""
WSGI config for MartialComp project - Production
Version: 2025-12-20 - Auto-détection version Python
"""
import os
import sys

# =============================================================================
# CONFIGURATION ABSOLUE - AUTO-DETECTION VERSION PYTHON
# =============================================================================
PROJECT_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
VENV_DIR = '/var/www/vhosts/martialcomp.com/venv'

# Auto-détecter la version Python au lieu de coder en dur python3.11
PYTHON_VERSION = f'{sys.version_info.major}.{sys.version_info.minor}'
VENV_SITE_PACKAGES = f'{VENV_DIR}/lib/python{PYTHON_VERSION}/site-packages'

# =============================================================================
# AJOUTER les chemins du venv EN PREMIER (sans supprimer les chemins stdlib)
# On garde les chemins système pour subprocess, os, etc.
# =============================================================================
if VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

APPS_DIR = os.path.join(PROJECT_DIR, 'apps')
if APPS_DIR not in sys.path:
    sys.path.insert(0, APPS_DIR)

# Changer le répertoire de travail
os.chdir(PROJECT_DIR)

# =============================================================================
# CHARGER LES VARIABLES D'ENVIRONNEMENT
# =============================================================================
try:
    from dotenv import load_dotenv
    env_path = os.path.join(PROJECT_DIR, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        print(f"[WSGI] .env chargé depuis {env_path}")
except ImportError:
    print("[WSGI] python-dotenv non installé, lecture .env manuelle...")
    env_path = os.path.join(PROJECT_DIR, '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# =============================================================================
# CONFIGURER DJANGO
# =============================================================================
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
