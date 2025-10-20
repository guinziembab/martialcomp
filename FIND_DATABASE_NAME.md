# TROUVER LE NOM CORRECT DE LA BASE DE DONNÉES

## 1. Vérifier la configuration Django
```bash
# Extraire les infos de la base depuis la config
grep -A10 "DATABASES" /var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py | grep -E "NAME|HOST|USER|PORT"

# Ou chercher dans les variables d'environnement
cat /var/www/vhosts/martialcomp.com/httpdocs/.env 2>/dev/null | grep -i DB_
```

## 2. Lister toutes les bases PostgreSQL
```bash
# Lister toutes les bases disponibles
sudo -u postgres psql -l

# Ou si ça ne marche pas
sudo su - postgres
psql -l
exit
```

## 3. Chercher dans les processus en cours
```bash
# Voir la connexion utilisée par l'app
ps aux | grep postgres | grep -v grep
```

## 4. Alternative : Créer un script Python pour afficher la config
```bash
cat > /tmp/show_db_config.py << 'EOF'
import os
import sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

try:
    from django.conf import settings
    db_config = settings.DATABASES['default']
    print("Configuration de la base de données:")
    print(f"  NAME: {db_config.get('NAME', 'Non défini')}")
    print(f"  USER: {db_config.get('USER', 'Non défini')}")
    print(f"  HOST: {db_config.get('HOST', 'Non défini')}")
    print(f"  PORT: {db_config.get('PORT', 'Non défini')}")
    print(f"  ENGINE: {db_config.get('ENGINE', 'Non défini')}")
except Exception as e:
    print(f"Erreur: {e}")
    # Essayer de lire les variables d'environnement
    print("\nVariables d'environnement DB:")
    for key in os.environ:
        if 'DB' in key or 'DATABASE' in key:
            print(f"  {key}: {os.environ[key]}")
EOF

/var/www/vhosts/martialcomp.com/venv/bin/python3 /tmp/show_db_config.py
```

## 5. Une fois le nom trouvé
Si par exemple la base s'appelle `martialcomp_prod` :
```bash
# Se connecter avec le bon nom
sudo -u postgres psql -d martialcomp_prod

# Ou avec l'utilisateur spécifique
psql -h localhost -U [USER_TROUVÉ] -d [DB_NAME_TROUVÉ]
```