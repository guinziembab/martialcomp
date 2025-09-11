#!/usr/bin/env python3
"""
Script simple pour migrer les données SQLite vers PostgreSQL
"""
import os
import shutil
import subprocess
import json

def backup_sqlite_data():
    """Sauvegarder les données SQLite"""
    print("🔄 Sauvegarde des données SQLite...")
    
    # Créer un fichier settings temporaire pour SQLite
    sqlite_settings = """
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-migration-temp'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'rosetta',
    'modeltranslation',
    'competitions',
    'organizations',
    'multitenant',
    'grades',
    'finances',
    'shop',
    'documents',
    'family_management',
    'permissions_manager',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'competitions' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'fr'
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('pt', 'Português'),
    ('no', 'Norsk'),
    ('ja', '日本語'),
    ('zh', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED = True
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
"""
    
    # Écrire le fichier de settings pour SQLite
    with open('config/settings_sqlite.py', 'w', encoding='utf-8') as f:
        f.write(sqlite_settings)
    
    try:
        # Export des données avec les settings SQLite
        result = subprocess.run([
            'python', 'manage.py', 'dumpdata',
            '--settings=config.settings_sqlite',
            '--natural-foreign',
            '--natural-primary',
            '--exclude=contenttypes',
            '--exclude=auth.Permission',
            '--exclude=sessions.Session',
            '--output=sqlite_backup.json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Données SQLite exportées")
            return True
        else:
            print(f"❌ Erreur export SQLite: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception lors de l'export: {e}")
        return False
    finally:
        # Nettoyer le fichier temporaire
        if os.path.exists('config/settings_sqlite.py'):
            os.remove('config/settings_sqlite.py')

def restore_to_postgresql():
    """Restaurer vers PostgreSQL"""
    print("🔄 Restauration vers PostgreSQL...")
    
    try:
        # Vérifier que le fichier de backup existe
        if not os.path.exists('sqlite_backup.json'):
            print("❌ Fichier sqlite_backup.json non trouvé")
            return False
        
        # Réappliquer les migrations sur PostgreSQL (nettoie la DB)
        print("  - Réinitialisation des migrations...")
        result = subprocess.run([
            'python', 'manage.py', 'migrate',
            '--run-syncdb'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Erreur migration: {result.stderr}")
            return False
        
        # Charger les données
        print("  - Chargement des données...")
        result = subprocess.run([
            'python', 'manage.py', 'loaddata',
            'sqlite_backup.json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Données restaurées vers PostgreSQL")
            return True
        else:
            print(f"❌ Erreur loaddata: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception lors de la restauration: {e}")
        return False

def main():
    """Migration complète"""
    print("🚀 Migration SQLite → PostgreSQL")
    
    # Vérifier que SQLite existe
    if not os.path.exists('db.sqlite3'):
        print("❌ Fichier db.sqlite3 non trouvé")
        return False
    
    # Backup SQLite
    if not backup_sqlite_data():
        return False
    
    # Restaurer vers PostgreSQL
    if not restore_to_postgresql():
        return False
    
    # Nettoyer
    if os.path.exists('sqlite_backup.json'):
        os.remove('sqlite_backup.json')
        print("🧹 Fichier de backup nettoyé")
    
    print("🎉 Migration terminée!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)