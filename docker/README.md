# Configuration Docker pour MartialComp

Cette configuration Docker permet de développer et déployer MartialComp dans des environnements isolés et reproductibles.

## 🚀 Démarrage rapide

### Prérequis
- [Docker](https://www.docker.com/products/docker-desktop) installé
- [Docker Compose](https://docs.docker.com/compose/install/) installé

### Environnement de développement

```bash
# Démarrer l'environnement de développement
./scripts/start_dev.sh

# Ou manuellement
cd docker/dev
docker-compose up -d

# Créer un superutilisateur
docker-compose exec web python manage.py createsuperuser --settings=config.settings.development
```

L'application sera accessible sur http://localhost:8000

### Environnement de staging

```bash
# Modifier les variables d'environnement dans docker/staging/.env
# Puis démarrer
./scripts/start_staging.sh

# Ou manuellement
cd docker/staging
docker-compose up -d
```

L'application sera accessible sur http://localhost

## 📁 Structure

```
docker/
├── dev/                    # Environnement de développement
│   ├── Dockerfile
│   └── docker-compose.yml
├── staging/                # Environnement de pré-production
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env
│   └── nginx/
│       └── default.conf
└── prod/                   # Environnement de production (à configurer)
```

## 🛠️ Commandes utiles

### Scripts automatisés

```bash
# Démarrer le développement
./scripts/start_dev.sh

# Démarrer le staging
./scripts/start_staging.sh

# Importer des données de production dans staging
./scripts/import_prod_data.sh backup.dump media.tar.gz

# Diagnostic d'authentification
docker-compose exec web python scripts/auth_diagnosis.py

# Utilitaires Docker
./scripts/docker_utils.sh help
```

### Commandes Docker Compose

```bash
# Voir les logs
docker-compose logs -f

# Exécuter des commandes Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py createsuperuser

# Accéder au shell du conteneur
docker-compose exec web bash

# Arrêter les services
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v
```

### Gestion de la base de données

```bash
# Créer une sauvegarde
docker-compose exec db pg_dump -U martialcomp martialcomp_dev > backup.sql

# Restaurer une sauvegarde
cat backup.sql | docker-compose exec -T db psql -U martialcomp martialcomp_dev

# Accéder à la console PostgreSQL
docker-compose exec db psql -U martialcomp martialcomp_dev
```

## ⚙️ Configuration

### Variables d'environnement

#### Développement
Les variables sont définies directement dans `docker/dev/docker-compose.yml`.

#### Staging
Modifiez le fichier `docker/staging/.env`:

```bash
DJANGO_SECRET_KEY=votre_cle_secrete_staging
DB_PASSWORD=mot_de_passe_securise
```

#### Production
Créez `docker/prod/.env` avec:

```bash
DJANGO_SECRET_KEY=cle_secrete_production_tres_securisee
DB_NAME=martialcomp_prod
DB_USER=martialcomp
DB_PASSWORD=mot_de_passe_tres_securise
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
BASE_URL=https://votre-domaine.com
EMAIL_HOST=smtp.votre-provider.com
EMAIL_HOST_USER=votre-email@domaine.com
EMAIL_HOST_PASSWORD=mot_de_passe_email
```

### Settings Django

La configuration utilise des settings modulaires:

- `config/settings/base.py` - Paramètres communs
- `config/settings/development.py` - Développement
- `config/settings/staging.py` - Pré-production
- `config/settings/production.py` - Production

## 🔧 Développement

### Hot reload
En développement, le code est monté en volume, permettant le rechargement automatique lors des modifications.

### Debug
Django Debug Toolbar est disponible en développement sur http://localhost:8000/__debug__/

### Tests
```bash
# Exécuter les tests
docker-compose exec web python manage.py test --settings=config.settings.development

# Avec coverage
docker-compose exec web coverage run --source='.' manage.py test --settings=config.settings.development
docker-compose exec web coverage report
```

## 📊 Monitoring

### Logs
Les logs sont disponibles via:
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis
```

### Métriques
- PostgreSQL: Accessible sur le port 5432
- Redis: Accessible sur le port 6379
- Nginx (staging/prod): Logs dans `/var/log/nginx/`

## 🚨 Dépannage

### Problèmes courants

#### Base de données non accessible
```bash
# Vérifier que PostgreSQL est démarré
docker-compose ps

# Voir les logs
docker-compose logs db

# Redémarrer le service
docker-compose restart db
```

#### Problèmes de permissions
```bash
# Reconstruire l'image
docker-compose build --no-cache web

# Vérifier les permissions des volumes
docker-compose exec web ls -la /app/
```

#### Migrations
```bash
# Réinitialiser les migrations (ATTENTION: perte de données)
docker-compose exec web python manage.py migrate --fake-initial

# Appliquer une migration spécifique
docker-compose exec web python manage.py migrate app_name migration_name
```

### Diagnostic
Utilisez le script de diagnostic pour vérifier la configuration:

```bash
docker-compose exec web python scripts/auth_diagnosis.py
```

## 🔒 Sécurité

### Développement
- DEBUG activé
- Secret key par défaut
- ALLOWED_HOSTS ouvert
- SSL désactivé

### Production
- DEBUG désactivé
- Secret key sécurisée
- ALLOWED_HOSTS restreint
- SSL obligatoire
- Headers de sécurité activés

## 📚 Ressources

- [Documentation Docker](https://docs.docker.com/)
- [Documentation Django](https://docs.djangoproject.com/)
- [Guide Docker original](../docker-guide.md)

Pour plus d'aide, consultez le guide complet dans `docker-guide.md`.