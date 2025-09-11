# Commandes manuelles pour transférer le fichier production.py sécurisé

## 1. Transférer le fichier depuis Windows

Ouvrez PowerShell et exécutez :

```powershell
# Transférer le fichier production.py sécurisé
scp production_secure.py psaserv@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py
```

## 2. Ou utiliser WinSCP

Si scp ne fonctionne pas, utilisez WinSCP :

1. Ouvrez WinSCP
2. Connectez-vous à `psaserv@martialcomp.com`
3. Naviguez vers `/var/www/vhosts/martialcomp.com/httpdocs/config/settings/`
4. Glissez-déposez le fichier `production_secure.py` et renommez-le en `production.py`

## 3. Vérifier le transfert

Connectez-vous en SSH et vérifiez :

```bash
ssh psaserv@martialcomp.com
cd /var/www/vhosts/martialcomp.com/httpdocs
ls -la config/settings/production.py
```

## 4. Tester la configuration

```bash
python manage.py check --deploy
```

## 5. Redémarrer les services

```bash
# Trouver le PID de Gunicorn
ps aux | grep gunicorn

# Redémarrer (remplacez [PID] par le vrai PID)
kill -HUP [PID]
```

## Fichier production.py sécurisé créé

Le fichier `production_secure.py` contient :

- ✅ DEBUG = False
- ✅ SECURE_SSL_REDIRECT = True
- ✅ SESSION_COOKIE_SECURE = True
- ✅ CSRF_COOKIE_SECURE = True
- ✅ SECURE_HSTS_SECONDS = 3600
- ✅ SECURE_HSTS_INCLUDE_SUBDOMAINS = True
- ✅ SECURE_HSTS_PRELOAD = True

Tous les autres paramètres de votre configuration existante sont conservés.
