# Configuration de Déploiement Production - MartialComp

## 🎯 Chemin de Production (Plesk)
**Chemin complet**: `/var/www/vhosts/martialcomp.com/httpdocs`

## 📁 Structure Finale en Production

```
/var/www/vhosts/martialcomp.com/
├── httpdocs/                    # Racine web (DocumentRoot)
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings/
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/
│   ├── templates/
│   ├── static/                  # Fichiers statiques sources
│   ├── staticfiles/             # Fichiers collectés (collectstatic)
│   ├── media/                   # Uploads utilisateurs
│   ├── locale/                  # Traductions
│   └── logs/                    # Logs Django
├── logs/                        # Logs Apache/Nginx (Plesk)
├── cgi-bin/
├── error_docs/
└── private/                     # Fichiers privés (hors web)
```

## ⚙️ Configuration Plesk Spécifique

### 1. Python Application (Passenger)
- **Startup File**: `passenger_wsgi.py` (à créer)
- **Application Root**: `/var/www/vhosts/martialcomp.com/httpdocs`
- **Application URL**: `/`

### 2. Fichier passenger_wsgi.py
Créer ce fichier à la racine :
```python
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(__file__))

# Définir les settings Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

# Import WSGI application
from config.wsgi import application
```

### 3. Variables d'Environnement (dans Plesk)
```
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=your-secret-key-here
DB_NAME=martialcomp_prod
DB_USER=martialcomp_user
DB_PASSWORD=xxx
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com
```

### 4. Directives Apache Additionnelles
```apache
# Servir les fichiers statiques
Alias /static/ /var/www/vhosts/martialcomp.com/httpdocs/staticfiles/
<Directory /var/www/vhosts/martialcomp.com/httpdocs/staticfiles>
    Require all granted
</Directory>

# Servir les fichiers media
Alias /media/ /var/www/vhosts/martialcomp.com/httpdocs/media/
<Directory /var/www/vhosts/martialcomp.com/httpdocs/media>
    Require all granted
</Directory>
```

## 🔒 Permissions Requises

```bash
# Propriétaire des fichiers (utilisateur Plesk)
chown -R martialcomp:psacln /var/www/vhosts/martialcomp.com/httpdocs/

# Permissions des dossiers
chmod 755 /var/www/vhosts/martialcomp.com/httpdocs/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/apps/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/config/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/static/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/templates/

# Dossiers avec écriture
chmod -R 775 /var/www/vhosts/martialcomp.com/httpdocs/media/
chmod -R 775 /var/www/vhosts/martialcomp.com/httpdocs/logs/
chmod -R 775 /var/www/vhosts/martialcomp.com/httpdocs/staticfiles/
```

## 📋 Checklist de Déploiement

1. **Préparation locale**
   - [ ] Exécuter `./clean_dev_for_production.sh`
   - [ ] Exécuter `./create_production_package_v2.sh`

2. **Transfer sur le serveur**
   ```bash
   scp martialcomp_production_*.tar.gz user@martialcomp.com:/tmp/
   ```

3. **Installation sur le serveur**
   ```bash
   cd /var/www/vhosts/martialcomp.com/httpdocs
   tar -xzf /tmp/martialcomp_production_*.tar.gz
   ```

4. **Configuration Python (Plesk)**
   - [ ] Créer l'application Python dans Plesk
   - [ ] Définir Python 3.8+
   - [ ] Installer virtualenv

5. **Installation des dépendances**
   ```bash
   source /var/www/vhosts/martialcomp.com/httpdocs/venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Configuration Django**
   ```bash
   python manage.py collectstatic --noinput
   python manage.py migrate
   python manage.py createsuperuser
   ```

7. **Vérifications finales**
   - [ ] Tester l'accès au site
   - [ ] Vérifier les logs d'erreurs
   - [ ] Tester l'upload de fichiers
   - [ ] Vérifier l'accès admin

## ⚠️ Notes Importantes

1. **Base de données**: S'assurer que PostgreSQL est installé et configuré
2. **SSL**: Activer Let's Encrypt dans Plesk
3. **Backups**: Configurer les sauvegardes automatiques Plesk
4. **Monitoring**: Activer la surveillance des ressources