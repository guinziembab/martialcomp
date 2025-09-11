# 🚀 Guide d'Installation MartialComp - IONOS Debian avec Plesk

## 📋 Vue d'ensemble

Ce guide détaille l'installation complète du système de synchronisation des environnements MartialComp sur **IONOS Debian avec Plesk**, en adaptant la configuration à votre architecture existante.

## 🎯 Architecture Actuelle Identifiée

```
┌─────────────────────────────────────────────────────┐
│                 Serveur IONOS Debian                │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │    Nginx    │──│  Gunicorn   │──│    Django   │  │
│  │  (Plesk)    │  │ (Port 8001) │  │  Application│  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│          │               │               │          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Fichiers   │  │PostgreSQL/  │  │   Redis     │  │
│  │ Statiques   │  │   MySQL     │  │ (optionnel) │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────┘
```

## 🛠️ Prérequis

- **Serveur** : IONOS Debian avec Plesk
- **Accès** : Root SSH
- **Python** : 3.9+ avec venv
- **Base de données** : PostgreSQL ou MySQL
- **Gunicorn** : Déjà configuré sur port 8001
- **Nginx** : Géré par Plesk

## 🔧 Installation Étape par Étape

### 1. Préparation du Serveur

```bash
# Connexion SSH au serveur IONOS
ssh root@your-server-ip

# Mise à jour du système
apt update && apt upgrade -y

# Installation des outils nécessaires
apt install -y git curl wget htop vim bc mailutils
```

### 2. Configuration de Base

```bash
# Naviguer vers le répertoire de l'application
cd /var/www/vhosts/martialcomp.com/httpdocs

# Créer les répertoires nécessaires
mkdir -p logs scripts backups

# Ajuster les permissions
chown -R www-data:www-data .
chmod -R 755 .
```

### 3. Installation des Fichiers de Configuration

```bash
# Télécharger les fichiers de configuration
wget -O config/settings/production.py https://raw.githubusercontent.com/your-repo/ionos-production-config.py

# Configuration Gunicorn
wget -O gunicorn.conf.py https://raw.githubusercontent.com/your-repo/ionos-gunicorn-config.py

# Service systemd
wget -O /etc/systemd/system/martialcomp.service https://raw.githubusercontent.com/your-repo/ionos-systemd-service.service

# Recharger systemd
systemctl daemon-reload
```

### 4. Configuration Nginx dans Plesk

```bash
# Backup de la configuration actuelle
cp /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup

# Appliquer la nouvelle configuration
cp /root/ionos-nginx-config.conf /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf

# Tester et recharger Nginx
nginx -t && systemctl reload nginx
```

### 5. Déploiement avec le Script Automatisé

```bash
# Copier le script de déploiement
cp /root/ionos-deployment-script.sh /var/www/vhosts/martialcomp.com/httpdocs/deploy.sh
chmod +x /var/www/vhosts/martialcomp.com/httpdocs/deploy.sh

# Exécuter le déploiement
cd /var/www/vhosts/martialcomp.com/httpdocs
./deploy.sh
```

### 6. Configuration des Variables d'Environnement

```bash
# Créer le fichier .env
cp /root/env-example .env

# Éditer avec vos valeurs
nano .env

# Exemple de configuration IONOS
cat > .env << 'EOF'
# Configuration IONOS
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com,*.martialcomp.com

# Base de données
DB_ENGINE=postgresql
DB_NAME=martialcomp
DB_USER=martialcomp
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Email IONOS
EMAIL_HOST=smtp.ionos.fr
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=your-email-password

# Autres services
STRIPE_PUBLISHABLE_KEY=pk_live_your-key
STRIPE_SECRET_KEY=sk_live_your-key
DEEPL_API_KEY=your-deepl-key
EOF
```

### 7. Installation des Scripts de Synchronisation

```bash
# Copier les scripts
cp /root/ionos-sync-script.sh scripts/sync.sh
cp /root/ionos-monitoring-script.sh scripts/monitoring.sh

# Rendre exécutables
chmod +x scripts/*.sh

# Tester le script de synchronisation
./scripts/sync.sh main
```

### 8. Configuration des Tâches Automatisées

```bash
# Configurer les tâches cron
cp /root/ionos-cron-setup.sh /tmp/cron-setup.sh
chmod +x /tmp/cron-setup.sh
/tmp/cron-setup.sh

# Vérifier les tâches cron
crontab -l
```

## 🔄 Workflow de Synchronisation

### 1. Synchronisation Manuelle

```bash
# Synchroniser depuis la branche main
cd /var/www/vhosts/martialcomp.com/httpdocs
./scripts/sync.sh main

# Synchroniser depuis staging
./scripts/sync.sh staging
```

### 2. Synchronisation Automatique

Les tâches cron automatisent :
- **Monitoring** : Toutes les 5 minutes
- **Backup** : Quotidien à 2h
- **Maintenance** : Hebdomadaire dimanche à 3h
- **SSL Check** : Mensuel le 1er à 10h

### 3. Déploiement d'Urgence

```bash
# Rollback rapide
cd /var/www/vhosts/martialcomp.com/httpdocs
git checkout HEAD~1
systemctl restart martialcomp
```

## 🛡️ Sécurité et Maintenance

### 1. Permissions Recommandées

```bash
# Ajuster les permissions
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs
chmod -R 644 /var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py
```

### 2. Monitoring

```bash
# Vérifier les services
systemctl status martialcomp
systemctl status nginx
systemctl status postgresql

# Consulter les logs
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
tail -f /var/log/gunicorn/error.log
tail -f /var/log/nginx/error.log
```

### 3. Backup et Restauration

```bash
# Backup manuel
./scripts/backup-daily.sh

# Restauration depuis backup
cd /var/www/vhosts/martialcomp.com/httpdocs
tar -xzf backups/files_daily_YYYYMMDD.tar.gz

# Restauration base de données
psql -U martialcomp -d martialcomp < backups/db_daily_YYYYMMDD.sql
```

## 📊 Tests et Vérification

### 1. Tests de Santé

```bash
# Test application locale
curl -f http://localhost:8001/health/

# Test HTTPS
curl -f https://martialcomp.com/health/

# Test base de données
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py shell -c "from django.db import connection; connection.ensure_connection(); print('DB OK')"
```

### 2. Tests de Performance

```bash
# Temps de réponse
curl -w "@curl-format.txt" -o /dev/null -s https://martialcomp.com/

# Charge serveur
htop
free -h
df -h
```

## 🔧 Dépannage

### 1. Problèmes Courants

**Service Gunicorn ne démarre pas :**
```bash
# Vérifier les logs
journalctl -u martialcomp -f

# Vérifier la configuration
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py check --deploy
```

**Erreurs de permissions :**
```bash
# Corriger les permissions
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs
```

**Problèmes de base de données :**
```bash
# Vérifier la connexion
psql -U martialcomp -d martialcomp -c "SELECT 1;"

# Migrations
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py migrate
```

### 2. Commandes Utiles

```bash
# Redémarrer tous les services
systemctl restart martialcomp
systemctl reload nginx

# Vérifier l'état
systemctl status martialcomp nginx postgresql

# Consulter les processus
ps aux | grep gunicorn
ps aux | grep nginx
```

## 📋 Checklist d'Installation

- [ ] Serveur IONOS préparé
- [ ] Fichiers de configuration appliqués
- [ ] Service systemd configuré
- [ ] Configuration Nginx mise à jour
- [ ] Variables d'environnement définies
- [ ] Scripts de synchronisation installés
- [ ] Tâches cron configurées
- [ ] Tests de santé réussis
- [ ] Monitoring actif
- [ ] Backup automatique configuré
- [ ] SSL vérifiés
- [ ] Permissions correctes
- [ ] Documentation mise à jour

## 🎯 Résultats Attendus

Après l'installation, vous devriez avoir :

✅ **Service Gunicorn** fonctionnel sur port 8001
✅ **Nginx** configuré comme proxy inverse
✅ **Application Django** accessible via HTTPS
✅ **Monitoring automatique** toutes les 5 minutes
✅ **Backup quotidien** à 2h du matin
✅ **Synchronisation Git** manuelle et automatique
✅ **Logs centralisés** et rotationnels
✅ **Alertes SSL** avant expiration
✅ **Maintenance automatique** hebdomadaire

## 🆘 Support

En cas de problème :
1. Consulter les logs : `/var/www/vhosts/martialcomp.com/httpdocs/logs/`
2. Vérifier les services : `systemctl status martialcomp nginx`
3. Tester la configuration : `python manage.py check --deploy`
4. Contacter l'équipe technique avec les logs d'erreur

---

Votre environnement MartialComp est maintenant optimisé pour IONOS avec synchronisation automatique ! 🚀