# COMMANDES À EXÉCUTER SUR LE SERVEUR PRODUCTION

## 1. DIAGNOSTIC DES PROBLÈMES DE CONNEXION

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs

# Test de connexion base de données
python3 manage.py shell --settings=config.settings.production -c "
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    print('✓ Connexion base de données OK')
except Exception as e:
    print(f'✗ Erreur base de données: {e}')
"

# Vérifier les migrations
python3 manage.py showmigrations --settings=config.settings.production | grep -E "^\[ \]"

# Test des utilisateurs
python3 manage.py shell --settings=config.settings.production -c "
from django.contrib.auth.models import User
try:
    count = User.objects.count()
    print(f'✓ Utilisateurs dans la base: {count}')
except Exception as e:
    print(f'✗ Erreur utilisateurs: {e}')
"
```

## 2. CORRECTIONS DE CONFIGURATION

```bash
# Backup du fichier settings
cp config/settings/production.py config/settings/production.py.backup

# Corriger les variables de base de données
sed -i "s/'NAME': config('POSTGRES_DB')/'NAME': config('DB_NAME')/g" config/settings/production.py
sed -i "s/'USER': config('POSTGRES_USER')/'USER': config('DB_USER')/g" config/settings/production.py
sed -i "s/'PASSWORD': config('POSTGRES_PASSWORD')/'PASSWORD': config('DB_PASSWORD')/g" config/settings/production.py
sed -i "s/'HOST': config('POSTGRES_HOST'/'HOST': config('DB_HOST'/g" config/settings/production.py
sed -i "s/'PORT': config('POSTGRES_PORT'/'PORT': config('DB_PORT'/g" config/settings/production.py

# Ajouter la configuration temporaire
cat >> config/settings/production.py << 'EOF'

# Configuration temporaire pour résoudre les problèmes de connexion
SOCIALACCOUNT_PROVIDERS = {}  # Désactiver temporairement

# Forcer HTTPS en production
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

# Simplifier les backends d'authentification
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
EOF
```

## 3. INSTALLATION DES DÉPENDANCES

```bash
# Activer l'environnement virtuel
source .venv/bin/activate

# Installer les dépendances manquantes
pip install django-cors-headers python-decouple
```

## 4. MIGRATIONS ET UTILISATEUR DE TEST

```bash
# Appliquer les migrations
python3 manage.py migrate --settings=config.settings.production

# Créer un utilisateur admin de test
python3 manage.py shell --settings=config.settings.production -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@martialcomp.com', 'TempPassword123!')
    print('✓ Utilisateur admin créé (admin/TempPassword123!)')
else:
    print('✓ Utilisateur admin existe déjà')
"

# Collecter les fichiers statiques
python3 manage.py collectstatic --noinput --settings=config.settings.production
```

## 5. REDÉMARRAGE DES SERVICES

```bash
# Redémarrer Apache et Nginx
systemctl restart apache2
systemctl restart nginx

# Vérifier l'état
systemctl is-active apache2
systemctl is-active nginx
```

## 6. TEST FINAL

```bash
# Test de la page de connexion
curl -I "https://martialcomp.com/accounts/login/"
```

## RÉSULTAT ATTENDU

Après ces corrections, vous devriez pouvoir :

1. **Aller sur** : https://martialcomp.com/accounts/login/
2. **Se connecter avec** : 
   - Nom d'utilisateur : `admin`
   - Mot de passe : `TempPassword123!`

## VÉRIFICATIONS IMPORTANTES

- ✅ Variables d'environnement corrigées
- ✅ Authentification sociale désactivée temporairement  
- ✅ Dépendances installées
- ✅ Migrations appliquées
- ✅ Utilisateur admin créé
- ✅ Services redémarrés

## EN CAS DE PROBLÈME

Si le problème persiste, vérifiez :
```bash
# Logs d'erreur
tail -f /var/log/apache2/error.log
tail -f /var/log/nginx/error.log
```