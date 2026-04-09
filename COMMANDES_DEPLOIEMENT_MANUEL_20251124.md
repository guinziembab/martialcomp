# Commandes de déploiement manuel - FIX CRITIQUE 24 novembre 2024

## ⚠️ IMPORTANT: Cause racine identifiée

L'erreur JavaScript `Uncaught SyntaxError: missing ) after argument list (at edit/:2570:5)` était causée par des **Django URL tags `{% url %}` dans le fichier base.html** (template parent), pas dans practitioner_form.html!

Les corrections ont été apportées aux lignes 231, 339 et 357 de [base.html](apps/competitions/templates/base.html).

---

## Option 1: Commandes SCP depuis votre machine locale

Si vous avez accès SSH depuis votre machine locale:

```bash
# Se positionner dans le répertoire du projet
cd c:\martial_hub_django\martialcomp

# Transférer les fichiers modifiés
scp apps/competitions/templates/base.html pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/

scp apps/competitions/views/club/registration_api.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/

scp apps/competitions/urls/__init__.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/

scp apps/competitions/urls/club.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/

scp apps/competitions/templates/competitions/club/practitioner_form.html pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/

scp apps/competitions/templates/competitions/dashboard/club.html pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/

scp apps/competitions/admin/__init__.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/admin/

scp apps/competitions/admin/practitioner.py pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/admin/
```

Puis se connecter au serveur:

```bash
ssh pierrep99@martialcomp.com
```

---

## Option 2: Via l'interface Plesk File Manager

1. Se connecter à Plesk: https://martialcomp.com:8443
2. Aller dans "Files" → "File Manager"
3. Naviguer vers `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/`
4. Uploader les fichiers suivants depuis votre machine locale:

### Fichiers à uploader:

#### 1. FIX CRITIQUE: base.html
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\templates\base.html`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/base.html`
- **Raison**: Correction des Django URL tags en JavaScript (lignes 231, 339, 357)

#### 2. registration_api.py
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\views\club\registration_api.py`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/registration_api.py`
- **Raison**: Ajout de la fonction `generate_license_number_api`

#### 3. urls/__init__.py
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\urls\__init__.py`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/__init__.py`
- **Raison**: Ajout de la route API pour génération de licence

#### 4. urls/club.py
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\urls\club.py`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/club.py`
- **Raison**: Import de la fonction generate_license_number_api

#### 5. practitioner_form.html
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\templates\competitions\club\practitioner_form.html`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/practitioner_form.html`
- **Raison**: Ajout de getCSRFToken() et correction URL API

#### 6. club.html (dashboard)
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\templates\competitions\dashboard\club.html`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/club.html`
- **Raison**: Implémentation du mode jour/nuit

#### 7. admin/__init__.py
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\admin\__init__.py`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/admin/__init__.py`
- **Raison**: Import du module practitioner admin

#### 8. admin/practitioner.py
- **Source locale**: `c:\martial_hub_django\martialcomp\apps\competitions\admin\practitioner.py`
- **Destination serveur**: `/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/admin/practitioner.py`
- **Raison**: Admin pour les pratiquants

---

## Étape 3: Commandes à exécuter sur le serveur

Une fois les fichiers transférés, se connecter au serveur via SSH ou Terminal Plesk:

```bash
# Se positionner dans le répertoire du projet
cd /var/www/vhosts/martialcomp.com/httpdocs

# Activer l'environnement virtuel
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Vérifier la syntaxe Python des fichiers modifiés
python -m py_compile apps/competitions/views/club/registration_api.py
python -m py_compile apps/competitions/urls/__init__.py
python -m py_compile apps/competitions/urls/club.py
python -m py_compile apps/competitions/admin/__init__.py
python -m py_compile apps/competitions/admin/practitioner.py

# Vérifier que les corrections JavaScript sont présentes dans base.html
grep -n "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html

# Si la commande ci-dessus retourne 3 lignes (231, 339, 357), les corrections sont présentes ✅

# Effacer le cache Python
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

# Recharger l'application (Passenger WSGI)
mkdir -p tmp
touch tmp/restart.txt

# OU si Gunicorn est utilisé:
# sudo systemctl restart gunicorn

echo "✓ Déploiement terminé"
```

---

## Tests à effectuer après déploiement

### Test 0: Vérifier l'absence d'erreur JavaScript (PRIORITAIRE) ✅
1. Ouvrir: https://martialcomp.com/en/competitions/club/practitioners/88/edit/
2. Appuyer sur **F12** pour ouvrir la console du navigateur
3. **VÉRIFIER**: Il ne doit **PLUS** y avoir l'erreur JavaScript à la ligne 2570
4. ✅ **Attendu**: Console propre, sans erreur `Uncaught SyntaxError`

### Test 1: Bouton Générer licence ✅
1. Sur la même page, remplir:
   - Date de naissance
   - Nom de famille
   - Au moins une discipline
2. Cliquer sur le bouton "**Générer**"
3. ✅ **Attendu**: Un numéro de licence apparaît au format `DISC-YYYY-CLUB-XXXX`
   - Exemple: `QKD-1990-0001-MA5K7T`

### Test 2: Mode jour/nuit ✅
1. Ouvrir: https://martialcomp.com/en/competitions/dashboard/club/
2. Chercher le bouton **☀️/🌙** en haut à droite
3. Cliquer dessus pour basculer entre mode clair et mode sombre
4. ✅ **Attendu**: Le thème change et reste persistant après rechargement (F5)

---

## En cas de problème

### Si l'erreur JavaScript persiste:
1. Vérifier que [base.html](apps/competitions/templates/base.html) a bien été transféré
2. Vérifier que le cache Python a été effacé
3. Vérifier que l'application a été rechargée (`touch tmp/restart.txt`)
4. Vider le cache du navigateur (Ctrl+Shift+Delete)

### Si le bouton Générer ne fonctionne pas:
1. Vérifier les logs Django pour les erreurs Python
2. Vérifier que l'URL `/api/generate-license-number/` est bien enregistrée
3. Ouvrir la console du navigateur (F12) et cliquer sur "Générer" pour voir les erreurs

### Vérifier les logs:
```bash
# Logs Django (si configurés)
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log

# Logs Apache/Nginx
tail -f /var/log/apache2/error.log
# OU
tail -f /var/log/nginx/error.log

# Logs Passenger
tail -f /var/log/passenger/passenger.log
```

---

## Résumé des corrections

### 1. FIX CRITIQUE: base.html (3 endroits)
Remplacement de Django `{% url %}` tags par JavaScript dynamique:
- Ligne 231: `loadNotifications()` function
- Ligne 339: `markAsRead()` function
- Ligne 357: `markAllAsRead()` function

### 2. Bouton Générer licence
- Ajout de l'API endpoint
- Correction du JavaScript dans practitioner_form.html
- Ajout de la fonction getCSRFToken()

### 3. Mode jour/nuit
- Ajout du toggle button
- Implémentation CSS avec variables
- Persistance via localStorage

---

**Date**: 24 novembre 2024
**Auteur**: Claude (IA Assistant)
**Version**: 1.0
