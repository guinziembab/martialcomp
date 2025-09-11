# DEBUG PRODUCTION vs DÉVELOPPEMENT

## 🚨 Problème
- ✅ DEV: Processus signup fonctionne
- ❌ PROD: "Une erreur inattendue est survenue" persiste

## 🔍 DIAGNOSTIC NÉCESSAIRE

### 1. Vérifier les logs de production

```bash
# Se connecter au serveur et aller dans le bon répertoire
cd /opt/martialcomp/app

# Vérifier les logs Gunicorn
tail -50 /opt/martialcomp/logs/gunicorn_error.log

# Vérifier les logs Django (si disponibles)
tail -50 /opt/martialcomp/logs/django_error.log

# Ou logs système
tail -50 /var/log/martialcomp.log
```

### 2. Activer le débogage temporaire

```bash
# Dans l'environnement virtuel
cd /opt/martialcomp/app

# Modifier temporairement les settings pour voir les erreurs
cp config/settings.py config/settings.py.backup_debug

# Activer DEBUG temporairement (ATTENTION: seulement pour diagnostic)
sed -i 's/DEBUG = False/DEBUG = True/' config/settings.py

# Redémarrer Gunicorn pour prendre en compte les changements
pkill -f gunicorn
sleep 3
```

### 3. Tester avec les logs détaillés

```bash
# Tester la création d'utilisateur directement en shell
python manage.py shell

# Dans le shell Django:
from django.contrib.auth.models import User
from competitions.models import UserProfile
import traceback

try:
    # Créer un utilisateur de test
    user = User.objects.create_user(
        username='debug_test_123',
        email='debug@test.com',
        password='debug123'
    )
    print("✅ Utilisateur créé")
    
    # Créer le profil
    profile = UserProfile.objects.create(
        user=user,
        role='spectator',
        onboarding_step='role_selection',
        onboarding_completed=False
    )
    print("✅ Profil créé")
    
    # Nettoyer
    user.delete()
    print("✅ Test OK")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    traceback.print_exc()

exit()
```

### 4. Vérifier les différences d'environnement

```bash
# Comparer les settings
diff /var/www/vhosts/martialcomp.com/httpdocs/config/settings.py /opt/martialcomp/app/config/settings.py

# Vérifier les versions des packages
pip list | grep -E "(django|psycopg2)"

# Vérifier la configuration de la base de données
python manage.py shell -c "from django.db import connection; print(connection.settings_dict)"
```

## 🔧 SOLUTIONS POSSIBLES

### Problème 1: Configuration de base de données différente

```python
# Dans settings.py, vérifier:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'nom_correct_db',
        'USER': 'user_correct',
        'PASSWORD': 'password_correct',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Problème 2: URLs ou namespaces différents

```bash
# Vérifier les URLs
python manage.py shell -c "from django.urls import reverse; print(reverse('dashboard:index'))"
```

### Problème 3: Problème de permissions ou de signaux

```python
# Dans le shell Django, vérifier les signaux:
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from competitions.models import UserProfile

# Voir si les signaux sont connectés
print(post_save._live_receivers(sender=User))
```

## 📋 COMMANDES DE DIAGNOSTIC COMPLÈTES

```bash
# 1. Logs détaillés
cd /opt/martialcomp/app && tail -100 /opt/martialcomp/logs/gunicorn_error.log

# 2. Test utilisateur direct
python manage.py shell << 'EOF'
from django.contrib.auth.models import User
from competitions.models import UserProfile
import traceback
try:
    user = User.objects.create_user('test_debug_456', 'test@test.com', 'test123')
    profile = UserProfile.objects.create(user=user, role='spectator')
    print("✅ OK")
    user.delete()
except Exception as e:
    print(f"❌ {e}")
    traceback.print_exc()
EOF

# 3. Vérifier les URLs
python manage.py shell -c "from django.urls import reverse; print(reverse('dashboard:index'))"

# 4. Comparer les settings
ls -la config/settings*.py
```

## 🎯 PROCHAINES ÉTAPES

1. **Exécuter les commandes de diagnostic**
2. **Partager les logs d'erreur**
3. **Identifier la différence entre dev et prod**
4. **Appliquer la correction spécifique**

---

**🔍 Commencez par les logs d'erreur pour identifier la cause exacte !**