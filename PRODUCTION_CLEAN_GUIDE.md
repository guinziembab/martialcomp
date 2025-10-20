# Guide de Nettoyage et Réinstallation Production

## 📋 Vue d'ensemble
Ce guide documente la procédure complète pour nettoyer et réinstaller MartialComp en production.

## 🚨 Éléments à Préserver (IMPORTANT)

### 1. Base de données
- **OBLIGATOIRE**: Sauvegarder la base PostgreSQL avant tout nettoyage
- Commande: `pg_dump -U user -d martialcomp_prod > backup_db.sql`

### 2. Uploads utilisateurs (media/)
- Photos de profil
- Documents uploadés
- Logos des clubs
- Tout contenu généré par les utilisateurs

### 3. Configuration sensible
- `.env` ou `.env.production`
- Certificats SSL (si custom)
- Clés API tierces

### 4. Données spécifiques
- Logs d'audit importants
- Rapports financiers générés
- Exports de données

## 📝 Procédure Complète

### Étape 1: Inventaire (5 min)
```bash
# Sur le serveur de production
cd /var/www/vhosts/martialcomp.com/httpdocs
./production_inventory.sh
```

### Étape 2: Sauvegarde (10-30 min)
```bash
# Créer une sauvegarde complète
./production_backup_before_clean.sh
```

### Étape 3: Vérification sauvegarde
```bash
# Vérifier l'intégrité
cd /var/www/vhosts/martialcomp.com/backups
tar -tzf martialcomp_full_backup_*.tar.gz | head -20

# Copier hors serveur (IMPORTANT!)
scp martialcomp_full_backup_*.tar.gz user@backup-server:/path/
```

### Étape 4: Nettoyage
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
./production_clean_all.sh
# Choisir option 1 (sélective) ou 2 (totale)
```

### Étape 5: Nouveau déploiement
```bash
# Transférer le nouveau package
scp martialcomp_production_*.tar.gz user@martialcomp.com:/tmp/

# Extraire
cd /var/www/vhosts/martialcomp.com/httpdocs
tar -xzf /tmp/martialcomp_production_*.tar.gz

# Permissions
./set_plesk_permissions.sh
```

### Étape 6: Configuration
```bash
# Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Dépendances
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env
nano .env  # Configurer avec les bonnes valeurs
```

### Étape 7: Django setup
```bash
# Migrations
python manage.py migrate

# Fichiers statiques
python manage.py collectstatic --noinput

# Superuser (si base vide)
python manage.py createsuperuser
```

### Étape 8: Restauration données
```bash
# Si nécessaire, restaurer la DB
psql -U user -d martialcomp_prod < /backups/backup_db.sql

# Restaurer media si nécessaire
tar -xzf /backups/*_media.tar.gz
```

## 🔍 Points de Vérification

### Avant nettoyage:
- [ ] Sauvegarde DB effectuée
- [ ] Sauvegarde fichiers effectuée
- [ ] Sauvegarde copiée hors serveur
- [ ] Configuration notée (.env)

### Après installation:
- [ ] Site accessible
- [ ] Login admin fonctionnel
- [ ] Upload fichiers OK
- [ ] Pas d'erreur 500
- [ ] Logs accessibles

## 🛟 Restauration d'urgence

Si problème après nettoyage:
```bash
cd /var/www/vhosts/martialcomp.com/httpdocs
rm -rf *
tar -xzf /var/www/vhosts/martialcomp.com/backups/martialcomp_full_backup_*.tar.gz
```

## 📞 Checklist Support

Si vous avez besoin d'aide:
1. Numéro de backup: `martialcomp_full_backup_YYYYMMDD_HHMMSS`
2. Logs d'erreur: `/var/www/vhosts/martialcomp.com/logs/error_log`
3. État Plesk: Screenshot panel Python
4. Commande problématique et message d'erreur exact