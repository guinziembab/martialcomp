#!/usr/bin/env python3
import subprocess
import sys

# Configuration SSH
SSH_HOST = "martialcomp.com"
SSH_USER = "psaserv"
REMOTE_PATH = "/var/www/vhosts/martialcomp.com/httpdocs"

# Nouvelle clé secrète générée
SECRET_KEY = "DzhqL8hNwhFBNwCxLlpCUlNvAKfqQw1uXN6Y-TE8JIp_GYcOJQy6b57-Cz8ef-csJCg"

def run_ssh_command(command):
    """Exécute une commande SSH"""
    ssh_cmd = f'ssh {SSH_USER}@{SSH_HOST} "{command}"'
    print(f"Exécution : {ssh_cmd}")
    result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erreur SSH : {result.stderr}")
        return False
    print(f"Succès : {result.stdout}")
    return True

def update_env_file():
    """Met à jour le fichier .env avec les paramètres de sécurité"""
    env_content = f'''DEBUG=False
SECRET_KEY={SECRET_KEY}
SECURE_HSTS_SECONDS=3600
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Configuration base de données
DB_NAME=martialcomp_db
DB_USER=martialcomp_user
DB_PASSWORD=martialcomp_password_2024
DB_HOST=localhost
DB_PORT=5432

# Configuration email (si nécessaire)
EMAIL_HOST=smtp.ionos.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@martialcomp.com
EMAIL_HOST_PASSWORD=your_email_password

# Configuration statiques
STATIC_URL=/static/
MEDIA_URL=/media/
'''
    
    # Créer le fichier .env temporaire
    with open('temp_env.txt', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    # Transférer le fichier .env
    scp_cmd = f'scp temp_env.txt {SSH_USER}@{SSH_HOST}:{REMOTE_PATH}/.env'
    print(f"Transfert du fichier .env : {scp_cmd}")
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Erreur de transfert : {result.stderr}")
        return False
    
    print("Fichier .env transféré avec succès")
    return True

def update_production_settings():
    """Met à jour le fichier production.py avec les paramètres de sécurité"""
    settings_content = '''from decouple import config, Csv
from .base import *

# Désactiver le mode DEBUG en production
DEBUG = config('DEBUG', default=False, cast=bool)

# Charger la clé secrète depuis les variables d'environnement
SECRET_KEY = config('SECRET_KEY')

# Configuration de la base de données
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# Paramètres de sécurité
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=3600, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Configuration des fichiers statiques
STATIC_URL = config('STATIC_URL', default='/static/')
MEDIA_URL = config('MEDIA_URL', default='/media/')

# Configuration des hôtes autorisés
ALLOWED_HOSTS = ['martialcomp.com', 'www.martialcomp.com', 'localhost', '127.0.0.1']

# Configuration des logs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/martialcomp/django.log',
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
'''
    
    # Créer le fichier production.py temporaire
    with open('temp_production.py', 'w', encoding='utf-8') as f:
        f.write(settings_content)
    
    # Transférer le fichier production.py
    scp_cmd = f'scp temp_production.py {SSH_USER}@{SSH_HOST}:{REMOTE_PATH}/config/settings/production.py'
    print(f"Transfert du fichier production.py : {scp_cmd}")
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Erreur de transfert : {result.stderr}")
        return False
    
    print("Fichier production.py transféré avec succès")
    return True

def restart_services():
    """Redémarre les services Django"""
    commands = [
        "cd /var/www/vhosts/martialcomp.com/httpdocs",
        "python manage.py check --deploy",
        "python manage.py collectstatic --noinput",
        "python manage.py migrate",
        "kill -HUP $(ps aux | grep gunicorn | grep -v grep | awk '{print $2}')"
    ]
    
    for cmd in commands:
        if not run_ssh_command(cmd):
            print(f"Erreur lors de l'exécution de : {cmd}")
            return False
    
    return True

def main():
    print("=== Mise à jour de la sécurité en production ===")
    
    # Étape 1 : Mettre à jour le fichier .env
    print("\n1. Mise à jour du fichier .env...")
    if not update_env_file():
        print("❌ Échec de la mise à jour du fichier .env")
        return
    
    # Étape 2 : Mettre à jour le fichier production.py
    print("\n2. Mise à jour du fichier production.py...")
    if not update_production_settings():
        print("❌ Échec de la mise à jour du fichier production.py")
        return
    
    # Étape 3 : Redémarrer les services
    print("\n3. Redémarrage des services...")
    if not restart_services():
        print("❌ Échec du redémarrage des services")
        return
    
    print("\n✅ Mise à jour de sécurité terminée avec succès !")
    print("\nVérifications recommandées :")
    print("- Tester l'accès au site web")
    print("- Vérifier les logs Django : /var/log/martialcomp/django.log")
    print("- Tester la connexion HTTPS")

if __name__ == "__main__":
    main() 