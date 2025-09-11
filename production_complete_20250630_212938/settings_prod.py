import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-martialcomp-secret-key-change-in-production-2025-auth-system'       

DEBUG = True

ALLOWED_HOSTS = ['*']

# Configuration CSRF pour la production
CSRF_TRUSTED_ORIGINS = [
  'https://martialcomp.com',
  'https://www.martialcomp.com',
  'http://martialcomp.com',
  'http://www.martialcomp.com',
]

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True

INSTALLED_APPS = [
  'django.contrib.admin',
  'django.contrib.auth',
  'django.contrib.contenttypes',
  'django.contrib.sessions',
  'django.contrib.messages',
  'django.contrib.staticfiles',
  'django.contrib.sites',
  'django_extensions',
  'widget_tweaks',
  'import_export',
  'rest_framework',
  'rest_framework_simplejwt',
  'oauth2_provider',
  'rosetta',
  'modeltranslation',
  'allauth',
  'allauth.account',
  'allauth.socialaccount',
  'allauth.socialaccount.providers.google',
  'allauth.socialaccount.providers.facebook',
  'competitions',
  'grades',
  'permissions_manager',
  'organizations',
  'finances',
  'shop',
  'documents',
  'multitenant',
  'api_auth',
  'family_management',
]

MIDDLEWARE = [
  'django.middleware.security.SecurityMiddleware',
  'django.contrib.sessions.middleware.SessionMiddleware',
  'django.middleware.locale.LocaleMiddleware',
  'django.middleware.common.CommonMiddleware',
  'django.middleware.csrf.CsrfViewMiddleware',
  'oauth2_provider.middleware.OAuth2TokenMiddleware',
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

# Base de données PostgreSQL avec le VRAI mot de passe
DATABASES = {
  'default': {
	  'ENGINE': 'django.db.backends.postgresql',
	  'NAME': 'martialcomp_db',
	  'USER': 'martialcomp_user',
	  'PASSWORD': 'AQWZSX123ok,',
	  'HOST': 'localhost',
	  'PORT': '5432',
  }
}

AUTH_PASSWORD_VALIDATORS = [
  {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
  {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
  {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
  {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
  ('fr', 'Français'),
  ('en', 'English'),
  ('es', 'Español'),
  ('it', 'Italiano'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
  'django.contrib.auth.backends.ModelBackend',
  'allauth.account.auth_backends.AuthenticationBackend',
  'oauth2_provider.backends.OAuth2Backend',
]

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

REST_FRAMEWORK = {
  'DEFAULT_AUTHENTICATION_CLASSES': (
	  'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
	  'rest_framework.authentication.SessionAuthentication',
  ),
  'DEFAULT_PERMISSION_CLASSES': [
	  'rest_framework.permissions.IsAuthenticated',
  ],
}

LOGGING = {
  'version': 1,
  'disable_existing_loggers': False,
  'handlers': {
	  'file': {
		  'level': 'INFO',
		  'class': 'logging.FileHandler',
		  'filename': '/var/www/vhosts/martialcomp.com/logs/django.log',
	  },
  },
  'loggers': {
	  'django': {
		  'handlers': ['file'],
		  'level': 'INFO',
		  'propagate': True,
	  },
  },
}

# Allauth redirections corrections
ACCOUNT_LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/dashboard/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'

# URLs d'authentification personnalisées
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'
# Configuration authentification sociale
SOCIALACCOUNT_PROVIDERS = {
  'google': {
	  'SCOPE': [
		  'profile',
		  'email',
	  ],
	  'AUTH_PARAMS': {
		  'access_type': 'online',
	  }
  },
  'facebook': {
	  'METHOD': 'oauth2',
	  'SCOPE': ['email', 'public_profile'],
	  'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
	  'INIT_PARAMS': {'cookie': True},
	  'FIELDS': [
		  'id',
		  'email',
		  'name',
		  'first_name',
		  'last_name',
		  'verified',
		  'locale',
		  'timezone',
		  'link',
		  'gender',
		  'updated_time',
	  ],
	  'EXCHANGE_TOKEN': True,
	  'LOCALE_FUNC': 'path.to.callable',
	  'VERIFIED_EMAIL': False,
	  'VERSION': 'v7.0',
  }
}

# Redirection après connexion sociale
SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_REDIRECT_URL = '/dashboard/'
SOCIALACCOUNT_SIGNUP_REDIRECT_URL = '/dashboard/'
