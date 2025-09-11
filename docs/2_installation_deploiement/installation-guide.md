# 🚀 Guide d'Installation - Synchronisation des Environnements MartialComp

## 📋 Vue d'ensemble

Ce guide détaille l'installation complète du système de synchronisation des environnements pour MartialComp avec Git et Docker.

## 🎯 Prérequis

### Système
- **OS** : Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Docker** : Version 20.10+
- **Docker Compose** : Version 2.0+
- **Git** : Version 2.20+
- **Python** : Version 3.9+

### Accès requis
- **GitHub** : Accès au repository MartialComp
- **Serveur Production** : Accès SSH avec sudo
- **Serveur Staging** : Accès SSH avec sudo (optionnel)
- **Plesk** : Accès administrateur

## 🔧 Installation Étape par Étape

### 1. Préparation du Repository

```bash
# Cloner le repository
git clone https://github.com/guinziembab/martialcomp.git
cd martialcomp

# Créer les branches nécessaires
git checkout -b develop
git checkout -b staging
git checkout main
```

### 2. Création de la Structure

```bash
# Créer la structure des répertoires
mkdir -p docker/{dev,staging,prod}
mkdir -p .github/workflows
mkdir -p requirements
mkdir -p scripts/{sync,deploy}
mkdir -p environments

# Copier les fichiers de configuration
cp /root/docker-compose.dev.yml ./docker-compose.dev.yml
cp /root/docker-compose.staging.yml ./docker-compose.staging.yml
cp /root/docker-compose.prod.yml ./docker-compose.prod.yml
```

### 3. Configuration Docker

#### Dockerfile de développement
```bash
# Créer le Dockerfile de développement
cat > docker/dev/Dockerfile << 'EOF'
FROM python:3.9-slim

# Configuration et installation des dépendances
# [Contenu du Dockerfile.dev]
EOF
```

#### Dockerfile de production
```bash
# Créer le Dockerfile de production
cat > docker/prod/Dockerfile << 'EOF'
FROM python:3.9-slim

# Configuration optimisée pour la production
# [Contenu du Dockerfile.prod]
EOF
```

### 4. Configuration des Requirements

```bash
# Requirements de base
cat > requirements/base.txt << 'EOF'
# [Contenu du requirements-base.txt]
EOF

# Requirements de développement
cat > requirements/dev.txt << 'EOF'
-r base.txt
# [Contenu du requirements-dev.txt]
EOF

# Requirements de production
cat > requirements/prod.txt << 'EOF'
-r base.txt
# [Contenu du requirements-prod.txt]
EOF
```

### 5. Configuration Django

```bash
# Créer les configurations Django
mkdir -p config/settings

# Settings de développement
cat > config/settings/development.py << 'EOF'
# [Contenu du settings-development.py]
EOF

# Settings de production
cat > config/settings/production.py << 'EOF'
# [Contenu du settings-production.py]
EOF
```

### 6. Variables d'Environnement

```bash
# Créer le fichier d'exemple
cp /root/env-example ./.env.example

# Créer les fichiers d'environnement
cp .env.example .env.dev
cp .env.example .env.staging
cp .env.example .env.prod

# Éditer chaque fichier avec les valeurs appropriées
nano .env.dev
nano .env.staging
nano .env.prod
```

### 7. Scripts de Synchronisation

```bash
# Script de synchronisation DB
cp /root/sync-db-to-dev.sh ./scripts/sync/sync-db-to-dev.sh
chmod +x ./scripts/sync/sync-db-to-dev.sh

# Script de synchronisation média
cat > scripts/sync/sync-media-to-dev.sh << 'EOF'
#!/bin/bash
# Script de synchronisation des médias prod -> dev

PROD_HOST="your-production-server.com"
PROD_USER="root"
PROD_MEDIA_PATH="/var/www/vhosts/martialcomp.com/httpdocs/media"
LOCAL_MEDIA_PATH="./media"

echo "🔄 Synchronisation des médias prod -> dev..."
rsync -avz --progress $PROD_USER@$PROD_HOST:$PROD_MEDIA_PATH/ $LOCAL_MEDIA_PATH/

echo "✅ Médias synchronisés avec succès!"
EOF

chmod +x ./scripts/sync/sync-media-to-dev.sh
```

### 8. Configuration GitHub Actions

```bash
# Créer le workflow GitHub Actions
mkdir -p .github/workflows
cp /root/github-actions-deploy.yml ./.github/workflows/deploy.yml
```

### 9. Configuration Plesk

```bash
# Créer la configuration Plesk
cp /root/plesk-adaptation.md ./docs/plesk-setup.md

# Script de déploiement Plesk
cat > scripts/deploy/deploy-plesk.sh << 'EOF'
#!/bin/bash
# Script de déploiement spécifique pour Plesk
# [Contenu du script de déploiement]
EOF

chmod +x ./scripts/deploy/deploy-plesk.sh
```

## 🚀 Déploiement Initial

### 1. Environnement de Développement

```bash
# Créer les répertoires nécessaires
mkdir -p logs media staticfiles

# Démarrer les services
docker-compose -f docker-compose.dev.yml up -d

# Vérifier que tout fonctionne
docker-compose -f docker-compose.dev.yml ps
curl http://localhost:8000/health/
```

### 2. Environnement de Staging

```bash
# Sur le serveur de staging
scp -r ./martialcomp staging-server:/var/www/

# Connecter au serveur de staging
ssh staging-server
cd /var/www/martialcomp

# Configurer les variables d'environnement
cp .env.example .env
nano .env  # Configurer les valeurs de staging

# Démarrer les services
docker-compose -f docker-compose.staging.yml up -d

# Vérifier
curl http://localhost:8001/health/
```

### 3. Environnement de Production

```bash
# Sur le serveur de production avec Plesk
scp -r ./martialcomp production-server:/var/www/vhosts/martialcomp.com/httpdocs/

# Connecter au serveur de production
ssh production-server
cd /var/www/vhosts/martialcomp.com/httpdocs

# Configurer les variables d'environnement
cp .env.example .env
nano .env  # Configurer les valeurs de production

# Configurer Nginx dans Plesk
# [Suivre les instructions du guide Plesk]

# Démarrer les services
docker-compose -f docker-compose.prod.yml up -d

# Vérifier
curl http://localhost:8002/health/
```

## 🔧 Configuration des Secrets GitHub

```bash
# Ajouter les secrets dans GitHub
# Settings -> Secrets and variables -> Actions

# Secrets requis :
DOCKER_USERNAME=your-docker-username
DOCKER_PASSWORD=your-docker-password
STAGING_SSH_KEY=your-staging-ssh-private-key
STAGING_USERNAME=your-staging-username
STAGING_HOST=your-staging-server.com
PRODUCTION_SSH_KEY=your-production-ssh-private-key
PRODUCTION_USERNAME=your-production-username
PRODUCTION_HOST=your-production-server.com
SLACK_WEBHOOK_URL=your-slack-webhook-url
```

## 📊 Vérification de l'Installation

### Tests Automatiques

```bash
# Tester l'environnement de développement
docker-compose -f docker-compose.dev.yml exec web python manage.py test

# Tester la synchronisation des données
./scripts/sync/sync-db-to-dev.sh

# Tester la synchronisation des médias
./scripts/sync/sync-media-to-dev.sh
```

### Tests Manuels

```bash
# Vérifier les services
docker-compose -f docker-compose.dev.yml ps

# Vérifier l'accès à l'application
curl http://localhost:8000/
curl http://localhost:8000/admin/
curl http://localhost:8000/api/health/

# Vérifier les logs
docker-compose -f docker-compose.dev.yml logs web
```

## 🔄 Workflow de Développement

### 1. Développement Local

```bash
# Créer une branche de fonctionnalité
git checkout develop
git checkout -b feature/nouvelle-fonctionnalite

# Développer la fonctionnalité
# [Faire vos modifications]

# Tester localement
docker-compose -f docker-compose.dev.yml exec web python manage.py test

# Commiter et pousser
git add .
git commit -m "Ajout de nouvelle fonctionnalité"
git push origin feature/nouvelle-fonctionnalite
```

### 2. Déploiement sur Staging

```bash
# Merger la fonctionnalité dans staging
git checkout staging
git merge feature/nouvelle-fonctionnalité
git push origin staging

# GitHub Actions déploie automatiquement sur staging
```

### 3. Déploiement en Production

```bash
# Merger staging dans main
git checkout main
git merge staging
git push origin main

# GitHub Actions déploie automatiquement en production
```

## 🛠️ Maintenance et Monitoring

### Sauvegardes Automatiques

```bash
# Ajouter au crontab
crontab -e

# Backup quotidien
0 2 * * * /var/www/vhosts/martialcomp.com/httpdocs/scripts/backup-daily.sh

# Monitoring
*/5 * * * * /var/www/vhosts/martialcomp.com/httpdocs/scripts/monitor-health.sh
```

### Monitoring des Logs

```bash
# Surveiller les logs en temps réel
docker-compose -f docker-compose.prod.yml logs -f web

# Analyser les logs d'erreurs
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
```

## 🆘 Résolution des Problèmes

### Problèmes Courants

1. **Services Docker qui ne démarrent pas**
   ```bash
   docker-compose down
   docker system prune -a
   docker-compose up -d --build
   ```

2. **Problèmes de permissions**
   ```bash
   sudo chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs
   sudo chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs
   ```

3. **Problèmes de base de données**
   ```bash
   docker-compose exec db psql -U martialcomp -d martialcomp_db
   # Vérifier la connexion et les données
   ```

### Rollback d'Urgence

```bash
# Revenir à la version précédente
git checkout main
git revert HEAD
git push origin main

# Ou utiliser un tag spécifique
git checkout v1.0.0
git push origin main
```

## 📚 Documentation Complémentaire

- **Guide Plesk** : `docs/plesk-setup.md`
- **Guide Docker** : `docs/docker-guide.md`
- **Guide API** : `docs/api-documentation.md`
- **Guide de Déploiement** : `docs/deployment-guide.md`

## ✅ Checklist d'Installation

- [ ] Repository cloné et branches créées
- [ ] Structure Docker configurée
- [ ] Requirements installés
- [ ] Variables d'environnement configurées
- [ ] Scripts de synchronisation testés
- [ ] GitHub Actions configurées
- [ ] Plesk configuré
- [ ] Tests automatiques passants
- [ ] Monitoring activé
- [ ] Backups configurés
- [ ] Documentation mise à jour

Votre environnement de synchronisation MartialComp est maintenant prêt ! 🎉