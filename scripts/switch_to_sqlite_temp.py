#!/usr/bin/env python3
"""
Script pour modifier temporairement settings.py pour utiliser SQLite
"""
import os
import shutil

def backup_and_modify_settings():
    settings_file = 'config/settings.py'
    backup_file = 'config/settings_postgres_backup.py'
    
    # Créer une sauvegarde
    if not os.path.exists(backup_file):
        shutil.copy2(settings_file, backup_file)
        print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le fichier actuel
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer la configuration PostgreSQL par SQLite
    postgres_config = '''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp',
        'USER': 'postgres',  # Remplacez par votre nom d'utilisateur PostgreSQL
        'PASSWORD': 'postgres',  # Remplacez par votre mot de passe PostgreSQL
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 secondes
        },
        'CONN_MAX_AGE': 60,  # Durée de vie des connexions en secondes
    }
}'''
    
    sqlite_config = '''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}'''
    
    # Remplacer la configuration
    new_content = content.replace(postgres_config, sqlite_config)
    
    # Sauvegarder le nouveau fichier
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Configuration modifiée pour utiliser SQLite")
    print(f"💾 Sauvegarde PostgreSQL: {backup_file}")
    print(f"🔄 Pour revenir à PostgreSQL: copier {backup_file} vers {settings_file}")

def restore_postgres_settings():
    settings_file = 'config/settings.py'
    backup_file = 'config/settings_postgres_backup.py'
    
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, settings_file)
        print(f"✅ Configuration PostgreSQL restaurée")
    else:
        print(f"❌ Fichier de sauvegarde non trouvé: {backup_file}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_postgres_settings()
    else:
        backup_and_modify_settings()