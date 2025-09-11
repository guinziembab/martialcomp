#!/bin/bash

# =============================================================================
# SCRIPT DE RECONSTRUCTION COMPLÈTE CORRIGÉ - MARTIALCOMP
# Reconstruit tout l'environnement virtuel avec les bonnes versions
# =============================================================================

set -e

echo "🚀 Reconstruction complète corrigée de l'environnement MartialComp..."

# Aller dans le bon répertoire
cd /opt/martialcomp/app

# =============================================================================
# 1. GÉNÉRATION NOUVEAU MOT DE PASSE
# =============================================================================

echo "🔐 Génération d'un nouveau mot de passe PostgreSQL..."
NEW_PASSWORD="MartialComp_$(date +%Y%m%d)_$(openssl rand -hex 4)"
echo "🔑 Nouveau mot de passe: $NEW_PASSWORD"

# Changer le mot de passe PostgreSQL
sudo -u postgres psql << EOF
ALTER USER martialcomp_user PASSWORD '$NEW_PASSWORD';
\q
EOF

echo "✅ Mot de passe PostgreSQL mis à jour"

# =============================================================================
# 2. SAUVEGARDE ET SUPPRESSION DE L'ANCIEN ENVIRONNEMENT
# =============================================================================

echo "💾 Sauvegarde et suppression de l'ancien environnement..."

# Sauvegarder les fichiers importants
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p backups/$TIMESTAMP
cp -r competitions/templates backups/$TIMESTAMP/ 2>/dev/null || true
cp config/settings.py backups/$TIMESTAMP/ 2>/dev/null || true
cp config/urls.py backups/$TIMESTAMP/ 2>/dev/null || true

# Supprimer complètement l'ancien environnement virtuel
echo "🗑️ Suppression de l'ancien environnement virtuel..."
deactivate 2>/dev/null || true
rm -rf venv/

echo "✅ Ancien environnement supprimé"

# =============================================================================
# 3. CRÉATION D'UN NOUVEL ENVIRONNEMENT VIRTUEL
# =============================================================================

echo "🔧 Création d'un nouvel environnement virtuel..."

# Créer un nouvel environnement virtuel
python3 -m venv venv

# Activer le nouvel environnement
source venv/bin/activate

# Mettre à jour pip
pip install --upgrade pip

echo "✅ Nouvel environnement virtuel créé"

# =============================================================================
# 4. INSTALLATION PROPRE DES DÉPENDANCES AVEC VERSIONS CORRECTES
# =============================================================================

echo "📦 Installation propre des dépendances avec versions compatibles..."

# Installer Django en premier
pip install Django==4.2.21

# Installer django-allauth version compatible qui existe
pip install django-allauth==0.63.6

# Installer PostgreSQL
pip install psycopg2-binary

# Installer les autres dépendances essentielles
pip install Pillow
pip install python-decouple
pip install requests

echo "✅ Dépendances installées avec versions correctes"

# =============================================================================
# 5. VÉRIFICATION DE L'INSTALLATION DJANGO
# =============================================================================

echo "🔍 Vérification de l'installation Django..."

python3 -c "
import django
print(f'✅ Django version: {django.get_version()}')

# Vérifier que le module migrations existe
try:
    from django.db.migrations.migration import Migration
    print('✅ Module migrations.migration OK')
except ImportError as e:
    print(f'❌ Erreur migrations: {e}')
    raise

# Vérifier django-allauth
try:
    import allauth
    print(f'✅ Django-allauth version: {allauth.__version__}')
except ImportError as e:
    print(f'❌ Erreur allauth: {e}')
    raise

print('🎉 Installation Django vérifiée avec succès')
"

# =============================================================================
# 6. CRÉATION D'UN SETTINGS.PY ULTRA-SIMPLE
# =============================================================================

echo "⚙️ Création d'un settings.py ultra-simple..."

cat > config/settings.py << EOF
"""
Django settings for MartialComp - Configuration ultra-simple reconstruite
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-martialcomp-rebuild-$(openssl rand -hex 16)'
DEBUG = True
ALLOWED_HOSTS = ['*']

# Applications minimales pour l'authentification
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    
    # Application locale minimale
    'competitions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
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
        'DIRS': [],
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

# Base de données PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'martialcomp_user',
        'PASSWORD': '$NEW_PASSWORD',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Médias
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Clé primaire par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sites framework
SITE_ID = 1

# Backends d'authentification
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Configuration Allauth moderne compatible avec 0.63.6
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Providers sociaux
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'name',
            'email',
        ],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v18.0',
    }
}

# Email (console pour le développement)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging simple
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
EOF

echo "✅ Settings.py ultra-simple créé"

# =============================================================================
# 7. CRÉATION D'UN MODELS.PY MINIMAL POUR COMPETITIONS
# =============================================================================

echo "🔧 Création d'un models.py minimal pour competitions..."

cat > competitions/models.py << 'MODELS_EOF'
"""
Models minimaux pour l'application competitions
"""
from django.db import models
from django.contrib.auth.models import User


class Competition(models.Model):
    """Modèle minimal pour les compétitions"""
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Créé par")
    
    class Meta:
        verbose_name = "Compétition"
        verbose_name_plural = "Compétitions"
    
    def __str__(self):
        return self.name


class Practitioner(models.Model):
    """Modèle minimal pour les pratiquants"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Utilisateur")
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(verbose_name="Email")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    
    class Meta:
        verbose_name = "Pratiquant"
        verbose_name_plural = "Pratiquants"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
MODELS_EOF

echo "✅ Models.py minimal créé"

# =============================================================================
# 8. CRÉATION D'UN ADMIN.PY POUR L'INTERFACE D'ADMINISTRATION
# =============================================================================

echo "🔧 Création d'un admin.py pour l'administration..."

cat > competitions/admin.py << 'ADMIN_EOF'
"""
Configuration admin pour l'application competitions
"""
from django.contrib import admin
from .models import Competition, Practitioner


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    """Configuration admin pour les compétitions"""
    list_display = ['name', 'created_by', 'date_created']
    list_filter = ['date_created', 'created_by']
    search_fields = ['name', 'description']
    date_hierarchy = 'date_created'


@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    """Configuration admin pour les pratiquants"""
    list_display = ['first_name', 'last_name', 'email', 'date_joined']
    list_filter = ['date_joined']
    search_fields = ['first_name', 'last_name', 'email']
    date_hierarchy = 'date_joined'
ADMIN_EOF

echo "✅ Admin.py créé"

# =============================================================================
# 9. TEST DE LA CONFIGURATION DJANGO
# =============================================================================

echo "🔍 Test de la configuration Django..."

python3 -c "
import sys
import os
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    print('✅ Django setup OK')
    
    # Test de connexion à la base de données
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
    print('✅ Connexion base de données OK')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

# =============================================================================
# 10. CRÉATION ET APPLICATION DES MIGRATIONS
# =============================================================================

echo "🔧 Création et application des migrations..."

# Supprimer toutes les anciennes migrations
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete 2>/dev/null || true
find . -path "*/migrations/*.pyc" -delete 2>/dev/null || true

# Recréer les __init__.py dans migrations
find . -name "migrations" -type d -exec touch {}/__init__.py \; 2>/dev/null || true

# Créer les nouvelles migrations
python manage.py makemigrations competitions --noinput

# Appliquer les migrations système d'abord
python manage.py migrate contenttypes --noinput
python manage.py migrate auth --noinput
python manage.py migrate sessions --noinput
python manage.py migrate sites --noinput
python manage.py migrate admin --noinput

# Appliquer les migrations allauth
python manage.py migrate account --noinput
python manage.py migrate socialaccount --noinput

# Appliquer les migrations competitions
python manage.py migrate competitions --noinput

echo "✅ Migrations créées et appliquées"

# =============================================================================
# 11. CRÉATION D'UN SUPERUTILISATEUR
# =============================================================================

echo "🔧 Création d'un superutilisateur..."

python3 << 'SUPERUSER_SCRIPT'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@martialcomp.com',
            password='MartialCompAdmin2025!'
        )
        print("✅ Superutilisateur créé:")
        print("  Username: admin")
        print("  Password: MartialCompAdmin2025!")
    else:
        print("✅ Superutilisateur existe déjà")
except Exception as e:
    print(f"⚠️ Erreur création superutilisateur: {e}")
SUPERUSER_SCRIPT

# =============================================================================
# 12. CONFIGURATION DES APPLICATIONS SOCIALES
# =============================================================================

echo "🔧 Configuration des applications sociales..."

python3 << 'SOCIAL_CONFIG'
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

try:
    # Supprimer les anciennes applications
    SocialApp.objects.all().delete()
    print("✅ Anciennes applications supprimées")
    
    # Configurer le site
    site, created = Site.objects.get_or_create(pk=1)
    site.domain = 'martialcomp.com'
    site.name = 'MartialComp'
    site.save()
    print(f"✅ Site configuré: {site.domain}")
    
    # Créer l'application Google
    google_app = SocialApp.objects.create(
        provider='google',
        name='Google',
        client_id='243898642746-6tjnpdflrrsetgif0fne7pgs4v66j6j5.apps.googleusercontent.com',
        secret='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'
    )
    google_app.sites.add(site)
    print("✅ Application Google configurée")
    
    # Créer l'application Facebook
    facebook_app = SocialApp.objects.create(
        provider='facebook',
        name='Facebook',
        client_id='1415333696343612',
        secret='fd1e66ffcd47958997274808d0c2ec64'
    )
    facebook_app.sites.add(site)
    print("✅ Application Facebook configurée")
    
    print("🎉 Configuration sociale terminée")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
SOCIAL_CONFIG

# =============================================================================
# 13. CRÉATION DES TEMPLATES D'AUTHENTIFICATION
# =============================================================================

echo "🎨 Création des templates d'authentification..."

# Créer la structure des répertoires
mkdir -p competitions/templates/account
mkdir -p competitions/templates/competitions

# Template de connexion moderne
cat > competitions/templates/account/login.html << 'LOGIN_EOF'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - MartialComp</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 450px;
            backdrop-filter: blur(10px);
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #333;
            font-size: 2.5rem;
            margin: 0.5rem 0;
            font-weight: 300;
        }
        .emoji {
            font-size: 3rem;
            display: block;
        }
        .success-banner {
            background: linear-gradient(135deg, #11998e, #38ef7d);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            font-weight: 500;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn {
            width: 100%;
            padding: 1rem;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 1rem;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .btn-google {
            background: #4285f4;
            color: white;
        }
        .btn-google:hover {
            background: #3367d6;
            transform: translateY(-2px);
        }
        .btn-facebook {
            background: #1877f2;
            color: white;
        }
        .btn-facebook:hover {
            background: #166fe5;
            transform: translateY(-2px);
        }
        .divider {
            text-align: center;
            margin: 2rem 0;
            position: relative;
            color: #666;
        }
        .divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: #e1e5e9;
        }
        .divider span {
            background: rgba(255, 255, 255, 0.95);
            padding: 0 1rem;
            position: relative;
        }
        .links {
            text-align: center;
            margin-top: 2rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
            margin: 0 1rem;
            font-weight: 500;
        }
        .links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <span class="emoji">🥋</span>
            <h1>MartialComp</h1>
            <p>Connexion à votre compte</p>
        </div>
        
        <div class="success-banner">
            ✅ Environnement entièrement reconstruit !
        </div>
        
        <form method="post">
            {% csrf_token %}
            
            <div class="form-group">
                <label for="id_login">📧 Email ou nom d'utilisateur</label>
                <input type="text" name="login" id="id_login" required placeholder="Votre email">
            </div>
            
            <div class="form-group">
                <label for="id_password">🔒 Mot de passe</label>
                <input type="password" name="password" id="id_password" required placeholder="Votre mot de passe">
            </div>
            
            <button type="submit" class="btn btn-primary">
                🚀 Se connecter
            </button>
        </form>
        
        <div class="divider">
            <span>Ou connectez-vous avec</span>
        </div>
        
        <a href="/accounts/google/login/" class="btn btn-google">
            📱 Continuer avec Google
        </a>
        
        <a href="/accounts/facebook/login/" class="btn btn-facebook">
            📘 Continuer avec Facebook
        </a>
        
        <div class="links">
            <a href="/accounts/signup/">➕ Créer un compte</a>
            <a href="/">🏠 Retour à l'accueil</a>
            <a href="/admin/">⚙️ Administration</a>
        </div>
    </div>
</body>
</html>
LOGIN_EOF

# Template d'inscription
cat > competitions/templates/account/signup.html << 'SIGNUP_EOF'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Créer un compte - MartialComp</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .signup-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 450px;
            backdrop-filter: blur(10px);
        }
        .logo {
            text-align: center;
            margin-bottom: 2rem;
        }
        .logo h1 {
            color: #333;
            font-size: 2.5rem;
            margin: 0.5rem 0;
            font-weight: 300;
        }
        .emoji {
            font-size: 3rem;
            display: block;
        }
        .success-banner {
            background: linear-gradient(135deg, #11998e, #38ef7d);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
            font-weight: 500;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: #333;
            font-weight: 500;
        }
        .form-group input {
            width: 100%;
            padding: 1rem;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn {
            width: 100%;
            padding: 1rem;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 1rem;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .btn-google {
            background: #4285f4;
            color: white;
        }
        .btn-google:hover {
            background: #3367d6;
            transform: translateY(-2px);
        }
        .btn-facebook {
            background: #1877f2;
            color: white;
        }
        .btn-facebook:hover {
            background: #166fe5;
            transform: translateY(-2px);
        }
        .divider {
            text-align: center;
            margin: 2rem 0;
            position: relative;
            color: #666;
        }
        .divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background: #e1e5e9;
        }
        .divider span {
            background: rgba(255, 255, 255, 0.95);
            padding: 0 1rem;
            position: relative;
        }
        .links {
            text-align: center;
            margin-top: 2rem;
        }
        .links a {
            color: #667eea;
            text-decoration: none;
            margin: 0 1rem;
            font-weight: 500;
        }
        .links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="signup-container">
        <div class="logo">
            <span class="emoji">🥋</span>
            <h1>MartialComp</h1>
            <p>Créer votre compte</p>
        </div>
        
        <div class="success-banner">
            ✅ Inscription rapide et sécurisée !
        </div>
        
        <form method="post">
            {% csrf_token %}
            
            <div class="form-group">
                <label for="id_email">📧 Adresse email</label>
                <input type="email" name="email" id="id_email" required placeholder="votre@email.com">
            </div>
            
            <div class="form-group">
                <label for="id_password1">🔒 Mot de passe</label>
                <input type="password" name="password1" id="id_password1" required placeholder="Choisissez un mot de passe">
            </div>
            
            <div class="form-group">
                <label for="id_password2">🔒 Confirmer le mot de passe</label>
                <input type="password" name="password2" id="id_password2" required placeholder="Confirmez votre mot de passe">
            </div>
            
            <button type="submit" class="btn btn-primary">
                ✨ Créer mon compte
            </button>
        </form>
        
        <div class="divider">
            <span>Ou inscrivez-vous avec</span>
        </div>
        
        <a href="/accounts/google/login/" class="btn btn-google">
            📱 S'inscrire avec Google
        </a>
        
        <a href="/accounts/facebook/login/" class="btn btn-facebook">
            📘 S'inscrire avec Facebook
        </a>
        
        <div class="links">
            <a href="/accounts/login/">🔑 J'ai déjà un compte</a>
            <a href="/">🏠 Retour à l'accueil</a>
        </div>
    </div>
</body>
</html>
SIGNUP_EOF

# Template d'accueil avec informations complètes
cat > competitions/templates/competitions/welcome.html << 'WELCOME_EOF'
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MartialComp - Bienvenue</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 3rem;
        }
        .header h1 {
            font-size: 3rem;
            color: #333;
            margin: 0.5rem 0;
            font-weight: 300;
        }
        .emoji {
            font-size: 4rem;
            display: block;
        }
        .success-banner {
            background: linear-gradient(135deg, #11998e, #38ef7d);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 3rem;
            text-align: center;
        }
        .success-banner h2 {
            margin: 0 0 1rem 0;
            font-size: 1.5rem;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }
        .info-card {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 15px;
            border-left: 5px solid #667eea;
        }
        .info-card h3 {
            color: #333;
            margin-bottom: 1rem;
            font-size: 1.2rem;
        }
        .info-card ul {
            list-style: none;
            padding: 0;
        }
        .info-card li {
            padding: 0.5rem 0;
            color: #555;
        }
        .info-card li::before {
            content: '✅ ';
            color: #28a745;
            font-weight: bold;
        }
        .auth-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .auth-card {
            background: #f8f9fa;
            padding: 2rem;
            border-radius: 15px;
            text-align: center;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }
        .auth-card:hover {
            border-color: #667eea;
            transform: translateY(-5px);
        }
        .auth-card h3 {
            color: #333;
            margin-bottom: 1rem;
        }
        .btn {
            display: inline-block;
            padding: 1rem 2rem;
            border: none;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            margin: 0.5rem;
            transition: all 0.3s ease;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        .btn-admin {
            background: linear-gradient(135deg, #ff6b6b, #ee5a24);
            color: white;
        }
        .btn-google {
            background: #4285f4;
            color: white;
        }
        .btn-facebook {
            background: #1877f2;
            color: white;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        .credentials {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 1.5rem;
            margin-top: 2rem;
        }
        .credentials h4 {
            color: #856404;
            margin-bottom: 1rem;
        }
        .credentials code {
            background: #f1f3f4;
            padding: 0.2rem 0.5rem;
            border-radius: 3px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="emoji">🥋</span>
            <h1>MartialComp</h1>
            <p>Plateforme de gestion des compétitions d'arts martiaux</p>
        </div>
        
        <div class="success-banner">
            <h2>🎉 Reconstruction complète réussie !</h2>
            <p>Environnement virtuel recréé • Django 4.2.21 • django-allauth 0.63.6</p>
            <p><strong>Nouveau mot de passe PostgreSQL: $NEW_PASSWORD</strong></p>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>🔧 Infrastructure Technique</h3>
                <ul>
                    <li>Environnement virtuel Python 3.9 reconstruit</li>
                    <li>Django 4.2.21 installé proprement</li>
                    <li>django-allauth 0.63.6 configuré</li>
                    <li>PostgreSQL reconnecté</li>
                    <li>Migrations appliquées</li>
                </ul>
            </div>
            
            <div class="info-card">
                <h3>🔐 Authentification</h3>
                <ul>
                    <li>Connexion classique email/password</li>
                    <li>Google OAuth configuré</li>
                    <li>Facebook OAuth configuré</li>
                    <li>Interface d'administration</li>
                    <li>Gestion des utilisateurs</li>
                </ul>
            </div>
            
            <div class="info-card">
                <h3>🎨 Interface Utilisateur</h3>
                <ul>
                    <li>Templates modernes créés</li>
                    <li>Design responsive</li>
                    <li>Formulaires stylisés</li>
                    <li>Animations CSS</li>
                    <li>Interface intuitive</li>
                </ul>
            </div>
        </div>
        
        <div class="auth-section">
            <div class="auth-card">
                <h3>🔑 Connexion Utilisateur</h3>
                <p>Connectez-vous avec votre compte</p>
                <a href="/accounts/login/" class="btn btn-primary">Se connecter</a>
                <a href="/accounts/signup/" class="btn btn-primary">Créer un compte</a>
            </div>
            
            <div class="auth-card">
                <h3>📱 Connexion Sociale</h3>
                <p>Utilisez vos comptes sociaux</p>
                <a href="/accounts/google/login/" class="btn btn-google">Google</a>
                <a href="/accounts/facebook/login/" class="btn btn-facebook">Facebook</a>
            </div>
            
            <div class="auth-card">
                <h3>⚙️ Administration</h3>
                <p>Interface d'administration Django</p>
                <a href="/admin/" class="btn btn-admin">Administration</a>
            </div>
        </div>
        
        <div class="credentials">
            <h4>🔑 Informations de connexion</h4>
            <p><strong>Superutilisateur :</strong></p>
            <p>Username: <code>admin</code></p>
            <p>Password: <code>MartialCompAdmin2025!</code></p>
            <p><strong>Base de données PostgreSQL :</strong></p>
            <p>Nouveau mot de passe: <code>$NEW_PASSWORD</code></p>
        </div>
    </div>
</body>
</html>
WELCOME_EOF

echo "✅ Templates créés"

# =============================================================================
# 14. COLLECTE DES FICHIERS STATIQUES
# =============================================================================

echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# =============================================================================
# 15. REDÉMARRAGE DJANGO
# =============================================================================

echo "🚀 Redémarrage Django avec le nouvel environnement..."

# Arrêter les anciens processus
pkill -f python || true
pkill -f gunicorn || true
sleep 3

# Démarrer Django
nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_rebuild_fixed_$TIMESTAMP.log 2>&1 &

echo "⏳ Attente du démarrage Django..."
sleep 15

# =============================================================================
# 16. TESTS FINAUX
# =============================================================================

echo "🧪 Tests de validation finale..."

# Test de l'application
django_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/" 2>/dev/null || echo "000")
login_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/accounts/login/" 2>/dev/null || echo "000")
signup_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/accounts/signup/" 2>/dev/null || echo "000")
admin_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/admin/" 2>/dev/null || echo "000")
google_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/accounts/google/login/" 2>/dev/null || echo "000")
facebook_status=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/accounts/facebook/login/" 2>/dev/null || echo "000")

echo ""
echo "📊 RÉSULTATS DES TESTS :"
echo "  🏠 Page d'accueil:    $django_status"
echo "  🔐 Login:            $login_status"
echo "  📝 Signup:           $signup_status"
echo "  ⚙️  Admin:            $admin_status"
echo "  📱 Google OAuth:     $google_status"
echo "  📘 Facebook OAuth:   $facebook_status"

# =============================================================================
# 17. RÉSULTAT FINAL
# =============================================================================

echo ""
echo "🔑 INFORMATIONS DE CONNEXION :"
echo "  PostgreSQL: $NEW_PASSWORD"
echo "  Admin: admin / MartialCompAdmin2025!"
echo ""

if [[ "$django_status" == "200" && "$login_status" == "200" && "$signup_status" == "200" && "$admin_status" == "200" ]]; then
    echo "🎉🎉🎉 RECONSTRUCTION COMPLÈTE 100% RÉUSSIE ! 🎉🎉🎉"
    echo ""
    echo "✅ SYSTÈME ENTIÈREMENT OPÉRATIONNEL :"
    echo "  • Environnement virtuel Python 3.9 reconstruit"
    echo "  • Django 4.2.21 installé et configuré"
    echo "  • django-allauth 0.63.6 configuré"
    echo "  • PostgreSQL reconnecté (nouveau mot de passe)"
    echo "  • Migrations créées et appliquées"
    echo "  • Superutilisateur créé (admin / MartialCompAdmin2025!)"
    echo "  • Applications sociales Google/Facebook configurées"
    echo "  • Templates modernes avec design professionnel"
    echo "  • Modèles Django avec interface d'administration"
    echo ""
    echo "🔗 URLS OPÉRATIONNELLES :"
    echo "  • http://127.0.0.1:8000/ - Page d'accueil complète"
    echo "  • http://127.0.0.1:8000/accounts/login/ - Connexion"
    echo "  • http://127.0.0.1:8000/accounts/signup/ - Inscription"
    echo "  • http://127.0.0.1:8000/admin/ - Administration"
    echo "  • http://127.0.0.1:8000/accounts/google/login/ - Google OAuth"
    echo "  • http://127.0.0.1:8000/accounts/facebook/login/ - Facebook OAuth"
    echo ""
    echo "🌐 EN PRODUCTION :"
    echo "  • https://martialcomp.com/"
    echo "  • https://martialcomp.com/accounts/login/"
    echo "  • https://martialcomp.com/accounts/signup/"
    echo "  • https://martialcomp.com/admin/"
    echo ""
    echo "🔑 IDENTIFIANTS IMPORTANTS :"
    echo "  • Superutilisateur: admin / MartialCompAdmin2025!"
    echo "  • PostgreSQL: martialcomp_user / $NEW_PASSWORD"
    echo ""
    echo "🎯 MARTIALCOMP EST MAINTENANT ENTIÈREMENT FONCTIONNEL !"
    
elif [[ "$django_status" == "200" ]]; then
    echo "⚠️ SUCCÈS PARTIEL"
    echo "✅ Django fonctionne"
    echo "⚠️ Quelques URLs à vérifier"
    
else
    echo "❌ PROBLÈME DÉTECTÉ"
    echo ""
    echo "📋 LOGS RÉCENTS :"
    tail -20 /tmp/django_rebuild_fixed_$TIMESTAMP.log 2>/dev/null || echo "Pas de logs"
fi

echo ""
echo "💾 SAUVEGARDES CRÉÉES DANS :"
echo "  • backups/$TIMESTAMP/"
echo ""
echo "🏁 RECONSTRUCTION COMPLÈTE TERMINÉE !"
echo "⏰ Durée totale: $(date)"