# Configuration de Production Django – MartialComp (IONOS/Plesk/Passenger)

## 1. Prérequis

- Accès SSH root ou admin sur le serveur
- Accès Plesk (si applicable)
- Accès au dossier du projet `/var/www/vhosts/martialcomp.com/httpdocs/`
- Python 3.9+ installé
- Passenger activé sur le VirtualHost
- Base de données PostgreSQL opérationnelle

---

## 2. Fichiers et Paramètres Critiques

### A. Django

- `config/settings/production.py` : paramètres prod (ALLOWED_HOSTS, DB, sécurité)
- `config/wsgi.py` ou `passenger_wsgi.py` : point d’entrée WSGI (doit pointer sur `config.settings.production`)
- `config/urls.py` : toutes les routes nécessaires, inclure une route de debug temporaire si besoin
- `manage.py` : pour les commandes Django (migrate, collectstatic)

### B. Apache/Passenger

- `/var/www/vhosts/system/martialcomp.com/conf/vhost.conf` : config personnalisée Plesk/Passenger
- `/etc/apache2/sites-enabled/martialcomp-proxy.conf` : config proxy Apache (si utilisée)

### C. Statiques & médias

- `static/` et `media/` : droits et accessibilité

---

## 3. Points de Vérification Essentiels

- [ ] **passenger_wsgi.py** : contient `os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')`
- [ ] **production.py** : ALLOWED_HOSTS inclut le domaine, l’IP, localhost
- [ ] **vhost.conf** : Passenger activé, bon chemin projet, bon fichier WSGI
- [ ] **collectstatic** : fichiers statiques collectés et accessibles
- [ ] **migrate** : toutes les migrations appliquées
- [ ] **Droits** : www-data (ou équivalent) a accès au code et aux statiques
- [ ] **Redémarrage** : Apache/Passenger redémarré après chaque modif critique
- [ ] **Test debug** : une route `/debug-host/` répond en JSON

---

## 4. Checklist de Validation

1. **Code déployé dans `/httpdocs/`**
2. **passenger_wsgi.py** pointe sur `config.settings.production`
3. **production.py** bien configuré (ALLOWED_HOSTS, DB, sécurité)
4. **vhost.conf** active Passenger sur le bon dossier
5. **collectstatic** exécuté
6. **migrate** exécuté
7. **Redémarrage Apache/Passenger**
8. **Test accès** :
   - `http://martialcomp.com:7080/debug-host/` (ou port configuré par IONOS)
   - Résultat JSON attendu

---

## 5. Exemple de Fichier passenger_wsgi.py

```python
import sys
import os
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

---

## 6. Exemple de Bloc Passenger dans vhost.conf

```apache
<IfModule mod_passenger.c>
  PassengerEnabled on
  PassengerAppRoot /var/www/vhosts/martialcomp.com/httpdocs
  PassengerAppType wsgi
  PassengerStartupFile passenger_wsgi.py
  PassengerPython /usr/bin/python3
  PassengerMinInstances 1
</IfModule>
```

---

## 7. Exemple de Route de Debug dans config/views.py

```python
from django.http import JsonResponse
from django.conf import settings

def debug_host(request):
    return JsonResponse({
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "Host header reçu": request.META.get("HTTP_HOST"),
        "SERVER_NAME": request.META.get("SERVER_NAME"),
        "SERVER_PORT": request.META.get("SERVER_PORT"),
    })
```

---

## 8. Commandes Utiles

- Appliquer les migrations :
  ```bash
  python3 manage.py migrate --settings=config.settings.production
  ```
- Collecter les statiques :
  ```bash
  python3 manage.py collectstatic --settings=config.settings.production
  ```
- Redémarrer Apache :
  ```bash
  systemctl restart apache2
  ```

---

## 9. Conseils

- Toujours vérifier les logs Apache/Passenger en cas d’erreur 503/500/400
- Toujours redémarrer Apache/Passenger après modification d’un fichier critique
- Tester d’abord en local (`curl http://localhost:7080/debug-host/`), puis depuis l’extérieur

---

## **Analyse et corrections**

### 1. **Balises `<VirtualHost>`**

- **Ne surtout pas ajouter de balises `<VirtualHost>` dans ce fichier sous Plesk** (c’est bon, tu n’en as pas).

### 2. **Section `<Directory>`**

- Elle est correcte, mais tu peux ajouter :  
  `Options -MultiViews +FollowSymLinks`  
  _(FollowSymLinks est parfois nécessaire pour certains serveurs, mais pas obligatoire si tout fonctionne sans)_

### 3. **Directives Passenger**

- **Tout est bien présent** :

  - `PassengerEnabled on`
  - `PassengerAppRoot ...`
  - `PassengerAppType wsgi`
  - `PassengerStartupFile passenger_wsgi.py`
  - `PassengerPython ...`
  - `PassengerMinInstances 1`

- **Optionnel mais recommandé** :  
  Ajoute le log Passenger pour le debug :
  ```
  PassengerLogLevel 7
  ```

### 4. **Emplacement des logs**

- Les chemins sont bons.

---

## **Version corrigée et optimisée de ton `vhost.conf`**

```apache
<code_block_to_apply_changes_from>
ServerName martialcomp.com
ServerAlias www.martialcomp.com

DocumentRoot /var/www/vhosts/martialcomp.com/httpdocs

<Directory /var/www/vhosts/martialcomp.com/httpdocs>
    Require all granted
    Options -MultiViews
    AllowOverride All
</Directory>

<IfModule mod_passenger.c>
    PassengerEnabled on
    PassengerAppRoot /var/www/vhosts/martialcomp.com/httpdocs
    PassengerAppType wsgi
    PassengerStartupFile passenger_wsgi.py
    PassengerPython /var/www/vhosts/martialcomp.com/httpdocs/.venv/bin/python
    PassengerMinInstances 1
    PassengerLogLevel 7
</IfModule>

ErrorLog /var/www/vhosts/martialcomp.com/logs/error.log
CustomLog /var/www/vhosts/martialcomp.com/logs/access.log combined
```

**Remarques :**

- J’ai juste ajouté `PassengerLogLevel 7` pour le debug.
- J’ai corrigé la fin de la ligne `CustomLog` (il y avait un `root@beautiful-ellis...` en trop, probablement un copier-coller du prompt).

---

## **Procédure pour appliquer la correction**

1. **Remplace le contenu de `/var/www/vhosts/system/martialcomp.com/conf/vhost.conf`** par la version ci-dessus.
2. **Reconstruis la configuration Apache de Plesk** :
   ```bash
   plesk bin apache_pref --reconfigure-domain martialcomp.com
   ```
3. **Redémarre Apache** :
   ```bash
   systemctl restart apache2
   ```
4. **Teste l’accès à ton site** (et à `/debug-host/`).

5. **Si tu as encore un 503, consulte à nouveau les logs** (ils seront beaucoup plus bavards grâce à `PassengerLogLevel 7`).

---

## **Résumé**

- Ta config était presque bonne, il manquait juste un peu de clarté sur le log et une correction sur la ligne `CustomLog`.
- Applique la version corrigée, redémarre, et teste.
- Si ça ne marche pas, copie-moi les nouveaux logs (ils devraient enfin montrer l’erreur Python/Django si elle existe).

**Tu es à deux doigts du succès : le reverse proxy fonctionne, Django répond en local, mais tu as une erreur 400 “Bad Request” côté client et un crash du service systemd Django à cause d’un problème de logging.**

---

## **Analyse des erreurs**

### 1. **Erreur 400 “Bad Request” sur toutes les URLs**

- **Cause la plus fréquente** :
  - Le domaine (`martialcomp.com`) n’est pas dans `ALLOWED_HOSTS` dans tes settings Django.
  - Ou bien, le header `Host` n’est pas transmis correctement (mais ta config nginx est bonne).

### 2. **Erreur de logging Django dans systemd**

```
ValueError: Unable to configure handler 'file'
```

- **Cause** :
  - Le chemin du fichier de log défini dans tes settings Django n’existe pas, ou les droits sont insuffisants.
  - Cela fait crasher le service systemd, mais le serveur lancé manuellement fonctionne.

---

## **Ce qu’il faut faire**

### **A. Corriger ALLOWED_HOSTS dans Django**

1. **Ouvre le fichier**  
   `/var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py`
2. **Vérifie la ligne** :
   ```python
   ALLOWED_HOSTS = [
       "martialcomp.com",
       "www.martialcomp.com",
       "127.0.0.1",
       "localhost",
       "212.227.78.104"
   ]
   ```
   **Ajoute tous les domaines et IP utilisés.**

---

### **B. Corriger la configuration du logging Django**

1. **Dans tes settings, cherche la section LOGGING** (souvent en bas du fichier).
2. **Vérifie le chemin du fichier de log**.  
   Exemple :
   ```python
   'filename': '/var/www/vhosts/martialcomp.com/httpdocs/logs/django.log',
   ```
   - **Assure-toi que le dossier existe** :
     ```bash
     mkdir -p /var/www/vhosts/martialcomp.com/httpdocs/logs
     chown www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs/logs
     chmod 755 /var/www/vhosts/martialcomp.com/httpdocs/logs
     ```
   - **Ou modifie le chemin pour pointer vers un dossier existant et accessible en écriture par www-data.**

---

### **C. Redémarre le service Django**

```bash
systemctl restart martialcomp-django.service
systemctl status martialcomp-django.service
```

---

### **D. Teste à nouveau l’accès au site**

```bash
curl -L -k https://martialcomp.com/
```

ou via ton navigateur.

---

### **E. Vérifie les logs si besoin**

- **Log Django** (si configuré)
- **Log nginx** :
  ```bash
  tail -n 40 /var/log/nginx/error.log
  ```

---

## **Résumé**

- **Erreur 400** = problème d’ALLOWED_HOSTS (corrige dans Django).
- **Crash systemd** = problème de chemin de log Django (corrige le chemin et les droits).
- **Redémarre le service, puis teste.**

---

**Dis-moi si tu veux le code exact à mettre dans la section LOGGING,  
ou si tu veux une vérification automatique de la config après correction.**

Tu es à la toute dernière étape !

---

## **Analyse et corrections**

### 1. **Balises `<VirtualHost>`**

- **Ne surtout pas ajouter de balises `<VirtualHost>` dans ce fichier sous Plesk** (c’est bon, tu n’en as pas).

### 2. **Section `<Directory>`**

- Elle est correcte, mais tu peux ajouter :  
  `Options -MultiViews +FollowSymLinks`  
  _(FollowSymLinks est parfois nécessaire pour certains serveurs, mais pas obligatoire si tout fonctionne sans)_

### 3. **Directives Passenger**

- **Tout est bien présent** :

  - `PassengerEnabled on`
  - `PassengerAppRoot ...`
  - `PassengerAppType wsgi`
  - `PassengerStartupFile passenger_wsgi.py`
  - `PassengerPython ...`
  - `PassengerMinInstances 1`

- **Optionnel mais recommandé** :  
  Ajoute le log Passenger pour le debug :
  ```
  PassengerLogLevel 7
  ```

### 4. **Emplacement des logs**

- Les chemins sont bons.

---

## **Version corrigée et optimisée de ton `vhost.conf`**

```apache
<code_block_to_apply_changes_from>
ServerName martialcomp.com
ServerAlias www.martialcomp.com

DocumentRoot /var/www/vhosts/martialcomp.com/httpdocs

<Directory /var/www/vhosts/martialcomp.com/httpdocs>
    Require all granted
    Options -MultiViews
    AllowOverride All
</Directory>

<IfModule mod_passenger.c>
    PassengerEnabled on
    PassengerAppRoot /var/www/vhosts/martialcomp.com/httpdocs
    PassengerAppType wsgi
    PassengerStartupFile passenger_wsgi.py
    PassengerPython /var/www/vhosts/martialcomp.com/httpdocs/.venv/bin/python
    PassengerMinInstances 1
    PassengerLogLevel 7
</IfModule>

ErrorLog /var/www/vhosts/martialcomp.com/logs/error.log
CustomLog /var/www/vhosts/martialcomp.com/logs/access.log combined
```

**Remarques :**

- J’ai juste ajouté `PassengerLogLevel 7` pour le debug.
- J’ai corrigé la fin de la ligne `CustomLog` (il y avait un `root@beautiful-ellis...` en trop, probablement un copier-coller du prompt).

---

## **Procédure pour appliquer la correction**

1. **Remplace le contenu de `/var/www/vhosts/system/martialcomp.com/conf/vhost.conf`** par la version ci-dessus.
2. **Reconstruis la configuration Apache de Plesk** :
   ```bash
   plesk bin apache_pref --reconfigure-domain martialcomp.com
   ```
3. **Redémarre Apache** :
   ```bash
   systemctl restart apache2
   ```
4. **Teste l’accès à ton site** (et à `/debug-host/`).

5. **Si tu as encore un 503, consulte à nouveau les logs** (ils seront beaucoup plus bavards grâce à `PassengerLogLevel 7`).

---

## **Résumé**

- Ta config était presque bonne, il manquait juste un peu de clarté sur le log et une correction sur la ligne `CustomLog`.
- Applique la version corrigée, redémarre, et teste.
- Si ça ne marche pas, copie-moi les nouveaux logs (ils devraient enfin montrer l’erreur Python/Django si elle existe).

**Tu es à deux doigts du succès : le reverse proxy fonctionne, Django répond en local, mais tu as une erreur 400 “Bad Request” côté client et un crash du service systemd Django à cause d’un problème de logging.**

---

## **Analyse des erreurs**

### 1. **Erreur 400 “Bad Request” sur toutes les URLs**

- **Cause la plus fréquente** :
  - Le domaine (`martialcomp.com`) n’est pas dans `ALLOWED_HOSTS` dans tes settings Django.
  - Ou bien, le header `Host` n’est pas transmis correctement (mais ta config nginx est bonne).

### 2. **Erreur de logging Django dans systemd**

```
ValueError: Unable to configure handler 'file'
```

- **Cause** :
  - Le chemin du fichier de log défini dans tes settings Django n’existe pas, ou les droits sont insuffisants.
  - Cela fait crasher le service systemd, mais le serveur lancé manuellement fonctionne.

---

## **Ce qu’il faut faire**

### **A. Corriger ALLOWED_HOSTS dans Django**

1. **Ouvre le fichier**  
   `/var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py`
2. **Vérifie la ligne** :
   ```python
   ALLOWED_HOSTS = [
       "martialcomp.com",
       "www.martialcomp.com",
       "127.0.0.1",
       "localhost",
       "212.227.78.104"
   ]
   ```
   **Ajoute tous les domaines et IP utilisés.**

---

### **B. Corriger la configuration du logging Django**

1. **Dans tes settings, cherche la section LOGGING** (souvent en bas du fichier).
2. **Vérifie le chemin du fichier de log**.  
   Exemple :
   ```python
   'filename': '/var/www/vhosts/martialcomp.com/httpdocs/logs/django.log',
   ```
   - **Assure-toi que le dossier existe** :
     ```bash
     mkdir -p /var/www/vhosts/martialcomp.com/httpdocs/logs
     chown www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs/logs
     chmod 755 /var/www/vhosts/martialcomp.com/httpdocs/logs
     ```
   - **Ou modifie le chemin pour pointer vers un dossier existant et accessible en écriture par www-data.**

---

### **C. Redémarre le service Django**

```bash
systemctl restart martialcomp-django.service
systemctl status martialcomp-django.service
```

---

### **D. Teste à nouveau l’accès au site**

```bash
curl -L -k https://martialcomp.com/
```

ou via ton navigateur.

---

### **E. Vérifie les logs si besoin**

- **Log Django** (si configuré)
- **Log nginx** :
  ```bash
  tail -n 40 /var/log/nginx/error.log
  ```

---

## **Résumé**

- **Erreur 400** = problème d’ALLOWED_HOSTS (corrige dans Django).
- **Crash systemd** = problème de chemin de log Django (corrige le chemin et les droits).
- **Redémarre le service, puis teste.**

---

**Dis-moi si tu veux le code exact à mettre dans la section LOGGING,  
ou si tu veux une vérification automatique de la config après correction.**

Tu es à la toute dernière étape !
