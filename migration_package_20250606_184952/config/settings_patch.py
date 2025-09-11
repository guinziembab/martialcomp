"""
Patch à ajouter au settings.py de production
"""

# ====== CONFIGURATION MULTILINGUE ======

# Packages requis à installer:
# pip install django-rosetta django-modeltranslation polib deepl

# À ajouter à INSTALLED_APPS (modeltranslation AVANT admin):
INSTALLED_APPS = [
    'modeltranslation',  # DOIT être avant django.contrib.admin
    'django.contrib.admin',
    # ... autres apps
    'rosetta',  # Interface de gestion des traductions
    # ... vos apps existantes
]

# À ajouter à MIDDLEWARE (LocaleMiddleware après SessionMiddleware):
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # AJOUT POUR i18n
    'django.middleware.common.CommonMiddleware',
    # ... autres middlewares
]

# Configuration des langues
LANGUAGE_CODE = 'fr'  # Langue par défaut
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('no', 'Norsk'),
    ('ja', '日本語'),
    ('zh', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('pt', 'Português'),
    ('ko', '한국어'),
]

# Chemins des traductions
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Configuration modeltranslation
MODELTRANSLATION_LANGUAGES = ('fr', 'en', 'es', 'de', 'it')
MODELTRANSLATION_DEFAULT_LANGUAGE = 'fr'

# Configuration Rosetta
ROSETTA_REQUIRES_AUTH = True  # Seuls les admins peuvent accéder
ROSETTA_MESSAGES_PER_PAGE = 50
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True

# ====== FIN CONFIGURATION MULTILINGUE ======
