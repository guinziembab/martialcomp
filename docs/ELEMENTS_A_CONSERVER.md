# Éléments à Conserver lors du Nettoyage de la Production

## Vue d'Ensemble

Ce document détaille tous les éléments qui doivent être conservés lors du nettoyage complet de la production avant la synchronisation avec l'environnement de développement.

## 📁 DOSSIERS DE CONFIGURATION (À CONSERVER)

### Fichiers de Configuration Django

- `config/production.py` - Configuration spécifique à la production
- `config/local.py` - Configuration locale (si existante)
- `production.env` - Variables d'environnement de production
- `.env` - Variables d'environnement générales

### Fichiers de Configuration Serveur

- `vhost.conf` - Configuration Nginx/Apache
- `passenger_wsgi.py` - Configuration Passenger (si utilisé)
- `nginx.conf` - Configuration Nginx personnalisée
- `gunicorn.conf` - Configuration Gunicorn

### Scripts de Maintenance

- `*.sh` - Tous les scripts de maintenance et d'administration
- `*.sql` - Scripts de base de données et dumps

## 📁 DOSSIERS DE DONNÉES (À CONSERVER)

### Fichiers Uploadés par les Utilisateurs

- `media/` - Fichiers média uploadés
- `uploads/` - Fichiers uploadés généraux
- `user_uploads/` - Uploads spécifiques aux utilisateurs
- `documents/` - Documents importants
- `certificates/` - Certificats et documents officiels
- `images/` - Images uploadées
- `videos/` - Vidéos uploadées

### Données Importantes

- `backups/` - Backups de l'application
- `production_*/` - Backups de production
- `martialcomp_backup*` - Backups spécifiques au projet

## 📁 DOSSIERS DE LOGS (À CONSERVER)

### Logs de l'Application

- `logs/` - Dossier principal des logs
- `*.log` - Fichiers de logs individuels
- `django.log` - Logs Django spécifiques
- `gunicorn.log` - Logs Gunicorn
- `nginx.log` - Logs Nginx

## 📁 DOSSIERS DE SÉCURITÉ (À CONSERVER)

### Certificats et SSL

- `ssl/` - Certificats SSL
- `certificates/` - Certificats divers
- `.htaccess` - Configuration Apache de sécurité
- `.htpasswd` - Mots de passe Apache

### Clés et Secrets

- `.ssh/` - Clés SSH (si présentes)
- `keys/` - Clés de chiffrement
- `secrets/` - Secrets de l'application

## 🗑️ DOSSIERS À SUPPRIMER

### Cache et Fichiers Temporaires

- `__pycache__/` - Cache Python
- `*.pyc` - Fichiers compilés Python
- `.pyo` - Fichiers optimisés Python
- `temp_*` - Fichiers temporaires
- `tmp/` - Dossier temporaire

### Environnements Virtuels

- `.venv/` - Environnement virtuel Python
- `venv/` - Environnement virtuel alternatif
- `temp_venv/` - Environnement virtuel temporaire
- `env/` - Environnement virtuel

### Développement et Debug

- `.git/` - Repository Git
- `node_modules/` - Modules Node.js
- `bower_components/` - Composants Bower
- `vendor/` - Dépendances PHP

### Fichiers de Développement

- `*.md` - Documentation Markdown
- `*.txt` - Fichiers texte
- `*.json` - Fichiers de configuration dev
- `*.yaml` - Fichiers YAML de dev
- `*.yml` - Fichiers YAML alternatifs

### Scripts de Debug et Test

- `test_*` - Scripts de test
- `debug_*` - Scripts de debug
- `fix_*` - Scripts de correction
- `cleanup_*` - Scripts de nettoyage
- `sync_*` - Scripts de synchronisation
- `rollback_*` - Scripts de rollback
- `diagnostic_*` - Scripts de diagnostic
- `execute_*` - Scripts d'exécution

### Documentation et Guides

- `GUIDE_*` - Guides de documentation
- `SYNC_*` - Documentation de synchronisation
- `RAPPORT_*` - Rapports divers
- `CLEANUP_*` - Documentation de nettoyage
- `CONFIGURATION_*` - Documentation de configuration
- `DEPLOY_*` - Documentation de déploiement
- `QUICK_FIX_*` - Corrections rapides

### Fichiers Spécifiques au Développement

- `*.bat` - Scripts Windows
- `docs/` - Documentation
- `scripts/` - Scripts de développement
- `deployment/` - Scripts de déploiement
- `archive/` - Archives
- `packages/` - Packages
- `Princing Model/` - Modèles de prix

### Fichiers Régénérés

- `staticfiles/` - Fichiers statiques (seront régénérés)
- `locale/` - Traductions (seront resynchronisées)
- `collectstatic/` - Fichiers collectés

## 🔧 Processus de Nettoyage

### Étape 1: Sauvegarde

```bash
# Créer un backup complet
./clean_production_complete.sh backup
```

### Étape 2: Analyse

```bash
# Analyser la structure actuelle
./clean_production_complete.sh analyze
```

### Étape 3: Nettoyage

```bash
# Nettoyage complet
./clean_production_complete.sh clean-complete

# OU nettoyage sélectif
./clean_production_complete.sh clean-selective
```

### Étape 4: Vérification

```bash
# Vérifier la structure après nettoyage
ssh root@martialcomp.com "cd /var/www/vhosts/martialcomp.com && ls -la"
```

## ⚠️ Points d'Attention

### Avant le Nettoyage

1. **Backup obligatoire** - Toujours créer un backup complet
2. **Vérification des données** - S'assurer qu'aucune donnée importante n'est perdue
3. **Arrêt des services** - Arrêter nginx et gunicorn avant nettoyage
4. **Vérification de l'espace** - S'assurer qu'il y a assez d'espace pour les backups

### Pendant le Nettoyage

1. **Surveillance** - Surveiller le processus de nettoyage
2. **Logs** - Consulter les logs pour détecter les erreurs
3. **Interruption** - Ne pas interrompre le processus

### Après le Nettoyage

1. **Vérification** - Vérifier que les éléments importants sont conservés
2. **Redémarrage** - Redémarrer les services
3. **Tests** - Tester le fonctionnement de base

## 🔄 Restauration

En cas de problème, les éléments conservés peuvent être restaurés :

```bash
# Restaurer les éléments conservés
./clean_production_complete.sh restore

# OU restaurer un backup complet
./rollback_production.sh complete BACKUP_DATE
```

## 📊 Vérification Post-Nettoyage

### Structure Attendue

```
/var/www/vhosts/martialcomp.com/
├── config/
│   ├── production.py
│   └── local.py
├── media/
├── uploads/
├── logs/
├── backups/
├── vhost.conf
├── passenger_wsgi.py
├── production.env
└── .env
```

### Commandes de Vérification

```bash
# Vérifier la structure
ssh root@martialcomp.com "cd /var/www/vhosts/martialcomp.com && tree -L 2"

# Vérifier les permissions
ssh root@martialcomp.com "cd /var/www/vhosts/martialcomp.com && ls -la"

# Vérifier l'espace disque
ssh root@martialcomp.com "df -h /var/www/vhosts/martialcomp.com"
```

---

**Note**: Ce document doit être mis à jour en fonction des évolutions du projet et des retours d'expérience.
