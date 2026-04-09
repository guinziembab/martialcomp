# Instructions de déploiement manuel - Import/Export Pratiquants

## Fichiers modifiés

1. `apps/competitions/views/club/import_export.py` - Logique d'import complète
2. `apps/competitions/templates/competitions/club/import_export.html` - Template amélioré
3. `config/settings/production.py` - Configuration CSRF pour production

## Déploiement automatique

Exécuter le script de déploiement :
```bash
./DEPLOY_IMPORT_EXPORT_PRODUCTION.sh
```

## Déploiement manuel

### 1. Se connecter au serveur de production

```bash
ssh pierrep99@martialcomp.com
```

### 2. Créer une sauvegarde

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
mkdir -p backups/$(date +%Y%m%d_%H%M%S)_import_export
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)_import_export"

# Sauvegarder les fichiers existants
cp apps/competitions/views/club/import_export.py $BACKUP_DIR/
cp apps/competitions/templates/competitions/club/import_export.html $BACKUP_DIR/
cp config/settings/production.py $BACKUP_DIR/
```

### 3. Copier les fichiers depuis votre machine locale

Depuis votre machine locale (dans le répertoire du projet) :

```bash
# Copier import_export.py
scp apps/competitions/views/club/import_export.py \
    pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/

# Copier le template
scp apps/competitions/templates/competitions/club/import_export.html \
    pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/

# Copier production.py
scp config/settings/production.py \
    pierrep99@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/config/settings/
```

### 4. Redémarrer le serveur Django

```bash
# Option 1: Redémarrer Gunicorn (recommandé)
sudo systemctl restart gunicorn

# Option 2: Si Gunicorn n'est pas en service systemd
sudo pkill -HUP gunicorn

# Option 3: Toucher wsgi.py pour rechargement automatique
touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py
```

### 5. Vérifier les permissions

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
chown -R www-data:www-data apps/competitions/views/club/import_export.py
chown -R www-data:www-data apps/competitions/templates/competitions/club/import_export.html
chown -R www-data:www-data config/settings/production.py
chmod 644 apps/competitions/views/club/import_export.py
chmod 644 apps/competitions/templates/competitions/club/import_export.html
chmod 644 config/settings/production.py
```

### 6. Vérifier les logs

```bash
# Voir les logs en temps réel
tail -f /var/log/django/martialcomp.log

# Voir les dernières erreurs
grep -i error /var/log/django/martialcomp.log | tail -20
```

## Tests après déploiement

1. **Tester l'import** :
   - Se connecter avec le compte `KP_admin`
   - Aller sur : `https://martialcomp.com/fr/competitions/club/import-export/#import-section`
   - Uploader le fichier `KP_admin_users.xlsx`
   - Vérifier les messages de succès/erreur

2. **Vérifier la configuration CSRF** :
   - L'erreur CSRF 403 ne devrait plus apparaître
   - Le token CSRF devrait être présent dans le formulaire

3. **Tester différents formats de date** :
   - Créer un fichier de test avec différentes dates
   - Vérifier que toutes les dates sont correctement parsées

## En cas de problème

### Restaurer depuis la sauvegarde

```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
BACKUP_DIR="backups/YYYYMMDD_HHMMSS_import_export"  # Remplacer par la date réelle

cp $BACKUP_DIR/import_export.py apps/competitions/views/club/
cp $BACKUP_DIR/import_export.html apps/competitions/templates/competitions/club/
cp $BACKUP_DIR/production.py config/settings/

# Redémarrer le serveur
sudo systemctl restart gunicorn
```

### Vérifier les erreurs

```bash
# Logs Django
tail -100 /var/log/django/martialcomp.log

# Logs Nginx (si erreur 502/503)
tail -100 /var/log/nginx/error.log

# Logs Gunicorn
journalctl -u gunicorn -n 50
```

## Améliorations déployées

### 1. Configuration CSRF
- ✅ Ajout de `CSRF_TRUSTED_ORIGINS` pour `martialcomp.com`
- ✅ Configuration des cookies CSRF pour HTTPS

### 2. Import Excel
- ✅ Fonction d'import complète avec validation
- ✅ Support de multiples formats de date
- ✅ Détection automatique des colonnes
- ✅ Gestion des erreurs détaillée

### 3. Gestion des dates
- ✅ Support de 11+ formats de date différents
- ✅ Détection automatique de l'ordre jour/mois
- ✅ Gestion des dates ambiguës
- ✅ Support des années à 2 chiffres

### 4. Template
- ✅ Vérification JavaScript du token CSRF
- ✅ Messages d'erreur améliorés
- ✅ Formulaire avec action explicite

## Notes importantes

- ⚠️ **Redémarrer le serveur est obligatoire** pour que les changements de `production.py` prennent effet
- ⚠️ **Vérifier les permissions** des fichiers copiés
- ⚠️ **Tester immédiatement** après le déploiement pour détecter les problèmes rapidement
- ⚠️ **Garder la sauvegarde** jusqu'à confirmation que tout fonctionne
