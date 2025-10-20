import os
from pathlib import Path
from .base import *  # noqa

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Test flags
DEBUG = False
RUNNING_TESTS = True

# Lightweight database for tests by default
if os.environ.get("TEST_USE_POSTGRES"):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'martialcomp_test'),
            'USER': os.environ.get('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': 0,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'test_db.sqlite3'),
        }
    }

# Faster password hashing during tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Emails go to memory
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Use dummy cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Sessions use DB for portability in tests
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Channels: in-memory layer for tests
ASGI_APPLICATION = 'config.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Disable migrations for faster and more reliable tests in dev
MIGRATION_MODULES = {
    'competitions': None,
    'organizations': None,
    'grades': None,
    'shop': None,
    'permissions_manager': None,
    'payment': None,
    'task_management': None,
    'membership': None,
    'finances': None,
    'family_management': None,
    'documents': None,
    'security': None,
    'accounts': None,
    'api_auth': None,
}

# Simplify logging output during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}
